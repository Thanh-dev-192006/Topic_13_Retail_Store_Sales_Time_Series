# Model Training Context — Safe Lag v3

> **Phạm vi tài liệu này**: Chỉ bao gồm các notebook training mới nhất:
> `LightGBM_training_safe_lag.ipynb`, `XGBoost_training_safe_lag.ipynb`, `SARIMA_training.ipynb`.  
> Metric chính: **RMSLE** (Root Mean Squared Logarithmic Error), target transform: `log1p` → `expm1`.

---

## 1. Data & Feature Setup (Safe Lag v3)

### 1.1 Splits

| Set | Ngày | Dòng | Vai trò |
|-----|------|------|---------|
| Train | 2013-01-01 → 2017-06-14 | 2,918,916 | Train model |
| Val | 2017-06-15 → 2017-07-31 | 55,242 | Early stopping + Optuna objective |
| Test (local) | 2017-08-01 → 2017-08-15 | 26,730 | Đánh giá final |

Nguồn: `data/processed/splits_safe_lag_v3/`

### 1.2 Feature Set v3 (47 features)

**8 features bị loại so với v1**:

| Feature bị loại | Lý do |
|----------------|-------|
| `lag_1`, `lag_2`, `lag_3`, `lag_7` | shift=1 → không tồn tại trong forecast window 16 ngày |
| `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28` | Phụ thuộc vào các lag ngắn trên |
| `rolling_std_7` | Tương tự |

**6 features thêm vào**:
`lag_16`, `lag_21`, `lag_35`, `rolling_mean_30`, `rolling_mean_28_safe`, `rolling_std_28_safe`

> Tất cả safe features dùng `shift=16` → đảm bảo không leakage khi forecast window = 16 ngày.

### 1.3 Encode Categorical (cả LGB và XGB dùng giống nhau)

```python
object_cols = X_train.select_dtypes(include=['object']).columns.tolist()
# Gồm: ['date', 'family', 'type', 'city', 'state', 'store_family']

for col in object_cols:
    le = LabelEncoder()
    combined = pd.concat([X_train[col], X_val[col], X_test[col]]).astype(str)
    le.fit(combined)          # fit trên toàn bộ để tránh unseen labels
    X_train[col] = le.transform(X_train[col].astype(str)).astype(np.int32)
    X_val[col]   = le.transform(X_val[col].astype(str)).astype(np.int32)
    X_test[col]  = le.transform(X_test[col].astype(str)).astype(np.int32)
```

---

## 2. LightGBM Safe Lag v3 — `LightGBM_training_safe_lag.ipynb`

> **Trạng thái**: Notebook đã cấu trúc lại hoàn chỉnh (2026-05-14). **Chưa chạy** — chưa có output.

### 2.1 Pipeline 9 Bước

| Bước | Nội dung |
|------|---------|
| **1** | Load từ `splits_safe_lag_v3/` + assert 47 cols + verify v3 features present/absent |
| **1b** | Encode categorical (LabelEncoder fit trên train+val+test) |
| **2** | Baseline training với params đơn giản, early stopping 100 rounds trên `X_train` |
| **3** | Baseline evaluation: định nghĩa `evaluate_metrics()`, đánh giá Val & Test, display table |
| **4** | Optuna tuning 45 trials (TPE sampler seed=42) → save `lightgbm_safe_lag_v3_optuna_best_params.json` |
| **5** | Retrain trên `X_train + X_val` với best params → save `lightgbm_safe_lag_v3_model.pkl` |
| **6** | Comparison table: Baseline vs Tuned (Val Gap + Test Gap) |
| **7** | Feature importance plot (top 20, baseline model) |
| **8** | Error analysis: actual vs predicted (val + test), holiday vs non-holiday, daily residual |
| **9** | Save model copy sang `notebooks/08_forecasting/` |

### 2.2 Baseline Params (Section 2)

```python
lgb.LGBMRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=150,
    min_child_samples=100,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=0.1,
    objective='regression',
    random_state=42,
    n_jobs=-1,
)
# fit với callbacks=[early_stopping(100), log_evaluation(100)]
```

### 2.3 Optuna Search Space (Section 4)

