# Hướng Dẫn Sử Dụng Dataset — Từ Issue #2 Trở Đi

> **Dự án:** Corporación Favorita Store Sales Forecasting · Ecuador 2013–2017
> **Metric:** RMSLE · **Target transform:** `log1p(sales)` · **Inverse:** `expm1(y_pred)`

---

## 1. Tổng Hợp Dataset Đã Được Tạo Ra

### 1.1 Từ Feature Engineering (`notebooks/04_feature_engineering/features/`)

| File | Kích Thước | Nội Dung | Tạo Bởi |
|------|-----------|----------|---------|
| `data/processed/train_temporal_features.csv` | 480 MB | 3,000,888 × 27 — 10 đặc trưng thời gian (year, month, day_of_week…) + 7 lag + 4 rolling | `feature_temporal.ipynb` |
| `data/processed/train_holiday_features.csv` | 181 MB | 3,000,888 × 15 — 9 đặc trưng ngày lễ (national/regional/local holiday, carnaval, earthquake, halo days) | `feature_holiday.ipynb` |
| `data/processed/train_oil_store_features.csv` | 453 MB | 3,000,888 × 17 — 5 đặc trưng giá dầu (oil_price, lag_7/14, rolling_28, pct_change) + 3 store encoding | `feature_oil_and_store.ipynb` |
| `data/processed/train_external_features.csv` | 428 MB | 3,000,888 × 15 — Kết hợp oil features + store features (cluster, store_type_encoded, city_freq, state_freq) | `feature_external.ipynb` |
| `data/processed/train_target_encoding.csv` | 223 MB | 3,000,888 × 8 — `store_family_te`: target encoding KFold OOF cho cặp (store, family) | `feature_target_encoding.ipynb` |
| `data/processed/test_target_encoding.csv` | 1.98 MB | 28,512 × 7 — `store_family_te` cho tập test (fit trên toàn bộ train) | `feature_target_encoding.ipynb` |

> **Lưu ý:** Thư mục `data/processed/cleaned/` chứa bản sao của các file trên — **không dùng cho modeling**, chỉ là backup trung gian từ quá trình merge.

---

### 1.2 Từ Issue #1 Model Setup (`models/issue1_model_setup.ipynb`)

| File | Kích Thước | Nội Dung | Dùng Cho |
|------|-----------|----------|---------|
| `data/processed/splits/train_features.csv` | 732 MB | 2,804,868 × 43 — Ma trận đặc trưng tập train (2013-01-01 → 2017-04-27) | Issue #3, #4, #5 |
| `data/processed/splits/train_target.csv` | 41 MB | 2,804,868 × 1 — `sales_log = log1p(sales)` tập train | Issue #3, #4, #5 |
| `data/processed/splits/val_features.csv` | 6.9 MB | 25,353 × 43 — Ma trận đặc trưng tập validation (2017-04-28 → 2017-05-12) | Issue #2, #3, #4, #5 |
| `data/processed/splits/val_target.csv` | 444 KB | 25,353 × 1 — `sales_log` tập validation (log scale) | Issue #3, #4 |
| `data/processed/splits/val_target_original.csv` | 166 KB | 25,353 × 1 — `sales` tập validation (thang gốc) — **dùng để tính RMSLE** | Issue #2, #3, #4, #5 |
| `data/processed/splits/test_features.csv` | 683 KB | 28,512 × 3 — Đặc trưng tập holdout cuộc thi (store_nbr, onpromotion, store_family_te) | Issue #5 |
| `data/processed/splits/split_metadata.csv` | < 1 KB | Thông tin meta: ngày chia tập, số dòng, số đặc trưng, metric | Tham khảo |
| `models/feature_columns.txt` | < 1 KB | Danh sách 43 tên đặc trưng (1 dòng/tên) — đảm bảo đúng thứ tự cột | Issue #3, #4, #5 |

---

### 1.3 File Nguồn Quan Trọng (Không Được Tạo Lại)

| File | Kích Thước | Nội Dung |
|------|-----------|----------|
| `data/processed/train_final.csv` | 937 MB | 2,830,221 × 51 — Dataset hoàn chỉnh: sales + toàn bộ 43 đặc trưng đã merge, **có cột `sales`** |
| `data/processed/test_final.csv` | 1.98 MB | 28,512 × 7 — Tập holdout cuộc thi (không có nhãn `sales`) |

---

## 2. Dataset Dùng Cho Issue #2 — ARIMA / SARIMA

ARIMA/SARIMA là mô hình univariate — chỉ cần chuỗi thời gian `sales` theo ngày cho từng cặp (store, family). Không sử dụng ma trận đặc trưng 43 cột.

