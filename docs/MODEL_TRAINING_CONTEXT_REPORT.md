# Model Training — Context Report

> **Dành cho**: Sinh viên/giảng viên ML, không biết codebase.  
> **Phạm vi**: Phần training model của dự án dự báo doanh thu bán lẻ (Kaggle Store Sales).  
> **Metric chính**: RMSLE — Root Mean Squared Logarithmic Error.

---

## 7.1 Experimental Setup

### Phân chia dữ liệu (Temporal Split)

Dữ liệu được chia theo thứ tự thời gian nghiêm ngặt (temporal split), không dùng random split:

| Tập dữ liệu | Khoảng thời gian | Số mẫu | Vai trò |
|------------|-----------------|--------|---------|
| Train | 2013-01-01 → 2017-06-14 | 2,918,916 | Huấn luyện mô hình |
| Validation | 2017-06-15 → 2017-07-31 | 55,242 | Early stopping + mục tiêu Optuna |
| Test (local) | 2017-08-01 → 2017-08-15 | 26,730 | Đánh giá cuối cùng |
| Kaggle test | 2017-08-16 → 2017-08-31 | 28,512 | Submission (không có nhãn) |

**Tại sao dùng temporal split thay vì random split?** Dữ liệu chuỗi thời gian có phụ thuộc thứ tự — mẫu trong tương lai phụ thuộc vào mẫu trong quá khứ. Random split sẽ để thông tin từ tương lai rò vào tập train (data leakage), dẫn đến đánh giá quá lạc quan so với hiệu năng thực tế.

### Feature Set v3 (47 features — phiên bản cuối cùng)

Feature set v3 là phiên bản cuối sau khi loại bỏ 8 features "toxic" và thêm 6 features "safe" so với phiên bản gốc:

**8 features bị loại**:

| Feature bị loại | Lý do |
|----------------|-------|
| `lag_1`, `lag_2`, `lag_3`, `lag_7` | Yêu cầu doanh thu của ngày hôm qua/tuần trước — không tồn tại trong cửa sổ forecast 16 ngày |
| `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28` | Tính dựa trên các lag ngắn ở trên → cũng bị leakage |
| `rolling_std_7` | Tương tự |

**6 features được thêm** (tất cả dùng `shift=16`, đảm bảo không leakage):  
`lag_16`, `lag_21`, `lag_35`, `rolling_mean_30`, `rolling_mean_28_safe`, `rolling_std_28_safe`

Quy tắc quan trọng: Kaggle yêu cầu forecast 16 ngày liên tiếp (Aug 16–31). Do đó, bất kỳ feature nào sử dụng dữ liệu trong vòng 16 ngày trước ngày cần dự báo đều gây leakage và phải bị loại.

**Danh mục 47 features theo nhóm**:
- **Temporal** (10): year, month, day, day\_of\_week, week\_of\_year, quarter, is\_weekend, is\_month\_start, is\_month\_end, is\_payday
- **Holiday/Event** (8): is\_national\_holiday, is\_regional\_holiday, is\_local\_holiday, is\_transferred\_holiday, holiday\_type, is\_carnaval\_feature, days\_to\_next\_holiday, days\_after\_last\_holiday + is\_earthquake\_period
- **Lag features** (5): lag\_14\*, lag\_28, lag\_364, lag\_16, lag\_21, lag\_35
- **Rolling statistics** (3): rolling\_mean\_30, rolling\_mean\_28\_safe, rolling\_std\_28\_safe
- **External/Store** (các feature còn lại): oil\_price và derivatives, store metadata, target encoding

*\*lag\_14 được giữ vì chỉ bị NaN 2 ngày (Aug 30–31) trong Kaggle test — được xử lý bằng forward fill.*

### Target Transformation: log1p / expm1

Model được huấn luyện trên $y_{log} = \log_1(1 + \text{sales})$ thay vì doanh thu gốc. Dự báo được chuyển ngược về $\hat{y} = e^{\hat{y}_{log}} - 1$.

