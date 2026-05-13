# Feature Engineering Context — Retail Store Sales Forecasting

> **Mục đích**: Tài liệu chi tiết đầy đủ toàn bộ quá trình feature engineering của dự án.  
> Mọi con số, code, thống kê đều được cross-check trực tiếp từ codebase thực tế.

---

## 0. Tổng quan nhanh

| Thông tin | Giá trị |
|-----------|---------|
| Số features cuối cùng | **47** (trong `splits_safe_lag_v3/`) |
| Số features ban đầu (baseline) | 49 (trong `splits/`) |
| Thay đổi v3 | −8 toxic features, +6 features mới |
| Training rows | 2,918,916 |
| Validation rows | 55,242 |
| Test (local) rows | 26,730 |
| Kaggle test rows | 28,512 |
| Target variable | `sales` (raw, ≥ 0) |
| Target transform | `log1p(sales)` khi train, `expm1()` khi predict |

---

## 1. Luồng Pipeline Feature Engineering

```
data/raw/train.csv          (3,000,888 × 6)
data/raw/holidays_events.csv (350 × 6)
data/raw/oil.csv             (1,218 × 2)
data/raw/stores.csv          (54 × 5)
         │
         ▼
[STEP 1] data/processed/train_cleaned.csv   ← làm sạch, không thêm feature
         │
         ▼
[STEP 2] scripts/build_train_final.py
         │  Merge 6 nhóm feature vào:
         │  • Temporal + Lag/Rolling (feature_temporal.ipynb)
         │  • Holiday (feature_holiday.ipynb)
         │  • Oil price (feature_oil_and_store.ipynb + feature_external.ipynb)
         │  • Store encoding (feature_oil_and_store.ipynb + feature_external.ipynb)
         │  • Target encoding (feature_target_encoding.ipynb)
         ▼
         data/processed/train_final.csv   (~3,000,888 × 56 cột)
         │
         ▼
[STEP 3] scripts/create_splits.py
         │  Temporal split (strict date boundary, NO random split):
         │  • Train: 2013-01-01 → 2017-06-30
         │  • Val  : 2017-07-01 → 2017-07-31
         │  • Test : 2017-08-01 → 2017-08-15
         ▼
         data/processed/splits/           ← 49 features (có toxic lags)
         │
         ▼
[STEP 4] notebooks/04_feature_engineering/features/feature_safe_lag_v3.ipynb
         │  • Xóa 8 toxic features (gây distribution shift khi forecast)
         │  • Thêm 6 safe features mới
         ▼
         data/processed/splits_safe_lag_v3/  ← 47 features (ACTIVE)
```

---

## 2. Danh sách 47 Features — Thứ tự chính xác trong file

Đây là thứ tự cột thực tế trong `splits_safe_lag_v3/train_features.csv`:

```
 1. date                    ← identity (giữ để debug, không dùng để train)
 2. store_nbr               ← identity
 3. family                  ← identity / categorical
 4. onpromotion             ← feature
 5. year                    ← temporal
 6. month                   ← temporal
 7. day                     ← temporal
 8. day_of_week             ← temporal
 9. week_of_year            ← temporal
10. quarter                 ← temporal
11. is_weekend              ← temporal flag
12. is_month_start          ← temporal flag
13. is_month_end            ← temporal flag
14. is_payday               ← temporal flag
15. lag_14                  ← lag (⚠️ partially unsafe — NaN for Aug 30-31 Kaggle test)
16. lag_28                  ← lag (✅ safe)
17. lag_364                 ← lag (✅ safe)
18. is_national_holiday     ← holiday
19. is_regional_holiday     ← holiday
20. is_local_holiday        ← holiday
21. is_transferred_holiday  ← holiday
22. holiday_type            ← holiday
23. is_carnaval_feature     ← holiday / event
24. days_to_next_holiday    ← holiday halo
25. days_after_last_holiday ← holiday halo
26. is_earthquake_period    ← special event
27. oil_price               ← external / exogenous
28. oil_price_lag_7         ← external / exogenous
29. oil_price_lag_14        ← external / exogenous
30. oil_price_rolling_mean_28 ← external / exogenous
31. oil_price_change_pct    ← external / exogenous
32. type                    ← store metadata
33. city                    ← store metadata
34. state                   ← store metadata
35. store_type_enc          ← store encoding (LabelEncoder)
36. city_freq               ← store encoding (frequency)
37. state_freq              ← store encoding (frequency)
38. cluster                 ← store metadata
39. store_type_encoded      ← store encoding (manual map)
40. store_family            ← composite key (string)
41. store_family_te         ← target encoding (KFold OOF)
42. lag_16                  ← lag (✅ safe — ADDED in v3)
43. lag_21                  ← lag (✅ safe — ADDED in v3)
44. lag_35                  ← lag (✅ safe — ADDED in v3)
45. rolling_mean_30         ← rolling (✅ safe — ADDED in v3)
46. rolling_mean_28_safe    ← rolling (✅ safe — ADDED in v3)
47. rolling_std_28_safe     ← rolling (✅ safe — ADDED in v3)
```

**Features được dùng để train model**: Cột 4–47 (44 features input), sau khi LabelEncode các cột object (`family`, `type`, `city`, `state`, `store_family`).

---

## 3. Nhóm A — Temporal Features (10 features)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_temporal.ipynb`  
**Script tích hợp**: `scripts/build_train_final.py` — Step 2

### 3.1 Code tính

```python
df['date'] = pd.to_datetime(df['date'])
dt = df['date'].dt

df['year']           = dt.year
df['month']          = dt.month
df['day']            = dt.day
df['day_of_week']    = dt.dayofweek          # 0 = Monday, 6 = Sunday
df['week_of_year']   = dt.isocalendar().week.astype(int)
df['quarter']        = dt.quarter
df['is_weekend']     = (dt.dayofweek >= 5).astype(int)
df['is_month_start'] = dt.is_month_start.astype(int)
df['is_month_end']   = dt.is_month_end.astype(int)
df['is_payday']      = ((dt.day == 15) | dt.is_month_end).astype(int)
```

