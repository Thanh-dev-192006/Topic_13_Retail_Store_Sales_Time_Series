"""
NaN Audit, Fill, Merge, and Validation Pipeline
for Store Sales Time Series Forecasting Project
"""

import os
import sys
import io

# Force UTF-8 output on Windows to avoid charmap encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────────
PROCESSED_DIR = "D:/Topic_13_Project/Topic_13_Retail_Store_Sales_Time_Series/data/processed"
CLEANED_DIR   = os.path.join(PROCESSED_DIR, "cleaned")
JOIN_KEYS     = ["date", "store_nbr", "family"]

TRAIN_FILES = {
    "train_cleaned":           os.path.join(PROCESSED_DIR, "train_cleaned.csv"),
    "train_temporal_features": os.path.join(PROCESSED_DIR, "train_temporal_features.csv"),
    "train_holiday_features":  os.path.join(PROCESSED_DIR, "train_holiday_features.csv"),
    "train_oil_store_features":os.path.join(PROCESSED_DIR, "train_oil_store_features.csv"),
    "train_external_features": os.path.join(PROCESSED_DIR, "train_external_features.csv"),
    "train_target_encoding":   os.path.join(PROCESSED_DIR, "train_target_encoding.csv"),
}

TEST_FILES = {
    "test_cleaned":          os.path.join(PROCESSED_DIR, "test_cleaned.csv"),
    "test_target_encoding":  os.path.join(PROCESSED_DIR, "test_target_encoding.csv"),
}

ALL_FILES = {**TRAIN_FILES, **TEST_FILES}

# ─── Helper ───────────────────────────────────────────────────────────────────
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", low_memory=False)

def save_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")

def nan_report(df: pd.DataFrame, label: str) -> dict:
    nan_counts = df.isnull().sum()
    nan_cols   = nan_counts[nan_counts > 0]
    print(f"\n  [{label}]  shape={df.shape}  total_NaN={nan_counts.sum()}")
    if nan_cols.empty:
        print("    -> No NaN values found.")
    else:
        for col, cnt in nan_cols.items():
            print(f"    NaN  {col}: {cnt}")
    return nan_cols.to_dict()

def fill_nan(df: pd.DataFrame, file_key: str) -> pd.DataFrame:
    """Apply domain-aware fill strategies."""
    df = df.copy()

    for col in df.columns:
        if col in JOIN_KEYS:
            continue

        col_lower = col.lower()
        n_nan = df[col].isnull().sum()
        if n_nan == 0:
            continue

        # --- Sales lag / rolling → fill 0
        if col_lower.startswith("lag_") or col_lower.startswith("rolling_"):
            if "oil" in col_lower:
                # Oil lag/rolling → forward-fill then 0
                df[col] = df[col].ffill().bfill().fillna(0)
            else:
                df[col] = df[col].fillna(0)

        # --- Oil-related columns (not lag/rolling) → ffill then 0
        elif "oil" in col_lower:
            df[col] = df[col].ffill().bfill().fillna(0)

        # --- Holiday / event features → fill 0
        elif any(kw in col_lower for kw in [
            "holiday", "event", "is_holiday", "is_local", "is_regional",
            "is_national", "transferred", "bridge", "workday"
        ]):
            df[col] = df[col].fillna(0)

        # --- Target encoding → fill with global mean
        elif any(kw in col_lower for kw in [
            "target_enc", "te_", "encoding", "mean_enc", "family_enc", "store_enc"
        ]):
            global_mean = df[col].mean()
            df[col] = df[col].fillna(global_mean)

        # --- Frequency / store encoding → fill with mode
        elif any(kw in col_lower for kw in [
            "freq", "mode", "store_type", "cluster", "city", "state"
        ]):
            mode_val = df[col].mode()
            fill_val = mode_val.iloc[0] if not mode_val.empty else 0
            df[col] = df[col].fillna(fill_val)

        # --- Fallback → fill 0
        else:
            df[col] = df[col].fillna(0)

    return df


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Audit All NaN Values
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("=== PHASE 1 — Audit All NaN Values ===")
print("=" * 60)

audit_results = {}
for key, path in ALL_FILES.items():
    if not os.path.exists(path):
        print(f"  [ERROR] File not found: {path}")
        sys.exit(1)
    df = load_csv(path)
    audit_results[key] = nan_report(df, key)

