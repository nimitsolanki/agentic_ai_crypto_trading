# agents/data_collector_agent.py
import asyncio
import logging
from typing import Dict, Optional
from services.exchange_service import ExchangeService
from services.message_broker import MessageBroker
from datetime import datetime

class DataCollectorAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.exchange = ExchangeService(config)
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        self.collection_interval = config['data_collection'].get('update_interval', 60)
        self.running = True

    async def collect_market_data(self, symbol: str) -> Optional[Dict]:
        """Collect market data for a symbol"""
        try:
            # Collect OHLCV data for different timeframes
            ohlcv_data = {}
            for timeframe in self.config['data_collection'].get('timeframes', ['1m']):
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe)
                if ohlcv:
                    ohlcv_data[timeframe] = ohlcv

            # Collect order book data
            order_book = await self.exchange.fetch_order_book(symbol)

            # Collect recent trades
            recent_trades = await self.exchange.fetch_recent_trades(symbol)

            # Combine all data
            market_data = {
                'symbol': symbol,
                'timestamp': self.exchange.get_current_timestamp(),
                'ohlcv': ohlcv_data,
                'order_book': order_book,
                'recent_trades': recent_trades
            }

            # Publish data to message broker
            await self.message_broker.publish(
                'market_data',
                market_data
            )

            return market_data

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None

    async def run(self):
        """Main loop for data collection"""
        self.logger.info("Starting Data Collector Agent...")
        
        while self.running:
            try:
                tasks = []
                for symbol in self.config['trading_pairs']:
                    tasks.append(self.collect_market_data(symbol))

                if tasks:
                    await asyncio.gather(*tasks)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                self.logger.error(f"Error in data collector main loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def stop(self):
        """Stop the data collector"""
        self.running = False