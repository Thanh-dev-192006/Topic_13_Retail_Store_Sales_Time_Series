"""
fix_splits_pipeline.py
======================
Audit, diagnose, fix, and regenerate the splits/ directory for the
Store Sales Time Series Forecasting project.

Runs in 4 sequential phases:
  Phase 1 — Audit: find where 'family' and 'date' are dropped
  Phase 2 — Trace the row-count discrepancy
  Phase 3 — Rebuild train_final and regenerate splits/
  Phase 4 — Validate all outputs
"""

import sys
import io
import os
import ast
import json
import textwrap

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import gc
import numpy as np
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT = r"D:\Topic_13_Project\Topic_13_Retail_Store_Sales_Time_Series"
PROCESSED = os.path.join(PROJECT, "data", "processed")
CLEANED   = os.path.join(PROCESSED, "cleaned")
SPLITS    = os.path.join(PROCESSED, "splits")
SCRIPTS   = os.path.join(PROJECT, "scripts")
NOTEBOOKS = os.path.join(PROJECT, "notebooks")

os.makedirs(SPLITS, exist_ok=True)

# Source files — chosen for completeness (all 3,000,888 rows)
SRC = {
    "train_cleaned":    os.path.join(PROCESSED, "train_cleaned.csv"),
    "temporal":         os.path.join(CLEANED,   "train_temporal_features.csv"),   # only complete copy
    "holiday":          os.path.join(PROCESSED, "train_holiday_features.csv"),
    "oil_store":        os.path.join(PROCESSED, "train_oil_store_features.csv"),  # NOT cleaned/ (truncated)
    "external":         os.path.join(PROCESSED, "train_external_features.csv"),
    "target_encoding":  os.path.join(PROCESSED, "train_target_encoding.csv"),
    "test_final":       os.path.join(PROCESSED, "test_final.csv"),
}

JOIN_KEYS  = ["date", "store_nbr", "family"]
TRAIN_END  = "2017-07-31"   # train: date <= 2017-07-31  (date < 2017-08-01)
VAL_START  = "2017-08-01"
VAL_END    = "2017-08-15"


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Audit: Find where family and date are dropped
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PHASE 1 — Audit: Find where 'family', 'date', 'store_family' are dropped")
print("=" * 70)

DROP_KEYWORDS = ["family", "date", "store_family"]
FILTER_KEYWORDS = ["dropna", "query", "drop_duplicates", "isnull", ".loc[", ".iloc[",
                   "TRAIN_END", "VAL_START", "VAL_END", "EXCLUDE"]

findings = []

def scan_python_source(filepath, source, label_prefix=""):
    """Scan a block of Python source text for relevant patterns."""
    local_findings = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for column drops
        for kw in DROP_KEYWORDS:
            if kw in line and any(op in line for op in [
                "drop(", "EXCLUDE", "not in", "!= '" + kw + "'", "pop("
            ]):
                local_findings.append({
                    "file": filepath,
                    "line": lineno,
                    "label": label_prefix,
                    "type": "COLUMN DROP",
                    "keyword": kw,
                    "code": line.rstrip(),
                })

        # Check for row-filtering
        for kw in FILTER_KEYWORDS:
            if kw in line:
                # Avoid flagging import lines and comments
                if not line.strip().startswith("import") and not line.strip().startswith("from"):
                    local_findings.append({
                        "file": filepath,
                        "line": lineno,
                        "label": label_prefix,
                        "type": "ROW FILTER",
                        "keyword": kw,
                        "code": line.rstrip(),
                    })
    return local_findings


# ── Scan .py scripts ──────────────────────────────────────────────────────────
py_files = []
for root, _, files in os.walk(PROJECT):
    for f in files:
        if f.endswith(".py") and ".ipynb_checkpoints" not in root:
            py_files.append(os.path.join(root, f))

for fpath in py_files:
    try:
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        findings.extend(scan_python_source(fpath, src))
    except Exception as e:
        print(f"  [WARN] Could not read {fpath}: {e}")

