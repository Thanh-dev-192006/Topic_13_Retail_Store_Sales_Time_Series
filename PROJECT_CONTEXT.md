# Project Context: Retail Store Sales Forecasting (Topic 13)

> **Mục đích file này**: Cung cấp toàn bộ context kỹ thuật của dự án để AI có thể viết report hoàn chỉnh mà không cần đọc lại codebase.

---

## 1. Tổng quan bài toán

### 1.1 Đề bài
Dự án tham gia cuộc thi Kaggle **"Store Sales — Time Series Forecasting"**. Nhiệm vụ là dự báo doanh số bán hàng (sales) theo ngày cho từng cặp (store, product family) trong tương lai 16 ngày.

- **Tổ chức**: Corporación Favorita — chuỗi bán lẻ lớn tại Ecuador
- **Metric đánh giá**: **RMSLE** (Root Mean Squared Logarithmic Error)
- **Khoảng dự báo Kaggle**: 2017-08-16 → 2017-08-31 (16 ngày)
- **Kaggle Score đã đạt** (trước khi sửa pipeline): **1.05175**
- **Local RMSLE** (Ensemble, Aug 01–15): **0.3974**

### 1.2 Đặc điểm nổi bật
- **3,000,888 dòng** dữ liệu training (54 cửa hàng × 33 gia đình sản phẩm × ~1,684 ngày)
- **31.3% zero sales** — bài toán sparse
- Phân phối lệch phải rất cao: skewness = 7.36, kurtosis = 154.56, CV = 308%
- Có tác động ngoại sinh: giá dầu (Ecuador là nền kinh tế dầu mỏ), ngày lễ quốc gia/khu vực/địa phương, sự kiện đặc biệt (trận động đất 2016)

---

## 2. Dữ liệu thô (Raw Data)

### 2.1 Danh sách file

| File | Kích thước | Mô tả |
|------|-----------|-------|
| `train.csv` | 3,000,888 × 6 | Dữ liệu huấn luyện chính |
| `test.csv` | 28,512 × 5 | Dữ liệu Kaggle cần dự báo |
| `holidays_events.csv` | 350 × 6 | Lịch ngày lễ Ecuador |
| `oil.csv` | 1,218 × 2 | Giá dầu WTI hàng ngày |
| `stores.csv` | 54 × 5 | Thông tin cửa hàng |
| `transactions.csv` | ~83,488 × 3 | Số giao dịch hàng ngày |
| `sample_submission.csv` | 28,512 × 2 | Định dạng nộp bài |

### 2.2 Schema chi tiết

**train.csv**
```
id           int64    — định danh hàng
date         object   — ngày (2013-01-01 to 2017-08-15)
store_nbr    int64    — mã cửa hàng (1–54)
family       object   — danh mục sản phẩm (33 loại)
sales        float64  — doanh số (target variable, ≥ 0)
onpromotion  int64    — số SKU đang khuyến mãi trong ngày đó
```

**holidays_events.csv** (350 × 6 trong raw; 338 rows sau khi lọc transferred=False trong processing)
```
date          — ngày lễ
type          — loại: Holiday / Event / Additional / Transfer / Bridge / Work Day
locale        — phạm vi: National / Regional / Local
locale_name   — tên quốc gia/tỉnh/thành phố áp dụng
description   — tên ngày lễ
transferred   — bool: ngày lễ bị dời sang ngày khác hay không
```

**oil.csv**
```
date, dcoilwtico   — giá dầu WTI (43 giá trị NaN = 3.53%, chủ yếu cuối tuần)
range: 26.19 → 110.62, mean: 67.71, std: 25.63
```

**stores.csv**
```
store_nbr, city, state, type (A/B/C/D/E), cluster (1–17)
- 54 cửa hàng tại 22 thành phố, 16 tỉnh/thành Ecuador
```

### 2.3 Thống kê dữ liệu train

| Metric | Giá trị |
|--------|---------|
| Tổng doanh số | $1,073,644,952 |
| Sales mean | $357.78 |
| Sales median | $11.00 |
| Sales std | $1,102 |
| Sales max | $124,717 |
| Zero sales | 939,130 / 3,000,888 (31.30%) |
| Ngày duy nhất | 1,684 ngày |
| Cửa hàng | 54 |
| Gia đình SP | 33 |
| Cặp (store, family) | 1,782 |

**Top stores by revenue**: #44 ($62.1M, 5.8%), #47, #3, #45, #46
**Top families**: GROCERY I (32.0%), BEVERAGES (20.2%), PRODUCE (11.4%), CLEANING (9.1%), DAIRY (6.0%)

---

## 3. Khám phá dữ liệu (EDA)

### 3.1 Phân tích tổng thể (Overall Sales Growth)

