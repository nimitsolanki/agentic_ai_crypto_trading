# agents/coordinator_agent.py
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, time
from services.message_broker import MessageBroker
from services.notification_service import TelegramNotificationService
from agents.data_collector_agent import DataCollectorAgent
from agents.market_analyst_agent import MarketAnalystAgent
from agents.risk_manager_agent import RiskManagerAgent
from agents.execution_agent import ExecutionAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent

class CoordinatorAgent:
    def __init__(self, config: Dict):
        """Initialize the coordinator agent with all sub-agents and services"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.message_broker = MessageBroker(config)
        self.notification_service = TelegramNotificationService(config)
        self.agents = {}
        self.system_status = {
            'running': False,
            'last_health_check': None,
            'errors': []
        }
        
    async def initialize_agents(self):
        """Initialize all trading system agents"""
        try:
            self.agents = {
                'data_collector': DataCollectorAgent(self.config, self.message_broker),
                'market_analyst': MarketAnalystAgent(self.config, self.message_broker),
                'risk_manager': RiskManagerAgent(self.config, self.message_broker),
                'portfolio_manager': PortfolioManagerAgent(self.config, self.message_broker),
                'execution': ExecutionAgent(self.config, self.message_broker)
            }
            
            await self.notification_service.send_message(
                "🚀 Trading System Initialized\n"
                "All agents are ready to start operations."
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize agents: {str(e)}"
            self.logger.error(error_msg)
            await self.notification_service.send_message(f"⚠️ {error_msg}")
            raise

    async def start_agents(self):
        """Start all agents"""
        try:
            self.system_status['running'] = True
            agent_tasks = []
            
            for agent_name, agent in self.agents.items():
                self.logger.info(f"Starting {agent_name}...")
                agent_tasks.append(
                    asyncio.create_task(
                        agent.run(),
                        name=f"agent_{agent_name}"
                    )
                )
            
            return agent_tasks
            
        except Exception as e:
            error_msg = f"Failed to start agents: {str(e)}"
            self.logger.error(error_msg)
            await self.notification_service.send_message(f"⚠️ {error_msg}")
            raise

    async def monitor_agents(self):
        """Monitor the health and performance of all agents"""
        while self.system_status['running']:
            try:
                health_status = await self.check_system_health()
                self.system_status['last_health_check'] = datetime.now()
                
                # Check for any unhealthy agents
                unhealthy_agents = [
                    name for name, status in health_status.items() 
                    if not status['healthy']
                ]
                
                if unhealthy_agents:
                    await self.handle_unhealthy_agents(unhealthy_agents)
                
                # Regular system status update (every 4 hours)
                if self.should_send_status_update():
                    await self.send_system_status()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                error_msg = f"Error in system monitoring: {str(e)}"
                self.logger.error(error_msg)
                self.system_status['errors'].append({
                    'time': datetime.now(),
                    'error': str(e)
                })
                await asyncio.sleep(60)

    async def check_system_health(self) -> Dict:
        """Check the health status of all agents"""
        health_status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                status = await agent.health_check() if hasattr(agent, 'health_check') else True
                health_status[agent_name] = {
                    'healthy': status,
                    'last_check': datetime.now(),
                    'error': None
                }
            except Exception as e:
                health_status[agent_name] = {
                    'healthy': False,
                    'last_check': datetime.now(),
                    'error': str(e)
                }
        
        return health_status

    async def handle_unhealthy_agents(self, unhealthy_agents: list):
        """Handle and attempt to recover unhealthy agents"""
        for agent_name in unhealthy_agents:
            try:
                self.logger.warning(f"Attempting to restart {agent_name}")
                await self.notification_service.send_message(
                    f"⚠️ Restarting {agent_name} due to health check failure"
                )
                
                # Stop the current agent
                if hasattr(self.agents[agent_name], 'stop'):
                    await self.agents[agent_name].stop()
                
                # Reinitialize the agent
                agent_class = type(self.agents[agent_name])
                self.agents[agent_name] = agent_class(self.config, self.message_broker)
                
                # Restart the agent
                asyncio.create_task(
                    self.agents[agent_name].run(),
                    name=f"agent_{agent_name}_restarted"
                )
                
            except Exception as e:
                error_msg = f"Failed to restart {agent_name}: {str(e)}"
                self.logger.error(error_msg)
                await self.notification_service.send_message(f"🚨 {error_msg}")

    async def send_system_status(self):
        """Send system status update to telegram"""
        try:
            # Gather performance metrics
            metrics = await self.get_performance_metrics()
            
            status_message = (
                "📊 System Status Update\n\n"
                f"System Uptime: {self.get_uptime()}\n"
                f"Active Agents: {len(self.agents)}\n"
                f"Last Health Check: {self.system_status['last_health_check'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Recent Errors: {len(self.system_status['errors'])}\n\n"
                "Performance Metrics:\n"
                f"Daily P&L: ${metrics['daily_pnl']:.2f}\n"
                f"Total Trades: {metrics['total_trades']}\n"
                f"Win Rate: {metrics['win_rate']:.2%}\n"
                f"Open Positions: {metrics['open_positions']}"
            )
            
            await self.notification_service.send_message(status_message)
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {str(e)}")

    async def get_performance_metrics(self) -> Dict:
        """Gather system performance metrics"""
        try:
            portfolio_agent = self.agents.get('portfolio_manager')
            if not portfolio_agent:
                return {
                    'daily_pnl': 0.0,
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'open_positions': 0
                }
            
            return {
                'daily_pnl': portfolio_agent.portfolio.daily_pnl,
                'total_trades': len(portfolio_agent.trade_history),
                'win_rate': portfolio_agent.calculate_win_rate(),
                'open_positions': len(portfolio_agent.portfolio.positions)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return {
                'daily_pnl': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'open_positions': 0
            }

    def get_uptime(self) -> str:
        """Calculate system uptime"""
        if not self.system_status.get('start_time'):
            return "Unknown"
        
        uptime = datetime.now() - self.system_status['start_time']
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m"

    def should_send_status_update(self) -> bool:
        """Determine if it's time to send a status update"""
        if not self.system_status.get('last_status_update'):
            return True
            
        hours_since_update = (
            datetime.now() - self.system_status['last_status_update']
        ).total_seconds() / 3600
        
        return hours_since_update >= 4

    async def shutdown(self):
        """Gracefully shutdown the system"""
        try:
            self.logger.info("Initiating system shutdown...")
            self.system_status['running'] = False
            
            # Stop all agents
            for agent_name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'stop'):
                        await agent.stop()
                    self.logger.info(f"Stopped {agent_name}")
                except Exception as e:
                    self.logger.error(f"Error stopping {agent_name}: {str(e)}")
            
            await self.notification_service.send_message(
                "🔄 Trading System Shutdown\n"
                "All agents have been stopped safely."
            )
            
        except Exception as e:
            error_msg = f"Error during shutdown: {str(e)}"
            self.logger.error(error_msg)
            await self.notification_service.send_message(f"🚨 {error_msg}")

    async def run(self):
        """Main loop for the coordinator agent"""
        try:
            self.logger.info("Starting Coordinator Agent...")
            self.system_status['start_time'] = datetime.now()
            
            # Initialize all agents
            await self.initialize_agents()
            
            # Start all agents
            agent_tasks = await self.start_agents()
            
            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_agents())
            
            # Combine all tasks
            all_tasks = agent_tasks + [monitor_task]
            
            # Run everything concurrently
            await asyncio.gather(*all_tasks)
            
        except Exception as e:
            error_msg = f"Critical error in coordinator agent: {str(e)}"
            self.logger.error(error_msg)
            await self.notification_service.send_message(f"🚨 {error_msg}")
            await self.shutdown()
            raise
        finally:
            await self.shutdown()