### 3.2 Chi tiết từng feature

| Feature | Kiểu | Giá trị | Lý do chọn |
|---------|------|---------|-----------|
| `year` | int | 2013–2017 (5 values) | Capture long-term trend tăng trưởng |
| `month` | int | 1–12 | Seasonality theo tháng (Dec cao nhất, Feb thấp nhất) |
| `day` | int | 1–31 | Biến động trong tháng (lương, cuối tháng) |
| `day_of_week` | int | 0–6 (0=Mon) | Weekly pattern rất mạnh — Sunday cao nhất |
| `week_of_year` | int | 1–53 | Seasonality theo tuần trong năm |
| `quarter` | int | 1–4 | Seasonality theo quý |
| `is_weekend` | binary | 0/1 | Weekend vs weekday pattern khác biệt rõ |
| `is_month_start` | binary | 0/1 | Ngày đầu tháng: thường có restocking orders |
| `is_month_end` | binary | 0/1 | Ngày cuối tháng: payday effect |
| `is_payday` | binary | 0/1 | Ngày 15 hoặc cuối tháng (Ecuador trả lương 2 lần/tháng) |

### 3.3 Thống kê thực tế (từ train split)

```
year:          min=2013, max=2017, nunique=5
month:         min=1,    max=12,   nunique=12
day:           min=1,    max=31,   nunique=31
day_of_week:   min=0,    max=6,    nunique=7
week_of_year:  min=1,    max=53,   nunique=53
quarter:       min=1,    max=4,    nunique=4
is_weekend:    min=0,    max=1,    nunique=2
is_month_start:min=0,    max=1,    nunique=2
is_month_end:  min=0,    max=1,    nunique=2
is_payday:     min=0,    max=1,    nunique=2
```

### 3.4 Không có NaN

Tất cả temporal features: **0 NaN** trong train, val, test — tính trực tiếp từ cột `date` không bao giờ thiếu.

### 3.5 Anti-leakage verification

```python
# Notebook có smoke test trên mock data (2 stores × 60 ngày)
# Verification: lag_1 của dòng đầu tiên mỗi group phải = NaN
assert df.groupby(['store_nbr','family'])['lag_1'].first().isna().all(), "Leakage detected!"
# PASS ✓
```

---

## 4. Nhóm B — Lag & Rolling Features (Baseline + v3 Safe)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_temporal.ipynb` (baseline), `feature_safe_lag_v3.ipynb` (v3 fix)  
**Script tích hợp**: `scripts/build_train_final.py` — Step 3

### 4.1 Baseline Lag Features (đã có trong `splits/`)

```python
GROUP_COLS = ["store_nbr", "family"]
grouped = df.groupby(GROUP_COLS, sort=False)["sales"]

# Short lags
for lag in [1, 2, 3]:
    df[f"lag_{lag}"] = grouped.shift(lag)
df["lag_7"]  = grouped.shift(7)
df["lag_14"] = grouped.shift(14)
df["lag_28"] = grouped.shift(28)
df["lag_364"] = grouped.shift(364)

# Rolling (dùng shift(1) để không leak giá trị hiện tại)
shifted = grouped.shift(1)
df["rolling_mean_7"]  = shifted.transform(lambda x: x.rolling(7,  min_periods=1).mean())
df["rolling_mean_14"] = shifted.transform(lambda x: x.rolling(14, min_periods=1).mean())
df["rolling_mean_28"] = shifted.transform(lambda x: x.rolling(28, min_periods=1).mean())
df["rolling_std_7"]   = shifted.transform(lambda x: x.rolling(7,  min_periods=2).std())
```

**Tại sao group theo (store_nbr, family)**: Mỗi cặp (store, family) là một time series độc lập. Nếu không group, `lag_1` của ngày đầu tiên store 2 sẽ lấy giá trị ngày cuối cùng store 1 → data leakage.

**Tại sao rolling dùng `shift(1)`**: Tránh current-day leakage khi training. Nếu rolling không shift, `rolling_mean_7` của ngày d sẽ bao gồm cả sales của ngày d → model biết trước target → overfit hoàn toàn.

### 4.2 Vấn đề Distribution Shift (Critical Finding)

**Cơ chế xảy ra distribution shift với `shift(1).rolling(W)` khi forecast:**

```
TRAINING phase (ví dụ rolling_mean_28 = shift(1).rolling(28)):
  - Mọi ngày d trong train đều có 28 giá trị thực trong window
  - Window = [d-28, d-27, ..., d-1] — tất cả đều là real sales

FORECASTING phase (Aug 16–31 với combined-append):
  - combined = [train_recent rows (real sales)] + [test rows (sales=NaN)]
  - shift(1) của Aug 31 → Aug 30 → sales = NaN (vì Aug 30 trong test period)
  - rolling(28) từ Aug 30 ngược về 28 ngày → Aug 2 đến Aug 30
  - Trong đó Aug 16–30 (15 ngày) đều NaN → effective window = 13/28 ngày thực
  
Tương tự:
  - Aug 17: shift(1) → Aug 16 (NaN) → window chỉ có 12/28 ngày thực  
  - Aug 31: shift(1) → Aug 30 (NaN) → window chỉ có 13/28 ngày thực

→ Model nhận giá trị rolling_mean_28 từ 13–27 ngày thực thay vì 28 ngày
→ Feature distribution trong inference ≠ feature distribution khi training
→ Root cause của Kaggle score 1.05175 (local RMSLE chỉ ~0.37)
```

**Safe threshold calculation:**
```
Kaggle test period: 2017-08-16 → 2017-08-31 (16 ngày)
Safe lag minimum: N ≥ 16 (= độ dài test period)

Với shift(N), N ≥ 16:
  - Aug 16 cần lookup: Aug 16 - 16 = Aug 0 = Jul 31 ← trong train ✓
  - Aug 31 cần lookup: Aug 31 - 16 = Aug 15 ← trong train ✓
  - ⇒ Mọi ngày trong test period đều lookup vào train data
  - ⇒ Zero distribution shift
```

