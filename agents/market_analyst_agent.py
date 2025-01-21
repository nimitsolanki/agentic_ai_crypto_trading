# agents/market_analyst_agent.py
import logging
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from services.message_broker import MessageBroker
from models.trade_signal import TradeSignal
from utils.indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands
from datetime import datetime

class MarketAnalystAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        # self.min_confidence = config['analysis']['min_confidence']
        # self.strategy_weights = config['analysis']['strategy_weights']

         # Get analysis config with defaults
        self.analysis_config = config.get('analysis', {})
        self.min_confidence = self.analysis_config.get('min_confidence', 0.6)
        self.strategy_weights = self.analysis_config.get('strategy_weights', {
            'trend_following': 0.4,
            'mean_reversion': 0.3,
            'momentum': 0.3
        })
        self.indicators_config = self.analysis_config.get('indicators', {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_threshold': 1.2
        })

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze market trend using multiple timeframes"""
        try:
            trends = {}
            for timeframe in ['short', 'medium', 'long']:
                if timeframe == 'short':
                    ma_short = df['close'].rolling(window=10).mean()
                    ma_long = df['close'].rolling(window=20).mean()
                elif timeframe == 'medium':
                    ma_short = df['close'].rolling(window=20).mean()
                    ma_long = df['close'].rolling(window=50).mean()
                else:
                    ma_short = df['close'].rolling(window=50).mean()
                    ma_long = df['close'].rolling(window=200).mean()

                trend_strength = (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1]
                trends[timeframe] = {
                    'direction': 'up' if trend_strength > 0 else 'down',
                    'strength': abs(trend_strength)
                }

            return trends

        except Exception as e:
            self.logger.error(f"Error analyzing trend: {str(e)}")
            return {}

    def analyze_support_resistance(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """Identify support and resistance levels"""
        try:
            pivot_points = []
            window_size = 20

            for i in range(window_size, len(df) - window_size):
                if all(df['high'].iloc[i] > df['high'].iloc[i-window_size:i]) and \
                   all(df['high'].iloc[i] > df['high'].iloc[i+1:i+window_size]):
                    pivot_points.append((df['high'].iloc[i], 'resistance'))
                if all(df['low'].iloc[i] < df['low'].iloc[i-window_size:i]) and \
                   all(df['low'].iloc[i] < df['low'].iloc[i+1:i+window_size]):
                    pivot_points.append((df['low'].iloc[i], 'support'))

            support_levels = sorted([price for price, type_ in pivot_points if type_ == 'support'])
            resistance_levels = sorted([price for price, type_ in pivot_points if type_ == 'resistance'])

            return support_levels, resistance_levels

        except Exception as e:
            self.logger.error(f"Error analyzing support/resistance: {str(e)}")
            return [], []

    def calculate_signal_confidence(self, indicators: Dict, market_state: Dict) -> float:
        """Calculate confidence level for trading signal"""
        try:
            confidence_factors = []

            # RSI confidence
            if 30 <= indicators['rsi'] <= 70:
                confidence_factors.append(0.5)
            elif indicators['rsi'] < 20 or indicators['rsi'] > 80:
                confidence_factors.append(1.0)
            else:
                confidence_factors.append(0.8)

            # Trend confidence
            trend_agreement = sum(1 for trend in market_state['trends'].values() 
                                if trend['direction'] == market_state['trends']['medium']['direction'])
            confidence_factors.append(trend_agreement / 3)

            # Volume confidence
            if indicators['volume_ratio'] > 1.5:
                confidence_factors.append(1.0)
            elif indicators['volume_ratio'] > 1.0:
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.3)

            return sum(confidence_factors) / len(confidence_factors)

        except Exception as e:
            self.logger.error(f"Error calculating signal confidence: {str(e)}")
            return 0.0

    async def analyze_market_data(self, market_data: Dict):
        """Process market data and generate trading signals"""
        try:
            symbol = market_data['symbol']
            data = market_data['data']
            
            # Create DataFrame from OHLCV data
            df = pd.DataFrame(data['ohlcv_1m'], 
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate technical indicators
            indicators = {
                'rsi': calculate_rsi(df['close']),
                'macd': calculate_macd(df['close']),
                'bb': calculate_bollinger_bands(df['close'])
            }
            
            # Analyze market state
            market_state = {
                'trends': self.analyze_trend(df),
                'support_resistance': self.analyze_support_resistance(df),
                'volatility': df['close'].pct_change().std(),
            }
            
            # Generate trading signals
            signals = self.generate_signals(df, indicators, market_state)
            
            if signals:
                await self.message_broker.publish(
                    'trading_signals',
                    {
                        'symbol': symbol,
                        'signals': [signal.__dict__ for signal in signals],
                        'market_state': market_state,
                        'timestamp': datetime.now().timestamp()
                    }
                )

        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")

    # In the generate_signals method:

    def generate_signals(self, df: pd.DataFrame, indicators: Dict, market_state: Dict) -> List[TradeSignal]:
        """Generate trading signals with enhanced strategy"""
        signals = []
        try:
            current_price = df['close'].iloc[-1]
            rsi = indicators['rsi'].iloc[-1]
            macd = indicators['macd']['macd'].iloc[-1]
            signal_line = indicators['macd']['signal'].iloc[-1]
            bb = indicators['bb']
            volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]

            # Trend following strategy
            if macd > signal_line and volume_ratio > 1.2:
                if current_price > bb['middle'].iloc[-1]:
                    confidence = min((macd - signal_line) / signal_line * 2, 0.95)
                    signals.append(TradeSignal(
                        symbol=df['symbol'].iloc[-1],
                        signal_type='trend_following',
                        direction='BUY',
                        confidence=confidence,
                        price=current_price,
                        metadata={'strategy': 'trend_following'}
                    ))

            # Mean reversion strategy
            elif rsi < 30 and current_price < bb['lower'].iloc[-1]:
                confidence = (30 - rsi) / 30
                signals.append(TradeSignal(
                    symbol=df['symbol'].iloc[-1],
                    signal_type='mean_reversion',
                    direction='BUY',
                    confidence=confidence,
                    price=current_price,
                    metadata={'strategy': 'mean_reversion'}
                ))

            # Take profit signals
            elif rsi > 70 or current_price > bb['upper'].iloc[-1]:
                signals.append(TradeSignal(
                    symbol=df['symbol'].iloc[-1],
                    signal_type='take_profit',
                    direction='SELL',
                    confidence=0.8,
                    price=current_price,
                    metadata={'strategy': 'take_profit'}
                ))

            return signals

        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return []

    async def run(self):
        """Main loop for market analysis"""
        self.logger.info("Starting Market Analyst Agent...")
        await self.message_broker.subscribe('market_data', self.analyze_market_data)
