# -*- coding: utf-8 -*-
"""ADX（Average Directional Index，平均動向指標）共用計算，用威爾德平滑法"""
import numpy as np
import pandas as pd
from atr_utils import compute_atr


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low = df["High"], df["Low"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move[(up_move > down_move) & (up_move > 0)]
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move[(down_move > up_move) & (down_move > 0)]

    atr_smoothed = compute_atr(df, period).replace(0, np.nan)

    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_smoothed)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr_smoothed)

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx.fillna(0)