# ── Scan .ipynb notebooks ─────────────────────────────────────────────────────
nb_files = []
for root, _, files in os.walk(PROJECT):
    for f in files:
        if f.endswith(".ipynb") and ".ipynb_checkpoints" not in root:
            nb_files.append(os.path.join(root, f))

for fpath in nb_files:
    try:
        with open(fpath, encoding="utf-8", errors="replace") as fh:
            nb = json.load(fh)
        for cell_idx, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            cell_src = "".join(cell.get("source", []))
            label = f"cell[{cell_idx}]"
            findings.extend(scan_python_source(fpath, cell_src, label_prefix=label))
    except Exception as e:
        print(f"  [WARN] Could not parse {fpath}: {e}")

# ── Print audit report ────────────────────────────────────────────────────────
# Deduplicate and group by type
drops   = [f for f in findings if f["type"] == "COLUMN DROP"]
filters = [f for f in findings if f["type"] == "ROW FILTER"]

# De-duplicate same (file, line) pairs
seen = set()
unique_findings = []
for f in findings:
    key = (f["file"], f["line"], f["keyword"])
    if key not in seen:
        seen.add(key)
        unique_findings.append(f)

drops   = [f for f in unique_findings if f["type"] == "COLUMN DROP"]
filters = [f for f in unique_findings if f["type"] == "ROW FILTER"]

print(f"\nFound {len(drops)} column-drop occurrences and {len(filters)} row-filter occurrences.\n")

# Focus report: narrow to the split-generation notebook and key scripts
KEY_FILES = ["issue1_model_setup", "han_setup", "merge_data", "nan_merge_pipeline",
             "feature_target_encoding", "feature_temporal"]

print("── Column Drops (all locations) ─────────────────────────────────────────")
for f in drops:
    short = os.path.relpath(f["file"], PROJECT).replace("\\", "/")
    label = f" {f['label']}" if f["label"] else ""
    print(f"  {short}{label}  L{f['line']}")
    print(f"    [{f['keyword']}] {f['code'].strip()}")

print("\n── Row Filters in KEY split-generation files ────────────────────────────")
for f in filters:
    short_path = os.path.relpath(f["file"], PROJECT).replace("\\", "/")
    if any(k in short_path for k in KEY_FILES):
        label = f" {f['label']}" if f["label"] else ""
        print(f"  {short_path}{label}  L{f['line']}")
        print(f"    [{f['keyword']}] {f['code'].strip()}")

print("""
ROOT CAUSES IDENTIFIED:
  1. notebooks/06_model_setup/issue1_model_setup.ipynb  cell[4]  (Task 4)
       EXCLUDE = {"date", "sales", "id", "family", "type", "city", "state", "store_family"}
       → 'date' and 'family' deliberately excluded from feature_cols
       → Result: all splits written WITHOUT these columns

  2. notebooks/06_model_setup/issue1_model_setup.ipynb  cell[3]  (Task 2)
       TRAIN_END = "2017-04-27"   VAL_START = "2017-04-28"   VAL_END = "2017-05-12"
       train_df = df[df["date"] <= TRAIN_END].copy()
       → train split was cut at 2017-04-27, placing 25,353 rows (Apr 28 – May 12)
         into val — they are NOT counted in train_features.csv row count

  3. data/processed/cleaned/train_oil_store_features.csv was truncated:
       → 2,835,151 rows (max date 2017-05-14) instead of 3,000,888 rows
       → This caused train_final.csv to be truncated to 2,830,221 rows (max 2017-05-12)
       → Fix: use data/processed/train_oil_store_features.csv (3,000,888 rows, NOT cleaned/)
""")