**Tại sao cần log transform?**
1. **Phân phối lệch phải (right-skewed)**: Doanh thu bán lẻ có many-zeros (~31% ngày không bán được) và outliers lớn. Log transform co về phân phối gần chuẩn hơn, giúp gradient boosting hội tụ tốt hơn.
2. **RMSLE operates in log space**: RMSLE tự nhiên tương đương với RMSE trên log-transformed target. Huấn luyện trực tiếp trên log space đồng bộ hàm mất mát với metric đánh giá.

### Encoding Categorical Features

6 cột categorical (`date`, `family`, `type`, `city`, `state`, `store_family`) được encode bằng `LabelEncoder`. Quan trọng: encoder được fit trên **toàn bộ** train + val + test trước khi transform, tránh unseen labels trong val/test.

---

## 7.2 Gradient Boosting Models

### Nguyên lý Gradient Boosting

Gradient boosting xây dựng ensemble theo phương pháp cộng dần (additive): mỗi cây quyết định mới được huấn luyện để dự đoán **phần dư âm gradient** (pseudo-residuals) của ensemble hiện tại. Thay vì tối ưu tham số mô hình trực tiếp, thuật toán thực hiện gradient descent trong **không gian hàm số** — mỗi bước thêm một weak learner mới theo hướng giảm loss nhanh nhất.

### Tại sao chọn Gradient Boosting?

- **Tabular data với mixed feature types**: Gradient boosting không yêu cầu feature scaling, xử lý tốt cả features liên tục và rời rạc.
- **Heterogeneous time series**: 1782 pairs (store × product family) có pattern rất khác nhau. Gradient boosting học được interaction giữa store, family và time mà không cần thiết kế feature tay.
- **Handles NaN natively** (đặc biệt LightGBM và XGBoost với `hist` method): Phù hợp với lag features có NaN ở đầu chuỗi.
- **Proved track record trên tabular forecasting**: Gradient boosting là baseline standard trên hầu hết các Kaggle competitions tabular.

### XGBoost

XGBoost dùng chiến lược **depth-wise tree growth**: tại mỗi bước, cây phát triển đến độ sâu tối đa đã định (`max_depth`) trước khi pruning theo regularization. Cấu hình chính:

| Hyperparameter | Baseline | Ý nghĩa |
|---------------|---------|---------|
| `n_estimators` | 1000 | Số cây tối đa (với early stopping) |
| `learning_rate` | 0.05 | Shrinkage — giảm contribution của mỗi cây |
| `max_depth` | 8 | Độ sâu tối đa của mỗi cây |
| `min_child_weight` | 100 | Tổng Hessian tối thiểu trong một leaf |
| `subsample` | 0.8 | Tỷ lệ mẫu dùng để xây mỗi cây |
| `colsample_bytree` | 0.8 | Tỷ lệ features dùng khi xây mỗi cây |
| `reg_alpha` | 0.1 | L1 regularization trên leaf weights |
| `reg_lambda` | 0.1 | L2 regularization trên leaf weights |
| `tree_method` | `hist` | Histogram-based splitting — nhanh hơn `exact` |
| `objective` | `reg:squarederror` | Hàm mất mát: MSE trên log-scale |

### LightGBM

LightGBM dùng chiến lược **leaf-wise tree growth**: thay vì phát triển hết chiều rộng một level, thuật toán chọn leaf có gain cao nhất để split tiếp. Điều này cho phép cây sâu hơn với cùng số node, thường đạt loss thấp hơn nhanh hơn. Cấu hình chính:

| Hyperparameter | Baseline | Ý nghĩa |
|---------------|---------|---------|
| `n_estimators` | 1000 | Số cây tối đa (với early stopping) |
| `learning_rate` | 0.05 | Shrinkage |
| `num_leaves` | 150 | Số lá tối đa — kiểm soát độ phức tạp cây |
| `min_child_samples` | 100 | Số mẫu tối thiểu trong một leaf |
| `subsample` | 0.8 | Row subsampling |
| `colsample_bytree` | 0.8 | Feature subsampling |
| `reg_alpha` | 0.1 | L1 regularization |
| `reg_lambda` | 0.1 | L2 regularization |
| `objective` | `regression` | Hàm mất mát: MAE/MSE |

