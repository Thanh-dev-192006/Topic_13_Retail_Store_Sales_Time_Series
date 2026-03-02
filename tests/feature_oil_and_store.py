import pandas as pd
from sklearn.preprocessing import LabelEncoder


# ======================
# OIL FEATURES
# ======================

def create_oil_features(oil_df):
    oil = oil_df.copy()
    oil["date"] = pd.to_datetime(oil["date"])
    oil = oil.sort_values("date").rename(columns={"dcoilwtico": "oil_price"})

    # Safe missing handling (no future info)
    oil["oil_price"] = oil["oil_price"].ffill()

    # Lag features (historical only)
    oil["oil_price_lag_7"] = oil["oil_price"].shift(7)
    oil["oil_price_lag_14"] = oil["oil_price"].shift(14)

    # Rolling trend (shift first to avoid leakage)
    oil["oil_price_rolling_mean_28"] = (
        oil["oil_price"].shift(1).rolling(28, min_periods=7).mean()
    )

    # Weekly shock
    oil["oil_price_change_pct"] = (
        oil["oil_price"] / oil["oil_price_lag_7"] - 1
    )


# ======================
# STORES FEATURES
# ======================

    def encode_store_features(train, test):

    train, test = train.copy(), test.copy()

    # 1. Label encode store_type (fit on train only)
    le = LabelEncoder()
    train["store_type_enc"] = le.fit_transform(train["store_type"])
    test["store_type_enc"] = le.transform(test["store_type"])

    # 2. Frequency encode city/state
    for col in ["city", "state"]:
        freq = train[col].value_counts(normalize=True)
        train[f"{col}_freq"] = train[col].map(freq)
        test[f"{col}_freq"] = test[col].map(freq).fillna(0)

    # 3. cluster keep the same

    return train, test

    return oil
