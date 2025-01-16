# services/exchange_service.py
import ccxt
import logging
from typing import Dict, List
import asyncio
from datetime import datetime

class ExchangeService:
    def __init__(self, config: Dict):
        self.config = config
        self.exchange = self._initialize_exchange()
        self.logger = logging.getLogger(__name__)

    def _initialize_exchange(self) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, self.config['exchange']['name'])
        exchange = exchange_class({
            'apiKey': self.config['exchange']['api_key'],
            'secret': self.config['exchange']['api_secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True,
                'testnet': self.config['exchange']['testnet']
            }
        })
        return exchange

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m') -> List[Dict]:
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe)
            return ohlcv
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {str(e)}")
            return []