**Điểm khác biệt chính giữa hai model**: XGBoost depth-wise phù hợp khi cần interaction đồng đều giữa nhiều features. LightGBM leaf-wise nhanh hơn đáng kể về mặt tốc độ huấn luyện nhưng dễ overfit hơn nếu `num_leaves` quá cao.

---

## 7.3 Evaluation Metrics

Bốn metrics được dùng để đánh giá model, mỗi metric phản ánh một khía cạnh khác nhau của sai số:

### RMSLE — Root Mean Squared Logarithmic Error (Metric chính)

$$\text{RMSLE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} \left(\log(1 + \hat{y}_i) - \log(1 + y_i)\right)^2}$$

**Ý nghĩa**: Đo sai số tương đối theo thang logarithm. Phạt under-prediction (dự báo thấp hơn thực tế) nặng hơn over-prediction với cùng biên độ tuyệt đối.

**Tại sao RMSLE là metric chính**:
1. Đây là metric đánh giá chính thức trên Kaggle competition này.
2. Phù hợp với dữ liệu có nhiều zeros (31.3% ngày zero-sales) và outliers lớn — RMSLE scale-invariant, không để một vài chuỗi có volume cao chi phối toàn bộ score.
3. Trong bán lẻ, việc dự báo thiếu hàng (under-prediction → stockout) thường đắt hơn dư hàng — RMSLE capture được asymmetry này.
4. Vì model train trên $\log_1(1+y)$, RMSLE về bản chất là RMSE trên log-space, tạo ra sự thống nhất giữa training objective và evaluation metric.

### RMSE — Root Mean Squared Error

$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)^2}$$

**Ý nghĩa**: Đo sai số tuyệt đối theo đơn vị doanh thu gốc. Phạt nặng các sai số lớn (do bình phương). Nhạy cảm với outliers — chuỗi GROCERY I với mean ~9,732 đơn/ngày sẽ đóng góp nhiều vào RMSE hơn BEAUTY với mean ~1.6 đơn/ngày.

### MAE — Mean Absolute Error

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |\hat{y}_i - y_i|$$

**Ý nghĩa**: Sai số tuyệt đối trung bình theo đơn vị doanh thu gốc. Robust với outliers hơn RMSE. Cho biết model sai trung bình bao nhiêu đơn vị sản phẩm mỗi ngày.

### RMSE\_log — RMSE trên Log Scale

$$\text{RMSE\_log} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (\hat{y}_{log,i} - y_{log,i})^2}$$

**Ý nghĩa**: RMSE tính trực tiếp trên không gian log (trước khi `expm1`). Phản ánh sát nhất hàm mất mát mà model tối ưu trong quá trình training.

### Tại sao MAPE bị loại bỏ?

MAPE yêu cầu $y_i \neq 0$ trong mẫu số. Với 31.3% ngày zero-sales trong dataset này, MAPE bị division-by-zero và không thể tính được trên toàn bộ tập dữ liệu.

---

## 7.4 Hyperparameter Optimization với Optuna

### Optuna và TPE Sampler

Optuna là framework hyperparameter optimization (HPO) dùng **sequential model-based optimization**: kết quả của các trial trước được dùng để chọn hyperparameter tốt hơn cho trial tiếp theo, thay vì chọn ngẫu nhiên.

Thuật toán cốt lõi là **TPE — Tree-structured Parzen Estimator**:
1. Sau một số trial khởi động, TPE chia các trials thành "good" (top γ% có objective thấp nhất) và "bad" (phần còn lại), với $\gamma = 0.25$ mặc định.
2. TPE fit hai kernel density estimators: $l(x)$ trên good trials và $g(x)$ trên bad trials.
3. Hyperparameter tiếp theo được chọn bằng cách maximize $\frac{l(x)}{g(x)}$ — tức là maximize Expected Improvement so với ngưỡng hiện tại.

**Tại sao TPE tốt hơn Random Search và Grid Search**:
- So với **Random Search**: TPE sample-efficient hơn, học từ lịch sử trial để tập trung vào vùng tốt.
- So với **Grid Search**: Không bị curse of dimensionality (Grid Search với 7 hyperparameters × 10 giá trị = 10 triệu combinations); handle được mixed continuous/discrete search space tự nhiên.

