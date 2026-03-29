"""
build_train_final.py
====================
Merge pipeline: rebuilds train_final.csv from scratch by combining all
feature groups (temporal, lag/rolling, holiday, oil, store, target encoding)
on the full training dataset (2013-01-01 → 2017-08-15).

All feature logic is preserved exactly as in the individual feature notebooks:
  notebooks/04_feature_engineering/features/feature_temporal.ipynb
  notebooks/04_feature_engineering/features/feature_holiday.ipynb
  notebooks/04_feature_engineering/features/feature_external.ipynb
  notebooks/04_feature_engineering/features/feature_oil_and_store.ipynb
  notebooks/04_feature_engineering/features/feature_target_encoding.ipynb

The intermediate CSV files written by those notebooks are no longer needed
(to_csv calls have been commented out). This script is the single authoritative
pipeline that produces train_final.csv.

Usage:
    python scripts/build_train_final.py
"""

import os
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import KFold

try:
    from category_encoders import TargetEncoder
    HAS_CATEGORY_ENCODERS = True
except ImportError:
    HAS_CATEGORY_ENCODERS = False
    warnings.warn("category_encoders not installed — store_family_te will be NaN. "
                  "Install with: pip install category_encoders")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE, "data", "raw")
PROC_DIR = os.path.join(BASE, "data", "processed")

TRAIN_CLEANED_PATH    = os.path.join(PROC_DIR, "train_cleaned.csv")
HOLIDAYS_CLEANED_PATH = os.path.join(PROC_DIR, "holidays_events_cleaned.csv")
STORES_CLEANED_PATH   = os.path.join(PROC_DIR, "stores_cleaned.csv")
OIL_CLEANED_PATH      = os.path.join(PROC_DIR, "cleaned_oil.csv")
OUTPUT_PATH           = os.path.join(PROC_DIR, "train_final.csv")

# ---------------------------------------------------------------------------
# ⚠️  LAG FEATURE AUDIT WARNING
# ---------------------------------------------------------------------------
# The following lag features are BELOW the 16-day minimum threshold required
# to prevent data leakage into a 16-day forecast horizon:
#   lag_1  (1 day)   — ⚠️ below 16-day threshold
#   lag_2  (2 days)  — ⚠️ below 16-day threshold
#   lag_3  (3 days)  — ⚠️ below 16-day threshold
#   lag_7  (7 days)  — ⚠️ below 16-day threshold
#   lag_14 (14 days) — ⚠️ below 16-day threshold
# Safe lags (≥16 days):
#   lag_28  (28 days)  — OK
#   lag_364 (364 days) — OK
# These features are kept as-is per project requirements. When using these
# features for direct multi-step forecasting over a 16-day horizon, ensure
# that the lag features are not populated with in-horizon values.
# ---------------------------------------------------------------------------

print("=" * 70)
print("BUILD TRAIN_FINAL.CSV — Full Feature Merge Pipeline")
print("=" * 70)


# ===========================================================================
# STEP 1 — Load base data
# ===========================================================================
print("\n[1/9] Loading base datasets...")
df = pd.read_csv(TRAIN_CLEANED_PATH, parse_dates=["date"])
df_holidays = pd.read_csv(HOLIDAYS_CLEANED_PATH, parse_dates=["date"])
df_stores   = pd.read_csv(STORES_CLEANED_PATH)
df_oil      = pd.read_csv(OIL_CLEANED_PATH)

df = df.sort_values(["store_nbr", "family", "date"]).reset_index(drop=True)

print(f"  Base train shape : {df.shape}")
print(f"  Date range       : {df['date'].min().date()} → {df['date'].max().date()}")
print(f"  Stores           : {df['store_nbr'].nunique()}")
print(f"  Families         : {df['family'].nunique()}")


# ===========================================================================
# STEP 2 — Temporal features  (from feature_temporal.ipynb)
# ===========================================================================
print("\n[2/9] Adding temporal features...")

dt = df["date"].dt
df["year"]           = dt.year
df["month"]          = dt.month
df["day"]            = dt.day
df["day_of_week"]    = dt.dayofweek          # 0 = Monday, 6 = Sunday
df["week_of_year"]   = dt.isocalendar().week.astype(int)
df["quarter"]        = dt.quarter
df["is_weekend"]     = (dt.dayofweek >= 5).astype(int)
df["is_month_start"] = dt.is_month_start.astype(int)
df["is_month_end"]   = dt.is_month_end.astype(int)
df["is_payday"]      = ((dt.day == 15) | dt.is_month_end).astype(int)

TEMPORAL_FEATURES = [
    "year", "month", "day", "day_of_week", "week_of_year", "quarter",
    "is_weekend", "is_month_start", "is_month_end", "is_payday",
]
print(f"  Temporal features added: {TEMPORAL_FEATURES}")


# ===========================================================================
# STEP 3 — Lag & rolling features  (from feature_temporal.ipynb)
# ===========================================================================
print("\n[3/9] Adding lag and rolling features...")