### ✅ File cần dùng

| File | Lý Do |
|------|-------|
| `data/processed/train_final.csv` | **File chính.** Chứa cột `sales`, `date`, `store_nbr`, `family` — lọc 5 cặp đại diện để lấy chuỗi thời gian |
| `data/processed/splits/val_target_original.csv` | Nhãn validation thang gốc — tính RMSLE so sánh với Issue #3, #4 |
| `data/processed/splits/val_features.csv` | Lấy `store_nbr` + đặc trưng thời gian để xác định 25,353 dòng validation thuộc cặp (store, family) nào |

### Gợi ý 5 cặp đại diện để train ARIMA

| Nhóm | Tiêu Chí Chọn | Cách Tìm |
|------|--------------|---------|
| High stable | `sales` cao, ít biến động | `store_family_te` cao, `rolling_std_7` thấp |
| Low sales | Doanh số thấp đều | Lọc cặp có median thấp |
| Clear seasonality | Đỉnh tháng 12 rõ | Kiểm tra ACF/PACF theo tháng |
| Many zeros | > 50% giá trị 0 | Đếm `sales == 0` theo cặp |
| High volatility | Độ lệch chuẩn cao | `rolling_std_7` hoặc `std` cao |

### ❌ File không cần ở Issue #2

| File | Lý Do Không Cần |
|------|----------------|
| `splits/train_features.csv` | ARIMA không dùng exogenous features (trừ SARIMAX) |
| `splits/train_target.csv` | Dùng `sales` gốc, không phải log-transformed |
| `splits/test_features.csv` | Tập holdout cuộc thi — chỉ dùng ở Issue #5 |
| `models/feature_columns.txt` | Không cần danh sách feature cho ARIMA thuần |
| Các file `train_*_features.csv` | Feature engineering intermediates — đã merge vào `train_final.csv` |

---

## 3. Dataset Dùng Cho Issue #3 — LightGBM

| File | Vai Trò |
|------|---------|
| `data/processed/splits/train_features.csv` | Ma trận X_train (2,804,868 × 43) |
| `data/processed/splits/train_target.csv` | y_train log-transformed |
| `data/processed/splits/val_features.csv` | Ma trận X_val để predict |
| `data/processed/splits/val_target.csv` | y_val log scale — dùng cho early stopping |
| `data/processed/splits/val_target_original.csv` | Tính RMSLE cuối (sau `expm1`) |
| `models/feature_columns.txt` | Load đúng thứ tự 43 cột: `cols = open(...).read().splitlines()` |

---

## 4. Dataset Dùng Cho Issue #4 — XGBoost

Giống Issue #3 — dùng cùng bộ file:

| File | Vai Trò |
|------|---------|
| `data/processed/splits/train_features.csv` | Ma trận X_train |
| `data/processed/splits/train_target.csv` | y_train log-transformed |
| `data/processed/splits/val_features.csv` | Ma trận X_val |
| `data/processed/splits/val_target.csv` | y_val log scale |
| `data/processed/splits/val_target_original.csv` | Tính RMSLE cuối |
| `models/feature_columns.txt` | Đảm bảo đúng thứ tự cột |

---

## 5. Dataset Dùng Cho Issue #5 — Ensemble

Issue #5 kết hợp predictions từ các mô hình trước. Cần:

| File | Nguồn | Vai Trò |
|------|-------|---------|
| `models/baseline/lgbm_val_predictions.csv` *(sẽ tạo)* | Issue #3 | Dự đoán LightGBM trên val set |
| `models/baseline/xgb_val_predictions.csv` *(sẽ tạo)* | Issue #4 | Dự đoán XGBoost trên val set |
| `models/baseline/arima_val_predictions.csv` *(sẽ tạo)* | Issue #2 | Dự đoán ARIMA cho 5 cặp đại diện |
| `data/processed/splits/val_target_original.csv` | Issue #1 | Ground truth để tối ưu trọng số ensemble |
| `data/processed/splits/test_features.csv` | Issue #1 | Tạo dự đoán cuối cho nộp bài |
| `data/processed/splits/val_features.csv` | Issue #1 | Ghép predictions với store/family info |

> **Lưu ý:** Các file `*_val_predictions.csv` phải lưu theo cấu trúc `[store_nbr, family, date, y_pred]` để có thể join với `val_target_original.csv` khi tính RMSLE ensemble.

---

## 6. Sơ Đồ Luồng Dữ Liệu