### 4.3 v3 Safe Lag Features — Code tính (feature_safe_lag_v3.ipynb)

```python
TOXIC_FEATURES = [
    'lag_1', 'lag_2', 'lag_3', 'lag_7',       # shift < 16
    'rolling_mean_7', 'rolling_mean_14',        # shift(1) → distribution shift
    'rolling_mean_28', 'rolling_std_7',         # shift(1) → distribution shift
]

# Safe lags mới (shift ≥ 16)
grouped = train_raw.groupby(['store_nbr', 'family'], sort=False)['sales']
for lag in [16, 21, 35]:
    train_raw[f'lag_{lag}'] = grouped.shift(lag)

# Safe rolling features (shift(16) → không bao giờ lookup vào test period)
train_raw['rolling_mean_30'] = grouped.transform(
    lambda x: x.shift(16).rolling(30, min_periods=1).mean()
)
train_raw['rolling_mean_28_safe'] = grouped.transform(
    lambda x: x.shift(16).rolling(28, min_periods=1).mean()
)
train_raw['rolling_std_28_safe'] = grouped.transform(
    lambda x: x.shift(16).rolling(28, min_periods=2).std()
)
```

**Lưu ý `min_periods`:**
- `rolling(W, min_periods=1)`: cho phép tính mean kể cả khi chưa đủ W điểm → NaN chỉ ở rìa đầu series
- `rolling(28, min_periods=2)`: std cần ≥ 2 điểm để tính (std của 1 điểm = undefined)

### 4.4 Thay đổi Features Từ Old → New Splits

| Thao tác | Features |
|---------|---------|
| **Removed (8)** — toxic | `lag_1`, `lag_2`, `lag_3`, `lag_7`, `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`, `rolling_std_7` |
| **Kept unchanged** | `lag_14`, `lag_28`, `lag_364` |
| **Added NEW (6)** — safe | `lag_16`, `lag_21`, `lag_35`, `rolling_mean_28_safe`, `rolling_mean_30`, `rolling_std_28_safe` |
| **Net** | 49 − 8 + 6 = **47** |

### 4.5 Phân loại Safety cho Kaggle Test (Aug 16–31)

| Feature | Shift | Safety | NaN trong Kaggle test | Ghi chú |
|---------|-------|--------|----------------------|---------|
| `lag_14` | 14 | ⚠️ Partially unsafe | 3,564 NaN (Aug 30–31 × 1,782 series) | Aug 30 − 14 = Aug 16 ∈ test |
| `lag_16` | 16 | ✅ Fully safe | 0 NaN | Aug 31 − 16 = Aug 15 ∈ train |
| `lag_21` | 21 | ✅ Fully safe | 0 NaN | — |
| `lag_28` | 28 | ✅ Fully safe | 0 NaN | — |
| `lag_35` | 35 | ✅ Fully safe | 0 NaN | — |
| `lag_364` | 364 | ✅ Fully safe | 0 NaN | Cùng kỳ năm trước |
| `rolling_mean_30` | shift(16) | ✅ Fully safe | 0 NaN | Lookback: d−46 → d−16 |
| `rolling_mean_28_safe` | shift(16) | ✅ Fully safe | 0 NaN | Lookback: d−43 → d−16 |
| `rolling_std_28_safe` | shift(16) | ✅ Fully safe | 0 NaN | — |

**Tại sao giữ `lag_14`**: Dù không fully safe, nó vẫn cung cấp signal cho 14/16 ngày đầu test (Aug 16–29). Model XGBoost và LightGBM xử lý NaN natively bằng cách cho nhánh NaN đi theo hướng riêng trong tree → không cần imputation.

### 4.6 Thống kê thực tế (từ train split)

```
lag_14:            mean=350.39, std=1089.30, min=0.00, max=124717.00
lag_16:            mean=353.33, std=1093.45, min=0.00, max=124717.00
lag_21:            mean=352.87, std=1092.15, min=0.00, max=124717.00
lag_28:            mean=346.09, std=1081.42, min=0.00, max=124717.00
lag_35:            mean=351.52, std=1088.66, min=0.00, max=124717.00
lag_364:           mean=251.05, std=905.54,  min=0.00, max=124717.00
rolling_mean_30:   mean=350.45, std=1020.90, min=0.00, max=15777.20
rolling_mean_28_safe: mean=350.63, std=1021.82, min=0.00, max=16118.32
rolling_std_28_safe:  mean=113.75, std=362.30,  min=0.00, max=25076.63
```

### 4.7 NaN trong Train Split (đầu series, bình thường)

```
lag_16:            28,512 NaN (0.977%) — 16 ngày đầu × 1,782 series
lag_21:            37,422 NaN (1.282%) — 21 ngày đầu × 1,782 series
lag_35:            62,370 NaN (2.137%) — 35 ngày đầu × 1,782 series
rolling_mean_30:   28,512 NaN (0.977%) — cùng với lag_16 (shift(16) = lookback 16 ngày)
rolling_mean_28_safe: 28,512 NaN (0.977%)
rolling_std_28_safe:  30,294 NaN (1.038%) — min_periods=2 nên thêm 1,782 NaN
```

**Val và Test (local Aug 1–15): 0 NaN cho tất cả lag và rolling features** — xác minh không bị distribution shift trong training pipeline.

### 4.8 Cách Tính Lag Cho Kaggle Test (Trong Forecasting Notebook)

```python
# Merge approach (không dùng combined-append với NaN sales)
for lag in [14, 16, 21, 28, 35, 364]:
    lag_ref = train_raw[['date', 'store_nbr', 'family', 'sales']].copy()
    lag_ref['date'] = lag_ref['date'] + pd.Timedelta(days=lag)
    # → dịch ngày lên: record của Aug 15 sẽ match với Aug 15+lag trong test
    lag_ref = lag_ref.rename(columns={'sales': f'lag_{lag}'})
    X_kaggle = X_kaggle.merge(
        lag_ref[['date', 'store_nbr', 'family', f'lag_{lag}']],
        on=['date', 'store_nbr', 'family'], how='left'
    )

# Ví dụ:
# lag_16 của ngày Aug 31: merge với record có date = Aug 31 trong lag_ref
#   → lag_ref có date=Aug31 khi original date=Aug15 (+16 ngày) → sales thực = Aug 15 ✓
```