**Xu hướng tăng trưởng**:
- CAGR 2013–2017: **8.34%**
- Tăng trưởng theo năm: 2013→2014 (+49.2%), 2014→2015 (+15.0%), 2015→2016 (+19.6%), 2016→2017 (-32.9%) *(2017 chỉ có dữ liệu đến Aug 15 — partial year, không so sánh công bằng với năm đầy đủ)*
- Biến động: std = $232,212/ngày, CV = 36.47%

**Mùa vụ**:
- Tháng cao nhất: December ($806,881/ngày trung bình)
- Tháng thấp nhất: February ($571,895/ngày)
- Ngày trong tuần cao nhất: Sunday ($822,767)
- Ngày trong tuần thấp nhất: Thursday ($505,269)

**Seasonal decomposition** (multiplicative, period=365):
- Có trend rõ ràng, tăng đến 2016 rồi giảm nhẹ
- Seasonal component mạnh theo tuần (weekly) và năm
- Residual: spike bất thường năm 2016 (động đất)

**Phân phối bán hàng hàng ngày**:
- Sau khi cap outliers (99th percentile = $1,215,894), có 17 ngày outlier (1.01%)
- Median daily total: $632,189

### 3.2 Phân tích Family (Product Category Analysis)

**Pareto**: 6 gia đình đóng góp ~80% doanh thu:
| Family | Share |
|--------|-------|
| GROCERY I | 31.99% |
| BEVERAGES | 20.21% |
| PRODUCE | 11.43% |
| CLEANING | 9.08% |
| DAIRY | 6.01% |
| BREAD/BAKERY | 3.92% |

**Mùa vụ theo gia đình** (seasonality_range = max/min tháng):
- BOOKS: 3.77 (cực kỳ mùa vụ — bán chạy đầu năm học)
- SCHOOL AND OFFICE SUPPLIES: 3.56
- FROZEN FOODS: 3.24

**Ảnh hưởng khuyến mãi** (promo_lift = sales_with_promo / sales_without_promo):
- PRODUCE: 2.08× (cao nhất)
- HOME CARE: 2.04×
- BEVERAGES: 1.49×

**Tăng trưởng cá biệt** (2014→2016):
- Tăng nhanh nhất: BABY CARE (7.35×)
- Giảm: LINGERIE (-27.9%), HOME APPLIANCES (-28.5%)

**Sparsity cao**: BOOKS (83% zero-day rate, CV=3.40), SCHOOL AND OFFICE SUPPLIES (39.8% zero-day rate)

### 3.3 Phân tích Oil & Holidays

**Oil price**:
- Tương quan nghịch giữa giá dầu và tăng trưởng doanh số (Ecuador phụ thuộc xuất khẩu dầu)
- Khi giá dầu giảm 2015–2016, doanh số tăng chậm lại
- 43 giá trị NaN (weekend/holiday trading days) → xử lý bằng forward-fill

**Holidays**:
- 338 ngày lễ (sau lọc transferred=False)
- Phân loại: Holiday (209), Event (56), Additional (51), Bridge (5), Transfer (12), Work Day (5)
- Ngày lễ quốc gia: 8.08% ngày; khu vực: 0.03%; địa phương: 0.40%
- Carnaval (tháng 2): event đặc biệt 5 năm, 2 ngày/năm
- Earthquake 2016-04-16: ảnh hưởng ~31 ngày

### 3.4 Phân tích Store Performance