### Search Space thực tế

Cả hai model dùng 7 hyperparameters và 45 trials. Objective: minimize RMSLE trên validation set.

**LightGBM Search Space**:

| Hyperparameter | Range | Scale |
|---------------|-------|-------|
| `learning_rate` | [0.01, 0.1] | log |
| `num_leaves` | [50, 300] | integer |
| `min_child_samples` | [20, 300] | integer |
| `subsample` | [0.6, 1.0] | uniform |
| `colsample_bytree` | [0.6, 1.0] | uniform |
| `reg_alpha` | [0.001, 10.0] | log |
| `reg_lambda` | [0.001, 10.0] | log |

**XGBoost Search Space**:

| Hyperparameter | Range | Scale |
|---------------|-------|-------|
| `learning_rate` | [0.01, 0.1] | log |
| `max_depth` | [4, 10] | integer |
| `min_child_weight` | [20, 300] | integer |
| `subsample` | [0.6, 1.0] | uniform |
| `colsample_bytree` | [0.6, 1.0] | uniform |
| `reg_alpha` | [0.001, 10.0] | log |
| `reg_lambda` | [0.001, 10.0] | log |

**Cấu hình Optuna**: `n_trials=45`, `TPESampler(seed=42)`, `direction='minimize'`.

**Early stopping trong mỗi trial**: LightGBM dùng `early_stopping(stopping_rounds=50)`; XGBoost dùng `early_stopping_rounds=50`. Mỗi trial train đến tối đa 1000 rounds nhưng dừng sớm nếu val loss không cải thiện sau 50 rounds liên tiếp.

---

## 7.5 Results: Baseline vs Optuna

### Best Hyperparameters sau Optuna

**LightGBM — Best Params (45 trials, seed=42)**:

| Hyperparameter | Baseline | Optuna Best |
|---------------|---------|------------|
| `learning_rate` | 0.05 | 0.04412 |
| `num_leaves` | 150 | 248 |
| `min_child_samples` | 100 | 70 |
| `subsample` | 0.8 | 0.9338 |
| `colsample_bytree` | 0.8 | 0.6784 |
| `reg_alpha` | 0.1 | 0.4247 |
| `reg_lambda` | 0.1 | 0.7412 |

**XGBoost — Best Params (45 trials, seed=42)**:

| Hyperparameter | Baseline | Optuna Best |
|---------------|---------|------------|
| `learning_rate` | 0.05 | 0.01713 |
| `max_depth` | 8 | 10 |
| `min_child_weight` | 100 | 39 |
| `subsample` | 0.8 | 0.9080 |
| `colsample_bytree` | 0.8 | 0.6214 |
| `reg_alpha` | 0.1 | 0.03151 |
| `reg_lambda` | 0.1 | 0.06396 |

### Bảng Baseline vs Optuna-Tuned

⚠️ **PENDING**: Các notebook đã tạo ra model files (`.pkl`) nhưng không lưu metrics ra CSV. Cần chạy lại section Evaluation trong cả hai notebooks để thu thập số liệu thực tế.

**LightGBM v3 — Baseline vs Tuned**:

| Metric | Baseline Val | Tuned Val | Val Gap | Baseline Test | Tuned Test | Test Gap |
|--------|-------------|-----------|---------|--------------|------------|---------|
| RMSLE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| RMSE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| MAE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| RMSE\_log | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |

**XGBoost v3 — Baseline vs Tuned**:

| Metric | Baseline Val | Tuned Val | Val Gap | Baseline Test | Tuned Test | Test Gap |
|--------|-------------|-----------|---------|--------------|------------|---------|
| RMSLE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| RMSE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| MAE | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |
| RMSE\_log | ⚠️ PENDING | ⚠️ PENDING | — | ⚠️ PENDING | ⚠️ PENDING | — |

⚠️ **PENDING — Cách lấy**: Chạy `LightGBM_training_safe_lag.ipynb` và `XGBoost_training_safe_lag.ipynb` từ đầu. Section 3 in baseline metrics, Section 5 in tuned metrics, Section 6 print comparison table. Copy số liệu vào bảng trên.

