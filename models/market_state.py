# models/market_state.py
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class MarketState:
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    trend: Dict
    volatility: float
    indicators: Dict
    support_levels: List[float]
    resistance_levels: List[float]