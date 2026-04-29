import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "notebooks" / "07_evaluation"


def lines(text: str) -> list[str]:
    return [f"{line}\n" for line in text.strip("\n").splitlines()]


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": lines(text),
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines(text),
    }


COMMON_IMPORTS = """
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_log_error
from sklearn.preprocessing import LabelEncoder
"""


COMMON_DATA_LOAD = """
def find_project_root(start: Path | None = None) -> Path:
    start = Path.cwd().resolve() if start is None else Path(start).resolve()
    candidates = [start, *start.parents]

    for candidate in candidates:
        if (candidate / "data" / "processed" / "splits").exists():
            return candidate
        nested = candidate / "Topic_13_Retail_Store_Sales_Time_Series"
        if (nested / "data" / "processed" / "splits").exists():
            return nested

    raise FileNotFoundError("Could not locate project root containing data/processed/splits")


BASE = find_project_root()
SPLIT_DIR = BASE / "data" / "processed" / "splits"

X_train = pd.read_csv(SPLIT_DIR / "train_features.csv")
y_train = pd.read_csv(SPLIT_DIR / "train_target.csv")
X_val = pd.read_csv(SPLIT_DIR / "val_features.csv")
y_val = pd.read_csv(SPLIT_DIR / "val_target.csv")
y_val_orig = pd.read_csv(SPLIT_DIR / "val_target_original.csv")

print(f"BASE: {BASE}")
print(f"X_train {X_train.shape} | X_val {X_val.shape}")
"""


COMMON_ENCODING = """
object_cols = X_train.select_dtypes(include=["object"]).columns.tolist()
label_encoders = {}

for col in object_cols:
    encoder = LabelEncoder()
    combined = pd.concat([X_train[col], X_val[col]], ignore_index=True).astype(str)
    encoder.fit(combined)

    X_train[col] = encoder.transform(X_train[col].astype(str)).astype(np.int32)
    X_val[col] = encoder.transform(X_val[col].astype(str)).astype(np.int32)
    label_encoders[col] = encoder

remaining_object_cols = X_train.select_dtypes(include=["object"]).columns.tolist()
if remaining_object_cols:
    raise ValueError(f"Still has object columns: {remaining_object_cols}")

print(f"Label encoded {len(object_cols)} columns")
"""


COMMON_HELPERS = """
def rmsle_from_log_arrays(y_true_log, y_pred_log) -> float:
    y_true = np.clip(np.expm1(np.asarray(y_true_log)), 0, None)
    y_pred = np.clip(np.expm1(np.asarray(y_pred_log)), 0, None)
    return float(np.sqrt(mean_squared_log_error(y_true, y_pred)))


def final_val_summary(model_name: str, val_pred_log) -> pd.DataFrame:
    summary = pd.DataFrame(
        {
            "model": [model_name],
            "val_rmsle": [rmsle_from_log_arrays(y_val["sales_log"], val_pred_log)],
            "best_round": [int(history.loc[history["val_rmsle"].idxmin(), "round"])],
            "best_val_rmsle": [float(history["val_rmsle"].min())],
        }
    )
    return summary


def plot_history(model_name: str) -> None:
    plt.figure(figsize=(12, 5))
    plt.plot(history["round"], history["train_rmsle"], label="Train RMSLE", linewidth=2)
    plt.plot(history["round"], history["val_rmsle"], label="Validation RMSLE", linewidth=2)
    best_idx = history["val_rmsle"].idxmin()
    plt.scatter(
        history.loc[best_idx, "round"],
        history.loc[best_idx, "val_rmsle"],
        color="crimson",
        s=60,
        label=f"Best val round = {int(history.loc[best_idx, 'round'])}",
        zorder=3,
    )
    plt.title(f"{model_name} RMSLE by Boosting Round")
    plt.xlabel("Boosting round")
    plt.ylabel("RMSLE")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.show()
"""


