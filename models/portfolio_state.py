# models/portfolio_state.py
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class Position:
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    side: str
    unrealized_pnl: float
    entry_time: datetime

@dataclass
class PortfolioState:
    total_equity: float
    available_balance: float
    positions: Dict[str, Position]
    daily_pnl: float
    total_pnl: float
    risk_metrics: Dict