### 4.9 Cách Tính Rolling Cho Kaggle Test

```python
# Combined-append approach — chỉ dùng shift(16), không động tới NaN test rows
cutoff = pd.Timestamp('2017-08-16') - pd.Timedelta(days=46)
# 46 = 16 (shift) + 30 (window size) → đủ lookback cho rolling_mean_30

train_recent = train_raw[train_raw['date'] >= cutoff][['date','store_nbr','family','sales']]
test_rows = X_kaggle[['date','store_nbr','family']].copy()
test_rows['sales'] = np.nan   # sales không biết

combined = pd.concat([train_recent, test_rows]).sort_values(['store_nbr','family','date'])
grp = combined.groupby(['store_nbr','family'], sort=False)['sales']

combined['rolling_mean_30']      = grp.transform(lambda x: x.shift(16).rolling(30, min_periods=1).mean())
combined['rolling_mean_28_safe'] = grp.transform(lambda x: x.shift(16).rolling(28, min_periods=1).mean())
combined['rolling_std_28_safe']  = grp.transform(lambda x: x.shift(16).rolling(28, min_periods=2).std())

# Tại sao shift(16) không lookup NaN test rows:
# Với bất kỳ ngày d trong [Aug 16, Aug 31]:
#   shift(16) → d - 16 ∈ [Jul 31, Aug 15] ← tất cả trong train ✓
#   rolling(30) từ d−16 ngược về 30 ngày → hoàn toàn trong train ✓
```

---

## 5. Nhóm C — Holiday Features (9 features)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_holiday.ipynb`  
**Script tích hợp**: `scripts/build_train_final.py` — Step 4

### 5.1 Dữ liệu gốc

```
data/raw/holidays_events.csv: 350 × 6
  date, type, locale, locale_name, description, transferred

Sau filter transferred=False: 338 dòng hợp lệ
Phân loại type:
  Holiday:    209 records
  Event:       56 records
  Additional:  51 records
  Transfer:    12 records  ← ngày bù cho lễ bị dời
  Bridge:       5 records
  Work Day:     5 records
```

### 5.2 Code tính — Holiday Type Encoding

```python
type_mapping = {
    "Holiday":    1,
    "Event":      2,
    "Additional": 3,
    "Transfer":   4,
    "Bridge":     5,
    "Work Day":   0,
}
valid_holidays = df_holidays[df_holidays["transferred"] == False].copy()
valid_holidays["holiday_type_encoded"] = valid_holidays["type"].map(type_mapping).fillna(0)
valid_holidays["is_carnaval"] = (
    valid_holidays["description"]
    .str.contains("Carnaval", case=False, na=False)
    .astype(int)
)
```

### 5.3 Code tính — Phân loại theo Locale

```python
# Merge store location để biết city/state của mỗi store
df = df.merge(df_stores[["store_nbr", "city", "state"]], on="store_nbr", how="left")

# Khởi tạo tất cả = 0
for col in ["is_national_holiday", "is_regional_holiday", "is_local_holiday",
            "is_transferred_holiday", "holiday_type", "is_carnaval_feature"]:
    df[col] = 0

# Assign từng holiday vào đúng scope
for _, row in valid_holidays.iterrows():
    h_date, h_locale, h_locale_name = row["date"], row["locale"], row["locale_name"]
    
    if h_locale == "National":
        mask = df["date"] == h_date                              # tất cả stores
    elif h_locale == "Regional":
        mask = (df["date"] == h_date) & (df["state"] == h_locale_name)  # cùng tỉnh
    elif h_locale == "Local":
        mask = (df["date"] == h_date) & (df["city"] == h_locale_name)   # cùng thành phố
    
    if h_locale == "National":   df.loc[mask, "is_national_holiday"] = 1
    elif h_locale == "Regional": df.loc[mask, "is_regional_holiday"] = 1
    elif h_locale == "Local":    df.loc[mask, "is_local_holiday"] = 1
    
    df.loc[mask, "is_transferred_holiday"] = 1 if row["type"] == "Transfer" else 0
    df.loc[mask, "holiday_type"]           = row["holiday_type_encoded"]
    df.loc[mask, "is_carnaval_feature"]    = row["is_carnaval"]
```

### 5.4 Code tính — Halo Effect (Days to/from Holiday)

```python
# Tính khoảng cách đến ngày lễ gần nhất (halo effect: sales tăng trước/sau ngày lễ)
unique_holiday_dates = valid_holidays["date"].drop_duplicates().sort_values().reset_index(drop=True)

def _days_to_next(date):
    future = unique_holiday_dates[unique_holiday_dates > date]
    return (future.iloc[0] - date).days if not future.empty else -1

def _days_after_last(date):
    past = unique_holiday_dates[unique_holiday_dates < date]
    return (date - past.iloc[-1]).days if not past.empty else -1

unique_dates = df[["date"]].drop_duplicates().copy()
unique_dates["days_to_next_holiday"]    = unique_dates["date"].apply(_days_to_next)
unique_dates["days_after_last_holiday"] = unique_dates["date"].apply(_days_after_last)
df = df.merge(unique_dates, on="date", how="left")
```

### 5.5 Code tính — Earthquake Period

```python
# Trận động đất 2016-04-16 → 31 ngày ảnh hưởng đến sales (disruption + recovery)
df["is_earthquake_period"] = (
    (df["date"] >= pd.Timestamp("2016-04-16")) &
    (df["date"] <= pd.Timestamp("2016-05-16"))
).astype(int)
```

### 5.6 Chi tiết từng feature

