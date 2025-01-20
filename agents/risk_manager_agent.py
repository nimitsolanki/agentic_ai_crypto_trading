# agents/risk_manager_agent.py
import logging
from typing import Dict, Tuple, Optional
from services.message_broker import MessageBroker
from models.portfolio_state import PortfolioState, Position
from datetime import datetime
import numpy as np

class RiskManagerAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        self.risk_limits = config['risk_management']
        self.portfolio_state = PortfolioState(
            total_equity=0.0,
            available_balance=0.0,
            positions={},
            daily_pnl=0.0,
            total_pnl=0.0,
            risk_metrics={}
        )
        self.historical_trades = []

    async def update_portfolio_state(self, portfolio_data: Dict):
        """Update portfolio state with latest data"""
        try:
            self.portfolio_state.total_equity = portfolio_data['total_equity']
            self.portfolio_state.available_balance = portfolio_data['available_balance']
            self.portfolio_state.positions = portfolio_data['positions']
            self.portfolio_state.daily_pnl = portfolio_data['daily_pnl']
            self.portfolio_state.risk_metrics = self.calculate_risk_metrics()
        except Exception as e:
            self.logger.error(f"Error updating portfolio state: {str(e)}")

    def calculate_risk_metrics(self) -> Dict:
        """Calculate portfolio risk metrics"""
        try:
            positions = self.portfolio_state.positions
            metrics = {
                'total_exposure': sum(pos.quantity * pos.current_price for pos in positions.values()),
                'largest_position': max((pos.quantity * pos.current_price for pos in positions.values()), default=0),
                'position_concentration': {},
                'value_at_risk': self.calculate_var(),
                'sharpe_ratio': self.calculate_sharpe_ratio()
            }
            
            # Calculate position concentration
            total_value = metrics['total_exposure']
            if total_value > 0:
                for symbol, pos in positions.items():
                    position_value = pos.quantity * pos.current_price
                    metrics['position_concentration'][symbol] = position_value / total_value
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}

    def calculate_var(self, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk"""
        try:
            if len(self.historical_trades) < 30:
                return 0.0
            
            returns = [trade['pnl_percentage'] for trade in self.historical_trades]
            var = np.percentile(returns, (1 - confidence_level) * 100)
            return abs(var) * self.portfolio_state.total_equity
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {str(e)}")
            return 0.0

    def calculate_position_size(self, signal: Dict, market_state: Dict) -> float:
        """Calculate optimal position size using Kelly Criterion and risk limits"""
        try:
            # Get win rate and risk-reward ratio
            win_rate = self.calculate_win_rate(signal['signal_type'])
            risk_reward = self.calculate_risk_reward(signal, market_state)
            
            # Kelly Criterion calculation
            kelly_fraction = win_rate - ((1 - win_rate) / risk_reward)
            kelly_fraction = max(0, min(kelly_fraction * 0.5, 0.2))  # Half Kelly, max 20%
            
            # Apply position sizing constraints
            available_capital = self.portfolio_state.available_balance
            max_position = min(
                available_capital * kelly_fraction,
                self.risk_limits['max_position_size'],
                available_capital * 0.1  # Max 10% of available capital
            )
            
            return max_position
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def calculate_exit_levels(self, entry_price: float, signal: Dict, 
                            market_state: Dict) -> Tuple[float, float]:
        """Calculate stop-loss and take-profit levels"""
        try:
            # Dynamic ATR-based stops
            atr = market_state.get('atr', entry_price * 0.02)
            
            if signal['direction'] == 'buy':
                stop_loss = entry_price - (atr * 3)
                take_profit = entry_price + (atr * 5)
            else:
                stop_loss = entry_price + (atr * 3)
                take_profit = entry_price - (atr * 5)
            
            return stop_loss, take_profit
        except Exception as e:
            self.logger.error(f"Error calculating exit levels: {str(e)}")
            return None, None

    async def evaluate_signal(self, signal_data: Dict):
        """Evaluate trading signal and make risk-adjusted decisions"""
        try:
            symbol = signal_data['symbol']
            signals = signal_data['signals']
            market_state = signal_data['market_state']
            
            for signal in signals:
                # Skip if signal confidence is too low
                if signal['confidence'] < self.config['analysis']['min_confidence']:
                    continue
                
                # Calculate position size
                position_size = self.calculate_position_size(signal, market_state)
                
                if position_size <= 0:
                    continue
                
                # Calculate exit levels
                stop_loss, take_profit = self.calculate_exit_levels(
                    signal['price'],
                    signal,
                    market_state
                )
                
                if not stop_loss or not take_profit:
                    continue
                
                # Validate trade against risk limits
                if self.validate_trade(symbol, position_size, stop_loss):
                    await self.publish_trade_decision(
                        symbol, signal, position_size, stop_loss, take_profit
                    )
        
        except Exception as e:
            self.logger.error(f"Error evaluating signal: {str(e)}")

    async def publish_trade_decision(self, symbol: str, signal: Dict, 
                                   position_size: float, stop_loss: float, 
                                   take_profit: float):
        """Publish trade decision to message broker"""
        try:
            decision = {
                'symbol': symbol,
                'signal_type': signal['signal_type'],
                'direction': signal['direction'],
                'position_size': position_size,
                'entry_price': signal['price'],
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('trade_decisions', decision)
            
        except Exception as e:
            self.logger.error(f"Error publishing trade decision: {str(e)}")

    async def run(self):
        """Main loop for risk manager agent"""
        self.logger.info("Starting Risk Manager Agent...")
        try:
            # Subscribe to relevant channels
            await self.message_broker.subscribe('trading_signals', self.evaluate_signal)
            await self.message_broker.subscribe('portfolio_updates', self.update_portfolio_state)
        except Exception as e:
            self.logger.error(f"Error in risk manager main loop: {str(e)}")