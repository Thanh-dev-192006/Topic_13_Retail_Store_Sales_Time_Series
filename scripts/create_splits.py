"""
create_splits.py
================
Temporal train / validation / test split on train_final.csv.

Split boundaries (fixed, non-random):
    Train : 2013-01-01  to  2017-06-30  (inclusive)
    Val   : 2017-07-01  to  2017-07-31  (inclusive)
    Test  : 2017-08-01  to  2017-08-15  (inclusive)

Outputs saved to data/processed/splits/:
    train_features.csv   -- X_train (all feature columns)
    train_target.csv     -- y_train (sales column)
    val_features.csv     -- X_val
    val_target.csv       -- y_val
    test_features.csv    -- X_test
    test_target.csv      -- y_test

Feature columns = ALL columns EXCEPT: sales, date, id

Usage:
    python scripts/create_splits.py
"""

import os
import sys
import pandas as pd

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR  = os.path.join(BASE, "data", "processed")
SPLITS_DIR = os.path.join(PROC_DIR, "splits")

TRAIN_FINAL_PATH = os.path.join(PROC_DIR, "train_final.csv")

# Fixed temporal split boundaries
TRAIN_START = "2013-01-01"
TRAIN_END   = "2017-06-30"
VAL_START   = "2017-07-01"
VAL_END     = "2017-07-31"
TEST_START  = "2017-08-01"
TEST_END    = "2017-08-15"

# Columns to exclude from the model-input feature set.
# NOTE: date, store_nbr, and family are kept in the saved CSV files for
#       evaluation, time-series plotting, and debugging (per project requirements).
#       Only 'sales' (target) and 'id' (row identifier) are dropped from the
#       saved feature files.
EXCLUDE_COLS = {"sales", "id"}

os.makedirs(SPLITS_DIR, exist_ok=True)

print("=" * 70)
print("CREATE TEMPORAL TRAIN / VAL / TEST SPLITS")
print("=" * 70)
print(f"  Train : {TRAIN_START} to {TRAIN_END}")
print(f"  Val   : {VAL_START} to {VAL_END}")
print(f"  Test  : {TEST_START} to {TEST_END}")

# ---------------------------------------------------------------------------
# Load train_final.csv
# ---------------------------------------------------------------------------
print(f"\n[1/5] Loading {TRAIN_FINAL_PATH} ...")
df = pd.read_csv(TRAIN_FINAL_PATH, parse_dates=["date"])
print(f"  Loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# ---------------------------------------------------------------------------
# Define feature columns
# ---------------------------------------------------------------------------
feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS]
print(f"\n[2/5] Feature columns ({len(feature_cols)} total):")
for c in feature_cols:
    print(f"  {c}")

# ---------------------------------------------------------------------------
# Apply temporal splits (NO random splitting -- date-boundary only)
# ---------------------------------------------------------------------------
print("\n[3/5] Applying temporal splits...")

train_df = df[(df["date"] >= TRAIN_START) & (df["date"] <= TRAIN_END)].copy()
val_df   = df[(df["date"] >= VAL_START)   & (df["date"] <= VAL_END)].copy()
test_df  = df[(df["date"] >= TEST_START)  & (df["date"] <= TEST_END)].copy()

X_train = train_df[feature_cols].reset_index(drop=True)
y_train = train_df["sales"].reset_index(drop=True).rename("sales")

X_val   = val_df[feature_cols].reset_index(drop=True)
y_val   = val_df["sales"].reset_index(drop=True).rename("sales")

X_test  = test_df[feature_cols].reset_index(drop=True)
y_test  = test_df["sales"].reset_index(drop=True).rename("sales")

# ---------------------------------------------------------------------------
# No-leakage assertion
# ---------------------------------------------------------------------------
print("\n[4/5] Verifying no data leakage across splits...")

train_max = pd.Timestamp(TRAIN_END)
val_min   = pd.Timestamp(VAL_START)
val_max   = pd.Timestamp(VAL_END)
test_min  = pd.Timestamp(TEST_START)

assert train_max < val_min,  f"LEAKAGE: train end ({TRAIN_END}) >= val start ({VAL_START})"
assert val_max   < test_min, f"LEAKAGE: val end ({VAL_END}) >= test start ({TEST_START})"
print(f"  PASS: train end ({TRAIN_END}) < val start ({VAL_START})")
print(f"  PASS: val end   ({VAL_END}) < test start ({TEST_START})")

# Verify actual data dates honour the boundaries
assert train_df["date"].max() <= train_max, "LEAKAGE: train data exceeds TRAIN_END"
assert val_df["date"].min()   >= val_min,  "LEAKAGE: val data precedes VAL_START"
assert val_df["date"].max()   <= val_max,  "LEAKAGE: val data exceeds VAL_END"
assert test_df["date"].min()  >= test_min, "LEAKAGE: test data precedes TEST_START"
print("  PASS: all split date ranges verified against boundaries")

# ---------------------------------------------------------------------------
# Shape and date range report
# ---------------------------------------------------------------------------
print("\n  Split summary:")
splits_info = [
    ("Train", X_train, y_train, train_df["date"]),
    ("Val",   X_val,   y_val,   val_df["date"]),
    ("Test",  X_test,  y_test,  test_df["date"]),
]
for name, X, y, dates in splits_info:
    print(f"  {name:<6}: X={X.shape}  y={y.shape}  "
          f"dates={dates.min().date()} to {dates.max().date()}")

# ---------------------------------------------------------------------------
# Save splits
# ---------------------------------------------------------------------------
print(f"\n[5/5] Saving splits to {SPLITS_DIR} ...")

saves = [
    ("train_features.csv", X_train),
    ("train_target.csv",   y_train.to_frame()),
    ("val_features.csv",   X_val),
    ("val_target.csv",     y_val.to_frame()),
    ("test_features.csv",  X_test),
    ("test_target.csv",    y_test.to_frame()),
]

for fname, data in saves:
    path = os.path.join(SPLITS_DIR, fname)
    data.to_csv(path, index=False)
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"  Saved: {fname:<25} shape={data.shape}  ({size_mb:.1f} MB)")

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("SPLIT SUMMARY")
print("=" * 70)
print(f"  Total rows in train_final.csv : {len(df):,}")
print(f"  X_train shape : {X_train.shape}")
print(f"  y_train shape : {y_train.shape}")
print(f"  X_val   shape : {X_val.shape}")
print(f"  y_val   shape : {y_val.shape}")
print(f"  X_test  shape : {X_test.shape}")
print(f"  y_test  shape : {y_test.shape}")
print(f"  Features ({len(feature_cols)}): {feature_cols}")
print(f"\n  Train date range : {train_df['date'].min().date()} to {train_df['date'].max().date()}")
print(f"  Val   date range : {val_df['date'].min().date()} to {val_df['date'].max().date()}")
print(f"  Test  date range : {test_df['date'].min().date()} to {test_df['date'].max().date()}")
print("\ncreate_splits.py complete.")
print("=" * 70)