GROUP_COLS = ["store_nbr", "family"]
grouped = df.groupby(GROUP_COLS, sort=False)["sales"]

# ⚠️ lag_1..lag_14 are below the 16-day threshold (see warning above)
for lag in [1, 2, 3]:
    df[f"lag_{lag}"] = grouped.shift(lag)
df["lag_7"]  = grouped.shift(7)
df["lag_14"] = grouped.shift(14)
df["lag_28"] = grouped.shift(28)
df["lag_364"] = grouped.shift(364)

# Rolling features (shift(1) guarantees no current-day leakage)
shifted = grouped.shift(1)
df["rolling_mean_7"]  = shifted.transform(lambda x: x.rolling(7,  min_periods=1).mean())
df["rolling_mean_14"] = shifted.transform(lambda x: x.rolling(14, min_periods=1).mean())
df["rolling_mean_28"] = shifted.transform(lambda x: x.rolling(28, min_periods=1).mean())
df["rolling_std_7"]   = shifted.transform(lambda x: x.rolling(7,  min_periods=2).std())

LAG_FEATURES = [
    "lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_28", "lag_364",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7",
]
print(f"  ⚠️  Lag features below 16-day threshold: lag_1, lag_2, lag_3, lag_7, lag_14")
print(f"  Safe lag features (≥16d):               lag_28, lag_364")
print(f"  Rolling features (shift(1) guaranteed): rolling_mean_7/14/28, rolling_std_7")


# ===========================================================================
# STEP 4 — Holiday features  (from feature_holiday.ipynb)
# ===========================================================================
print("\n[4/9] Adding holiday / calendar / earthquake features...")

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

# Merge store city/state for locale matching
df = df.merge(df_stores[["store_nbr", "city", "state"]], on="store_nbr", how="left")

# Initialise holiday columns
for col in ["is_national_holiday", "is_regional_holiday", "is_local_holiday",
            "is_transferred_holiday", "holiday_type", "is_carnaval_feature"]:
    df[col] = 0

# Assign holiday flags row-by-row using precomputed masks
for _, row in valid_holidays.iterrows():
    h_date, h_locale, h_locale_name = row["date"], row["locale"], row["locale_name"]
    if h_locale == "National":
        mask = df["date"] == h_date
    elif h_locale == "Regional":
        mask = (df["date"] == h_date) & (df["state"] == h_locale_name)
    elif h_locale == "Local":
        mask = (df["date"] == h_date) & (df["city"] == h_locale_name)
    else:
        continue
    if h_locale == "National":
        df.loc[mask, "is_national_holiday"] = 1
    elif h_locale == "Regional":
        df.loc[mask, "is_regional_holiday"] = 1
    elif h_locale == "Local":
        df.loc[mask, "is_local_holiday"] = 1
    df.loc[mask, "is_transferred_holiday"] = int(row["transferred"])
    df.loc[mask, "holiday_type"]           = row["holiday_type_encoded"]
    df.loc[mask, "is_carnaval_feature"]    = row["is_carnaval"]

# Halo features: days to/from nearest holiday
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

# Earthquake flag (2016-04-16 to 2016-05-16)
df["is_earthquake_period"] = (
    (df["date"] >= pd.Timestamp("2016-04-16")) &
    (df["date"] <= pd.Timestamp("2016-05-16"))
).astype(int)

# Drop store location columns used only for locale matching
df = df.drop(columns=["city", "state"])

HOLIDAY_FEATURES = [
    "is_national_holiday", "is_regional_holiday", "is_local_holiday",
    "is_transferred_holiday", "holiday_type", "is_carnaval_feature",
    "days_to_next_holiday", "days_after_last_holiday", "is_earthquake_period",
]
print(f"  Holiday features added: {HOLIDAY_FEATURES}")


# ===========================================================================
# STEP 5 — Oil price features  (from feature_oil_and_store.ipynb + feature_external.ipynb)
# ===========================================================================
print("\n[5/9] Adding oil price features...")

oil = df_oil.copy().rename(columns={"dcoilwtico": "oil_price"})
oil["date"] = pd.to_datetime(oil["date"])
oil = oil[["date", "oil_price"]].sort_values("date").reset_index(drop=True)

# Fill calendar gaps (weekends / holidays have no trading)
full_range = pd.DataFrame({
    "date": pd.date_range(start=oil["date"].min(), end=oil["date"].max(), freq="D")
})
oil = full_range.merge(oil, on="date", how="left")
oil["oil_price"] = oil["oil_price"].ffill().bfill()

# Oil lag and rolling features
oil["oil_price_lag_7"]            = oil["oil_price"].shift(7)
oil["oil_price_lag_14"]           = oil["oil_price"].shift(14)
oil["oil_price_rolling_mean_28"]  = oil["oil_price"].shift(1).rolling(28, min_periods=7).mean()
oil["oil_price_change_pct"]       = oil["oil_price"].pct_change(periods=7)

