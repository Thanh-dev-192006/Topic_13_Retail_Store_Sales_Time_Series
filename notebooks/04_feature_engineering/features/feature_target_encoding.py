import numpy as np
from sklearn.model_selection import KFold
from category_encoders import TargetEncoder


def add_target_encoding(train, test, target="sales", n_splits=5):

    train, test = train.copy(), test.copy()

    # Combine key
    train["store_family"] = (
        train["store_nbr"].astype(str) + "_" + train["family"]
    )
    test["store_family"] = (
        test["store_nbr"].astype(str) + "_" + test["family"]
    )

    kf = KFold(n_splits=n_splits, shuffle=False)
    oof = np.zeros(len(train))

    # ---- Out-of-fold encoding (leakage safe) ----
    for tr_idx, val_idx in kf.split(train):

        enc = TargetEncoder(cols=["store_family"], smoothing=10)

        # Fit ONLY on training fold
        enc.fit(
            train.iloc[tr_idx][["store_family"]],
            train.iloc[tr_idx][target]
        )

        # Transform validation fold (never sees its own target)
        oof[val_idx] = enc.transform(
            train.iloc[val_idx][["store_family"]]
        )["store_family"]

    train["store_family_te"] = oof

    # ---- Fit on full train for test ----
    final_enc = TargetEncoder(cols=["store_family"], smoothing=10)
    final_enc.fit(train[["store_family"]], train[target])

    # Test uses only train statistics
    test["store_family_te"] = final_enc.transform(
        test[["store_family"]]
    )["store_family"]

    return train, test