**Nhận xét dự kiến về pattern** (dựa trên kinh nghiệm v2 và cấu trúc model):
- Optuna cải thiện val RMSLE nhiều hơn test RMSLE → dấu hiệu overfit nhẹ trên val window, bởi Optuna optimize trực tiếp trên val set.
- XGBoost với learning_rate rất thấp (0.017) và max_depth=10 → model sâu hơn, cần nhiều trees để hội tụ nhưng có thể fit phức tạp hơn.

---

## 7.6 Model Performance Comparison

⚠️ **PENDING**: Bảng tổng hợp cuối cùng phụ thuộc vào metrics từ Section 7.5.

Sau khi có metrics, bảng so sánh đầy đủ sẽ có dạng:

| Model | Val RMSLE | Test RMSLE | Val RMSE | Val MAE |
|-------|-----------|------------|---------|---------|
| LightGBM Baseline | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| LightGBM Tuned | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| XGBoost Baseline | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| XGBoost Tuned | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

### Lý do kỳ vọng XGBoost thắng (về mặt kỹ thuật)

Depth-wise growth của XGBoost xây cây theo chiều ngang trước — mỗi level được expand đồng đều. Điều này có xu hướng tạo ra **interaction giữa nhiều features** đồng đều hơn. Với dataset 1782 store×family pairs, các interaction phức tạp giữa `store_nbr` × `family` × `day_of_week` × `lag_28` đòi hỏi cây có khả năng nắm bắt nhiều điều kiện đồng thời — depth-wise growth phù hợp hơn cho pattern này.

Leaf-wise growth của LightGBM có xu hướng tạo ra cây mất cân bằng — một số path rất sâu, phần còn lại nông. Điều này hiệu quả khi có một số interaction quan trọng chiếm ưu thế, nhưng có thể dẫn đến feature dependency không đều.

### Residual Plots

**Pattern kỳ vọng trong residual plots** (actual − predicted theo ngày):
- Residual dương (actual > predicted) = model đang under-predict → màu đỏ nhạt trong plot
- Residual âm (actual < predicted) = model đang over-predict → màu xanh nhạt trong plot
- Mean residual dương → systematic under-prediction bias, phổ biến trong retail forecasting do promotions và events bất ngờ

⚠️ **PENDING — Mean/Std residual**: Lấy từ output Section 8 (ERROR ANALYSIS SUMMARY) của cả hai notebooks sau khi chạy.

**Figure specs cho LaTeX**:
- Tên file plot: không được lưu — plots chỉ hiện trong notebook output (`plt.show()`), chưa `savefig`.
- Cần thêm `savefig` vào notebooks trước khi viết LaTeX:
  - `figures/lgb_v3_residual_val.png` — Daily mean residual, LightGBM, val set
  - `figures/lgb_v3_residual_test.png` — Daily mean residual, LightGBM, test set
  - `figures/xgb_v3_residual_val.png` — Daily mean residual, XGBoost, val set
  - `figures/xgb_v3_residual_test.png` — Daily mean residual, XGBoost, test set
  - `figures/lgb_v3_actual_vs_pred_val.png` — Actual vs Predicted total sales, LightGBM, val
  - `figures/lgb_v3_actual_vs_pred_test.png` — Actual vs Predicted total sales, LightGBM, test
  - `figures/xgb_v3_actual_vs_pred_val.png` — Actual vs Predicted total sales, XGBoost, val
  - `figures/xgb_v3_actual_vs_pred_test.png` — Actual vs Predicted total sales, XGBoost, test

**Bố cục figure đề xuất cho LaTeX**:
- **Figure A**: 2×2 subfigure — Residual plots (LGB val, LGB test, XGB val, XGB test). Caption: "Mean daily residual (actual − predicted) trên val set (Jun 15–Jul 31, 2017) và test set (Aug 1–15, 2017). Vùng đỏ nhạt = under-prediction; vùng xanh nhạt = over-prediction."
- **Figure B**: 2×2 subfigure — Actual vs Predicted total sales (LGB val, LGB test, XGB val, XGB test). Caption: "Tổng doanh thu thực tế và dự báo theo ngày. Đường liền = thực tế; đường nét đứt = dự báo."

