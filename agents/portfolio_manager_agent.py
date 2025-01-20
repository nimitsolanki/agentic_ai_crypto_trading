# agents/portfolio_manager_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from services.message_broker import MessageBroker
from models.portfolio_state import PortfolioState, Position

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
        
        # Historical data
        self.trade_history = []
        self.daily_snapshots = []
        self.running = True

    def calculate_win_rate(self) -> float:
        """Calculate win rate from trade history"""
        try:
            if not self.trade_history:
                return 0.0
            
            winning_trades = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
            return winning_trades / len(self.trade_history)
            
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {str(e)}")
            return 0.0

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
                    position.entry_price = total_value / new_quantity if new_quantity > 0 else price
                    position.quantity = new_quantity
                else:
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
            
            # Record trade in history
            self.trade_history.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'price': price,
                'quantity': quantity,
                'value': position_value,
                'pnl': 0.0  # Will be updated when position is closed
            })
            
            # Update portfolio metrics
            await self.calculate_portfolio_metrics()
            
            # Publish portfolio update
            await self.publish_portfolio_update()
            
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")

    async def calculate_portfolio_metrics(self):
        """Calculate portfolio metrics"""
        try:
            # Calculate total equity and P&L
            total_equity = self.portfolio.available_balance
            unrealized_pnl = 0.0
            
            for position in self.portfolio.positions.values():
                position_value = position.quantity * position.current_price
                total_equity += position_value
                unrealized_pnl += position.unrealized_pnl
            
            self.portfolio.total_equity = total_equity
            self.portfolio.risk_metrics = {
                'total_exposure': sum(abs(p.quantity * p.current_price) for p in self.portfolio.positions.values()),
                'unrealized_pnl': unrealized_pnl,
                'position_count': len(self.portfolio.positions)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {str(e)}")

    async def publish_portfolio_update(self):
        """Publish portfolio update to message broker"""
        try:
            update = {
                'total_equity': self.portfolio.total_equity,
                'available_balance': self.portfolio.available_balance,
                'positions': {
                    symbol: {
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'unrealized_pnl': pos.unrealized_pnl
                    } for symbol, pos in self.portfolio.positions.items()
                },
                'risk_metrics': self.portfolio.risk_metrics,
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('portfolio_updates', update)
            
        except Exception as e:
            self.logger.error(f"Error publishing portfolio update: {str(e)}")

    async def run(self):
        """Main loop for portfolio manager"""
        self.logger.info("Starting Portfolio Manager Agent...")
        try:
            # Subscribe to execution results
            await self.message_broker.subscribe('execution_results', self.update_position)
            
            # Main loop for periodic updates
            while self.running:
                await self.calculate_portfolio_metrics()
                await self.publish_portfolio_update()
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            self.logger.error(f"Error in portfolio manager main loop: {str(e)}")

    async def stop(self):
        """Stop the portfolio manager"""
        self.running = False# agents/portfolio_manager_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from services.message_broker import MessageBroker
from models.portfolio_state import PortfolioState, Position

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
        
        # Historical data
        self.trade_history = []
        self.daily_snapshots = []
        self.running = True

    def calculate_win_rate(self) -> float:
        """Calculate win rate from trade history"""
        try:
            if not self.trade_history:
                return 0.0
            
            winning_trades = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
            return winning_trades / len(self.trade_history)
            
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {str(e)}")
            return 0.0

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
                    position.entry_price = total_value / new_quantity if new_quantity > 0 else price
                    position.quantity = new_quantity
                else:
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
            
            # Record trade in history
            self.trade_history.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'price': price,
                'quantity': quantity,
                'value': position_value,
                'pnl': 0.0  # Will be updated when position is closed
            })
            
            # Update portfolio metrics
            await self.calculate_portfolio_metrics()
            
            # Publish portfolio update
            await self.publish_portfolio_update()
            
        except Exception as e:
            self.logger.error(f"Error updating position: {str(e)}")

    async def calculate_portfolio_metrics(self):
        """Calculate portfolio metrics"""
        try:
            # Calculate total equity and P&L
            total_equity = self.portfolio.available_balance
            unrealized_pnl = 0.0
            
            for position in self.portfolio.positions.values():
                position_value = position.quantity * position.current_price
                total_equity += position_value
                unrealized_pnl += position.unrealized_pnl
            
            self.portfolio.total_equity = total_equity
            self.portfolio.risk_metrics = {
                'total_exposure': sum(abs(p.quantity * p.current_price) for p in self.portfolio.positions.values()),
                'unrealized_pnl': unrealized_pnl,
                'position_count': len(self.portfolio.positions)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {str(e)}")

    async def publish_portfolio_update(self):
        """Publish portfolio update to message broker"""
        try:
            update = {
                'total_equity': self.portfolio.total_equity,
                'available_balance': self.portfolio.available_balance,
                'positions': {
                    symbol: {
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'unrealized_pnl': pos.unrealized_pnl
                    } for symbol, pos in self.portfolio.positions.items()
                },
                'risk_metrics': self.portfolio.risk_metrics,
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('portfolio_updates', update)
            
        except Exception as e:
            self.logger.error(f"Error publishing portfolio update: {str(e)}")

    async def run(self):
        """Main loop for portfolio manager"""
        self.logger.info("Starting Portfolio Manager Agent...")
        try:
            # Subscribe to execution results
            await self.message_broker.subscribe('execution_results', self.update_position)
            
            # Main loop for periodic updates
            while self.running:
                await self.calculate_portfolio_metrics()
                await self.publish_portfolio_update()
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            self.logger.error(f"Error in portfolio manager main loop: {str(e)}")

    async def stop(self):
        """Stop the portfolio manager"""
        self.running = False