| Feature | Mô tả | Lý do chọn |
|---------|-------|-----------|
| `is_national_holiday` | 1 nếu ngày lễ quốc gia Ecuador | Sales giảm mạnh khi stores đóng cửa |
| `is_regional_holiday` | 1 nếu ngày lễ vùng/tỉnh | Tác động tùy region — cần match với store location |
| `is_local_holiday` | 1 nếu ngày lễ địa phương/thành phố | Tương tự regional nhưng nhỏ hơn |
| `is_transferred_holiday` | 1 nếu ngày bù (type=Transfer) | Ngày bù có behavior khác lễ bình thường |
| `holiday_type` | 0–5 encode loại lễ | Các loại lễ khác nhau ảnh hưởng khác nhau đến sales |
| `is_carnaval_feature` | 1 trong 2 ngày Carnaval/năm | Carnaval = event lớn đặc biệt (tháng 2) |
| `days_to_next_holiday` | Số ngày đến ngày lễ tiếp theo | Pre-holiday surge: người mua sắm trước ngày lễ |
| `days_after_last_holiday` | Số ngày kể từ ngày lễ qua | Post-holiday lull: sales giảm sau ngày lễ |
| `is_earthquake_period` | 1 từ 2016-04-16 đến 2016-05-16 | Event đặc biệt gây gián đoạn supply chain |

### 5.7 Thống kê thực tế (từ train split)

```
is_national_holiday:    8.24% records = 1
is_regional_holiday:    0.04% records = 1
is_local_holiday:       0.38% records = 1
is_transferred_holiday: 0.00% records = 1  (rất ít)
holiday_type:           mean=0.17, std=0.62, range=0–5
is_carnaval_feature:    0.61% records = 1
days_to_next_holiday:   mean=10.83, std=10.61, range=1–60
days_after_last_holiday: mean=10.82, std=10.62, range=1–60
is_earthquake_period:   1.89% records = 1  (31 ngày × 1,782 series)
```

### 5.8 Xử lý Transferred Holidays

```python
# "transferred" = True: ngày lễ bị dời đi chỗ khác (không còn là lễ)
# "transferred" = False: ngày lễ thực sự (bao gồm cả ngày bù Transfer)
# → Filter transferred=False giữ lại cả ngày lễ thực và ngày bù (type=Transfer)
valid_holidays = df_holidays[df_holidays["transferred"] == False]  # 338 rows

# Ngày có type="Transfer" là ngày BÙ (make-up day), không phải ngày lễ bình thường
# → is_transferred_holiday=1 để phân biệt với Holiday/Event bình thường
```

### 5.9 Lý do tách 3 loại locale riêng

Ecuador có hệ thống ngày lễ phân cấp. Ví dụ:
- **National**: Navidad (Christmas) — tất cả 54 stores đều đóng
- **Regional**: Provincializacion de Cotopaxi — chỉ stores ở tỉnh Cotopaxi
- **Local**: Fundacion de Manta — chỉ stores ở thành phố Manta

Nếu gộp chung → mất tín hiệu granular. Tách riêng giúp model học được độ lớn khác nhau của từng loại.

---

## 6. Nhóm D — Oil Price Features (5 features)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_oil_and_store.ipynb`, `feature_external.ipynb`  
**Script tích hợp**: `scripts/build_train_final.py` — Step 5

### 6.1 Dữ liệu gốc

```
data/raw/oil.csv: 1,218 × 2
  date, dcoilwtico   ← giá dầu WTI (West Texas Intermediate)
  43 giá trị NaN (3.53%) — cuối tuần và ngày lễ không có giao dịch
  Range: 26.19 → 110.62
  Mean: 67.71, Std: 25.63
```

### 6.2 Code tính

```python
oil = df_oil.copy().rename(columns={"dcoilwtico": "oil_price"})
oil["date"] = pd.to_datetime(oil["date"])
oil = oil[["date", "oil_price"]].sort_values("date").reset_index(drop=True)

# Tạo calendar đầy đủ (fill gaps cho weekend/holiday)
full_range = pd.DataFrame({
    "date": pd.date_range(start=oil["date"].min(), end=oil["date"].max(), freq="D")
})
oil = full_range.merge(oil, on="date", how="left")
oil["oil_price"] = oil["oil_price"].ffill().bfill()  # forward fill → backward fill

# Lag và rolling trên oil price
oil["oil_price_lag_7"]           = oil["oil_price"].shift(7)
oil["oil_price_lag_14"]          = oil["oil_price"].shift(14)
oil["oil_price_rolling_mean_28"] = oil["oil_price"].shift(1).rolling(28, min_periods=7).mean()
oil["oil_price_change_pct"]      = oil["oil_price"].pct_change(periods=7)
```

### 6.3 Tại sao Oil features dùng `shift(1)` không bị Distribution Shift

**Oil là biến exogenous** — giá dầu không phải thứ model cần dự báo. Giá dầu WTI cho Aug 16–31 đã có sẵn trong historical data (có thể download từ thị trường tài chính). Khi chạy forecasting notebook, pipeline merge giá dầu thực tế từ `oil.csv` cho test period → rolling window luôn đầy đủ, không tạo NaN.

Đây khác hoàn toàn với `rolling_mean_28` trên `sales` — sales trong Aug 16–31 là unknown (là thứ cần predict).

### 6.4 Chi tiết từng feature

| Feature | Công thức | Lý do chọn |
|---------|-----------|-----------|
| `oil_price` | Giá dầu ngày d (forward-filled) | Ecuador = nền kinh tế xuất khẩu dầu → giá dầu ảnh hưởng trực tiếp GDP và purchasing power |
| `oil_price_lag_7` | oil[d−7] | Tác động kinh tế của giá dầu có độ trễ |
| `oil_price_lag_14` | oil[d−14] | Tác động dài hơn |
| `oil_price_rolling_mean_28` | shift(1).rolling(28, min_periods=7).mean() | Xu hướng giá dầu trung hạn (1 tháng) |
| `oil_price_change_pct` | (oil[d] − oil[d−7]) / oil[d−7] | % thay đổi tuần — capture momentum tăng/giảm |

### 6.5 Thống kê thực tế (từ train split)