def build_lightgbm_notebook() -> dict:
    best_params = """
import lightgbm as lgb


def lgb_rmsle_metric(y_true_log, y_pred_log):
    return "rmsle", rmsle_from_log_arrays(y_true_log, y_pred_log), False


best_params = {
    "n_estimators": 1000,
    "learning_rate": 0.03452197544347247,
    "num_leaves": 209,
    "min_child_samples": 199,
    "subsample": 0.9044243675990947,
    "colsample_bytree": 0.6878203016641873,
    "reg_alpha": 0.0010446251525877439,
    "reg_lambda": 0.0037601083080145018,
    "objective": "regression",
    "random_state": 42,
    "n_jobs": -1,
    "verbose": -1,
}

model = lgb.LGBMRegressor(**best_params)
model.fit(
    X_train,
    y_train["sales_log"],
    eval_set=[(X_train, y_train["sales_log"]), (X_val, y_val["sales_log"])],
    eval_names=["train", "val"],
    eval_metric=lgb_rmsle_metric,
    callbacks=[lgb.log_evaluation(period=100)],
)
"""

    extract_history = """
results = model.evals_result_

history = pd.DataFrame(
    {
        "round": np.arange(1, len(results["train"]["rmsle"]) + 1),
        "train_rmsle": results["train"]["rmsle"],
        "val_rmsle": results["val"]["rmsle"],
    }
)

history.head()
"""

    summary_cell = """
plot_history("LightGBM")

val_pred_log = model.predict(X_val)
summary = final_val_summary("LightGBM", val_pred_log)
summary
"""

    return notebook(
        title="LightGBM Training With RMSLE Logging",
        description=(
            "Notebook tối giản để train LightGBM bằng bộ tham số tối ưu từ "
            "`notebooks/07_evaluation/LightGBM_training_v2_out.ipynb`, log eval set và plot RMSLE theo từng boosting round."
        ),
        extra_cells=[best_params, extract_history, summary_cell],
    )


def build_xgboost_notebook() -> dict:
    best_params = """
import xgboost as xgb


def rmsle_xgb(y_true_log, y_pred_log):
    return rmsle_from_log_arrays(y_true_log, y_pred_log)


best_params = {
    "n_estimators": 1000,
    "learning_rate": 0.05661765609380996,
    "max_depth": 10,
    "min_child_weight": 62,
    "subsample": 0.891754215404674,
    "colsample_bytree": 0.7928782229160452,
    "reg_alpha": 0.06528187294151135,
    "reg_lambda": 0.05430278926785755,
    "objective": "reg:squarederror",
    "tree_method": "hist",
    "random_state": 42,
    "n_jobs": -1,
    "eval_metric": rmsle_xgb,
}

model = xgb.XGBRegressor(**best_params)
model.fit(
    X_train,
    y_train["sales_log"],
    eval_set=[(X_train, y_train["sales_log"]), (X_val, y_val["sales_log"])],
    verbose=100,
)
"""

    extract_history = """
results = model.evals_result()
metric_name = next(
    key for key in results["validation_0"].keys() if "rmsle" in key.lower()
)

history = pd.DataFrame(
    {
        "round": np.arange(1, len(results["validation_0"][metric_name]) + 1),
        "train_rmsle": results["validation_0"][metric_name],
        "val_rmsle": results["validation_1"][metric_name],
    }
)

history.head()
"""

    summary_cell = """
plot_history("XGBoost")

val_pred_log = model.predict(X_val)
summary = final_val_summary("XGBoost", val_pred_log)
summary
"""

    return notebook(
        title="XGBoost Training With RMSLE Logging",
        description=(
            "Notebook tối giản để train XGBoost bằng bộ tham số tối ưu từ "
            "`notebooks/07_evaluation/XGBoost_training_out.ipynb`, log eval set và plot RMSLE theo từng boosting round."
        ),
        extra_cells=[best_params, extract_history, summary_cell],
    )


def notebook(title: str, description: str, extra_cells: list[str]) -> dict:
    cells = [
        markdown_cell(f"# {title}\n\n{description}"),
        code_cell(COMMON_IMPORTS),
        code_cell(COMMON_DATA_LOAD),
        code_cell(COMMON_ENCODING),
        code_cell(COMMON_HELPERS),
    ]
    cells.extend(code_cell(cell) for cell in extra_cells)

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(path: Path, content: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    write_notebook(
        OUTPUT_DIR / "LightGBM_rmsle_boosting_rounds.ipynb",
        build_lightgbm_notebook(),
    )
    write_notebook(
        OUTPUT_DIR / "XGBoost_rmsle_boosting_rounds.ipynb",
        build_xgboost_notebook(),
    )
    print("Created notebooks:")
    print(f"- {OUTPUT_DIR / 'LightGBM_rmsle_boosting_rounds.ipynb'}")
    print(f"- {OUTPUT_DIR / 'XGBoost_rmsle_boosting_rounds.ipynb'}")


if __name__ == "__main__":
    main()