```python
params = {
    'learning_rate'    : trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
    'num_leaves'       : trial.suggest_int('num_leaves', 50, 300),
    'min_child_samples': trial.suggest_int('min_child_samples', 20, 300),
    'subsample'        : trial.suggest_float('subsample', 0.6, 1.0),
    'colsample_bytree' : trial.suggest_float('colsample_bytree', 0.6, 1.0),
    'reg_alpha'        : trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
    'reg_lambda'       : trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
    # n_estimators=1000, early_stopping=50, objective='regression'
}
# Objective function: minimize RMSLE trên y_val_orig['sales'] (original scale)
```

### 2.4 Retrain Params (Section 5)

```python
best_params = {
    **best_optuna_params,   # từ Optuna step
    'n_estimators': 1000,
    'objective'   : 'regression',
    'random_state': 42,
    'n_jobs'      : -1,
}
# Không có early_stopping vì fit trên toàn bộ train+val
```

### 2.5 Idempotent Design

Notebook check file trước khi chạy:
- `models/lightgbm_safe_lag_v3_optuna_best_params.json` → nếu tồn tại: load; nếu không: chạy Optuna
- `models/lightgbm_safe_lag_v3_model.pkl` → nếu tồn tại: load; nếu không: retrain

Đảm bảo không vô tình load params v1 (`lightgbm_optuna_best_params.json`) cho model v3.

### 2.6 Output Files

| File | Nội dung |
|------|---------|
| `models/lightgbm_safe_lag_v3_optuna_best_params.json` | Best hyperparams (45 Optuna trials, seed=42) |
| `models/lightgbm_safe_lag_v3_model.pkl` | Final model (retrained trên Train+Val) |
| `notebooks/08_forecasting/lgb_safe_lag_v3_model.pkl` | Copy để forecasting notebook dùng |

### 2.7 Metrics (Pending)

| | Val RMSLE | Test RMSLE | Val RMSE | Val MAE |
|-|-----------|------------|----------|---------|
| Baseline | — | — | — | — |
| Tuned | — | — | — | — |

---

## 3. XGBoost Safe Lag v3 — `XGBoost_training_safe_lag.ipynb`

> **Trạng thái**: Notebook đã cấu trúc lại hoàn chỉnh (2026-05-14). **Chưa chạy** — chưa có output.

### 3.1 Pipeline 9 Bước

Giống LightGBM (Section 2.1) với các khác biệt sau:
- Bước 2: dùng `XGBRegressor` với `tree_method='hist'`, `early_stopping_rounds=100`, `verbose=100`
- Bước 5: retrain dùng `.fit(X_train_val, y_train_val, verbose=100)`
- Bước 9: thêm save `xgb_v3_label_encoders.pkl` cho inference

### 3.2 Baseline Params (Section 2)

```python
xgb.XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=8,
    min_child_weight=100,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=0.1,
    objective='reg:squarederror',
    tree_method='hist',
    early_stopping_rounds=100,
    random_state=42,
    n_jobs=-1,
)
```

### 3.3 Optuna Search Space (Section 4)

```python
params = {
    'learning_rate'       : trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
    'max_depth'           : trial.suggest_int('max_depth', 4, 10),
    'min_child_weight'    : trial.suggest_int('min_child_weight', 20, 300),
    'subsample'           : trial.suggest_float('subsample', 0.6, 1.0),
    'colsample_bytree'    : trial.suggest_float('colsample_bytree', 0.6, 1.0),
    'reg_alpha'           : trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
    'reg_lambda'          : trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
    'early_stopping_rounds': 50,
    # n_estimators=1000, objective='reg:squarederror', tree_method='hist'
}
# fit với eval_set=[(X_val, y_val)], verbose=False
```

### 3.4 Retrain Params (Section 5)

```python
best_params = {
    **best_optuna_params,
    'n_estimators': 1000,
    'objective'   : 'reg:squarederror',
    'tree_method' : 'hist',
    'random_state': 42,
    'n_jobs'      : -1,
}
# fit(X_train_val, y_train_val, verbose=100) — không có early_stopping
```

### 3.5 Output Files

