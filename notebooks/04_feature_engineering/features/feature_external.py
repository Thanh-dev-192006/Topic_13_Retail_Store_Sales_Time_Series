import pandas as pd
import numpy as np

# PHẦN 1: OIL PRICE FEATURES
def add_oil_features(
    df: pd.DataFrame,
    oil_df: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:
   
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # Bước 1: Chuẩn bị oil_df — tạo một bảng giá dầu hoàn chỉnh theo ngày
    oil = oil_df.copy()
    oil = oil.rename(columns={"dcoilwtico": "oil_price"})
    oil["date"] = pd.to_datetime(oil["date"])
    oil = oil[["date", "oil_price"]].sort_values("date").reset_index(drop=True)

    # Tạo dải ngày liên tục từ ngày đầu đến ngày cuối trong dữ liệu dầu
    # (để không bỏ sót ngày cuối tuần/ngày lễ khi tính rolling/lag)
    full_date_range = pd.DataFrame({
        "date": pd.date_range(start=oil["date"].min(), end=oil["date"].max(), freq="D")
    })
    oil = full_date_range.merge(oil, on="date", how="left")

    # Bước 2: Xử lý Missing Values bằng Forward Fill (ffill)
    # Lý do dùng ffill: cuối tuần/ngày lễ không có giá dầu mới,
    # nhưng giá dầu ngày hôm qua vẫn là thông tin tốt nhất ta có.
    oil["oil_price"] = oil["oil_price"].ffill()

    # Backward fill cho trường hợp thiếu ở đầu chuỗi (hiếm)
    oil["oil_price"] = oil["oil_price"].bfill()

    # Bước 3: Tạo Lag Features
    # Tại sao cần lag?
    # → Tác động kinh tế của giá dầu không xảy ra ngay lập tức.
    #   Khi giá dầu tăng, người dân & chính phủ mất vài tuần mới điều chỉnh
    #   hành vi chi tiêu. EDA cho thấy lag 14 ngày có correlation tốt nhất.

    oil["oil_price_lag_7"]  = oil["oil_price"].shift(7)   # 1 tuần trước
    oil["oil_price_lag_14"] = oil["oil_price"].shift(14)  # 2 tuần trước (best lag)

    # Bước 4: Rolling Mean 28 ngày
    # Tại sao cần rolling mean?
    # → Giá dầu dao động hàng ngày, rolling mean 28 ngày "làm mịn" 
    #   nhiễu ngắn hạn và nắm bắt xu hướng dài hơn (bull/bear market).
    # min_periods=1: tính trung bình dù chưa đủ 28 ngày (tránh NaN đầu chuỗi)

    oil["oil_price_rolling_mean_28"] = (
        oil["oil_price"].rolling(window=28, min_periods=1).mean()
    )

    # Bước 5: Percentage Change (% thay đổi so với tuần trước)
    # Tại sao cần oil_price_change_pct?
    # → Capture được "shock bất ngờ": giá dầu tăng 10% trong 1 tuần 
    #   có tác động tâm lý khác hẳn mức tăng nhỏ từng ngày.
    # pct_change(7): so sánh với cùng ngày tuần trước

    oil["oil_price_change_pct"] = oil["oil_price"].pct_change(periods=7)

    # Bước 6: Merge vào DataFrame chính
    oil_cols = [
        "date",
        "oil_price",
        "oil_price_lag_7",
        "oil_price_lag_14",
        "oil_price_rolling_mean_28",
        "oil_price_change_pct",
    ]
    df = df.merge(oil[oil_cols], on="date", how="left")

    return df


# PHẦN 2: STORE & PRODUCT ENCODING

def add_store_encoding(
    df: pd.DataFrame,
    stores_df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()
    stores = stores_df.copy()

    # Bước 1: Label Encoding cho store_type (A, B, C, D, E → 0, 1, 2, 3, 4)
    # store_type chỉ có 5 loại duy nhất → Label Encoding đơn giản là đủ.
    # Chuyển A→0, B→1, ... theo thứ tự alphabet (nhất quán, không ngẫu nhiên).
    type_mapping = {t: i for i, t in enumerate(sorted(stores["type"].unique()))}
    stores["store_type_encoded"] = stores["type"].map(type_mapping)

    # Bước 2: Frequency Encoding cho city và state
    # Frequency encoding: thay tên thành phố/tỉnh bằng xác suất xuất hiện
    # Các thành phố lớn có nhiều cửa hàng → giá trị freq cao hơn
    # → model hiểu được quy mô địa lý một cách ngầm định

    city_freq  = stores["city"].value_counts(normalize=True).to_dict()
    state_freq = stores["state"].value_counts(normalize=True).to_dict()

    stores["city_freq"]  = stores["city"].map(city_freq)
    stores["state_freq"] = stores["state"].map(state_freq)

    # Bước 3: Giữ cluster nguyên (đã là số)
    # cluster là số từ 1-17, LightGBM xử lý trực tiếp được.
    # Không cần encode thêm.

    # Bước 4: Merge vào DataFrame chính theo store_nbr
    store_cols = [
        "store_nbr",
        "cluster",            # giữ nguyên
        "store_type_encoded", # A-E → 0-4
        "city_freq",          # frequency của thành phố
        "state_freq",         # frequency của tỉnh/bang
    ]
    df = df.merge(stores[store_cols], on="store_nbr", how="left")

    return df


# PHẦN 3: PIPELINE TỔNG HỢP

def build_external_features(
    df: pd.DataFrame,
    oil_df: pd.DataFrame,
    stores_df: pd.DataFrame,
    date_col: str = "date",
) -> pd.DataFrame:

    df = add_oil_features(df, oil_df, date_col=date_col)
    df = add_store_encoding(df, stores_df)
    return df


# PHẦN 4: DANH SÁCH TÊN FEATURES (để dùng ở bước model sau)

OIL_FEATURE_NAMES = [
    "oil_price",
    "oil_price_lag_7",
    "oil_price_lag_14",
    "oil_price_rolling_mean_28",
    "oil_price_change_pct",
]

STORE_FEATURE_NAMES = [
    "cluster",
    "store_type_encoded",
    "city_freq",
    "state_freq",
]

ALL_EXTERNAL_FEATURE_NAMES = OIL_FEATURE_NAMES + STORE_FEATURE_NAMES


# QUICK SMOKE-TEST

if __name__ == "__main__":
    print("=" * 60)
    print("SMOKE TEST: feature_external.py")
    print("=" * 60)

    # --- Tạo data giả để test ---
    np.random.seed(42)
    dates = pd.date_range("2016-01-01", periods=90, freq="D")

    # DataFrame chính (train giả)
    mock_train = pd.DataFrame({
        "date":      list(dates) * 3,
        "store_nbr": [1] * 90 + [2] * 90 + [3] * 90,
        "family":    ["GROCERY I"] * 270,
        "sales":     np.random.rand(270) * 1000,
    })

    # Oil DataFrame giả (thêm vài NaN để test ffill)
    mock_oil = pd.DataFrame({
        "date":        pd.date_range("2015-12-01", periods=120, freq="D"),
        "dcoilwtico":  np.where(
            np.random.rand(120) < 0.15,  # 15% ngày thiếu giá (cuối tuần/lễ)
            np.nan,
            50 + np.random.randn(120) * 5  # giá dầu ~50 USD
        ),
    })

    # Stores DataFrame giả
    mock_stores = pd.DataFrame({
        "store_nbr": [1, 2, 3],
        "type":      ["A", "B", "A"],
        "cluster":   [1, 3, 1],
        "city":      ["Quito", "Guayaquil", "Quito"],
        "state":     ["Pichincha", "Guayas", "Pichincha"],
    })

    # --- Chạy pipeline ---
    result = build_external_features(mock_train, mock_oil, mock_stores)

    print(f"\nShape đầu vào:  {mock_train.shape}")
    print(f"Shape đầu ra:   {result.shape}")

    print("\n--- Kiểm tra từng feature ---")
    all_ok = True
    for col in ALL_EXTERNAL_FEATURE_NAMES:
        if col in result.columns:
            null_pct = result[col].isna().mean() * 100
            sample_val = result[col].dropna().iloc[0] if not result[col].dropna().empty else "N/A"
            print(f"  ✓  {col:<35}  NaN={null_pct:5.1f}%  sample={sample_val:.4f}" if isinstance(sample_val, float) else f"  ✓  {col:<35}  NaN={null_pct:5.1f}%  sample={sample_val}")
        else:
            print(f"  ✗  {col:<35}  MISSING!")
            all_ok = False

    # --- Kiểm tra oil_price không còn NaN sau ffill ---
    oil_nan = result["oil_price"].isna().sum()
    print(f"\nSau ffill, oil_price NaN còn lại: {oil_nan} (phải = 0 hoặc rất nhỏ)")

    # --- Kiểm tra store_type_encoded ---
    unique_types = result["store_type_encoded"].unique()
    print(f"store_type_encoded unique values: {sorted(unique_types)}")

    # --- Kiểm tra city_freq trong khoảng [0, 1] ---
    assert result["city_freq"].dropna().between(0, 1).all(), "city_freq ngoài khoảng [0,1]!"
    print("city_freq trong khoảng [0, 1]: ✓")

    # --- Kiểm tra lag_14 có giá trị sau 14 ngày đầu ---
    lag14_after_warmup = result[result["date"] >= dates[14]]["oil_price_lag_14"]
    nan_after = lag14_after_warmup.isna().sum()
    print(f"oil_price_lag_14 NaN sau warmup 14 ngày: {nan_after} (nên thấp)")

    print("\n" + ("✅ TẤT CẢ TESTS PASSED!" if all_ok else "❌ CÓ LỖI, kiểm tra lại!"))
    print("\n--- Xem trước 3 dòng đầu ---")
    print(result[["date", "store_nbr"] + ALL_EXTERNAL_FEATURE_NAMES].head(3).to_string())