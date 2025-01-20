# agents/portfolio_manager_agent.py
import logging
from typing import Dict, List, Optional
from services.message_broker import MessageBroker
from models.portfolio_state import PortfolioState, Position
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import asdict

class PortfolioManagerAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.message_broker = message_broker
        self.logger = logging.getLogger(__name__)
        
        # Initialize portfolio state
        self.portfolio = PortfolioState(
            total_equity=config.get('initial_capital', 10000.0),
            available_balance=config.get('initial_capital', 10000.0),
            positions={},
            daily_pnl=0.0,
            total_pnl=0.0,
            risk_metrics={}
        )
        
        # Historical data for analytics
        self.trade_history = []
        self.daily_snapshots = []
        self.position_updates = []
        
        # Configuration parameters
        self.max_position_size = config['risk_management']['max_position_size']
        self.max_drawdown = config['risk_management'].get('max_drawdown', 0.15)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.1)
        
    async def update_position(self, execution_data: Dict):
        """Update portfolio state based on trade execution"""
        try:
            symbol = execution_data['symbol']
            price = execution_data['execution_price']
            quantity = execution_data['executed_quantity']
            side = execution_data['direction']
            timestamp = datetime.fromtimestamp(execution_data['timestamp'])
            
            # Calculate position value
            position_value = price * quantity
            
            # Update available balance
            if side == 'BUY':
                self.portfolio.available_balance -= position_value
            else:
                self.portfolio.available_balance += position_value
            
            # Update or create position
            if symbol in self.portfolio.positions:
                position = self.portfolio.positions[symbol]
                old_quantity = position.quantity
                
                if side == 'BUY':
                    # Update average entry price for buys
                    total_value = (position.entry_price * old_quantity) + (price * quantity)
                    new_quantity = old_quantity + quantity
                    new_entry_price = total_value / new_quantity if new_quantity > 0 else price
                    position.entry_price = new_entry_price
                    position.quantity = new_quantity
                else:
                    # Handle sells
                    position.quantity -= quantity
                
                # Remove position if quantity is zero
                if abs(position.quantity) < 1e-8:
                    del self.portfolio.positions[symbol]
            else:
                # Create new position
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    entry_price=price,
                    current_price=price,
                    quantity=quantity if side == 'BUY' else -quantity,
                    side=side,
                    unrealized_pnl=0.0,
                    entry_time=timestamp
                )
            
            # Record position update
            self.position_updates.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'action': side,
                'price': price,
                'quantity': quantity,
                'position_value': position_value
            })
            
            # Update portfolio metrics
            await self.calculate_portfolio_metrics()
            
            # Publish updated portfolio state
            await self.publish_portfolio_update()
            
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")
            
    async def update_market_prices(self, market_data: Dict):
        """Update current prices and unrealized P&L"""
        try:
            symbol = market_data['symbol']
            current_price = market_data['data']['close'][-1]
            
            if symbol in self.portfolio.positions:
                position = self.portfolio.positions[symbol]
                old_price = position.current_price
                position.current_price = current_price
                
                # Update unrealized P&L
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                
                # Check for rebalancing needs
                price_change = abs(current_price - old_price) / old_price
                if price_change > self.rebalance_threshold:
                    await self.check_rebalancing_needs(symbol)
                    
            await self.calculate_portfolio_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating market prices: {str(e)}")
            
    async def calculate_portfolio_metrics(self):
        """Calculate comprehensive portfolio metrics"""
        try:
            # Calculate total equity and P&L
            total_equity = self.portfolio.available_balance
            total_unrealized_pnl = 0.0
            
            for position in self.portfolio.positions.values():
                position_value = position.quantity * position.current_price
                total_equity += position_value
                total_unrealized_pnl += position.unrealized_pnl
            
            self.portfolio.total_equity = total_equity
            
            # Calculate daily P&L
            today = datetime.now().date()
            if self.daily_snapshots and self.daily_snapshots[-1]['date'].date() == today:
                start_equity = self.daily_snapshots[-1]['start_equity']
                self.portfolio.daily_pnl = total_equity - start_equity
            
            # Calculate risk metrics
            self.portfolio.risk_metrics = {
                'total_exposure': sum(abs(p.quantity * p.current_price) for p in self.portfolio.positions.values()),
                'largest_position_size': max((abs(p.quantity * p.current_price) for p in self.portfolio.positions.values()), default=0),
                'position_count': len(self.portfolio.positions),
                'unrealized_pnl': total_unrealized_pnl,
                'drawdown': self.calculate_drawdown(),
                'sharpe_ratio': self.calculate_sharpe_ratio(),
                'concentration_risk': self.calculate_concentration_risk()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {str(e)}")
            
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        try:
            if not self.daily_snapshots:
                return 0.0
            
            equity_series = [snapshot['total_equity'] for snapshot in self.daily_snapshots]
            peak = max(equity_series)
            return (peak - self.portfolio.total_equity) / peak
            
        except Exception as e:
            self.logger.error(f"Error calculating drawdown: {str(e)}")
            return 0.0
            
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio using daily returns"""
        try:
            if len(self.daily_snapshots) < 30:  # Need sufficient data
                return 0.0
                
            daily_returns = []
            for i in range(1, len(self.daily_snapshots)):
                prev_equity = self.daily_snapshots[i-1]['total_equity']
                curr_equity = self.daily_snapshots[i]['total_equity']
                daily_return = (curr_equity - prev_equity) / prev_equity
                daily_returns.append(daily_return)
                
            if not daily_returns:
                return 0.0
                
            returns_array = np.array(daily_returns)
            avg_return = np.mean(returns_array)
            std_dev = np.std(returns_array)
            
            if std_dev == 0:
                return 0.0
                
            daily_risk_free = risk_free_rate / 252  # Annualized to daily
            sharpe = (avg_return - daily_risk_free) / std_dev * np.sqrt(252)
            
            return sharpe
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return 0.0
            
    def calculate_concentration_risk(self) -> Dict:
        """Calculate portfolio concentration metrics"""
        try:
            total_exposure = sum(abs(p.quantity * p.current_price) for p in self.portfolio.positions.values())
            
            if total_exposure == 0:
                return {'concentration_score': 0.0, 'largest_concentration': 0.0}
                
            concentrations = {}
            for symbol, position in self.portfolio.positions.items():
                position_exposure = abs(position.quantity * position.current_price)
                concentrations[symbol] = position_exposure / total_exposure
                
            concentration_score = sum(c * c for c in concentrations.values())
            largest_concentration = max(concentrations.values()) if concentrations else 0.0
            
            return {
                'concentration_score': concentration_score,
                'largest_concentration': largest_concentration,
                'positions': concentrations
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating concentration risk: {str(e)}")
            return {'concentration_score': 0.0, 'largest_concentration': 0.0}
            
    async def check_rebalancing_needs(self, symbol: str):
        """Check if portfolio rebalancing is needed"""
        try:
            position = self.portfolio.positions.get(symbol)
            if not position:
                return
                
            position_value = abs(position.quantity * position.current_price)
            position_weight = position_value / self.portfolio.total_equity
            
            if position_weight > self.max_position_size:
                # Calculate required reduction
                target_value = self.portfolio.total_equity * self.max_position_size
                reduction_needed = position_value - target_value
                
                if reduction_needed > 0:
                    await self.suggest_rebalancing(symbol, reduction_needed)
                    
        except Exception as e:
            self.logger.error(f"Error checking rebalancing needs: {str(e)}")
            
    async def suggest_rebalancing(self, symbol: str, reduction_amount: float):
        """Publish rebalancing suggestion"""
        try:
            position = self.portfolio.positions[symbol]
            reduction_quantity = reduction_amount / position.current_price
            
            rebalance_suggestion = {
                'symbol': symbol,
                'action': 'SELL' if position.quantity > 0 else 'BUY',
                'quantity': reduction_quantity,
                'reason': 'Position size exceeds maximum allowed',
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('rebalance_suggestions', rebalance_suggestion)
            
        except Exception as e:
            self.logger.error(f"Error suggesting rebalancing: {str(e)}")
            
    async def create_daily_snapshot(self):
        """Create daily portfolio snapshot"""
        try:
            snapshot = {
                'date': datetime.now(),
                'total_equity': self.portfolio.total_equity,
                'available_balance': self.portfolio.available_balance,
                'positions': {symbol: asdict(pos) for symbol, pos in self.portfolio.positions.items()},
                'risk_metrics': self.portfolio.risk_metrics,
                'daily_pnl': self.portfolio.daily_pnl
            }
            
            self.daily_snapshots.append(snapshot)
            
            # Keep last 90 days of snapshots
            if len(self.daily_snapshots) > 90:
                self.daily_snapshots.pop(0)
                
        except Exception as e:
            self.logger.error(f"Error creating daily snapshot: {str(e)}")
            
    async def publish_portfolio_update(self):
        """Publish current portfolio state"""
        try:
            portfolio_state = {
                'total_equity': self.portfolio.total_equity,
                'available_balance': self.portfolio.available_balance,
                'positions': {symbol: asdict(pos) for symbol, pos in self.portfolio.positions.items()},
                'daily_pnl': self.portfolio.daily_pnl,
                'risk_metrics': self.portfolio.risk_metrics,
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('portfolio_updates', portfolio_state)
            
        except Exception as e:
            self.logger.error(f"Error publishing portfolio update: {str(e)}")
            
    async def run(self):
        """Main loop for portfolio manager agent"""
        self.logger.info("Starting Portfolio Manager Agent...")
        try:
            # Subscribe to relevant channels
            await self.message_broker.subscribe('execution_results', self.update_position)
            await self.message_broker.subscribe('market_data', self.update_market_prices)
            
            # Start daily snapshot creation
            while True:
                await self.create_daily_snapshot()
                await asyncio.sleep(86400)  # Wait for 24 hours
                
        except Exception as e:
            self.logger.error(f"Error in portfolio manager main loop: {str(e)}")