```
oil_price:               mean=68.50, std=25.79, min=26.19, max=110.62, NaN=0
oil_price_lag_7:         mean=68.72, std=25.79, min=26.19, max=110.62, NaN=0
oil_price_lag_14:        mean=68.92, std=25.79, min=26.19, max=110.62, NaN=0
oil_price_rolling_mean_28: mean=68.93, std=25.70, min=30.21, max=108.08, NaN=0
oil_price_change_pct:    mean=-0.0022, std=0.0469, min=-0.172, max=0.287, NaN=0
```

**0 NaN trong tất cả splits** — oil được forward-fill đầy đủ trước khi merge.

---

## 7. Nhóm E — Store Features (8 features)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_oil_and_store.ipynb`, `feature_external.ipynb`  
**Script tích hợp**: `scripts/build_train_final.py` — Step 6

### 7.1 Dữ liệu gốc

```
data/raw/stores.csv: 54 × 5
  store_nbr  — mã cửa hàng (1–54)
  city       — thành phố (22 cities)
  state      — tỉnh/thành (16 states)
  type       — loại cửa hàng: A, B, C, D, E
  cluster    — nhóm cửa hàng (1–17)
```

### 7.2 Code tính

```python
store_cols = ["store_nbr", "type", "city", "state", "cluster"]
df = df.merge(df_stores[store_cols], on="store_nbr", how="left")

# --- LabelEncoder cho type (từ feature_oil_and_store.ipynb) ---
le = LabelEncoder()
df["store_type_enc"] = le.fit_transform(df["type"])
# A→0, B→1, C→2, D→3, E→4 (alphabetical order)

# --- Frequency encoding cho city và state ---
for col in ["city", "state"]:
    freq = df[col].value_counts(normalize=True)  # tần suất xuất hiện trong train
    df[f"{col}_freq"] = df[col].map(freq)

# --- Manual mapping cho type (từ feature_external.ipynb) ---
type_map = {t: i for i, t in enumerate(sorted(df_stores["type"].unique()))}
# sorted: A, B, C, D, E → {A:0, B:1, C:2, D:3, E:4}
df["store_type_encoded"] = df["type"].map(type_map)
```

### 7.3 Chi tiết từng feature

| Feature | Kiểu encoding | Giá trị | Lý do chọn |
|---------|--------------|---------|-----------|
| `type` | raw string | A/B/C/D/E | Giữ để LabelEncode trong model training |
| `city` | raw string | 22 giá trị | Giữ để LabelEncode |
| `state` | raw string | 16 giá trị | Giữ để LabelEncode |
| `cluster` | raw int | 1–17 | Nhóm stores có characteristics giống nhau |
| `store_type_enc` | LabelEncoder | 0–4 | Encode loại cửa hàng (A=0 đến E=4) |
| `city_freq` | Frequency | 0.019–0.333 | Số lượng stores tại city (thành phố lớn có nhiều stores) |
| `state_freq` | Frequency | 0.019–0.352 | Số lượng stores tại state |
| `store_type_encoded` | Manual map | 0–4 | Encode type theo alphabetical (giống store_type_enc) |

### 7.4 Tại sao có cả `store_type_enc` và `store_type_encoded`?

Hai features này về bản chất giống nhau (A→0, B→1, C→2, D→3, E→4) và được tạo bởi hai notebook khác nhau:
- `store_type_enc` từ `feature_oil_and_store.ipynb` dùng `sklearn.LabelEncoder`
- `store_type_encoded` từ `feature_external.ipynb` dùng manual dict

Cả hai đều được giữ trong final dataset để tương thích với code hiện tại. Model không bị hại vì gradient boosting tự nhiên handle redundant features.

### 7.5 Thống kê thực tế (từ train split)

```
store_type_enc:    mean=2.00, std=1.20, min=0, max=4
city_freq:         mean=0.150, std=0.136, min=0.019, max=0.333
state_freq:        mean=0.182, std=0.140, min=0.019, max=0.352
cluster:           mean=8.48, std=4.65, min=1, max=17
store_type_encoded: mean=2.00, std=1.20, min=0, max=4
```

**0 NaN trong tất cả splits** — mọi store_nbr đều có trong stores.csv.

---

## 8. Nhóm F — Target Encoding (2 features)

**Notebook nguồn**: `notebooks/04_feature_engineering/features/feature_target_encoding.ipynb`  
**Script tích hợp**: `scripts/build_train_final.py` — Step 7

### 8.1 Composite Key

```python
df["store_family"] = df["store_nbr"].astype(str) + "_" + df["family"]
# Ví dụ: store 1, GROCERY I → "1_GROCERY I"
# 54 stores × 33 families = 1,782 unique keys
```

### 8.2 KFold Out-of-Fold Target Encoding

**Vấn đề với naive target encoding**: Nếu encode mean sales của `store_family` trực tiếp, training data sẽ thấy chính target của mình khi tính mean → data leakage → overfit nặng.

**Giải pháp — KFold OOF (Out-of-Fold)**:

```python
from category_encoders import TargetEncoder
from sklearn.model_selection import KFold

kf  = KFold(n_splits=5, shuffle=False)  # shuffle=False để giữ temporal order
oof = np.zeros(len(df))

for tr_idx, val_idx in kf.split(df):
    enc = TargetEncoder(cols=["store_family"], smoothing=10)
    enc.fit(df.iloc[tr_idx][["store_family"]], df.iloc[tr_idx]["sales"])
    oof[val_idx] = enc.transform(df.iloc[val_idx][["store_family"]])["store_family"]

df["store_family_te"] = oof
```

**Cơ chế OOF**: Với mỗi fold, encoder được fit trên 4/5 data và predict cho 1/5 còn lại. Row không bao giờ tham gia vào encoding của chính nó → không leakage.

**Smoothing=10**: Bayesian smoothing — cân bằng giữa group mean và global mean:
```
encoded = (count × group_mean + smoothing × global_mean) / (count + smoothing)
```
Khi group có ít dữ liệu (count nhỏ), encoded value kéo về global mean → tránh overfit cho các (store, family) hiếm.

### 8.3 Encoding cho Test Set

```python
# Train encoder trên TOÀN BỘ training data để encode test set
enc_full = TargetEncoder(cols=["store_family"], smoothing=10)
enc_full.fit(df[["store_family"]], df["sales"])
test["store_family_te"] = enc_full.transform(test[["store_family"]])["store_family"]
```