| File | Nội dung |
|------|---------|
| `models/xgboost_safe_lag_v3_optuna_best_params.json` | Best hyperparams (45 Optuna trials, seed=42) |
| `models/xgboost_safe_lag_v3_model.pkl` | Final model (retrained trên Train+Val) |
| `notebooks/08_forecasting/xgb_safe_lag_v3_model.pkl` | Copy để forecasting notebook dùng |
| `notebooks/08_forecasting/xgb_v3_label_encoders.pkl` | LabelEncoders cho inference |

### 3.6 Metrics (Pending)

| | Val RMSLE | Test RMSLE | Val RMSE | Val MAE |
|-|-----------|------------|----------|---------|
| Baseline | — | — | — | — |
| Tuned | — | — | — | — |

---

## 4. Hàm Evaluate Metrics (Dùng Trong Cả Hai Notebooks)

```python
y_test_orig = pd.DataFrame({'sales': np.expm1(y_test['sales_log'])})

def evaluate_metrics(y_true_log, y_pred_log, y_true_orig, label=''):
    y_pred_orig = np.clip(np.expm1(y_pred_log), 0, None)
    y_true_orig = np.clip(y_true_orig, 0, None)

    rmsle    = np.sqrt(mean_squared_log_error(y_true_orig, y_pred_orig))
    rmse     = np.sqrt(mean_squared_error(y_true_orig, y_pred_orig))
    mae      = mean_absolute_error(y_true_orig, y_pred_orig)
    rmse_log = np.sqrt(mean_squared_error(y_true_log, y_pred_log))

    return {'RMSLE': rmsle, 'RMSE': rmse, 'MAE': mae, 'RMSE_log': rmse_log}
```

> `clip(expm1(...), 0, None)`: inverse log-transform rồi clip về 0 vì RMSLE không xác định với giá trị âm.

Comparison table (Section 6) cấu trúc:

```python
metrics_order = ['RMSLE', 'RMSE', 'MAE', 'RMSE_log']
summary = pd.DataFrame({
    'Metric'       : metrics_order,
    'Baseline Val' : [...], 'Tuned Val'    : [...], 'Val Gap'  : [...],
    'Baseline Test': [...], 'Tuned Test'   : [...], 'Test Gap' : [...],
})
# Val Gap / Test Gap âm = cải thiện sau tuning
```

---

## 5. SARIMA Benchmark — `SARIMA_training.ipynb`

### 5.1 Mục tiêu

Classical baseline để so sánh với ML models. Train SARIMA trên **5 series đại diện** covering 5 sales patterns khác nhau.

### 5.2 Data

```python
raw = pd.read_csv('data/processed/train_final.csv',
                  usecols=['date', 'store_nbr', 'family', 'sales'])
# 3,000,888 rows | 2013-01-01 → 2017-08-15

TRAIN_END = '2017-07-31'   # SARIMA train đến đây
VAL_START = '2017-08-01'   # Forecast từ đây
VAL_END   = '2017-08-15'   # Forecast đến đây (15 bước)
```

> Lưu ý: SARIMA dùng `train_final.csv` trực tiếp, không qua splits v3. ML models trong benchmark này là phiên bản `safe_lag_v2` (chứ chưa phải v3).

### 5.3 Chọn 5 Series Đại Diện

Tiêu chí lựa chọn tự động dựa trên stats của 1782 pairs (store × family):

| Pattern | Store | Family | Chỉ số đặc trưng |
|---------|-------|--------|-----------------|
| high_stable | 44 | GROCERY I | mean=9732.2, cv=0.369 |
| low_sales | 19 | BEAUTY | mean=1.590, zero_ratio=0.282 |
| seasonality | 52 | MEATS | acf_lag7=0.942 |
| many_zeros | 1 | BABY CARE | zero_ratio=1.000 |
| high_volatility | 19 | LAWN AND GARDEN | cv=28.899, max_ratio=1112.7 |

Thống kê tổng quan 1782 pairs:

```
      mean     std       cv  zero_ratio
mean  356.8   194.8    1.456       0.314
std   960.1   502.4    2.139       0.324
50%    19.8    19.8    0.998       0.309
max  9732.2  5584.7   28.899       1.000
```

### 5.4 Model & Training