- 54 cửa hàng tại 22 thành phố, 16 tỉnh
- Store types: A, B, C, D, E (E là cao cấp nhất)
- Top 4 cửa hàng = 20.3% doanh thu; Top 10 = 40.2%
- Cửa hàng cao nhất (#44) tạo ra 23× so với thấp nhất
- Cluster: 17 nhóm cửa hàng (feature hữu ích cho encoding)

### 3.5 Phân tích Transactions

- Số giao dịch hàng ngày có tương quan cao với sales
- Patterns giống sales về mùa vụ và xu hướng

---

## 4. Feature Engineering

### 4.1 Kiến trúc Pipeline

```
train_cleaned.csv
    + holidays_events_cleaned.csv
    + stores_cleaned.csv
    + cleaned_oil.csv
         ↓
  build_train_final.py   (merge tất cả features)
         ↓
  train_final.csv   (3,000,888 × ~56 cột)
         ↓
  create_splits.py  (temporal split)
         ↓
  splits/train/val/test (49 features)
         ↓
  feature_safe_lag_v3.ipynb  (sửa distribution shift)
         ↓
  splits_safe_lag_v3/train/val/test (47 features)
```

### 4.2 Nhóm Feature (47 features trong v3)

#### A. Temporal Features (10)
| Feature | Mô tả |
|---------|-------|
| `year` | Năm (2013–2017) |
| `month` | Tháng (1–12) |
| `day` | Ngày trong tháng (1–31) |
| `day_of_week` | Ngày trong tuần (0=Mon, 6=Sun) |
| `week_of_year` | Tuần trong năm (1–53) |
| `quarter` | Quý (1–4) |
| `is_weekend` | 1 nếu Sat/Sun |
| `is_month_start` | 1 nếu ngày đầu tháng |
| `is_month_end` | 1 nếu ngày cuối tháng |
| `is_payday` | 1 nếu ngày 15 hoặc cuối tháng (ngày lương) |

#### B. Lag Features trong v3 (6)

Safe threshold: `shift(N)` với **N ≥ 16** đảm bảo lookup luôn nằm trong training data khi dự báo Aug 16–31.

| Feature | Shift | Trạng thái | Mô tả |
|---------|-------|-----------|-------|
| `lag_14` | shift(14) | ⚠️ Partially unsafe | Doanh số 14 ngày trước — NaN cho 2 ngày cuối test (Aug 30–31) |
| `lag_16` | shift(16) | ✅ Safe boundary | Doanh số 16 ngày trước (điểm ranh giới an toàn) |
| `lag_21` | shift(21) | ✅ Safe | Doanh số 21 ngày trước (3 tuần) |
| `lag_28` | shift(28) | ✅ Safe | Doanh số 28 ngày trước (4 tuần) |
| `lag_35` | shift(35) | ✅ Safe | Doanh số 35 ngày trước (5 tuần) |
| `lag_364` | shift(364) | ✅ Safe | Doanh số cùng kỳ năm trước |

> **Về lag_14**: shift=14 < 16, nên Aug 30 cần Aug 16 và Aug 31 cần Aug 17 (đều thuộc test period → NaN). Tổng NaN = 2 ngày × 1,782 series = **3,564 NaN** cho Aug 30–31. Model XGBoost/LightGBM xử lý NaN natively nên được giữ lại như một trade-off (có thêm signal cho 14 ngày đầu test).

> **Lưu ý counting**: `lag_14`, `lag_28`, `lag_364` đã có trong old splits (v2) và được GIỮ LẠI. Chỉ `lag_16`, `lag_21`, `lag_35` là **thực sự mới** được thêm vào v3.

#### C. Safe Rolling Features (3)
Dùng `shift(16).rolling(W)` thay vì `shift(1).rolling(W)` để tránh distribution shift:

| Feature | Công thức | Window |
|---------|-----------|--------|
| `rolling_mean_30` | shift(16).rolling(30).mean() | 30 ngày |
| `rolling_mean_28_safe` | shift(16).rolling(28).mean() | 28 ngày |
| `rolling_std_28_safe` | shift(16).rolling(28).std() | 28 ngày |

#### D. Holiday Features (9)
| Feature | Mô tả |
|---------|-------|
| `is_national_holiday` | Ngày lễ quốc gia (8.08% records) |
| `is_regional_holiday` | Ngày lễ vùng/tỉnh (0.03%) |
| `is_local_holiday` | Ngày lễ địa phương/thành phố (0.40%) |
| `is_transferred_holiday` | Ngày bù lễ bị dời (type=Transfer) |
| `holiday_type` | Encode loại lễ: 0=WorkDay, 1=Holiday, 2=Event, 3=Additional, 4=Transfer, 5=Bridge |
| `is_carnaval_feature` | Carnaval event (tháng 2 hàng năm) |
| `days_to_next_holiday` | Số ngày đến ngày lễ tiếp theo |
| `days_after_last_holiday` | Số ngày kể từ ngày lễ gần nhất |
| `is_earthquake_period` | 1 trong khoảng 2016-04-16 đến 2016-05-16 |

#### E. Oil Price Features (5)
| Feature | Mô tả |
|---------|-------|
| `oil_price` | Giá dầu WTI ngày đó (forward-filled) |
| `oil_price_lag_7` | Giá dầu 7 ngày trước |
| `oil_price_lag_14` | Giá dầu 14 ngày trước |
| `oil_price_rolling_mean_28` | TB 28 ngày của giá dầu (shift(1)) |
| `oil_price_change_pct` | % thay đổi giá dầu so với 7 ngày trước |

> Oil range trong train: 26.19 → 110.62, mean: 67.92

> **Tại sao oil features dùng shift(1) không bị distribution shift**: Giá dầu là biến **ngoại sinh (exogenous)** — giá trị thực cho Aug 16–31 đã có sẵn trong `oil.csv` (không phải target cần dự báo như `sales`). Khi forecasting, pipeline merge oil price thực tế cho test period → window rolling luôn có giá trị đầy đủ, không tạo NaN như khi dùng shift(1) trên sales. Đây là điểm khác biệt căn bản với rolling features trên sales.

#### F. Store Features (8)
| Feature | Cách tính | Mô tả |
|---------|-----------|-------|
| `type` | raw | Loại cửa hàng (A/B/C/D/E) |
| `city` | raw | Thành phố |
| `state` | raw | Tỉnh/thành |
| `cluster` | raw | Cluster ID (1–17) |
| `store_type_enc` | LabelEncoder | Encode loại cửa hàng |
| `city_freq` | Frequency encoding | Tần suất thành phố trong train |
| `state_freq` | Frequency encoding | Tần suất tỉnh trong train |
| `store_type_encoded` | Manual mapping (sorted alpha) | Encode loại cửa hàng theo thứ tự |

#### G. Identity & Target Encoding (3)
| Feature | Mô tả |
|---------|-------|
| `store_family` | Composite key: `{store_nbr}_{family}` |
| `store_family_te` | KFold Out-of-Fold Target Encoding (k=5, smoothing=10) |
| `onpromotion` | Số SKU đang khuyến mãi |

### 4.3 Vấn đề Distribution Shift (Critical Finding)

**Vấn đề gốc rễ** của Kaggle score cao (1.05175):

Trong pipeline cũ (v2), các rolling features được tính bằng `shift(1).rolling(W)`:
- Khi **training**: window luôn có đủ W giá trị thực
- Khi **forecasting** Aug 16–31 với combined-append approach:
  - Test rows có `sales = NaN`
  - `shift(1)` của Aug 31 → Aug 30 (NaN vì trong test period)
  - Effective rolling window thu nhỏ từ 28 xuống còn 1 khi đến Aug 31
  - → Model nhận feature distribution hoàn toàn khác so với lúc train

**Giải pháp (v3)**: Dùng `shift(16).rolling(W)`:
- `shift(16)` của bất kỳ ngày nào trong Aug 16–31 đều trỏ về ≤ Aug 15 (trong train data)
- Toàn bộ window W luôn nằm trong real historical data
- Zero distribution shift đảm bảo

**Features bị loại bỏ** (8 toxic features):
- `lag_1`, `lag_2`, `lag_3`, `lag_7` (shift < 16, dễ tạo leakage khi forecast trực tiếp)
- `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28` (shift(1) → distribution shift)
- `rolling_std_7` (shift(1) → distribution shift)

**Net change**: 49 features → 47 features (−8 toxic, +6 mới)

| Thao tác | Features |
|---------|---------|
| Removed (8) | `lag_1`, `lag_2`, `lag_3`, `lag_7`, `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`, `rolling_std_7` |
| Added NEW (6) | `lag_16`, `lag_21`, `lag_35`, `rolling_mean_28_safe`, `rolling_mean_30`, `rolling_std_28_safe` |
| Kept unchanged | `lag_14`, `lag_28`, `lag_364` + tất cả features khác |

49 − 8 + 6 = **47** ✓ (xác minh từ `splits_safe_lag_v3/train_features.csv`)

---

## 5. Chia dữ liệu (Data Splits)

### 5.1 Temporal Split Strategy

Không dùng random split — chỉ dùng date boundary để tránh data leakage.

| Split | Start | End | Rows |
|-------|-------|-----|------|
| Train | 2013-01-01 | 2017-06-30 | 2,918,916 |
| Val | 2017-07-01 | 2017-07-31 | 55,242 |
| Test (local) | 2017-08-01 | 2017-08-15 | 26,730 |
| Kaggle test | 2017-08-16 | 2017-08-31 | 28,512 |

### 5.2 Target Transform

```python
y_train_log = np.log1p(y_train)   # log(1 + sales)
predictions = np.expm1(model.predict(X))  # exp(pred) - 1
predictions = np.clip(predictions, 0, None)  # không cho âm
```

### 5.3 Evaluation Metric

```python
RMSLE = sqrt(mean((log(pred+1) - log(actual+1))^2))
```

---

## 6. Mô hình SARIMA (Classical Baseline)

### 6.1 Kiểm tra tính dừng (Stationarity)

**Dữ liệu**: Tổng doanh số hàng ngày (aggregate toàn bộ 54 stores × 33 families)
**Series length**: 1,688 ngày (sau forward-fill 4 giá trị NaN)

**Kiểm định**:
- **ADF Test** (Augmented Dickey-Fuller): H0 = có unit root (non-stationary)
- **KPSS Test** (Kwiatkowski-Phillips-Schmidt-Shin): H0 = stationary

**Kết quả**:

| d | ADF stat | ADF p-val | Verdict ADF | KPSS stat | KPSS p-val | Verdict KPSS | Combined |
|---|---------|-----------|-------------|-----------|------------|--------------|---------|
| 0 | −2.6233 | 0.0883 | Non-stationary | 5.7232 | 0.01 | Non-stationary | ❌ NON-STATIONARY |
| 1 | −11.3511 | 0.0000 | Stationary | 0.0648 | 0.10 | Stationary | ✅ STATIONARY |
| 2 | −12.7401 | 0.0000 | Stationary | 0.0493 | 0.10 | Stationary | ✅ STATIONARY |

**Khuyến nghị**: d = 1 (minimum differencing để đạt stationarity)

**Seasonal decomposition** (additive, period=7):
- Trend mạnh: tăng 2013→2016, phẳng 2016→2017
- Seasonal component: chu kỳ tuần rõ ràng
- Residual: spike nhỏ, phân phối gần normal sau loại trend+seasonal

**Files lưu**: `daily_total_sales.csv`, `daily_total_sales_d1.csv`

### 6.2 Training SARIMA

**Objective**: Thiết lập baseline cổ điển để so sánh với gradient boosting

**5 series đại diện** (chọn từ 1,782 cặp store-family):

| Pattern | Store | Family | mean | cv | zero_ratio | Đặc điểm |
|---------|-------|--------|------|----|-----------|---------|
| high_stable | 44 | GROCERY I | 9,732 | 0.369 | 0.0 | Doanh số cao, ổn định |
| low_sales | 19 | BEAUTY | 1.59 | — | 0.282 | Doanh số thấp, nhiều zero |
| seasonality | 52 | MEATS | — | — | 0.0 | acf_lag7 = 0.942 (seasonality mạnh) |
| many_zeros | 1 | BABY CARE | — | — | 1.000 | 100% zero (degenerate) |
| high_volatility | 19 | LAWN AND GARDEN | — | 28.899 | 0.0 | cv = 28.9, max_ratio = 1112.7 |

**Model**: `SARIMAX(1,1,1)(1,1,1,7)` cố định cho tất cả series
- p=1, d=1, q=1 (AR(1), I(1), MA(1))
- P=1, D=1, Q=1, s=7 (seasonal weekly)
- Fallback: ARIMA(1,1,1) nếu SARIMA không hội tụ

**Khoảng validation**: Aug 01–15 (15 ngày)

### 6.3 Kết quả Benchmark

| Store | Family | Pattern | SARIMA RMSLE | LightGBM RMSLE | XGBoost RMSLE |
|-------|--------|---------|-------------|---------------|--------------|
| 1 | BABY CARE | many_zeros | **0.0000** | 0.0216 | 0.0330 |
| 19 | LAWN AND GARDEN | high_volatility | **0.0071** | 0.0442 | 0.0435 |
| 44 | GROCERY I | high_stable | 0.1951 | **0.1465** | 0.1654 |
| 52 | MEATS | seasonality | 0.3098 | **0.1243** | 0.1702 |
| 19 | BEAUTY | low_sales | 0.3556 | **0.3135** | 0.3164 |

**Nhận xét**:
- SARIMA thắng trên BABY CARE vì series toàn zero → dự báo zero = perfect
- SARIMA có RMSLE=0.0071 cho LAWN AND GARDEN (nghi ngờ — có thể do model fit tốt 15 ngày tình cờ)
- LightGBM **thắng trên 3/5 series** thực chất, đặc biệt MEATS (gap lớn: 0.1243 vs 0.3098)
- XGBoost thứ 2 trên hầu hết series

**Lưu ý vấn đề**:
- BABY CARE RMSLE = 0.0000 là **degenerate case** (zero_ratio=1.0, không phản ánh năng lực SARIMA thực)
- Model order cố định (1,1,1)(1,1,1,7) không được tối ưu cho từng series
- Dữ liệu training cắt tại 2017-07-31 (1,669 ngày training)

---

## 7. Mô hình Machine Learning

### 7.1 XGBoost

**Thư viện**: `xgboost` với GPU acceleration

**Hyperparameters** (Optuna-tuned, được lưu tại `models/xgboost_optuna_best_params.json`):
```json
{
  "learning_rate": 0.05662,
  "max_depth": 10,
  "min_child_weight": 62,
  "subsample": 0.8918,
  "colsample_bytree": 0.7929,
  "reg_alpha": 0.0653,
  "reg_lambda": 0.0543
}
```

**Fixed params**:
```python
n_estimators = 1000
tree_method = "hist"   # GPU-friendly histogram method
device = "cuda"        # GPU acceleration
objective = "reg:squarederror"
eval_metric = "rmse"
```

**Training data**: splits_safe_lag_v3 (2,918,916 × 47)

**Preprocessing**: LabelEncoder cho các cột object (`family`, `type`, `city`, `state`, `store_family`)

**Saved model**: `models/xgboost_safe_lag_v2_model.pkl`
*(Note: file tên "v2" nhưng được train trên feature set v3 — naming convention dùng "v2" để chỉ lần train thứ hai với safe lags, không liên quan đến v3 feature set)*

### 7.2 LightGBM

**Thư viện**: `lightgbm` với GPU acceleration

**Hyperparameters** (Optuna-tuned, được lưu tại `models/lightgbm_optuna_best_params.json`):
```json
{
  "learning_rate": 0.03452,
  "num_leaves": 209,
  "min_child_samples": 199,
  "subsample": 0.9044,
  "colsample_bytree": 0.6878,
  "reg_alpha": 0.00104,
  "reg_lambda": 0.00376
}
```

**Fixed params**:
```python
n_estimators = 1000
device = "gpu"    # LightGBM GPU (KHÔNG dùng tree_method)
objective = "regression"
metric = "rmse"
```

> **Quan trọng**: LightGBM dùng `device='gpu'` (không có param `tree_method` như XGBoost)

**Saved model**: `models/lightgbm_safe_lag_v2_model.pkl`
*(Cùng naming convention: "v2" trong tên file = lần thứ hai với safe lags, train trên v3 features)*

### 7.3 Hyperparameter Tuning (Optuna)

- Framework: Optuna (Bayesian optimization / TPE sampler)
- Params được lưu sẵn vào JSON — **không re-tune** khi train lại
- Mỗi model được tune riêng trên validation set (Jul 2017)

---

## 8. Forecasting Pipeline

### 8.1 Chiến lược Dự báo

**Direct Multi-step Forecast** (không iterative/recursive):
- Gọi `model.predict()` một lần cho toàn bộ 28,512 dòng (16 ngày × 1,782 series)
- Không có error propagation giữa các bước dự báo
- Đơn giản, nhanh, không tích lũy sai số

### 8.2 Tính Lag Features cho Kaggle Test

**Vấn đề**: Kaggle test period (Aug 16–31) không có giá trị `sales` → không thể tính lag trực tiếp.

**Giải pháp** (Merge approach):
```python
# Với mỗi lag N (14, 16, 21, 28, 35, 364):
lag_ref = train_raw[['date','store_nbr','family','sales']].copy()
lag_ref['date'] = lag_ref['date'] + pd.Timedelta(days=N)  # dịch ngày lên
lag_ref = lag_ref.rename(columns={'sales': f'lag_{N}'})
X_kaggle = X_kaggle.merge(lag_ref, on=['date','store_nbr','family'], how='left')
```

Ví dụ: `lag_16` của ngày Aug 31 → merge với record Aug 15 (=Aug31 - 16 ngày) trong train.

**Xác minh**: lag_16/21/28/35/364 đều có 0 NaN cho Aug 16–31 ✓
lag_14 có 3,564 NaN chỉ cho **2 ngày cuối** (Aug 30–31), vì Aug 30 − 14 = Aug 16 và Aug 31 − 14 = Aug 17 (thuộc test period).

### 8.3 Tính Rolling Features cho Kaggle Test

**Giải pháp** (Combined-append approach với shift(16) only):
```python
cutoff = test_start - pd.Timedelta(days=46)  # cần 46 ngày lookback cho shift(16).rolling(30)
train_recent = train_raw[train_raw['date'] >= cutoff][['date','store_nbr','family','sales']]
test_rows = X_kaggle[['date','store_nbr','family']].copy()
test_rows['sales'] = np.nan

combined = pd.concat([train_recent, test_rows])
grp = combined.groupby(['store_nbr','family'], sort=False)['sales']

# Chỉ dùng shift(16) — không bao giờ lookup vào NaN test rows
combined['rolling_mean_30']      = grp.transform(lambda x: x.shift(16).rolling(30, min_periods=1).mean())
combined['rolling_mean_28_safe'] = grp.transform(lambda x: x.shift(16).rolling(28, min_periods=1).mean())
combined['rolling_std_28_safe']  = grp.transform(lambda x: x.shift(16).rolling(28, min_periods=2).std())
```

**Xác minh**: rolling_mean_30, rolling_mean_28_safe, rolling_std_28_safe đều có 0 NaN ✓

### 8.4 Ensemble

```python
lgb_weight = 0.3
xgb_weight = 0.7

# Predict trong log space
lgb_pred_log = lgb_model.predict(X_kaggle)
xgb_pred_log = xgb_model.predict(X_kaggle)

# Ensemble
ensemble_log = lgb_weight * lgb_pred_log + xgb_weight * xgb_pred_log

# Inverse transform
predictions = np.expm1(ensemble_log)
predictions = np.clip(predictions, 0, None)
```

**Thống kê predictions**:
- min: 0.0000
- max: 16,478.34
- mean: 424.67
- NaN: 0

### 8.5 Kết quả Đánh giá

**Local Test (Aug 01–15)**:
| Model | RMSLE | RMSE | MAE |
|-------|-------|------|-----|
| Ensemble (LGB 0.3 + XGB 0.7) | **0.3974** | 215.66 | 62.56 |
| Baseline (toxic lags, direct) | 0.3704 | — | — |

> **Lưu ý**: Local test có thể chênh với Kaggle do distribution shift ở pipeline cũ (v2) — v3 đã fix vấn đề này.

**Kaggle Score** (nộp bài từ v2 pipeline cũ): **1.05175**

**Output file**: `notebooks/08_forecasting/submission_safe_lag_v2.csv`
- Format: `id, sales`
- 28,512 dòng

---

## 9. Kiến trúc Project

### 9.1 Cấu trúc thư mục

```
Topic_13_Retail_Store_Sales_Time_Series/
├── config.py                          # Paths: PROJECT_ROOT, DATA_DIR, RAW_DIR, PROCESSED_DIR, MODELS_DIR
├── scripts/
│   ├── build_train_final.py           # Merge tất cả features → train_final.csv
│   └── create_splits.py               # Temporal split → splits/
├── data/
│   ├── raw/                           # train.csv, test.csv, holidays_events.csv, oil.csv, stores.csv, transactions.csv
│   └── processed/
│       ├── train_cleaned.csv          # Dữ liệu train đã làm sạch
│       ├── test_cleaned.csv           # Dữ liệu test đã làm sạch
│       ├── train_final.csv            # Full featured dataset (3M × ~56 cols)
│       ├── splits/                    # Original splits (49 features — có toxic lags)
│       └── splits_safe_lag_v3/        # **Active splits** (47 features — safe lags only)
│           ├── train_features.csv     (2,918,916 × 47)
│           ├── train_target.csv
│           ├── val_features.csv       (55,242 × 47)
│           ├── val_target.csv
│           ├── test_features.csv      (26,730 × 47)
│           └── test_target.csv
├── models/
│   ├── xgboost_optuna_best_params.json
│   ├── lightgbm_optuna_best_params.json
│   ├── xgboost_safe_lag_v2_model.pkl  # XGBoost trained on v3 features
│   └── lightgbm_safe_lag_v2_model.pkl # LightGBM trained on v3 features
├── notebooks/
│   ├── 01_data_exploration/           # EDA notebooks (train, oil, stores, holidays, transactions)
│   ├── 03_eda_deep_dive/              # Deep EDA (sales growth, family analysis, oil/holidays, store performance)
│   ├── 04_feature_engineering/features/
│   │   ├── feature_temporal.ipynb     # Temporal + lag features
│   │   ├── feature_holiday.ipynb      # Holiday features
│   │   ├── feature_oil_and_store.ipynb # Oil + store encoding
│   │   ├── feature_external.ipynb     # External data features
│   │   ├── feature_target_encoding.ipynb # KFold OOF target encoding
│   │   └── feature_safe_lag_v3.ipynb  # **Active**: Remove toxic lags, add safe lags → splits_safe_lag_v3/
│   ├── 05_SARIMA/
│   │   ├── 01_stationarity_checks.ipynb # ADF + KPSS tests on daily aggregate
│   │   ├── SARIMA_training.ipynb       # SARIMA(1,1,1)(1,1,1,7) on 5 representative series
│   │   └── arima_benchmark_results.csv
│   ├── 06_evaluation/
│   │   ├── XGBoost_training_safe_lag.ipynb   # **Active**: XGBoost on v3 features
│   │   └── LightGBM_training_safe_lag.ipynb  # **Active**: LightGBM on v3 features
│   └── 08_forecasting/
│       ├── forecasting_safe_lag_v2.ipynb     # **Active**: Direct forecast + ensemble
│       └── submission_safe_lag_v2.csv        # Kaggle submission file
```

### 9.2 Thứ tự chạy Pipeline (Active)

```
1. scripts/build_train_final.py             → data/processed/train_final.csv
2. scripts/create_splits.py                 → data/processed/splits/
3. notebooks/04.../feature_safe_lag_v3.ipynb → data/processed/splits_safe_lag_v3/
4. notebooks/06.../XGBoost_training_safe_lag.ipynb   → models/xgboost_safe_lag_v2_model.pkl
5. notebooks/06.../LightGBM_training_safe_lag.ipynb  → models/lightgbm_safe_lag_v2_model.pkl
6. notebooks/08.../forecasting_safe_lag_v2.ipynb     → submission_safe_lag_v2.csv
```

---

## 10. Thư viện Sử dụng

| Thư viện | Phiên bản phổ biến | Mục đích |
|----------|-------------------|---------|
| `pandas` | ≥1.5 | Xử lý dữ liệu, aggregation, merge |
| `numpy` | ≥1.24 | Tính toán số học, log1p, expm1 |
| `scikit-learn` | ≥1.2 | LabelEncoder, KFold, metrics |
| `category_encoders` | ≥2.5 | TargetEncoder (OOF) |
| `xgboost` | ≥1.7 | XGBoost với GPU (CUDA) |
| `lightgbm` | ≥3.3 | LightGBM với GPU |
| `optuna` | ≥3.0 | Hyperparameter tuning (Bayesian) |
| `statsmodels` | ≥0.14 | SARIMAX, ADF test, KPSS test, ACF/PACF |
| `matplotlib` | ≥3.6 | Visualization |
| `seaborn` | ≥0.12 | Statistical plots |
| `pathlib` | stdlib | Path management |
| `pickle` | stdlib | Model serialization |
| `json` | stdlib | Params loading/saving |

---

## 11. Visualization Đã Tạo

### EDA Plots

1. **Daily Total Sales Trend** (2013–2017): Line plot với 3-month moving average
2. **Monthly Sales Bar Chart**: Monthly aggregation với MoM growth rates
3. **Seasonal Decomposition** (multiplicative, period=365): Observed, Trend, Seasonal, Residual
4. **YoY Comparison**: 5 năm overlaid trên cùng 1 chart
5. **Sales Distribution**: Histogram + Box plot by year + Box plot by day_of_week + Zero sales frequency
6. **Heatmap day_of_week × month**: Average sales intensity
7. **Top 15 Families Bar Chart**: Horizontal bar chart by total revenue
8. **Stacked Area Chart**: Sales contribution by family over time (top 8 + Other)
9. **Family × Month Seasonality Heatmap**: Index = month_mean / overall_mean
10. **Promo vs No-Promo Grouped Bar**: Mean sales with/without promotion per family
11. **Family Correlation Heatmap**: Pearson correlation top 12 families

### Stationarity Plots (SARIMA)

12. **Raw Series + Rolling Statistics**: Total daily sales với 90-day rolling mean/std
13. **Seasonal Decomposition** (additive, period=7): Cho aggregate daily series
14. **ACF + PACF** (lags=60): Cho d=0, d=1, d=2
15. **First Difference Series**: Rolling mean/std sau differencing

### Feature Engineering Plots

16. **Lag NaN Analysis**: Bar chart NaN count theo lag depth

---

## 12. Quan sát Quan trọng & Insights

### 12.1 Về Dữ liệu
- **Extreme sparsity**: 31.3% zero sales — RMSLE metric phù hợp hơn RMSE vì penalize cả dự báo âm và quá cao
- **Heavy right tail**: median $11 nhưng mean $358 → cần log transform
- **Temporal pattern mạnh**: weekly seasonality dominant (SARIMA seasonal order s=7)
- **Ecuador oil dependency**: Giá dầu giảm 2015–2016 tương quan với tốc độ tăng trưởng chậm lại

### 12.2 Về Feature Engineering
- **Safe lag threshold = 16 ngày**: Với Kaggle test 16 ngày, mọi `shift(N)` với N ≥ 16 đều an toàn
- **Target encoding hiệu quả**: `store_family_te` encode mean sales của từng cặp store-family, KFold OOF tránh leakage
- **Earthquake feature**: 31-ngày sau 2016-04-16 là event đặc biệt gây disruption

### 12.3 Về Model
- **LightGBM > XGBoost** trên hầu hết series riêng lẻ: thắng 4/5 series trong SARIMA benchmark (BABY CARE, GROCERY I, MEATS, BEAUTY); XGBoost chỉ thắng nhẹ trên LAWN AND GARDEN (0.0435 vs 0.0442)
- **Ensemble 70/30** (XGB/LGB) cho kết quả tốt hơn single model
- **GPU acceleration**: tree_method='hist' + device='cuda' cho XGBoost; device='gpu' cho LightGBM
- **Optuna Bayesian tuning**: max_depth=10 (sâu), num_leaves=209 (LGB) — cả hai ưu tiên low learning rate với nhiều trees

### 12.4 Về Pipeline
- **Distribution shift là root cause** của Kaggle score 1.05175 (local RMSLE chỉ 0.37): rolling features tính bằng shift(1) bị degradation khi forecast
- **Direct forecast đơn giản hơn iterative**: không cần loop, không accumulate error
- **Merge approach cho lags** (thay vì combined-append): rõ ràng hơn, dễ debug hơn

---

## 13. Kết quả Tổng hợp

| Pipeline | Features | Local RMSLE (Aug 1-15) | Kaggle Score |
|----------|----------|----------------------|-------------|
| Baseline (toxic lags, direct) | 49 | 0.3704 | ~1.05 (v2 có shift issue) |
| Safe Lag v2 | 45 | ~0.37 | 1.05175 (vẫn có distribution shift) |
| **Safe Lag v3 (current)** | **47** | **0.3974** | **Pending** (submission_safe_lag_v2.csv) |

> Local RMSLE của v3 cao hơn v2 (0.3974 vs 0.37) trên local test (Aug 1-15), nhưng Kaggle test (Aug 16-31) dự kiến tốt hơn đáng kể vì không còn distribution shift.

---

## 14. Thông tin Nhóm (Team)

| Thành viên | Nhiệm vụ |
|-----------|---------|
| **Thanh** | EDA tổng thể (train.csv, overall sales growth), Feature engineering chính, Pipeline integration |
| **Hai** | EDA oil.csv, EDA oil & holidays deep dive |
| **Han** | EDA stores.csv, Store performance analysis |
| **Lan** | EDA transactions.csv, Family EDA (promo & seasonality) |
| **Trung** | EDA holidays_events.csv |

---

*File này được tạo tự động bằng cách đọc toàn bộ codebase vào ngày 2026-05-12.*
*Được audit và cập nhật lần cuối: 2026-05-12 — cross-check với codebase thực tế.*
*Sử dụng file này để cung cấp context cho AI viết report mà không cần đọc lại code.*