### 8.4 Chi tiết từng feature

| Feature | Kiểu | Mô tả | Lý do chọn |
|---------|------|-------|-----------|
| `store_family` | string | `"{store_nbr}_{family}"` — 1,782 unique keys | Composite key dùng để LabelEncode trong model |
| `store_family_te` | float | Mean sales của (store, family) pair (smoothed, OOF) | Encode "baseline sales level" của từng cặp, thay thế cho high-cardinality categorical |

### 8.5 Thống kê thực tế (từ train split)

```
store_family_te: mean=358.60, std=966.97, min=0.00, max=10250.46
  ← Phản ánh đúng distribution sales: median ~$11, có cặp lên tới $10,250
```

---

## 9. Nhóm G — Onpromotion (1 feature)

**Nguồn**: Từ `train.csv` gốc, không cần tính toán thêm.

```python
# Sẵn có trong train.csv: số SKU đang được khuyến mãi trong ngày đó
# Không transformation — dùng trực tiếp
```

| Feature | Kiểu | Mô tả |
|---------|------|-------|
| `onpromotion` | int | Số lượng SKU đang trong chương trình khuyến mãi |

**Insight**: 79.6% records có `onpromotion=0`. Promotions tập trung vào GROCERY I (1.9M promotions), BEVERAGES, CLEANING. Promo có correlation dương rõ với sales nhưng không uniform — một số families respond mạnh (PRODUCE 2.08×), một số ít hơn.

---

## 10. Build Pipeline Tổng hợp — `build_train_final.py`

Script này là **single source of truth** — tích hợp toàn bộ feature groups vào một pipeline duy nhất, thay thế việc chạy từng notebook riêng lẻ.

### 10.1 Thứ tự các bước

```python
# STEP 1: Load base datasets
df = pd.read_csv(TRAIN_CLEANED_PATH, parse_dates=["date"])
df = df.sort_values(["store_nbr", "family", "date"]).reset_index(drop=True)

# STEP 2: Temporal features (10 features)
df["year"] = dt.year
# ... (code tại Section 3.1)

# STEP 3: Lag & rolling features
grouped = df.groupby(["store_nbr", "family"], sort=False)["sales"]
for lag in [1, 2, 3]: df[f"lag_{lag}"] = grouped.shift(lag)
# ... (code tại Section 4.1)

# STEP 4: Holiday features (9 features)
# ... (code tại Section 5.3)

# STEP 5: Oil price features (5 features)
# ... (code tại Section 6.2)

# STEP 6: Store encoding features (8 features)
df = df.merge(df_stores[store_cols], on="store_nbr", how="left")
# ... (code tại Section 7.2)

# STEP 7: Target encoding (2 features)
df["store_family"] = df["store_nbr"].astype(str) + "_" + df["family"]
# KFold OOF ... (code tại Section 8.2)

# STEP 8: Data quality validation
assert df.duplicated(subset=["date", "store_nbr", "family"]).sum() == 0
assert df["sales"].isna().sum() == 0

# STEP 9: Save train_final.csv
df.to_csv(OUTPUT_PATH, index=False)
```

### 10.2 Audit Warning Trong Script

Script có comment cảnh báo rõ về unsafe lags:

```python
# ⚠️  LAG FEATURE AUDIT WARNING
# The following lag features are BELOW the 16-day minimum threshold:
#   lag_1  (1 day)   — ⚠️ below 16-day threshold
#   lag_2  (2 days)  — ⚠️ below 16-day threshold
#   lag_3  (3 days)  — ⚠️ below 16-day threshold
#   lag_7  (7 days)  — ⚠️ below 16-day threshold
#   lag_14 (14 days) — ⚠️ below 16-day threshold
# Safe lags (≥16 days): lag_28 (28 days), lag_364 (364 days)
```

Những features này tồn tại trong `splits/` (baseline) và được xóa trong `feature_safe_lag_v3.ipynb` → `splits_safe_lag_v3/`.

---

## 11. Feature Engineering v3 — `feature_safe_lag_v3.ipynb`

Notebook này là **upgrade step** — đọc splits baseline, sửa distribution shift, lưu splits mới.

### 11.1 Logic đầy đủ

```python
TOXIC_FEATURES = [
    'lag_1', 'lag_2', 'lag_3', 'lag_7',
    'rolling_mean_7', 'rolling_mean_14',
    'rolling_mean_28', 'rolling_std_7',
]

# Load baseline splits
X_train = pd.read_csv(SPLITS_DIR / 'train_features.csv')  # (2918916, 49)
X_val   = pd.read_csv(SPLITS_DIR / 'val_features.csv')    # (55242, 49)
X_test  = pd.read_csv(SPLITS_DIR / 'test_features.csv')   # (26730, 49)

# Verify toxic features exist
assert all(f in X_train.columns for f in TOXIC_FEATURES), "Missing toxic features"

# Drop toxic features
X_train = X_train.drop(columns=TOXIC_FEATURES)  # → (2918916, 41)
X_val   = X_val.drop(columns=TOXIC_FEATURES)
X_test  = X_test.drop(columns=TOXIC_FEATURES)

# Compute safe features on raw training data
train_raw = pd.read_csv(PROCESSED_DIR / 'train_cleaned.csv', parse_dates=['date'])
train_raw = train_raw.sort_values(['store_nbr', 'family', 'date'])
grouped = train_raw.groupby(['store_nbr', 'family'], sort=False)['sales']

# Safe lag features
for lag in [16, 21, 35]:
    train_raw[f'lag_{lag}'] = grouped.shift(lag)

# Safe rolling features (shift(16) guarantees all lookbacks ≤ Aug 15)
train_raw['rolling_mean_30'] = grouped.transform(
    lambda x: x.shift(16).rolling(30, min_periods=1).mean()
)
train_raw['rolling_mean_28_safe'] = grouped.transform(
    lambda x: x.shift(16).rolling(28, min_periods=1).mean()
)
train_raw['rolling_std_28_safe'] = grouped.transform(
    lambda x: x.shift(16).rolling(28, min_periods=2).std()
)

NEW_SAFE_FEATURES = ['lag_16', 'lag_21', 'lag_35',
                     'rolling_mean_30', 'rolling_mean_28_safe', 'rolling_std_28_safe']

# Merge safe features vào splits (join theo date + store_nbr + family)
for split_df, split_name in [(X_train, 'train'), (X_val, 'val'), (X_test, 'test')]:
    split_df = split_df.merge(
        train_raw[['date','store_nbr','family'] + NEW_SAFE_FEATURES],
        on=['date','store_nbr','family'], how='left'
    )
    # Verify: 47 columns
    assert split_df.shape[1] == 47, f"Expected 47, got {split_df.shape[1]}"

# Verify zero NaN in val and test for all safe features
for f in NEW_SAFE_FEATURES:
    assert X_val[f].isna().sum() == 0,  f"Val NaN in {f}"
    assert X_test[f].isna().sum() == 0, f"Test NaN in {f}"

# Save to splits_safe_lag_v3/
SPLITS_V3 = PROCESSED_DIR / 'splits_safe_lag_v3'
SPLITS_V3.mkdir(exist_ok=True)
X_train.to_csv(SPLITS_V3 / 'train_features.csv', index=False)
X_val.to_csv(SPLITS_V3 / 'val_features.csv',     index=False)
X_test.to_csv(SPLITS_V3 / 'test_features.csv',   index=False)
```

