# utils/indicators.py
import pandas as pd
import numpy as np
from typing import Dict

def calculate_rsi(data: pd.Series, periods: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data: pd.Series) -> Dict[str, pd.Series]:
    exp1 = data.ewm(span=12, adjust=False).mean()
    exp2 = data.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return {'macd': macd, 'signal': signal}

def calculate_bollinger_bands(data: pd.Series, window: int = 20) -> Dict[str, pd.Series]:
    sma = data.rolling(window=window).mean()
    std = data.rolling(window=window).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    return {
        'middle': sma,
        'upper': upper_band,
        'lower': lower_band
    }