# models/trade_signal.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class TradeSignal:
    symbol: str
    timestamp: datetime
    signal_type: str
    direction: str
    confidence: float
    indicators: Dict
    price: float
    metadata: Dict