print("\n>>> Phase 1 complete.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Handle All NaN Values
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("=== PHASE 2 — Handle All NaN Values ===")
print("=" * 60)

os.makedirs(CLEANED_DIR, exist_ok=True)
print(f"  Output directory: {CLEANED_DIR}")

cleaned_dfs = {}

for key, path in ALL_FILES.items():
    df_raw = load_csv(path)
    df_filled = fill_nan(df_raw, key)

    remaining = df_filled.isnull().sum().sum()
    if remaining > 0:
        bad_cols = df_filled.isnull().sum()
        bad_cols = bad_cols[bad_cols > 0]
        print(f"\n  [FAIL] {key} still has {remaining} NaN after fill:")
        for col, cnt in bad_cols.items():
            print(f"    {col}: {cnt}")
        sys.exit(1)
    else:
        print(f"  [{key}]  → All NaN filled. shape={df_filled.shape}")

    out_path = os.path.join(CLEANED_DIR, f"{key}.csv")
    save_csv(df_filled, out_path)
    cleaned_dfs[key] = df_filled

print("\n>>> Phase 2 complete. All files saved to cleaned/\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Merge Into Final Datasets
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("=== PHASE 3 — Merge Into Final Datasets ===")
print("=" * 60)

def safe_merge(base: pd.DataFrame, other: pd.DataFrame, label: str) -> pd.DataFrame:
    """Left-merge other into base, dropping duplicate non-key columns."""
    # Verify join keys exist in other
    missing_keys = [k for k in JOIN_KEYS if k not in other.columns]
    if missing_keys:
        print(f"  [ERROR] {label} is missing join keys: {missing_keys}")
        sys.exit(1)

    base_row_count = len(base)

    # Drop columns already in base (except join keys)
    base_cols_no_keys = set(base.columns) - set(JOIN_KEYS)
    other_cols_to_drop = [c for c in other.columns if c in base_cols_no_keys]
    if other_cols_to_drop:
        print(f"    Dropping duplicate cols from {label}: {other_cols_to_drop}")
        other = other.drop(columns=other_cols_to_drop)

    merged = base.merge(other, on=JOIN_KEYS, how="left")

    if len(merged) != base_row_count:
        print(f"  [ERROR] Row count changed after merging {label}: "
              f"{base_row_count} → {len(merged)}")
        sys.exit(1)

    print(f"    Merged {label}: shape now {merged.shape}")
    return merged


# ── TRAIN ──────────────────────────────────────────────────────────────────
print("\n--- Building TRAIN final dataset ---")

train_base = cleaned_dfs["train_cleaned"].copy()
print(f"  Base (train_cleaned): {train_base.shape}")

train_merge_order = [
    ("train_temporal_features",  cleaned_dfs["train_temporal_features"]),
    ("train_holiday_features",   cleaned_dfs["train_holiday_features"]),
    ("train_oil_store_features", cleaned_dfs["train_oil_store_features"]),
    ("train_external_features",  cleaned_dfs["train_external_features"]),
    ("train_target_encoding",    cleaned_dfs["train_target_encoding"]),
]

train_final = train_base
for label, df_feat in train_merge_order:
    train_final = safe_merge(train_final, df_feat, label)

# Fill any NaN introduced by left-joins
train_final = fill_nan(train_final, "train_final_post_merge")

# Assert zero NaN
total_nan = train_final.isnull().sum().sum()
if total_nan > 0:
    print(f"\n  [ERROR] train_final still has {total_nan} NaN after merge!")
    bad_cols = train_final.isnull().sum()
    print(bad_cols[bad_cols > 0])
    sys.exit(1)

train_final_path = os.path.join(PROCESSED_DIR, "train_final.csv")
save_csv(train_final, train_final_path)
print(f"\n  train_final saved → {train_final_path}  shape={train_final.shape}")


# ── TEST ───────────────────────────────────────────────────────────────────
print("\n--- Building TEST final dataset ---")

test_base = cleaned_dfs["test_cleaned"].copy()
print(f"  Base (test_cleaned): {test_base.shape}")

# Merge test_target_encoding first
test_final = safe_merge(test_base, cleaned_dfs["test_target_encoding"], "test_target_encoding")

# Merge temporal, holiday, oil, external features from train feature files
# (these are store/family/date level features — overlap with test keys)
test_extra_order = [
    ("train_temporal_features",  cleaned_dfs["train_temporal_features"]),
    ("train_holiday_features",   cleaned_dfs["train_holiday_features"]),
    ("train_oil_store_features", cleaned_dfs["train_oil_store_features"]),
    ("train_external_features",  cleaned_dfs["train_external_features"]),
]

for label, df_feat in test_extra_order:
    # Only merge if the feature file has keys that overlap with test dates
    test_dates = set(test_final["date"].unique())
    feat_dates = set(df_feat["date"].unique()) if "date" in df_feat.columns else set()
    overlap = test_dates & feat_dates

    if not overlap:
        print(f"    Skipping {label}: no overlapping dates with test set.")
        continue

    test_final = safe_merge(test_final, df_feat, label)

# Fill any remaining NaN (test has no sales history, so lag/rolling will be 0)
test_final = fill_nan(test_final, "test_final_post_merge")

# Assert zero NaN
total_nan_test = test_final.isnull().sum().sum()
if total_nan_test > 0:
    print(f"\n  [ERROR] test_final still has {total_nan_test} NaN after merge!")
    bad_cols = test_final.isnull().sum()
    print(bad_cols[bad_cols > 0])
    sys.exit(1)

test_final_path = os.path.join(PROCESSED_DIR, "test_final.csv")
save_csv(test_final, test_final_path)
print(f"\n  test_final saved → {test_final_path}  shape={test_final.shape}")

print("\n>>> Phase 3 complete.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Validation Report
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("=== PHASE 4 — Validation Report (train_final) ===")
print("=" * 60)

df = train_final.copy()

# Ensure date column is parsed
df["date"] = pd.to_datetime(df["date"])

shape          = df.shape
date_min       = df["date"].min()
date_max       = df["date"].max()
unique_dates   = df["date"].nunique()
unique_stores  = df["store_nbr"].nunique()
unique_families= df["family"].nunique()
total_nan      = df.isnull().sum().sum()

# Zero sales percentage
if "sales" in df.columns:
    zero_sales_pct = (df["sales"] == 0).mean() * 100
else:
    zero_sales_pct = float("nan")

# Feature group counts
lag_cols      = [c for c in df.columns if c.lower().startswith("lag_")]
rolling_cols  = [c for c in df.columns if c.lower().startswith("rolling_")]
holiday_cols  = [c for c in df.columns if any(kw in c.lower() for kw in [
                    "holiday", "event", "is_holiday", "transferred", "bridge", "workday"])]
oil_cols      = [c for c in df.columns if "oil" in c.lower()]
encoding_cols = [c for c in df.columns if any(kw in c.lower() for kw in [
                    "target_enc", "te_", "encoding", "mean_enc", "family_enc", "store_enc",
                    "freq", "cluster"])]

print(f"""
  Shape                  : {shape}
  Date range             : {date_min.date()} → {date_max.date()}
  Unique dates           : {unique_dates}
  Unique stores          : {unique_stores}
  Unique families        : {unique_families}
  Total NaN              : {total_nan}
  Zero-sales percentage  : {zero_sales_pct:.2f}%

  Feature group counts:
    lag_* features       : {len(lag_cols)}  →  {lag_cols[:5]}{'...' if len(lag_cols) > 5 else ''}
    rolling_* features   : {len(rolling_cols)}  →  {rolling_cols[:5]}{'...' if len(rolling_cols) > 5 else ''}
    holiday features     : {len(holiday_cols)}  →  {holiday_cols}
    oil features         : {len(oil_cols)}  →  {oil_cols}
    encoding features    : {len(encoding_cols)}  →  {encoding_cols}

  All columns ({len(df.columns)} total):
""")

for i, col in enumerate(df.columns):
    dtype = df[col].dtype
    n_null = df[col].isnull().sum()
    print(f"    [{i:03d}] {col:<45} dtype={str(dtype):<10} NaN={n_null}")

print("\n>>> Phase 4 complete.")
print("\n" + "=" * 60)
print("  PIPELINE FINISHED SUCCESSFULLY")
print("=" * 60)
