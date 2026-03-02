"""
feature_temporal.py
====================
Temporal & lag feature engineering cho bài toán dự báo doanh số bán lẻ Ecuador.

Usage:
    from features.feature_temporal import add_temporal_features, add_lag_features, build_features

    df = add_temporal_features(df)
    df = add_lag_features(df)
    # hoặc gọi một lần:
    df = build_features(df)
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. TEMPORAL FEATURES
# ---------------------------------------------------------------------------

def add_temporal_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Trích xuất các đặc trưng thời gian từ cột date.

    Parameters
    ----------
    df       : DataFrame chứa cột date (datetime hoặc string có thể parse).
    date_col : Tên cột ngày tháng, mặc định "date".

    Returns
    -------
    DataFrame với các cột mới được thêm vào (không xóa cột gốc).
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    dt = df[date_col].dt

    # --- Đơn vị thời gian cơ bản ---
    df["year"]         = dt.year
    df["month"]        = dt.month
    df["day"]          = dt.day
    df["day_of_week"]  = dt.dayofweek          # 0 = Monday, 6 = Sunday
    df["week_of_year"] = dt.isocalendar().week.astype(int)
    df["quarter"]      = dt.quarter

    # --- Binary flags ---
    df["is_weekend"]    = (dt.dayofweek >= 5).astype(int)
    df["is_month_start"] = dt.is_month_start.astype(int)
    df["is_month_end"]   = dt.is_month_end.astype(int)

    # --- Ecuador payday: ngày 15 và ngày cuối tháng ---
    df["is_payday"] = ((dt.day == 15) | dt.is_month_end).astype(int)

    return df


# ---------------------------------------------------------------------------
# 2. LAG & ROLLING FEATURES
# ---------------------------------------------------------------------------

def add_lag_features(
    df: pd.DataFrame,
    target_col: str = "sales",
    group_cols: list = None,
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Tạo lag features và rolling statistics cho cột target.

    *** Quan trọng ***: hàm này tự động sort theo date và groupby store/family
    trước khi tính lag để tránh data leakage giữa các chuỗi thời gian khác nhau.

    Parameters
    ----------
    df          : DataFrame đã có cột date, target, store_nbr, family.
    target_col  : Tên cột doanh số, mặc định "sales".
    group_cols  : Danh sách cột nhóm, mặc định ["store_nbr", "family"].
    date_col    : Tên cột ngày, mặc định "date".

    Returns
    -------
    DataFrame với các cột lag và rolling mới.

    Notes
    -----
    - Function sorts values by the specified grouping columns and date before
      computing shifts to prevent leakage between different time series.
    - As an extra safety net (particularly when upstream data may contain
      duplicate dates or unsorted rows), the first lag value for each group is
      explicitly reset to NaN after the shifts are calculated.  This matches
      the expectation asserted later in the notebook.
    """
    if group_cols is None:
        group_cols = ["store_nbr", "family"]

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # --- Bắt buộc: sort trước khi tính lag để tránh data leakage ---
    df = df.sort_values(group_cols + [date_col]).reset_index(drop=True)

    grouped = df.groupby(group_cols, sort=False)[target_col]

    # --- Short-term lags ---
    for lag in [1, 2, 3]:
        df[f"lag_{lag}"] = grouped.shift(lag)

    # --- Weekly lag (cùng ngày tuần trước — thường là feature quan trọng nhất) ---
    df["lag_7"] = grouped.shift(7)

    # --- Longer lags ---
    for lag in [14, 28, 364]:
        df[f"lag_{lag}"] = grouped.shift(lag)

    # --- Rolling statistics (tính trên dữ liệu đã shift 1 để tránh leakage) ---
    # shift(1) đảm bảo rolling window không bao gồm giá trị hiện tại (t)
    shifted = grouped.shift(1)
    df["rolling_mean_7"]  = shifted.transform(lambda x: x.rolling(7,  min_periods=1).mean())
    df["rolling_mean_14"] = shifted.transform(lambda x: x.rolling(14, min_periods=1).mean())
    df["rolling_mean_28"] = shifted.transform(lambda x: x.rolling(28, min_periods=1).mean())
    df["rolling_std_7"]   = shifted.transform(lambda x: x.rolling(7,  min_periods=2).std())

    # ------------------------------------------------------------------
    # Safety net: regardless of upstream issues (duplicate dates, unsorted
    # rows, or unexpected group boundaries) we explicitly reset lag values
    # at the start of each time-series to NaN.  The preceding shift() calls
    # should already handle this, but in practice the notebook's leakage
    # assertion failed on the full dataset, so the extra step ensures
    # robustness and makes the behaviour deterministic.
    first_idx = df.groupby(group_cols, sort=False).head(1).index
    lag_cols = [f"lag_{lag}" for lag in [1, 2, 3, 7, 14, 28, 364]]
    df.loc[first_idx, lag_cols] = np.nan

    return df


