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
        """Initialize the exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.config['exchange']['name'])
            exchange = exchange_class({
                'apiKey': self.config['exchange'].get('api_key'),
                'secret': self.config['exchange'].get('api_secret'),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                    'testnet': self.config['exchange'].get('testnet', True)
                }
            })
            return exchange
        except Exception as e:
            self.logger.error(f"Error initializing exchange: {str(e)}")
            raise

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1m') -> List:
        """Fetch OHLCV data"""
        try:
            # Convert to async operation
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe
            )
            return ohlcv
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {str(e)}")
            return []

    async def fetch_order_book(self, symbol: str) -> Dict:
        """Fetch order book data"""
        try:
            order_book = await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.fetch_order_book,
                symbol
            )
            return order_book
        except Exception as e:
            self.logger.error(f"Error fetching order book: {str(e)}")
            return {'bids': [], 'asks': []}

    async def fetch_recent_trades(self, symbol: str) -> List:
        """Fetch recent trades"""
        try:
            trades = await asyncio.get_event_loop().run_in_executor(
                None,
                self.exchange.fetch_trades,
                symbol
            )
            return trades
        except Exception as e:
            self.logger.error(f"Error fetching recent trades: {str(e)}")
            return []

    def get_current_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(datetime.now().timestamp() * 1000)