```python
# Primary: SARIMAX(1,1,1)(1,1,1,7) — seasonal period = 7 ngày
model = SARIMAX(series_log, order=(1,1,1), seasonal_order=(1,1,1,7),
                enforce_stationarity=False, enforce_invertibility=False)
fit = model.fit(disp=False, maxiter=50, method='lbfgs')

# Fallback: ARIMA(1,1,1) nếu timeout >60s hoặc fit thất bại
# n_train = 1669 ngày/series
```

**Training log** (thực tế chạy):

```
store 44 - GROCERY I:       SARIMAX(1,1,1)(1,1,1,7), RMSLE = 0.1951  (1s)
store 19 - BEAUTY:          SARIMAX(1,1,1)(1,1,1,7), RMSLE = 0.3556  (1s)
store 52 - MEATS:           SARIMAX(1,1,1)(1,1,1,7), RMSLE = 0.3098  (1s)
store  1 - BABY CARE:       SARIMAX(1,1,1)(1,1,1,7), RMSLE = 0.0000  (1s)  ← all zeros
store 19 - LAWN AND GARDEN: SARIMAX(1,1,1)(1,1,1,7), RMSLE = 0.0071  (1s)
```

> BABY CARE: series all-zeros toàn training → SARIMA dự báo zero đúng hoàn toàn (RMSLE=0). ConvergenceWarning xuất hiện nhưng kết quả vẫn hợp lệ trong trường hợp này.

### 5.5 Kết Quả So Sánh (Aug 01–15, 15 ngày)

ML models dùng để so sánh là `lgb_safe_lag_v2_model.pkl` và `xgb_safe_lag_v2_model.pkl` (phiên bản cũ hơn v3):

```
 store  family           pattern      sarima     lgb     xgb
     1  BABY CARE        many_zeros   0.0000  0.0216  0.0330
    19  LAWN AND GARDEN  high_vol     0.0071  0.0442  0.0435
    44  GROCERY I        high_stable  0.1951  0.1465  0.1654
    52  MEATS            seasonality  0.3098  0.1243  0.1702
    19  BEAUTY           low_sales    0.3556  0.3135  0.3164
```

### 5.6 Phân Tích Kết Quả

| Pattern | Kết quả | Nhận xét |
|---------|---------|---------|
| **many_zeros** | SARIMA thắng (0.0000 vs LGB 0.0216) | Trivial: series all-zero, SARIMA dự báo đúng mặc nhiên |
| **high_volatility** | SARIMA thắng (0.0071 vs LGB 0.0442) | LAWN AND GARDEN cực kỳ volatile; SARIMA may mắn ở 15 ngày này |
| **high_stable** | LGB thắng (0.1465 vs SARIMA 0.1951) | GROCERY I volume lớn, ML khai thác cross-store/family info tốt hơn |
| **seasonality** | LGB thắng rõ (0.1243 vs SARIMA 0.3098) | MEATS có weekly seasonality, nhưng ML học từ toàn bộ store+family |
| **low_sales** | LGB thắng nhẹ (0.3135 vs SARIMA 0.3556) | Cả hai khó với BEAUTY sales thấp |

**Kết luận**: ML > SARIMA ở 3/5 patterns có ý nghĩa thực tế (high_stable, seasonality, low_sales). SARIMA chỉ thắng ở edge cases.

**Output**: `notebooks/06_modeling/ARIMA/arima_benchmark_results.csv`

---

## 6. Model File Catalog (v3)

| File | Model | Trạng thái |
|------|-------|-----------|
| `models/lightgbm_safe_lag_v3_optuna_best_params.json` | LightGBM v3 | Chưa tạo |
| `models/lightgbm_safe_lag_v3_model.pkl` | LightGBM v3 | Chưa tạo |
| `notebooks/08_forecasting/lgb_safe_lag_v3_model.pkl` | LightGBM v3 | Chưa tạo |
| `models/xgboost_safe_lag_v3_optuna_best_params.json` | XGBoost v3 | Chưa tạo |
| `models/xgboost_safe_lag_v3_model.pkl` | XGBoost v3 | Chưa tạo |
| `notebooks/08_forecasting/xgb_safe_lag_v3_model.pkl` | XGBoost v3 | Chưa tạo |
| `notebooks/08_forecasting/xgb_v3_label_encoders.pkl` | XGBoost v3 | Chưa tạo |
| `notebooks/06_modeling/ARIMA/arima_benchmark_results.csv` | SARIMA | **Đã có** |
