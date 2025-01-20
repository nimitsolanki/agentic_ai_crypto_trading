# agents/data_collector_agent.py
import asyncio
import logging
from typing import Dict, List
from services.exchange_service import ExchangeService
from services.message_broker import MessageBroker
from models.market_state import MarketState
from datetime import datetime

class DataCollectorAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.exchange = ExchangeService(config)
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        self.collection_interval = config['data_collection']['update_interval']

    async def collect_market_data(self, symbol: str) -> Dict:
        """Collect comprehensive market data for a symbol"""
        try:
            data = {}
            
            # Collect data for different timeframes
            for timeframe in self.config['data_collection']['timeframes']:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe)
                data[f'ohlcv_{timeframe}'] = ohlcv

            # Collect order book data
            order_book = await self.exchange.fetch_order_book(symbol)
            data['order_book'] = order_book

            # Collect recent trades
            recent_trades = await self.exchange.fetch_recent_trades(symbol)
            data['recent_trades'] = recent_trades

            # If futures market, collect funding rate
            if self.config['exchange'].get('market_type') == 'future':
                funding_rate = await self.exchange.fetch_funding_rate(symbol)
                data['funding_rate'] = funding_rate

            return data

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None

    async def process_and_publish_data(self, symbol: str, data: Dict):
        """Process collected data and publish to message broker"""
        try:
            if data:
                market_state = MarketState(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=data['ohlcv_1m'][-1][4],  # Close price from 1m timeframe
                    volume=data['ohlcv_1m'][-1][5],  # Volume from 1m timeframe
                    trend={},  # Will be filled by market analyst
                    volatility=0.0,  # Will be filled by market analyst
                    indicators={},
                    support_levels=[],
                    resistance_levels=[]
                )

                await self.message_broker.publish(
                    'market_data',
                    {
                        'symbol': symbol,
                        'data': data,
                        'market_state': market_state.__dict__,
                        'timestamp': datetime.now().timestamp()
                    }
                )

        except Exception as e:
            self.logger.error(f"Error processing data for {symbol}: {str(e)}")

    async def run(self):
        """Main loop for data collection"""
        self.logger.info("Starting Data Collector Agent...")
        
        while True:
            try:
                tasks = []
                for symbol in self.config['trading_pairs']:
                    # Collect data for each symbol
                    data = await self.collect_market_data(symbol)
                    if data:
                        tasks.append(self.process_and_publish_data(symbol, data))

                if tasks:
                    await asyncio.gather(*tasks)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                self.logger.error(f"Error in data collector main loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying