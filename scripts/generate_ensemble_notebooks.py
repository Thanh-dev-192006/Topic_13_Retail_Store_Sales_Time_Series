import json
from pathlib import Path
from textwrap import dedent


METADATA = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.12.6",
    },
}


def source_lines(text: str) -> list[str]:
    return dedent(text).lstrip("\n").splitlines(keepends=True)


def md_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source_lines(text),
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines(text),
    }


COMMON_LOAD = """
import os
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.metrics import mean_squared_log_error
from sklearn.preprocessing import LabelEncoder


def find_project_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "data" / "processed" / "splits").exists():
            return candidate
    if (cwd / "Topic_13_Retail_Store_Sales_Time_Series").exists():
        return cwd / "Topic_13_Retail_Store_Sales_Time_Series"
    raise FileNotFoundError("Could not locate project root from current working directory.")


BASE = find_project_root()
SPLIT_DIR = BASE / "data" / "processed" / "splits"

X_train = pd.read_csv(SPLIT_DIR / "train_features.csv")
y_train = pd.read_csv(SPLIT_DIR / "train_target.csv")
X_val = pd.read_csv(SPLIT_DIR / "val_features.csv")
y_val = pd.read_csv(SPLIT_DIR / "val_target.csv")
X_test = pd.read_csv(SPLIT_DIR / "test_features.csv")
y_test = pd.read_csv(SPLIT_DIR / "test_target.csv")
y_val_orig = pd.read_csv(SPLIT_DIR / "val_target_original.csv")

X_train_raw = X_train.copy()
X_val_raw = X_val.copy()
X_test_raw = X_test.copy()

y_test_orig = pd.DataFrame({"sales": np.expm1(y_test["sales_log"])})

xgb_best_model = joblib.load(BASE / "notebooks" / "08_forecasting" / "xgb_best_model.pkl")
lgb_best_model = joblib.load(BASE / "notebooks" / "08_forecasting" / "lgb_best_model.pkl")


def rmsle_from_log(y_true, pred_log):
    y_true = np.clip(np.asarray(y_true, dtype=float), 0, None)
    y_pred = np.clip(np.expm1(np.asarray(pred_log, dtype=float)), 0, None)
    return np.sqrt(mean_squared_log_error(y_true, y_pred))


def build_summary_rows():
    return [
        {
            "Approach": "LightGBM (tuned)",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], lgb_val_pred), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], lgb_test_pred), 6),
        },
        {
            "Approach": "XGBoost (tuned)",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], xgb_val_pred), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], xgb_test_pred), 6),
        },
    ]
"""


COMMON_ENCODE = """
object_cols = X_train.select_dtypes(include=["object"]).columns.tolist()
label_encoders = {}

for col in object_cols:
    le = LabelEncoder()
    combined = pd.concat([X_train[col], X_val[col], X_test[col]], ignore_index=True).astype(str)
    le.fit(combined)

    X_train[col] = le.transform(X_train[col].astype(str)).astype(np.int32)
    X_val[col] = le.transform(X_val[col].astype(str)).astype(np.int32)
    X_test[col] = le.transform(X_test[col].astype(str)).astype(np.int32)

    label_encoders[col] = le

rest = X_train.select_dtypes(include=["object"]).columns.tolist()
if rest:
    raise ValueError(f"Still has object columns after encoding: {rest}")

print(f"Encoded {len(object_cols)} categorical columns.")
print(f"X_train {X_train.shape} | X_val {X_val.shape} | X_test {X_test.shape}")
"""


COMMON_PRED = """
lgb_val_pred = lgb_best_model.predict(X_val)
lgb_test_pred = lgb_best_model.predict(X_test)
lgb_train_pred = lgb_best_model.predict(X_train)

xgb_val_pred = xgb_best_model.predict(X_val)
xgb_test_pred = xgb_best_model.predict(X_test)
xgb_train_pred = xgb_best_model.predict(X_train)

weight_grid = np.round(np.arange(0.0, 1.01, 0.01), 2)

global_results = []
for lgb_w in weight_grid:
    xgb_w = round(1 - lgb_w, 2)
    val_blend = lgb_w * lgb_val_pred + xgb_w * xgb_val_pred
    test_blend = lgb_w * lgb_test_pred + xgb_w * xgb_test_pred
    global_results.append(
        {
            "Weights": f"LGB{lgb_w:.2f}-XGB{xgb_w:.2f}",
            "LGB Weight": lgb_w,
            "XGB Weight": xgb_w,
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], test_blend), 6),
        }
    )

global_blend_df = pd.DataFrame(global_results).sort_values("Val RMSLE").reset_index(drop=True)
best_global = global_blend_df.iloc[0]
best_global_lgb_w = float(best_global["LGB Weight"])
best_global_xgb_w = float(best_global["XGB Weight"])
best_global_val_blend = best_global_lgb_w * lgb_val_pred + best_global_xgb_w * xgb_val_pred
best_global_test_blend = best_global_lgb_w * lgb_test_pred + best_global_xgb_w * xgb_test_pred

print("Best global blend:")
print(best_global.to_string())
"""


def build_plot_cell(pred_expr: str, title_suffix: str, split_name: str, actual_expr: str, date_expr: str) -> str:
    return f"""
date_{split_name.lower()} = pd.to_datetime({date_expr})

blend_{split_name.lower()}_df = pd.DataFrame(
    {{
        "date": date_{split_name.lower()}.values,
        "actual": {actual_expr},
        "predicted": np.maximum(np.expm1({pred_expr}), 0),
    }}
)
blend_{split_name.lower()}_df["residual"] = blend_{split_name.lower()}_df["actual"] - blend_{split_name.lower()}_df["predicted"]

daily_{split_name.lower()} = blend_{split_name.lower()}_df[["date", "actual", "predicted"]].groupby("date").sum()

plt.figure(figsize=(14, 5))
plt.plot(daily_{split_name.lower()}.index, daily_{split_name.lower()}["actual"], label="Actual", color="#58a6ff")
plt.plot(daily_{split_name.lower()}.index, daily_{split_name.lower()}["predicted"], label="Predicted", color="#3fb950", linestyle="--")
plt.title("Total Sales - Actual vs Predicted - {title_suffix} ({split_name} Set)")
plt.legend()
plt.tight_layout()
plt.show()

daily_resid_{split_name.lower()} = blend_{split_name.lower()}_df.groupby("date")["residual"].mean()

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(daily_resid_{split_name.lower()}.index, daily_resid_{split_name.lower()}.values, color="#9467bd", linewidth=1.5)
ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.fill_between(
    daily_resid_{split_name.lower()}.index,
    daily_resid_{split_name.lower()}.values,
    0,
    where=daily_resid_{split_name.lower()}.values > 0,
    alpha=0.15,
    color="#d62728",
    label="Under-predict",
)
ax.fill_between(
    daily_resid_{split_name.lower()}.index,
    daily_resid_{split_name.lower()}.values,
    0,
    where=daily_resid_{split_name.lower()}.values < 0,
    alpha=0.15,
    color="#58a6ff",
    label="Over-predict",
)
ax.set_title("Mean daily residual - {title_suffix} ({split_name} Set)")
ax.set_xlabel("Date")
ax.set_ylabel("Residual")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"""


REGIME_METHOD = """
def build_regime_labels(df: pd.DataFrame) -> pd.Series:
    holiday_cols = [
        "is_national_holiday",
        "is_regional_holiday",
        "is_local_holiday",
        "is_transferred_holiday",
    ]
    is_holiday_like = df[holiday_cols].fillna(0).sum(axis=1).gt(0) | pd.to_numeric(df["holiday_type"], errors="coerce").fillna(0).gt(0)
    is_promo = pd.to_numeric(df["onpromotion"], errors="coerce").fillna(0).gt(0)
    is_weekend = pd.to_numeric(df["is_weekend"], errors="coerce").fillna(0).eq(1)

    labels = np.select(
        [
            is_promo & is_holiday_like,
            is_promo & ~is_holiday_like & is_weekend,
            is_promo & ~is_holiday_like & ~is_weekend,
            ~is_promo & is_holiday_like,
            ~is_promo & ~is_holiday_like & is_weekend,
        ],
        [
            "promo_holiday",
            "promo_weekend",
            "promo_regular",
            "holiday_only",
            "weekend_only",
        ],
        default="regular_day",
    )
    return pd.Series(labels, index=df.index)


val_regimes = build_regime_labels(X_val_raw)
test_regimes = build_regime_labels(X_test_raw)

regime_results = []
regime_weight_map = {}
min_rows = 1000

for regime_name in sorted(val_regimes.unique()):
    mask = val_regimes == regime_name
    if mask.sum() < min_rows:
        regime_weight_map[regime_name] = (best_global_lgb_w, best_global_xgb_w)
        regime_results.append(
            {
                "regime": regime_name,
                "val_rows": int(mask.sum()),
                "lgb_weight": best_global_lgb_w,
                "xgb_weight": best_global_xgb_w,
                "val_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], best_global_val_blend[mask]), 6),
                "strategy": "fallback_global",
            }
        )
        continue

    best_score = None
    best_weights = None
    for lgb_w in weight_grid:
        xgb_w = round(1 - lgb_w, 2)
        blend = lgb_w * lgb_val_pred[mask] + xgb_w * xgb_val_pred[mask]
        score = rmsle_from_log(y_val_orig.loc[mask, "sales"], blend)
        if best_score is None or score < best_score:
            best_score = score
            best_weights = (lgb_w, xgb_w)

    regime_weight_map[regime_name] = best_weights
    regime_results.append(
        {
            "regime": regime_name,
            "val_rows": int(mask.sum()),
            "lgb_weight": best_weights[0],
            "xgb_weight": best_weights[1],
            "val_rmsle": round(best_score, 6),
            "strategy": "regime_search",
        }
    )


def apply_regime_weights(regime_series: pd.Series, lgb_pred: np.ndarray, xgb_pred: np.ndarray) -> np.ndarray:
    output = np.zeros(len(regime_series), dtype=float)
    for regime_name, (lgb_w, xgb_w) in regime_weight_map.items():
        mask = regime_series == regime_name
        output[mask] = lgb_w * lgb_pred[mask] + xgb_w * xgb_pred[mask]
    return output


regime_val_blend = apply_regime_weights(val_regimes, lgb_val_pred, xgb_val_pred)
regime_test_blend = apply_regime_weights(test_regimes, lgb_test_pred, xgb_test_pred)

regime_weight_df = pd.DataFrame(regime_results).sort_values(["strategy", "val_rmsle", "regime"]).reset_index(drop=True)
print(regime_weight_df.to_string(index=False, float_format="{:.6f}".format))
"""


REGIME_COMPARISON = """
summary = pd.DataFrame(
    build_summary_rows()
    + [
        {
            "Approach": f"Global blend {best_global['Weights']}",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], best_global_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], best_global_test_blend), 6),
        },
        {
            "Approach": "Regime-based blend",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], regime_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], regime_test_blend), 6),
        },
    ]
)

print("\\nAll Approaches - Val vs Test RMSLE")
print("=" * 55)
print(summary.to_string(index=False, float_format="{:.6f}".format))
print("=" * 55)

best_row = summary.loc[summary["Val RMSLE"].idxmin()]
print(f"\\nBest approach by validation: {best_row['Approach']} (Val RMSLE={best_row['Val RMSLE']:.6f})")
"""


REGIME_DIAGNOSTIC = """
val_regime_metrics = []
for regime_name in sorted(val_regimes.unique()):
    mask = val_regimes == regime_name
    val_regime_metrics.append(
        {
            "regime": regime_name,
            "rows": int(mask.sum()),
            "lgb_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], lgb_val_pred[mask]), 6),
            "xgb_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], xgb_val_pred[mask]), 6),
            "regime_blend_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], regime_val_blend[mask]), 6),
        }
    )

val_regime_metrics_df = pd.DataFrame(val_regime_metrics).sort_values("regime_blend_rmsle", ascending=False)
print("Validation performance by regime")
print(val_regime_metrics_df.to_string(index=False, float_format="{:.6f}".format))
"""


STORE_METHOD = """
val_store_type = X_val_raw["type"].astype(str)
test_store_type = X_test_raw["type"].astype(str)

store_type_rows = []
store_type_weight_map = {}

for store_type in sorted(val_store_type.unique()):
    mask = val_store_type == store_type
    best_score = None
    best_weights = None
    for lgb_w in weight_grid:
        xgb_w = round(1 - lgb_w, 2)
        blend = lgb_w * lgb_val_pred[mask] + xgb_w * xgb_val_pred[mask]
        score = rmsle_from_log(y_val_orig.loc[mask, "sales"], blend)
        if best_score is None or score < best_score:
            best_score = score
            best_weights = (lgb_w, xgb_w)

    store_type_weight_map[store_type] = best_weights
    store_type_rows.append(
        {
            "store_type": store_type,
            "val_rows": int(mask.sum()),
            "lgb_weight": best_weights[0],
            "xgb_weight": best_weights[1],
            "val_rmsle": round(best_score, 6),
        }
    )


def apply_store_type_weights(store_type_series: pd.Series, lgb_pred: np.ndarray, xgb_pred: np.ndarray) -> np.ndarray:
    output = np.zeros(len(store_type_series), dtype=float)
    for store_type, (lgb_w, xgb_w) in store_type_weight_map.items():
        mask = store_type_series == store_type
        output[mask] = lgb_w * lgb_pred[mask] + xgb_w * xgb_pred[mask]
    return output


store_val_blend = apply_store_type_weights(val_store_type, lgb_val_pred, xgb_val_pred)
store_test_blend = apply_store_type_weights(test_store_type, lgb_test_pred, xgb_test_pred)

store_type_weight_df = pd.DataFrame(store_type_rows).sort_values("val_rmsle").reset_index(drop=True)
print(store_type_weight_df.to_string(index=False, float_format="{:.6f}".format))
"""


STORE_COMPARISON = """
summary = pd.DataFrame(
    build_summary_rows()
    + [
        {
            "Approach": f"Global blend {best_global['Weights']}",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], best_global_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], best_global_test_blend), 6),
        },
        {
            "Approach": "Store-type blend",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], store_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], store_test_blend), 6),
        },
    ]
)

print("\\nAll Approaches - Val vs Test RMSLE")
print("=" * 55)
print(summary.to_string(index=False, float_format="{:.6f}".format))
print("=" * 55)

best_row = summary.loc[summary["Val RMSLE"].idxmin()]
print(f"\\nBest approach by validation: {best_row['Approach']} (Val RMSLE={best_row['Val RMSLE']:.6f})")
"""


STORE_DIAGNOSTIC = """
store_type_metrics = []
for store_type in sorted(val_store_type.unique()):
    mask = val_store_type == store_type
    store_type_metrics.append(
        {
            "store_type": store_type,
            "rows": int(mask.sum()),
            "lgb_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], lgb_val_pred[mask]), 6),
            "xgb_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], xgb_val_pred[mask]), 6),
            "store_blend_rmsle": round(rmsle_from_log(y_val_orig.loc[mask, "sales"], store_val_blend[mask]), 6),
        }
    )

store_type_metrics_df = pd.DataFrame(store_type_metrics).sort_values("store_blend_rmsle", ascending=False)
print("Validation performance by store type")
print(store_type_metrics_df.to_string(index=False, float_format="{:.6f}".format))
"""


RESIDUAL_LOAD = """
import os
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_log_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler


def find_project_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "data" / "processed" / "splits").exists():
            return candidate
    if (cwd / "Topic_13_Retail_Store_Sales_Time_Series").exists():
        return cwd / "Topic_13_Retail_Store_Sales_Time_Series"
    raise FileNotFoundError("Could not locate project root from current working directory.")


BASE = find_project_root()
SPLIT_DIR = BASE / "data" / "processed" / "splits"

X_train = pd.read_csv(SPLIT_DIR / "train_features.csv")
y_train = pd.read_csv(SPLIT_DIR / "train_target.csv")
X_val = pd.read_csv(SPLIT_DIR / "val_features.csv")
y_val = pd.read_csv(SPLIT_DIR / "val_target.csv")
X_test = pd.read_csv(SPLIT_DIR / "test_features.csv")
y_test = pd.read_csv(SPLIT_DIR / "test_target.csv")
y_val_orig = pd.read_csv(SPLIT_DIR / "val_target_original.csv")

X_train_raw = X_train.copy()
X_val_raw = X_val.copy()
X_test_raw = X_test.copy()

y_test_orig = pd.DataFrame({"sales": np.expm1(y_test["sales_log"])})

xgb_best_model = joblib.load(BASE / "notebooks" / "08_forecasting" / "xgb_best_model.pkl")
lgb_best_model = joblib.load(BASE / "notebooks" / "08_forecasting" / "lgb_best_model.pkl")


def rmsle_from_log(y_true, pred_log):
    y_true = np.clip(np.asarray(y_true, dtype=float), 0, None)
    y_pred = np.clip(np.expm1(np.asarray(pred_log, dtype=float)), 0, None)
    return np.sqrt(mean_squared_log_error(y_true, y_pred))


def build_summary_rows():
    return [
        {
            "Approach": "LightGBM (tuned)",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], lgb_val_pred), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], lgb_test_pred), 6),
        },
        {
            "Approach": "XGBoost (tuned)",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], xgb_val_pred), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], xgb_test_pred), 6),
        },
    ]
"""


RESIDUAL_METHOD = """
def build_correction_features(df: pd.DataFrame, lgb_pred: np.ndarray, xgb_pred: np.ndarray, base_pred: np.ndarray) -> pd.DataFrame:
    feature_cols = [
        "onpromotion",
        "is_weekend",
        "is_month_start",
        "is_month_end",
        "is_payday",
        "is_national_holiday",
        "is_regional_holiday",
        "is_local_holiday",
        "is_transferred_holiday",
        "holiday_type",
        "days_to_next_holiday",
        "days_after_last_holiday",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_28",
        "rolling_std_7",
        "oil_price",
        "month",
        "day_of_week",
        "week_of_year",
        "store_family_te",
    ]
    out = df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).copy()
    out["lgb_pred_log"] = lgb_pred
    out["xgb_pred_log"] = xgb_pred
    out["base_blend_log"] = base_pred
    out["pred_gap_log"] = xgb_pred - lgb_pred
    out["pred_mean_log"] = (xgb_pred + lgb_pred) / 2.0
    return out


X_val_corr = build_correction_features(X_val_raw, lgb_val_pred, xgb_val_pred, best_global_val_blend)
X_test_corr = build_correction_features(X_test_raw, lgb_test_pred, xgb_test_pred, best_global_test_blend)

ridge_model = Pipeline(
    steps=[
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ]
)

val_residual_log = y_val["sales_log"].to_numpy() - best_global_val_blend
ridge_model.fit(X_val_corr, val_residual_log)

val_correction = ridge_model.predict(X_val_corr)
test_correction = ridge_model.predict(X_test_corr)

corrected_val_blend = best_global_val_blend + val_correction
corrected_test_blend = best_global_test_blend + test_correction

coef_df = pd.DataFrame(
    {
        "feature": X_val_corr.columns,
        "coefficient": ridge_model.named_steps["ridge"].coef_,
    }
).sort_values("coefficient", key=np.abs, ascending=False).reset_index(drop=True)

print("Top correction features")
print(coef_df.head(15).to_string(index=False, float_format="{:.6f}".format))
"""


RESIDUAL_COMPARISON = """
summary = pd.DataFrame(
    build_summary_rows()
    + [
        {
            "Approach": f"Global blend {best_global['Weights']}",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], best_global_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], best_global_test_blend), 6),
        },
        {
            "Approach": "Residual-corrected blend",
            "Val RMSLE": round(rmsle_from_log(y_val_orig["sales"], corrected_val_blend), 6),
            "Test RMSLE": round(rmsle_from_log(y_test_orig["sales"], corrected_test_blend), 6),
        },
    ]
)

print("\\nAll Approaches - Val vs Test RMSLE")
print("=" * 55)
print(summary.to_string(index=False, float_format="{:.6f}".format))
print("=" * 55)

best_row = summary.loc[summary["Val RMSLE"].idxmin()]
print(f"\\nBest approach by validation: {best_row['Approach']} (Val RMSLE={best_row['Val RMSLE']:.6f})")
"""


RESIDUAL_DIAGNOSTIC = """
correction_df = pd.DataFrame(
    {
        "date": pd.to_datetime(X_test_raw[["year", "month", "day"]]).values,
        "base_prediction": np.maximum(np.expm1(best_global_test_blend), 0),
        "corrected_prediction": np.maximum(np.expm1(corrected_test_blend), 0),
        "actual": y_test_orig["sales"].values,
    }
)
correction_df["correction_amount"] = correction_df["corrected_prediction"] - correction_df["base_prediction"]

daily_correction = correction_df.groupby("date")[["actual", "base_prediction", "corrected_prediction", "correction_amount"]].sum()

plt.figure(figsize=(14, 4))
plt.plot(daily_correction.index, daily_correction["correction_amount"], color="#ff7b72", linewidth=1.5)
plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
plt.title("Daily correction amount on test set")
plt.xlabel("Date")
plt.ylabel("Sales delta")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

print("Largest daily correction magnitudes")
print(
    daily_correction["correction_amount"]
    .abs()
    .sort_values(ascending=False)
    .head(10)
    .rename("abs_daily_correction")
    .to_string(float_format="{:.2f}".format)
)
"""


