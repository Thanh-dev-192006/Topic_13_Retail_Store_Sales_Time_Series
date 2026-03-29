"""
validate_and_finalize.py
========================
Quick validation pass on train_final_v2.csv (the complete feature-merged
dataset) and promotion to train_final.csv.

This script does NOT recompute features from scratch. It:
  1. Loads train_final_v2.csv (2013-01-01 to 2017-08-15, all features)
  2. Runs all required quality checks
  3. Forward-fills oil_price nulls (expected ~3-5% from weekend/holiday gaps)
  4. Saves the validated result as train_final.csv (overwrites old truncated file)

To fully rebuild train_final.csv from raw inputs, use:
    python scripts/build_train_final.py   (slow -- recomputes all features)
"""

import os
import sys
import pandas as pd
import numpy as np

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE, "data", "processed")

SRC_PATH = os.path.join(PROC_DIR, "train_final_v2.csv")
DST_PATH = os.path.join(PROC_DIR, "train_final.csv")

print("=" * 70)
print("VALIDATE & FINALIZE -- train_final_v2.csv -> train_final.csv")
print("=" * 70)

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
print(f"\n[1/6] Loading {SRC_PATH} ...")
df = pd.read_csv(SRC_PATH, parse_dates=["date"])
print(f"  Loaded   : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  Dates    : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Stores   : {df['store_nbr'].nunique()}")
print(f"  Families : {df['family'].nunique()}")

# ---------------------------------------------------------------------------
# Sort by composite key
# ---------------------------------------------------------------------------
print("\n[2/6] Sorting by (store_nbr, family, date)...")
df = df.sort_values(["store_nbr", "family", "date"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# Duplicate check
# ---------------------------------------------------------------------------
print("\n[3/6] Checking for duplicate (date, store_nbr, family) rows...")
dup_count = df.duplicated(subset=["date", "store_nbr", "family"]).sum()
assert dup_count == 0, f"FAIL: {dup_count} duplicate rows detected on composite key!"
print(f"  PASS: No duplicate rows on (date, store_nbr, family)  [0 duplicates]")

# ---------------------------------------------------------------------------
# Sales null check
# ---------------------------------------------------------------------------
print("\n[4/6] Checking sales column for nulls...")
sales_nulls = df["sales"].isna().sum()
assert sales_nulls == 0, f"FAIL: {sales_nulls} null values in sales column!"
print(f"  PASS: No null values in sales  [min={df['sales'].min():.0f}, max={df['sales'].max():.0f}]")

# ---------------------------------------------------------------------------
# Oil price forward-fill (weekend / holiday gaps expected at ~3-5%)
# ---------------------------------------------------------------------------
print("\n[5/6] Handling oil_price nulls (forward-fill)...")
oil_null_before = df["oil_price"].isna().sum()
oil_null_pct    = oil_null_before / len(df) * 100
print(f"  oil_price nulls before ffill : {oil_null_before:,} ({oil_null_pct:.2f}%)")

if oil_null_before > 0:
    # Sort by date first so ffill is temporally correct
    df = df.sort_values("date").reset_index(drop=True)
    df["oil_price"] = df["oil_price"].ffill().bfill()
    # Re-sort to composite key order
    df = df.sort_values(["store_nbr", "family", "date"]).reset_index(drop=True)
    oil_null_after = df["oil_price"].isna().sum()
    print(f"  oil_price nulls after ffill  : {oil_null_after:,}")
    if oil_null_after == 0:
        print("  PASS: oil_price fully imputed via forward-fill")
    else:
        print(f"  WARNING: {oil_null_after} oil_price nulls remain (check oil date coverage)")
else:
    print("  oil_price has 0 nulls -- no fill needed")

# ---------------------------------------------------------------------------
# Full null rate audit
# ---------------------------------------------------------------------------
print("\n[6/6] Null rate audit -- all feature columns:")

EXCLUDE = {"id", "date", "sales"}
HIGH_NULL_THRESHOLD = 0.05
high_null_cols = []

for col in df.columns:
    if col in EXCLUDE:
        continue
    rate = df[col].isna().mean()
    if rate > 0:
        flag = "  <-- WARNING: > 5%" if rate > HIGH_NULL_THRESHOLD else ""
        print(f"  {col:<40} {rate*100:6.2f}%{flag}")
        if rate > HIGH_NULL_THRESHOLD:
            high_null_cols.append((col, rate))

print()
if high_null_cols:
    print("  WARNING -- COLUMNS WITH NULL RATE > 5% (review before training):")
    for col, rate in high_null_cols:
        print(f"     {col}: {rate*100:.2f}%")
else:
    print("  PASS: No feature column exceeds 5% null rate")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "-" * 70)
print("VALIDATED DATASET SUMMARY")
print("-" * 70)
print(f"  Shape      : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  Date range : {df['date'].min().date()} to {df['date'].max().date()}")
print(f"  Sales nulls: {df['sales'].isna().sum()}")
print(f"  Duplicates : {df.duplicated(subset=['date','store_nbr','family']).sum()}")
print(f"  Columns ({df.shape[1]}):")
for c in df.columns:
    print(f"    {c}")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
print(f"\nSaving to {DST_PATH} ...")
df.to_csv(DST_PATH, index=False)
print(f"  SAVED: {df.shape[0]:,} rows x {df.shape[1]} cols -> train_final.csv")
print("\n" + "=" * 70)
print("validate_and_finalize.py complete.")
print("=" * 70)
