# agents/execution_agent.py
import logging
from typing import Dict, Optional
from services.message_broker import MessageBroker
from services.exchange_service import ExchangeService
from datetime import datetime
import asyncio

class ExecutionAgent:
    def __init__(self, config: Dict, message_broker: MessageBroker):
        self.config = config
        self.message_broker = message_broker
        self.exchange = ExchangeService(config)
        self.logger = logging.getLogger(__name__)
        self.active_orders = {}
        self.order_queue = asyncio.Queue()
        self.retry_attempts = config['execution']['retry_attempts']
        self.retry_delay = config['execution']['retry_delay']

    async def execute_trade(self, trade_decision: Dict) -> Optional[Dict]:
        """Execute trade with retry logic"""
        try:
            symbol = trade_decision['symbol']
            position_size = trade_decision['position_size']
            direction = trade_decision['direction']
            
            # Create main order
            order = await self.create_order(
                symbol=symbol,
                order_type='MARKET',
                side=direction.upper(),
                amount=position_size
            )
            
            if order:
                # Set stop loss
                stop_loss_order = await self.create_order(
                    symbol=symbol,
                    order_type='STOP_LOSS_LIMIT',
                    side='SELL' if direction == 'buy' else 'BUY',
                    amount=position_size,
                    price=trade_decision['stop_loss'],
                    params={'stopPrice': trade_decision['stop_loss']}
                )
                
                # Set take profit
                take_profit_order = await self.create_order(
                    symbol=symbol,
                    order_type='LIMIT',
                    side='SELL' if direction == 'buy' else 'BUY',
                    amount=position_size,
                    price=trade_decision['take_profit']
                )
                
                # Track orders
                self.active_orders[order['id']] = {
                    'main_order': order,
                    'stop_loss': stop_loss_order,
                    'take_profit': take_profit_order,
                    'trade_decision': trade_decision
                }
                
                await self.publish_execution_result(order, trade_decision)
                return order
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return None

    async def create_order(self, **order_params) -> Optional[Dict]:
        """Create order with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                order = await self.exchange.create_order(**order_params)
                return order
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    self.logger.error(f"Final attempt failed: {str(e)}")
                    return None
                await asyncio.sleep(self.retry_delay)

    async def monitor_orders(self):
        """Monitor and update status of active orders"""
        while True:
            try:
                for order_id, order_info in list(self.active_orders.items()):
                    # Check main order status
                    status = await self.exchange.fetch_order_status(order_id)
                    
                    if status == 'filled':
                        # Update stop loss and take profit orders
                        await self.adjust_exit_orders(order_info)
                    elif status == 'canceled' or status == 'expired':
                        # Clean up related orders
                        await self.cancel_related_orders(order_info)
                        del self.active_orders[order_id]
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring orders: {str(e)}")
                await asyncio.sleep(60)

    async def publish_execution_result(self, order: Dict, trade_decision: Dict):
        """Publish execution results to message broker"""
        try:
            result = {
                'symbol': trade_decision['symbol'],
                'order_id': order['id'],
                'execution_price': order['price'],
                'executed_quantity': order['filled'],
                'direction': trade_decision['direction'],
                'timestamp': datetime.now().timestamp()
            }
            
            await self.message_broker.publish('execution_results', result)
            
        except Exception as e:
            self.logger.error(f"Error publishing execution result: {str(e)}")

    async def run(self):
        """Main loop for execution agent"""
        self.logger.info("Starting Execution Agent...")
        try:
            # Start order monitoring
            monitor_task = asyncio.create_task(self.monitor_orders())
            
            # Subscribe to trade decisions
            await self.message_broker.subscribe('trade_decisions', 
                lambda decision: self.order_queue.put_nowait(decision))
            
            # Process order queue
            while True:
                trade_decision = await self.order_queue.get()
                await self.execute_trade(trade_decision)
                
        except Exception as e:
            self.logger.error(f"Error in execution agent main loop: {str(e)}")