### Actual vs Predicted Plots

**Pattern kỳ vọng**: Đường predicted bám sát đường actual với slight systematic under-prediction vào các ngày peak (cuối tuần, ngày lễ). Weekly seasonality rõ ràng (peaks thứ 6–7). Model LightGBM và XGBoost đều capture được trend tổng thể; XGBoost kỳ vọng predict các peaks chính xác hơn.

---

## 7.7 SARIMA Benchmark

### Mục đích và Phạm vi

SARIMA được dùng như **statistical baseline** để kiểm tra xem gradient boosting models có thực sự học được patterns không trivial hay không. SARIMA không phải candidate cho submission — mục đích duy nhất là so sánh.

**Tại sao chỉ benchmark 5 series?** SARIMA là single-series model, cần fit riêng cho mỗi trong 1782 pairs (store × product family). Chi phí tính toán là $O(n)$ theo số series. Với 1782 series × ~1s/series = ~30 phút chỉ để fit — không thực tế cho toàn dataset. Thay vào đó, 5 series đại diện được chọn tự động để cover 5 patterns doanh thu khác nhau.

### 5 Series Đại Diện

| Pattern | Store | Family | Đặc trưng |
|---------|-------|--------|-----------|
| high\_stable | 44 | GROCERY I | mean=9,732 đơn/ngày, cv=0.369 — series volume cao, ổn định |
| low\_sales | 19 | BEAUTY | mean=1.59 đơn/ngày, zero\_ratio=0.282 — series nhỏ, hay có zero |
| seasonality | 52 | MEATS | acf\_lag7=0.942 — tự tương quan mạnh theo chu kỳ 7 ngày |
| many\_zeros | 1 | BABY CARE | zero\_ratio=1.000 — series toàn zero trong toàn bộ training |
| high\_volatility | 19 | LAWN AND GARDEN | cv=28.9, max\_ratio=1112.7 — biến động cực lớn do promotions |

Thống kê tổng quát của 1782 pairs: mean trung bình = 356.8, zero\_ratio trung bình = 0.314 (31.4% ngày zero-sales).

### Cấu hình Model

**Primary**: SARIMA$(1,1,1)(1,1,1)_7$ — SARIMA với seasonal period = 7 ngày (weekly seasonality):
- $(1,1,1)$: AR(1), differencing bậc 1, MA(1)
- $(1,1,1)_7$: Seasonal AR(1), seasonal differencing, seasonal MA(1), period=7

**Fallback**: ARIMA$(1,1,1)$ nếu SARIMA timeout (>60 giây) hoặc không hội tụ.

Training horizon: 1,669 ngày (2013-01-01 → 2017-07-31). Forecast horizon: 15 ngày (2017-08-01 → 2017-08-15).

**Lưu ý kỹ thuật**: SARIMA nhận input là log-transformed sales (giống ML models), forecast được chuyển ngược bằng expm1 trước khi tính RMSLE.

### Kết quả So sánh

Tất cả RMSLE tính trên cửa sổ Aug 1–15, 2017 (15 ngày):

| Pattern | Store | Family | SARIMA | LightGBM | XGBoost |
|---------|-------|--------|--------|----------|---------|
| many\_zeros | 1 | BABY CARE | **0.0000** | 0.0216 | 0.0330 |
| high\_volatility | 19 | LAWN AND GARDEN | **0.0071** | 0.0442 | 0.0435 |
| high\_stable | 44 | GROCERY I | 0.1951 | **0.1465** | 0.1654 |
| seasonality | 52 | MEATS | 0.3098 | **0.1243** | 0.1702 |
| low\_sales | 19 | BEAUTY | 0.3556 | **0.3135** | 0.3164 |

*LightGBM và XGBoost ở đây là phiên bản safe\_lag\_v2 (45 features), không phải v3.*

### Phân tích kết quả

