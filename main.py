from datetime import datetime, date, timedelta
import pandas as pd
import pickle
import numpy as np
from time import time

with open("mod.pkl", "rb") as f:
    MOD = pickle.load(f)


def get_r_hat(A, B):
    start_time = time()
    weekday = str(A.index[-1].day_of_week)
    full_pred_df = pd.DataFrame()
    pred_idx = A.index[-1]
    for j in A:
        pred_df = pd.DataFrame({
            "asset": [str(j)],
            "weekday_" + str(weekday): [1],
            "log_vol_sum": [np.log(sum(B.loc[pred_idx - timedelta(minutes=MOD.minute_lag):pred_idx][j]))],
            "interval_high": [max(A.loc[pred_idx - timedelta(minutes=MOD.minute_lag):pred_idx][j])],
            "interval_low": [min(A.loc[pred_idx - timedelta(minutes=MOD.minute_lag):pred_idx][j])],
            "rsi": [sum([max(x, 0) for x in A.loc[pred_idx - timedelta(minutes=MOD.rsi_k):pred_idx][j]]) /
                    (sum([max(x, 0) for x in A.loc[pred_idx - timedelta(minutes=MOD.rsi_k):pred_idx][j]]) +
                    sum([max(-x, 0) for x in A.loc[pred_idx - timedelta(minutes=MOD.rsi_k):pred_idx][j]]))],
        })
        pred_df = pred_df.assign(**{"weekday_" + str(c): [0] for c in range(7) if c != weekday})

        pred_df["rel_price_range"] = 2 * (pred_df["interval_high"] - pred_df["interval_low"]) / (
            pred_df["interval_high"] + pred_df["interval_low"])
        pred_df["range_volatility"] = np.sqrt(
            np.square(np.log(np.exp(pred_df["interval_high"]) / np.exp(pred_df["interval_low"]))) / (4 * np.log(2))
        )

        for ell in range(1, MOD.minute_lag + 1):
            pred_df = pred_df.assign(**dict(
                A.shift(ell).rename(
                columns={k: "asset_" + str(k) + "_lag_" + str(ell) for k in A}).loc[pred_idx]
            ))
            pred_df["vw_price_lag_" + str(ell)] = (A[j].shift(ell) * B[j].shift(ell))[pred_idx]

        full_pred_df = pd.concat([full_pred_df, pred_df], axis=0)

    full_pred_df = pd.get_dummies(full_pred_df, columns=["asset"], prefix="asset").reset_index(drop=True)
    return MOD.predict(full_pred_df[MOD.regressor_cols])