```
RAW DATA (data/raw/)
    │
    ▼
data/processed/train_cleaned.csv          (preprocessing)
data/processed/test_cleaned.csv
    │
    ▼
[Feature Engineering Notebooks]
    ├── train_temporal_features.csv        (lag, rolling, calendar)
    ├── train_holiday_features.csv         (holiday flags, halo effects)
    ├── train_oil_store_features.csv       (oil price, store encoding)
    ├── train_external_features.csv        (oil + store combined)
    ├── train_target_encoding.csv          (store_family_te, KFold OOF)
    └── test_target_encoding.csv           (store_family_te, full-train fit)
    │
    ▼
data/processed/train_final.csv            ← MERGE của tất cả features (937 MB)
data/processed/test_final.csv             ← Test holdout (không có sales)
    │
    ▼
[Issue #1: models/issue1_model_setup.ipynb]
    │
    ├── data/processed/splits/
    │       ├── train_features.csv         → Issue #3, #4
    │       ├── train_target.csv           → Issue #3, #4
    │       ├── val_features.csv           → Issue #2, #3, #4, #5
    │       ├── val_target.csv             → Issue #3, #4
    │       ├── val_target_original.csv    → Issue #2, #3, #4, #5  ← RMSLE
    │       ├── test_features.csv          → Issue #5
    │       └── split_metadata.csv         → Tham khảo
    │
    └── models/feature_columns.txt         → Issue #3, #4, #5
    │
    ├── Issue #2: ARIMA/SARIMA
    │       └── Input: train_final.csv + val_target_original.csv
    │       └── Output: models/baseline/arima_val_predictions.csv
    │
    ├── Issue #3: LightGBM
    │       └── Input: splits/train_features + train_target + val_*
    │       └── Output: models/baseline/lgbm_val_predictions.csv
    │
    ├── Issue #4: XGBoost
    │       └── Input: splits/train_features + train_target + val_*
    │       └── Output: models/baseline/xgb_val_predictions.csv
    │
    └── Issue #5: Ensemble
            └── Input: arima + lgbm + xgb predictions + val_target_original
            └── Output: models/ensemble/final_submission.csv
```

---

## 7. Lưu Ý Quan Trọng

### Thứ tự cột phải nhất quán
Khi load `train_features.csv` và `val_features.csv`, luôn dùng `feature_columns.txt` để chọn cột theo đúng thứ tự:
```python
feature_cols = open("models/feature_columns.txt").read().splitlines()
X_train = pd.read_csv("splits/train_features.csv")[feature_cols]
X_val   = pd.read_csv("splits/val_features.csv")[feature_cols]
```

### Inverse transform bắt buộc trước khi tính RMSLE
Mô hình predict ra log scale — phải chuyển về thang gốc trước khi so sánh:
```python
from sklearn.metrics import mean_squared_log_error
import numpy as np

y_pred_log   = model.predict(X_val)
y_pred_orig  = np.expm1(y_pred_log)          # Inverse của log1p
y_true_orig  = pd.read_csv("splits/val_target_original.csv")["sales"]
rmsle        = np.sqrt(mean_squared_log_error(y_true_orig, np.clip(y_pred_orig, 0, None)))
```

### Issue #2 dùng `train_final.csv`, không dùng `splits/`
ARIMA cần chuỗi thời gian `sales` nguyên gốc — file `splits/train_target.csv` đã được log1p. Load trực tiếp từ `train_final.csv` và lọc theo `(store_nbr, family)`:
```python
df = pd.read_csv("data/processed/train_final.csv", parse_dates=["date"])
ts = df[(df["store_nbr"] == 44) & (df["family"] == "GROCERY I")][["date", "sales"]].set_index("date")
```

### Validation split thực tế ≠ mô tả ban đầu
`train_final.csv` kết thúc tại **2017-05-12**, không phải 2017-07-31.
Validation trong Issue #1 là **2017-04-28 → 2017-05-12** (15 ngày).
Competition holdout `test_final.csv` là **2017-08-16 → 2017-08-31** — không có nhãn `sales`.

### `test_features.csv` chỉ có 3 cột
`splits/test_features.csv` (28,512 × 3) chỉ chứa: `store_nbr`, `onpromotion`, `store_family_te`.
Các mô hình tree-based (LightGBM, XGBoost) không thể predict trực tiếp từ file này — cần bổ sung temporal features từ `test_final.csv` trước.

### Không dùng file trong `data/processed/cleaned/`
Thư mục `cleaned/` chứa bản sao trung gian — nội dung trùng với các file trong `data/processed/`. Chỉ dùng file tại `data/processed/` và `data/processed/splits/`.