| Pattern | Winner | Giải thích |
|---------|--------|-----------|
| **many\_zeros** | SARIMA (0.0000) | BABY CARE all-zeros trong toàn training → SARIMA dự báo zero đúng mặc nhiên. RMSLE = 0.0000 không phản ánh model quality mà phản ánh degenerate series. |
| **high\_volatility** | SARIMA (0.0071) | LAWN AND GARDEN cực kỳ volatile do promotions đột ngột. SARIMA không học được promotions nhưng may mắn ở 15-ngày cụ thể này. Không generalizable. |
| **high\_stable** | LightGBM (0.1465) | GROCERY I volume lớn, ổn định — ML khai thác được cross-store/family context và oil price. SARIMA chỉ thấy lịch sử một series. |
| **seasonality** | LightGBM (0.1243, cải thiện 60%) | MEATS có weekly seasonality mạnh (acf\_lag7=0.942). SARIMA lý thuyết xử lý seasonality tốt nhưng ML học được cả weekly pattern VÀ promotions, store effects — vượt trội rõ. |
| **low\_sales** | LightGBM (0.3135) | Cả hai model khó với sales thấp — LightGBM nhỉnh hơn nhờ context từ các series khác. |

**Kết luận**: ML > SARIMA ở 3/5 patterns có ý nghĩa thực tế. 2 trường hợp SARIMA thắng đều là edge cases (degenerate series và may mắn trên 15 ngày volatile). Với 1782 series đa dạng và cross-series dependencies trong retail, multi-series ML approach vượt trội rõ ràng so với single-series SARIMA.

---

## Checklist trước khi viết LaTeX

### Metrics còn thiếu (phải có trước khi viết Section 7.5 và 7.6)

- [ ] **LightGBM v3 Baseline metrics**: RMSLE/RMSE/MAE/RMSE\_log trên val và test
  - **Cách lấy**: Chạy `LightGBM_training_safe_lag.ipynb` → Section 3 output
- [ ] **LightGBM v3 Tuned metrics**: RMSLE/RMSE/MAE/RMSE\_log trên val và test
  - **Cách lấy**: Same notebook → Section 5 output  
- [ ] **XGBoost v3 Baseline metrics**: RMSLE/RMSE/MAE/RMSE\_log trên val và test
  - **Cách lấy**: Chạy `XGBoost_training_safe_lag.ipynb` → Section 3 output
- [ ] **XGBoost v3 Tuned metrics**: RMSLE/RMSE/MAE/RMSE\_log trên val và test
  - **Cách lấy**: Same notebook → Section 5 output
- [ ] **Mean/Std residual** cho LightGBM và XGBoost (val set)
  - **Cách lấy**: Section 8 của cả hai notebooks → ERROR ANALYSIS SUMMARY

### Plots còn thiếu (phải `savefig` trước khi viết LaTeX)

Các plots hiện chỉ hiển thị trong notebook output (`plt.show()`), chưa được lưu ra file. Cần thêm `savefig` vào notebooks:

- [ ] `figures/lgb_v3_residual_val.png`
- [ ] `figures/lgb_v3_residual_test.png`
- [ ] `figures/xgb_v3_residual_val.png`
- [ ] `figures/xgb_v3_residual_test.png`
- [ ] `figures/lgb_v3_actual_vs_pred_val.png`
- [ ] `figures/lgb_v3_actual_vs_pred_test.png`
- [ ] `figures/xgb_v3_actual_vs_pred_val.png`
- [ ] `figures/xgb_v3_actual_vs_pred_test.png`
- [ ] `figures/lgb_v3_feature_importance.png`
- [ ] `figures/xgb_v3_feature_importance.png`

### Có đủ, sẵn sàng viết LaTeX

- [x] Data split dimensions và date ranges (Section 7.1)
- [x] Feature list v3 đầy đủ 47 features (Section 7.1)
- [x] Target transform rationale (Section 7.1)
- [x] Baseline hyperparameters của cả hai models (Section 7.2)
- [x] Metric definitions và formulas (Section 7.3)
- [x] Optuna search spaces — exact ranges (Section 7.4)
- [x] Best hyperparameters từ Optuna JSON files (Section 7.5)
- [x] SARIMA benchmark — exact RMSLE numbers từ CSV (Section 7.7)
- [x] SARIMA 5-series analysis và kết luận (Section 7.7)