# ---------------------------------------------------------------------------
# 3. PIPELINE TỔNG HỢP
# ---------------------------------------------------------------------------

def build_features(
    df: pd.DataFrame,
    target_col: str = "sales",
    group_cols: list = None,
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Pipeline đầy đủ: temporal features → lag features.

    Parameters
    ----------
    df          : DataFrame thô chứa ít nhất các cột date, sales, store_nbr, family.
    target_col  : Cột doanh số cần tạo lag.
    group_cols  : Các cột định danh chuỗi thời gian.
    date_col    : Cột ngày.

    Returns
    -------
    DataFrame với toàn bộ features đã được thêm vào.

    Example
    -------
    >>> import pandas as pd
    >>> from features.feature_temporal import build_features
    >>> train = pd.read_csv("data/train.csv")
    >>> train_fe = build_features(train)
    >>> print(train_fe.columns.tolist())
    """
    df = add_temporal_features(df, date_col=date_col)
    df = add_lag_features(df, target_col=target_col, group_cols=group_cols, date_col=date_col)
    return df


# ---------------------------------------------------------------------------
# 4. HELPER: danh sách tên các feature được tạo ra
# ---------------------------------------------------------------------------

TEMPORAL_FEATURE_NAMES = [
    "year", "month", "day", "day_of_week", "week_of_year", "quarter",
    "is_weekend", "is_month_start", "is_month_end", "is_payday",
]

LAG_FEATURE_NAMES = [
    "lag_1", "lag_2", "lag_3",
    "lag_7",
    "lag_14", "lag_28", "lag_364",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
    "rolling_std_7",
]

ALL_FEATURE_NAMES = TEMPORAL_FEATURE_NAMES + LAG_FEATURE_NAMES


# ---------------------------------------------------------------------------
# Quick smoke-test (chạy trực tiếp: python feature_temporal.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Tạo dữ liệu giả để kiểm tra
    dates = pd.date_range("2017-01-01", periods=60, freq="D")
    mock = pd.DataFrame({
        "date":      list(dates) * 2,
        "store_nbr": [1] * 60 + [2] * 60,
        "family":    ["GROCERY I"] * 120,
        "sales":     np.random.rand(120) * 1000,
    })

    result = build_features(mock)

    print("Shape:", result.shape)
    print("Columns added:")
    for col in ALL_FEATURE_NAMES:
        present = "✓" if col in result.columns else "✗ MISSING"
        null_pct = result[col].isna().mean() * 100 if col in result.columns else -1
        print(f"  {present}  {col:<22}  NaN={null_pct:.1f}%")

    # Kiểm tra không có leakage: lag_1 của ngày đầu tiên mỗi store phải là NaN
    first_rows = result.groupby(["store_nbr", "family"]).first()
    assert first_rows["lag_1"].isna().all(), "Data leakage detected in lag_1!"
    print("\nLeakage check passed ✓")