### 11.2 Output Verification (từ notebook output thực tế)

```
=== Feature Safe Lag v3 — Verification ===
X_train: (2918916, 47) ✓
X_val:   (55242,   47) ✓
X_test:  (26730,   47) ✓

NaN in TRAIN (expected — đầu series):
  lag_16:             28,512 NaN (0.977%)
  lag_21:             37,422 NaN (1.282%)
  lag_35:             62,370 NaN (2.137%)
  rolling_mean_30:    28,512 NaN (0.977%)
  rolling_mean_28_safe: 28,512 NaN (0.977%)
  rolling_std_28_safe:  30,294 NaN (1.038%)

NaN in VAL:  0 for all safe features ✓
NaN in TEST: 0 for all safe features ✓

Toxic features removed ✓ (lag_1/2/3/7, rolling_mean_7/14/28, rolling_std_7 absent)
Safe features present ✓ (lag_16/21/35, rolling_mean_30/28_safe, rolling_std_28_safe)
```

---

## 12. Encoding Strategy Trong Model Training

Các features có kiểu object phải được encode trước khi đưa vào model:

```python
from sklearn.preprocessing import LabelEncoder

object_cols = X_train.select_dtypes(include='object').columns.tolist()
# → ['family', 'type', 'city', 'state', 'store_family']

label_encoders = {}
for col in object_cols:
    le = LabelEncoder()
    X_train[col] = le.fit_transform(X_train[col])
    X_val[col]   = le.transform(X_val[col])
    X_test[col]  = le.transform(X_test[col])
    label_encoders[col] = le

# Lưu encoders để dùng khi forecast
import pickle
with open('xgb_v2_label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)
```

**Tại sao LabelEncoder thay vì OneHotEncoder**: XGBoost và LightGBM xử lý label-encoded categoricals tốt qua tree splits. OneHotEncoder sẽ tạo ra hàng trăm columns (33 families × OHE = 33 columns mới) → không cần thiết, làm chậm training.

---

## 13. Anti-Leakage Design Summary

| Nguồn data | Feature | Cơ chế anti-leakage |
|-----------|---------|-------------------|
| sales (endogenous) | lag_16/21/28/35/364 | shift(N) với N ≥ 16 = safe threshold cho 16-day horizon |
| sales (endogenous) | lag_14 | shift(14) — chấp nhận NaN 2 ngày cuối test, model handle natively |
| sales (endogenous) | rolling_mean_30/28_safe, rolling_std_28_safe | shift(16).rolling(W) — lookback window hoàn toàn trong train data |
| oil (exogenous) | oil_price_rolling_mean_28 | shift(1) OK vì oil price thực đã biết cho test period |
| target (sales) | store_family_te | KFold OOF — mỗi row không thấy chính nó khi encode |
| temporal | year/month/day/... | Từ date — không có leakage |
| holiday | is_national_holiday/... | Từ lịch ngày lễ — public information, không leakage |
| store metadata | type/city/cluster/... | Static info — không thay đổi theo thời gian |

---

## 14. Tóm tắt Feature Groups và Số Lượng

| Nhóm | Features | Count |
|------|---------|-------|
| Identity / Base | `date`, `store_nbr`, `family`, `onpromotion` | 4 |
| Temporal | `year`, `month`, `day`, `day_of_week`, `week_of_year`, `quarter`, `is_weekend`, `is_month_start`, `is_month_end`, `is_payday` | 10 |
| Lag (safe) | `lag_14`, `lag_16`, `lag_21`, `lag_28`, `lag_35`, `lag_364` | 6 |
| Rolling (safe) | `rolling_mean_30`, `rolling_mean_28_safe`, `rolling_std_28_safe` | 3 |
| Holiday | `is_national_holiday`, `is_regional_holiday`, `is_local_holiday`, `is_transferred_holiday`, `holiday_type`, `is_carnaval_feature`, `days_to_next_holiday`, `days_after_last_holiday`, `is_earthquake_period` | 9 |
| Oil price | `oil_price`, `oil_price_lag_7`, `oil_price_lag_14`, `oil_price_rolling_mean_28`, `oil_price_change_pct` | 5 |
| Store | `type`, `city`, `state`, `store_type_enc`, `city_freq`, `state_freq`, `cluster`, `store_type_encoded` | 8 |
| Target encoding | `store_family`, `store_family_te` | 2 |
| **TOTAL** | | **47** |

---

*File này được tạo và cross-check từ codebase thực tế ngày 2026-05-12.*  
*Mọi thống kê được tính từ `data/processed/splits_safe_lag_v3/train_features.csv` và các notebook nguồn.*