TOP_UNDER = """
top_under_dates = (
    blend_test_df.groupby("date")["residual"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .rename("mean_residual")
)
print("Top under-predicted dates")
print(top_under_dates.to_string(float_format="{:.2f}".format))
"""


TOP_OVER = """
top_over_dates = (
    blend_test_df.groupby("date")["residual"]
    .mean()
    .sort_values(ascending=True)
    .head(10)
    .rename("mean_residual")
)
print("Top over-predicted dates")
print(top_over_dates.to_string(float_format="{:.2f}".format))
"""


def build_notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": METADATA,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def regime_notebook() -> dict:
    cells = [
        md_cell("## 1. Load Dataset and Import libraries"),
        code_cell(COMMON_LOAD),
        code_cell(COMMON_ENCODE),
        md_cell("## 2. Predictions"),
        code_cell(COMMON_PRED),
        md_cell("## 3. Regime-based Weighted Ensemble"),
        code_cell(REGIME_METHOD),
        md_cell("## 4. Comparison Table: Single Models vs Ensemble"),
        code_cell(REGIME_COMPARISON),
        md_cell("## 5. Residual Plots"),
        code_cell(build_plot_cell("regime_val_blend", "Regime-based blend", "Val", 'y_val_orig["sales"].values', 'X_val_raw[["year", "month", "day"]]')),
        code_cell(build_plot_cell("regime_test_blend", "Regime-based blend", "Test", 'y_test_orig["sales"].values', 'X_test_raw[["year", "month", "day"]]')),
        code_cell(REGIME_DIAGNOSTIC),
        code_cell(TOP_UNDER),
        code_cell(TOP_OVER),
    ]
    return build_notebook(cells)


def store_type_notebook() -> dict:
    cells = [
        md_cell("## 1. Load Dataset and Import libraries"),
        code_cell(COMMON_LOAD),
        code_cell(COMMON_ENCODE),
        md_cell("## 2. Predictions"),
        code_cell(COMMON_PRED),
        md_cell("## 3. Store-type Weighted Ensemble"),
        code_cell(STORE_METHOD),
        md_cell("## 4. Comparison Table: Single Models vs Ensemble"),
        code_cell(STORE_COMPARISON),
        md_cell("## 5. Residual Plots"),
        code_cell(build_plot_cell("store_val_blend", "Store-type blend", "Val", 'y_val_orig["sales"].values', 'X_val_raw[["year", "month", "day"]]')),
        code_cell(build_plot_cell("store_test_blend", "Store-type blend", "Test", 'y_test_orig["sales"].values', 'X_test_raw[["year", "month", "day"]]')),
        code_cell(STORE_DIAGNOSTIC),
        code_cell(TOP_UNDER),
        code_cell(TOP_OVER),
    ]
    return build_notebook(cells)


def residual_notebook() -> dict:
    cells = [
        md_cell("## 1. Load Dataset and Import libraries"),
        code_cell(RESIDUAL_LOAD),
        code_cell(COMMON_ENCODE),
        md_cell("## 2. Predictions"),
        code_cell(COMMON_PRED),
        md_cell("## 3. Residual Correction Ensemble"),
        code_cell(RESIDUAL_METHOD),
        md_cell("## 4. Comparison Table: Single Models vs Ensemble"),
        code_cell(RESIDUAL_COMPARISON),
        md_cell("## 5. Residual Plots"),
        code_cell(build_plot_cell("corrected_val_blend", "Residual-corrected blend", "Val", 'y_val_orig["sales"].values', 'X_val_raw[["year", "month", "day"]]')),
        code_cell(build_plot_cell("corrected_test_blend", "Residual-corrected blend", "Test", 'y_test_orig["sales"].values', 'X_test_raw[["year", "month", "day"]]')),
        code_cell(RESIDUAL_DIAGNOSTIC),
        code_cell(TOP_UNDER),
        code_cell(TOP_OVER),
    ]
    return build_notebook(cells)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "notebooks" / "08_forecasting"
    output_dir.mkdir(parents=True, exist_ok=True)

    notebooks = {
        "Ensemble_regime_weighted.ipynb": regime_notebook(),
        "Ensemble_store_type_weighted.ipynb": store_type_notebook(),
        "Ensemble_residual_correction.ipynb": residual_notebook(),
    }

    for name, notebook in notebooks.items():
        output_path = output_dir / name
        output_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Created: {output_path}")


if __name__ == "__main__":
    main()