OIL_COLS = [
    "date", "oil_price", "oil_price_lag_7", "oil_price_lag_14",
    "oil_price_rolling_mean_28", "oil_price_change_pct",
]
df = df.merge(oil[OIL_COLS], on="date", how="left")

# Forward-fill any remaining oil_price nulls (dates outside oil date range)
df["oil_price"] = df["oil_price"].ffill().bfill()

OIL_FEATURES = [
    "oil_price", "oil_price_lag_7", "oil_price_lag_14",
    "oil_price_rolling_mean_28", "oil_price_change_pct",
]
print(f"  Oil features added: {OIL_FEATURES}")
print(f"  oil_price nulls remaining: {df['oil_price'].isna().sum()}")


# ===========================================================================
# STEP 6 — Store encoding features
#           (from feature_oil_and_store.ipynb AND feature_external.ipynb)
#           Both encodings are preserved to match the existing train_final schema.
# ===========================================================================
print("\n[6/9] Adding store encoding features...")

store_cols = ["store_nbr", "type", "city", "state", "cluster"]
df = df.merge(df_stores[store_cols], on="store_nbr", how="left")

# --- From feature_oil_and_store.ipynb: LabelEncoder-based ---
le = LabelEncoder()
df["store_type_enc"] = le.fit_transform(df["type"])

for col in ["city", "state"]:
    freq = df[col].value_counts(normalize=True)
    df[f"{col}_freq"] = df[col].map(freq)

# --- From feature_external.ipynb: explicit type_mapping ---
type_map = {t: i for i, t in enumerate(sorted(df_stores["type"].unique()))}
df["store_type_encoded"] = df["type"].map(type_map)

STORE_FEATURES = [
    "type", "city", "state", "cluster",
    "store_type_enc", "city_freq", "state_freq", "store_type_encoded",
]
print(f"  Store features added: {STORE_FEATURES}")


# ===========================================================================
# STEP 7 — Target encoding  (from feature_target_encoding.ipynb)
# ===========================================================================
print("\n[7/9] Adding target encoding (store_family_te)...")

df["store_family"] = df["store_nbr"].astype(str) + "_" + df["family"]

if HAS_CATEGORY_ENCODERS:
    kf  = KFold(n_splits=5, shuffle=False)
    oof = np.zeros(len(df))
    for tr_idx, val_idx in kf.split(df):
        enc = TargetEncoder(cols=["store_family"], smoothing=10)
        enc.fit(df.iloc[tr_idx][["store_family"]], df.iloc[tr_idx]["sales"])
        oof[val_idx] = enc.transform(df.iloc[val_idx][["store_family"]])["store_family"]
    df["store_family_te"] = oof
    print("  store_family_te computed via out-of-fold TargetEncoder (k=5).")
else:
    df["store_family_te"] = np.nan
    print("  WARNING: store_family_te set to NaN — install category_encoders.")


# ===========================================================================
# STEP 8 — Data quality validation
# ===========================================================================
print("\n[8/9] Running data quality checks...")

# Duplicate check
dup_count = df.duplicated(subset=["date", "store_nbr", "family"]).sum()
assert dup_count == 0, f"FAIL: {dup_count} duplicate rows on (date, store_nbr, family)"
print(f"  ✓ No duplicate rows on (date, store_nbr, family)")

# Sales null check
sales_nulls = df["sales"].isna().sum()
assert sales_nulls == 0, f"FAIL: {sales_nulls} null values in sales column"
print(f"  ✓ No null values in sales column")

# Null rate report
print("\n  Null rates per feature column:")
exclude_from_null_check = {"id", "date", "sales"}
HIGH_NULL_THRESHOLD = 0.05
high_null_cols = []
for col in df.columns:
    if col in exclude_from_null_check:
        continue
    null_rate = df[col].isna().mean()
    if null_rate > 0:
        flag = " ⚠️  > 5%" if null_rate > HIGH_NULL_THRESHOLD else ""
        print(f"    {col:<35} {null_rate*100:5.2f}%{flag}")
        if null_rate > HIGH_NULL_THRESHOLD:
            high_null_cols.append((col, null_rate))

if not high_null_cols:
    print("  ✓ No feature column has null rate > 5%")
else:
    print(f"\n  ⚠️  Columns with null rate > 5% (may need imputation before training):")
    for col, rate in high_null_cols:
        print(f"    {col}: {rate*100:.2f}%")

# Date range check
print(f"\n  Date range : {df['date'].min().date()} → {df['date'].max().date()}")
print(f"  Final shape: {df.shape}")


# ===========================================================================
# STEP 9 — Save train_final.csv
# ===========================================================================
print(f"\n[9/9] Saving to {OUTPUT_PATH} ...")
df.to_csv(OUTPUT_PATH, index=False)
print(f"  ✓ Saved: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"  Columns: {df.columns.tolist()}")

print("\n" + "=" * 70)
print("build_train_final.py complete.")
print(f"Output : {OUTPUT_PATH}")
print("=" * 70)