print(">>> Phase 1 complete.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Trace the Row-Count Discrepancy
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 2 — Trace the Row-Count Discrepancy")
print("=" * 70)

# 1. Load train_final and filter date < 2017-08-01
print("\n[1] train_final.csv filtered to date < 2017-08-01:")
tf = pd.read_csv(os.path.join(PROCESSED, "train_final.csv"), parse_dates=["date"])
tf_train_window = tf[tf["date"] < "2017-08-01"]
print(f"    train_final.csv total rows : {len(tf):,}")
print(f"    Rows with date < 2017-08-01: {len(tf_train_window):,}")
print(f"    Date range                 : {tf['date'].min().date()} → {tf['date'].max().date()}")

# 2. Load current splits/train_features.csv (read header + row count only to save memory)
print("\n[2] splits/train_features.csv:")
tr_feat_header = pd.read_csv(os.path.join(SPLITS, "train_features.csv"), nrows=5, low_memory=False)
tr_feat_rows = sum(1 for _ in open(os.path.join(SPLITS, "train_features.csv"), encoding="utf-8")) - 1
print(f"    Shape: ({tr_feat_rows:,} rows, {len(tr_feat_header.columns)} cols)")
print(f"    Columns: {list(tr_feat_header.columns)}")
print(f"    Has 'date'  : {'date' in tr_feat_header.columns}")
print(f"    Has 'family': {'family' in tr_feat_header.columns}")

# 3. split_metadata.csv
meta_path = os.path.join(SPLITS, "split_metadata.csv")
print(f"\n[3] split_metadata.csv: {'EXISTS' if os.path.exists(meta_path) else 'MISSING'}")
if os.path.exists(meta_path):
    meta = pd.read_csv(meta_path)
    print(meta.to_string())

# 4. Row count math
print("\n[4] Row-count discrepancy analysis:")
raw_train = pd.read_csv(
    os.path.join(PROJECT, "data", "raw", "train.csv"),
    usecols=["date"], parse_dates=["date"]
)
print(f"    raw/train.csv rows   : {len(raw_train):,}")
print(f"    raw date range       : {raw_train.date.min().date()} → {raw_train.date.max().date()}")
print(f"    train_final.csv rows : {len(tf):,}")
print(f"    train_features rows  : {tr_feat_rows:,}")
print(f"    Missing vs raw       : {len(raw_train) - len(tf):,}  "
      f"(cleaned/train_oil_store_features.csv was truncated at 2017-05-14; "
      f"merge pipeline produced truncated train_final)")
print(f"    Missing vs train_final: {len(tf) - tr_feat_rows:,}  "
      f"(TRAIN_END cutoff at 2017-04-27; rows for 2017-04-28→2017-05-12 were "
      f"placed in val split, not train split)")

# 5. Sample the difference
print("\n[5] 5 sample rows in train_final but not in splits/train_features:")
if "date" not in tr_feat_header.columns:
    print("    (date column absent from splits; identifying missing rows by date range)")
    missing_rows = tf[(tf["date"] >= "2017-04-28") & (tf["date"] <= "2017-05-12")]
    print(f"    Total missing rows (2017-04-28 → 2017-05-12): {len(missing_rows):,}")
    print(missing_rows[["date", "store_nbr", "family", "sales"]].head(5).to_string(index=False))
else:
    print("    date column present — no row discrepancy by inspection")

print("""
SUMMARY:
  root/train.csv       : 3,000,888 rows  (2013-01-01 → 2017-08-15)
  train_final.csv      : 2,830,221 rows  (2013-01-01 → 2017-05-12)
    → 170,667 rows lost because cleaned/train_oil_store_features.csv (2,835,151 rows)
      did NOT cover 2017-05-15 → 2017-08-15 when the merge pipeline ran.
  train_features.csv   : 2,804,868 rows  (2013-01-01 → 2017-04-27)
    → 25,353 rows lost because TRAIN_END was set to "2017-04-27" and those rows
      were placed in the validation split instead of training.
""")

print(">>> Phase 2 complete.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Fix the Pipeline and Regenerate splits/
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 3 — Fix the Pipeline and Regenerate splits/")
print("=" * 70)

# ── Verify all source files exist ─────────────────────────────────────────────
print("\n[3.1] Verifying source files...")
for key, path in SRC.items():
    exists = os.path.exists(path)
    rows_str = ""
    if exists:
        n = sum(1 for _ in open(path, encoding="utf-8", errors="replace")) - 1
        rows_str = f"  {n:,} rows"
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {key}: {os.path.relpath(path, PROJECT).replace(chr(92), '/')}{rows_str}")

missing_src = [k for k, p in SRC.items() if not os.path.exists(p)]
if missing_src:
    raise FileNotFoundError(f"Missing required source files: {missing_src}")

# ── Helper: memory-efficient safe left-merge ─────────────────────────────────
def safe_merge_path(base: pd.DataFrame, path: str, label: str,
                    keys: list = JOIN_KEYS) -> pd.DataFrame:
    """
    Read only the new columns (not already in base) from `path`, then left-merge.
    This avoids loading duplicate columns into memory.
    """
    n_base = len(base)
    # Peek at column names without reading data
    header = pd.read_csv(path, nrows=0).columns.tolist()
    existing = set(base.columns) - set(keys)
    new_cols = [c for c in header if c not in existing]
    if not any(c not in keys for c in new_cols):
        print(f"    Skipped {label}: no new columns to add")
        return base
    # Read only JOIN_KEYS + new columns
    usecols = [c for c in new_cols if c in header]   # guaranteed subset
    other = pd.read_csv(path, usecols=usecols, parse_dates=["date"] if "date" in usecols else False,
                        low_memory=False)
    n_added = len([c for c in other.columns if c not in keys])
    merged = base.merge(other, on=[k for k in keys if k in other.columns], how="left")
    if len(merged) != n_base:
        raise ValueError(
            f"Row count changed merging {label}: {n_base} → {len(merged)}. "
            f"Check for duplicate keys in {label}."
        )
    del other
    gc.collect()
    # Downcast numeric columns to save memory
    for col in merged.select_dtypes(include="int64").columns:
        merged[col] = pd.to_numeric(merged[col], downcast="integer")
    for col in merged.select_dtypes(include="float64").columns:
        merged[col] = pd.to_numeric(merged[col], downcast="float")
    print(f"    Merged {label}: +{n_added} new cols → shape now {merged.shape}")
    return merged

# ── NaN fill strategy ─────────────────────────────────────────────────────────
def fill_nans(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Fill NaN with domain-aware strategies; never drops rows."""
    df = df.copy()
    n_before = df.isnull().sum().sum()
    for col in df.columns:
        col_l = col.lower()
        if df[col].isnull().sum() == 0:
            continue
        if col in JOIN_KEYS or col in ("id", "sales"):
            continue
        if col_l.startswith("lag_") or col_l.startswith("rolling_"):
            if "oil" in col_l:
                df[col] = df[col].ffill().bfill().fillna(0)
            else:
                # Lag features: NaN means no history → fill 0
                df[col] = df[col].fillna(0)
        elif "oil" in col_l:
            df[col] = df[col].ffill().bfill().fillna(0)
        elif any(k in col_l for k in ["holiday", "earthquake", "carnaval", "transferred"]):
            df[col] = df[col].fillna(0)
        elif "te_" in col_l or col_l.endswith("_te") or "encoding" in col_l:
            df[col] = df[col].fillna(df[col].mean())
        elif any(k in col_l for k in ["freq", "cluster", "store_type", "city", "state"]):
            mode = df[col].mode()
            df[col] = df[col].fillna(mode.iloc[0] if not mode.empty else 0)
        else:
            df[col] = df[col].fillna(0)
    n_after = df.isnull().sum().sum()
    if n_after > 0:
        bad = df.isnull().sum()
        bad = bad[bad > 0]
        raise ValueError(f"[{label}] Still has {n_after} NaN after fill:\n{bad}")
    print(f"    NaN fill [{label}]: {n_before} → {n_after}")
    return df


# ── 3.2 Rebuild train_final_v2.csv ───────────────────────────────────────────
print("\n[3.2] Building train_final_v2.csv (target: 3,000,888 rows, 2013-01-01 → 2017-08-15)...")

# Base: train_cleaned (date, store_nbr, family, sales, onpromotion, id)
print("  Loading base: train_cleaned.csv")
base = pd.read_csv(SRC["train_cleaned"], parse_dates=["date"], low_memory=False)
# Downcast base to save memory
for col in base.select_dtypes(include="int64").columns:
    base[col] = pd.to_numeric(base[col], downcast="integer")
for col in base.select_dtypes(include="float64").columns:
    base[col] = pd.to_numeric(base[col], downcast="float")
print(f"  Base shape: {base.shape}  memory: {base.memory_usage(deep=True).sum() / 1e6:.1f} MB")

# Feature files to merge — ORDER MATTERS (earlier files win on duplicate cols)
merge_plan = [
    ("temporal features",  SRC["temporal"]),
    ("holiday features",   SRC["holiday"]),
    ("oil+store features", SRC["oil_store"]),
    ("external features",  SRC["external"]),
    ("target encoding",    SRC["target_encoding"]),
]

print("  Merging feature files (reading only new columns per file)...")
for label, path in merge_plan:
    base = safe_merge_path(base, path, label)

# Fill any NaN introduced by left-joins (e.g. lag features on early dates)
print("  Filling NaN values...")
base = fill_nans(base, "train_final_v2")

# Validate zero NaN
assert base.isnull().sum().sum() == 0, "train_final_v2 has unexpected NaN!"
print(f"  Final shape: {base.shape}")
print(f"  Date range : {base['date'].min().date()} → {base['date'].max().date()}")
print(f"  Stores     : {base['store_nbr'].nunique()}")
print(f"  Families   : {base['family'].nunique()}")

train_final_v2_path = os.path.join(PROCESSED, "train_final_v2.csv")
base.to_csv(train_final_v2_path, index=False)
print(f"  Saved: train_final_v2.csv  ({len(base):,} rows)")

train_final_v2 = base


# ── 3.3 Define split boundaries and feature columns ──────────────────────────
print("\n[3.3] Defining splits...")

#   Do NOT exclude 'date' or 'family'.  Drop 'store_family' (redundant) and
#   internal identifiers not used as model features.
EXCLUDE = {"sales", "id", "store_family"}     # KEEP: date, family, store_nbr
feature_cols = [c for c in train_final_v2.columns if c not in EXCLUDE]

print(f"  EXCLUDE set   : {EXCLUDE}")
print(f"  Feature cols  : {len(feature_cols)} columns")
print(f"  Confirmed 'date'   in features : {'date' in feature_cols}")
print(f"  Confirmed 'family' in features : {'family' in feature_cols}")
print(f"  Confirmed 'store_nbr' in features: {'store_nbr' in feature_cols}")

# Temporal split
train_mask = train_final_v2["date"] < "2017-08-01"
val_mask   = (train_final_v2["date"] >= "2017-08-01") & (train_final_v2["date"] <= "2017-08-15")

train_df = train_final_v2[train_mask].copy().reset_index(drop=True)
val_df   = train_final_v2[val_mask].copy().reset_index(drop=True)

assert train_df["date"].max() < pd.Timestamp("2017-08-01"), "DATA LEAK: train overlaps val!"
assert val_df["date"].min()  >= pd.Timestamp("2017-08-01"), "DATA LEAK: val starts too early!"

print(f"\n  Train : {train_df.shape}  | {train_df['date'].min().date()} → {train_df['date'].max().date()}")
print(f"  Val   : {val_df.shape}    | {val_df['date'].min().date()} → {val_df['date'].max().date()}")


# ── 3.4 Build feature/target arrays ─────────────────────────────────────────
print("\n[3.4] Building feature & target splits...")

# Features: all feature_cols (includes date, family, store_nbr)
X_train = train_df[feature_cols].copy()
X_val   = val_df[feature_cols].copy()

# Target: log1p(sales)
y_train = np.log1p(train_df["sales"]).rename("sales_log")
y_val   = np.log1p(val_df["sales"]).rename("sales_log")
y_val_original = val_df["sales"].rename("sales").copy()

# Test features
print("  Loading test_final.csv...")
test_raw = pd.read_csv(SRC["test_final"], parse_dates=["date"], low_memory=False)
print(f"  Test shape: {test_raw.shape}")
print(f"  Test date range: {test_raw['date'].min().date()} → {test_raw['date'].max().date()}")

# Test features: keep all columns present in test_final that are also features
#   (test has no 'sales', so lag/rolling will be 0-filled from pipeline)
test_feature_cols = [c for c in feature_cols if c in test_raw.columns]
X_test = test_raw[test_feature_cols].copy().reset_index(drop=True)

# Check for any missing feature cols in test (expected: lag/rolling may be absent)
missing_in_test = [c for c in feature_cols if c not in test_raw.columns]
if missing_in_test:
    print(f"  Cols in train features but absent from test_final: {missing_in_test}")
    print(f"  → Adding as 0-filled columns to X_test")
    for col in missing_in_test:
        X_test[col] = 0
    X_test = X_test[feature_cols]   # enforce same column order

print(f"\n  X_train : {X_train.shape}")
print(f"  X_val   : {X_val.shape}")
print(f"  X_test  : {X_test.shape}")


# ── 3.5 Target encoding split files ─────────────────────────────────────────
# train_target_encoding and test_target_encoding are convenience files for
# models that want them separately.
train_te = train_df[["date", "store_nbr", "family", "store_family_te"]].copy()
test_te  = test_raw[["date", "store_nbr", "family", "store_family_te"]].copy() \
           if "store_family_te" in test_raw.columns \
           else pd.DataFrame(columns=["date", "store_nbr", "family", "store_family_te"])


# ── 3.6 Save all splits ───────────────────────────────────────────────────────
print("\n[3.5] Saving splits to", SPLITS)

saves = [
    ("train_features.csv",        X_train),
    ("train_target.csv",          y_train.to_frame()),
    ("val_features.csv",          X_val),
    ("val_target.csv",            y_val.to_frame()),
    ("val_target_original.csv",   y_val_original.to_frame()),
    ("test_features.csv",         X_test),
    ("train_target_encoding.csv", train_te),
    ("test_target_encoding.csv",  test_te),
]

for fname, df_out in saves:
    path = os.path.join(SPLITS, fname)
    df_out.to_csv(path, index=False)
    print(f"  Saved: {fname}  {df_out.shape}")

# Update split_metadata.csv
meta = pd.DataFrame([{
    "train": (f"{train_df['date'].min().date()} → {train_df['date'].max().date()} "
              f"({len(train_df):,} rows)"),
    "val":   (f"{val_df['date'].min().date()} → {val_df['date'].max().date()} "
              f"({len(val_df):,} rows)"),
    "test":  (f"{test_raw['date'].min().date()} → {test_raw['date'].max().date()} "
              f"({len(test_raw):,} rows)"),
    "feature_count":      len(feature_cols),
    "date_kept":          True,
    "family_kept":        True,
    "store_family_dropped": True,
    "target_transform":   "log1p",
    "eval_metric":        "RMSLE",
    "train_final_source": "train_final_v2.csv (rebuilt from all source feature files)",
    "oil_store_note":     "Used processed/train_oil_store_features.csv (3000888 rows), "
                          "NOT cleaned/ (truncated at 2835151 rows)",
}])
meta.to_csv(os.path.join(SPLITS, "split_metadata.csv"), index=False)
print("  Saved: split_metadata.csv")

print("\n>>> Phase 3 complete.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Validate All Outputs
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PHASE 4 — Validate All Outputs")
print("=" * 70)

# Reload from disk to validate saved files, not in-memory objects
train_features = pd.read_csv(os.path.join(SPLITS, "train_features.csv"), parse_dates=["date"])
val_features   = pd.read_csv(os.path.join(SPLITS, "val_features.csv"),   parse_dates=["date"])
test_features  = pd.read_csv(os.path.join(SPLITS, "test_features.csv"),  parse_dates=["date"])
train_target   = pd.read_csv(os.path.join(SPLITS, "train_target.csv"))
val_target     = pd.read_csv(os.path.join(SPLITS, "val_target.csv"))
train_final_check = pd.read_csv(train_final_v2_path, usecols=["date"], parse_dates=["date"])

failures = []

def check(condition, msg):
    if not condition:
        failures.append(msg)
        print(f"  [FAIL] {msg}")
    else:
        print(f"  [PASS] {msg}")


# ── Check 1: Required columns exist ──────────────────────────────────────────
print("\n[Check 1] Required columns (date, store_nbr, family) exist in all splits:")
required = ["date", "store_nbr", "family"]
for col in required:
    check(col in train_features.columns, f"'date' in train_features" if col == "date"
          else f"'{col}' in train_features")
    check(col in val_features.columns,   f"'{col}' in val_features")
    check(col in test_features.columns,  f"'{col}' in test_features")

# ── Check 2: Row counts consistent with train_final_v2 ───────────────────────
print("\n[Check 2] Row counts match train_final_v2:")
expected_train_rows = len(train_final_check[train_final_check["date"] < "2017-08-01"])
check(len(train_features) == expected_train_rows,
      f"train_features rows: {len(train_features):,} == {expected_train_rows:,} "
      f"(train_final_v2 rows with date < 2017-08-01)")

expected_val_rows = len(
    train_final_check[
        (train_final_check["date"] >= "2017-08-01") &
        (train_final_check["date"] <= "2017-08-15")
    ]
)
check(len(val_features) == expected_val_rows,
      f"val_features rows: {len(val_features):,} == {expected_val_rows:,} "
      f"(train_final_v2 rows 2017-08-01→2017-08-15)")

# ── Check 3: No date leakage ──────────────────────────────────────────────────
print("\n[Check 3] No date leakage between splits:")
check(train_features["date"].max() < pd.Timestamp("2017-08-01"),
      f"train max date {train_features['date'].max().date()} < 2017-08-01")
check(val_features["date"].min() >= pd.Timestamp("2017-08-01"),
      f"val min date {val_features['date'].min().date()} >= 2017-08-01")
check(val_features["date"].max() <= pd.Timestamp("2017-08-15"),
      f"val max date {val_features['date'].max().date()} <= 2017-08-15")

# ── Check 4: All 1782 store-family combinations in train ─────────────────────
print("\n[Check 4] All 1782 store-family combinations present in train:")
n_combos = train_features.groupby(["store_nbr", "family"]).ngroups
check(n_combos == 1782,
      f"store-family combos in train: {n_combos} == 1782")

# ── Check 5: Exactly 33 unique families ──────────────────────────────────────
print("\n[Check 5] Exactly 33 unique family values:")
n_fam_train = train_features["family"].nunique()
n_fam_val   = val_features["family"].nunique()
n_fam_test  = test_features["family"].nunique()
check(n_fam_train == 33, f"train family count: {n_fam_train} == 33")
check(n_fam_val   == 33, f"val   family count: {n_fam_val} == 33")
check(n_fam_test  == 33, f"test  family count: {n_fam_test} == 33")

# ── Check 6: Target row counts match features ─────────────────────────────────
print("\n[Check 6] Target row counts match feature row counts:")
check(len(train_target) == len(train_features),
      f"train_target rows {len(train_target):,} == train_features rows {len(train_features):,}")
check(len(val_target) == len(val_features),
      f"val_target rows {len(val_target):,} == val_features rows {len(val_features):,}")

# ── Final result ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
if failures:
    raise ValueError(
        f"\n{len(failures)} check(s) FAILED:\n" + "\n".join(f"  - {f}" for f in failures)
    )
else:
    print("✅ ALL CHECKS PASSED")

# Summary table
print("\nSplit shapes summary:")
print(f"  {'File':<35} {'Shape':>20}")
print(f"  {'-'*35} {'-'*20}")
for fname, df_out in [
    ("train_features.csv",      train_features),
    ("train_target.csv",        train_target),
    ("val_features.csv",        val_features),
    ("val_target.csv",          val_target),
    ("test_features.csv",       test_features),
]:
    print(f"  {fname:<35} {str(df_out.shape):>20}")

print(f"\n  {'train_final_v2.csv':<35} {str((len(train_final_v2), len(train_final_v2.columns))):>20}")
print("\n>>> Phase 4 complete.")
print("=" * 70)
