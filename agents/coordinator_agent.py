# agents/coordinator_agent.py
import asyncio
import logging
from typing import Dict
from agents.data_collector_agent import DataCollectorAgent
from agents.market_analyst_agent import MarketAnalystAgent
from agents.risk_manager_agent import RiskManagerAgent
from agents.execution_agent import ExecutionAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent
from services.message_broker import MessageBroker

class CoordinatorAgent:
    def __init__(self, config: Dict):
        self.config = config
        self.message_broker = MessageBroker(config)
        # Get risk_tolerance from config, default to moderate (0.5) if not specified
        self.risk_tolerance = config.get('risk_management', {}).get('risk_tolerance', 0.5)
        self.agents = self.initialize_agents()
        self.logger = logging.getLogger(__name__)

    def initialize_agents(self):
        """Initialize all trading agents"""
        try:
            return {
                'data_collector': DataCollectorAgent(self.config, self.message_broker),
                'market_analyst': MarketAnalystAgent(self.config, self.message_broker),
                'risk_manager': RiskManagerAgent(self.config, self.message_broker),
                'execution': ExecutionAgent(self.config, self.message_broker),
                'portfolio_manager': PortfolioManagerAgent(self.config, self.message_broker)
            }
        except Exception as e:
            self.logger.error(f"Error initializing agents: {str(e)}")
            raise

    async def monitor_system(self):
        """Monitor the health and performance of all agents"""
        while True:
            try:
                # Monitor agent health
                for agent_name, agent in self.agents.items():
                    if not await self.check_agent_health(agent):
                        await self.restart_agent(agent_name, agent)
                
                # Monitor overall system performance
                await self.analyze_system_performance()
                
                await asyncio.sleep(self.config.get('monitoring_interval', 60))
            except Exception as e:
                self.logger.error(f"System monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def check_agent_health(self, agent) -> bool:
        """Check if an agent is functioning properly"""
        try:
            # Add health check logic here
            return True
        except Exception:
            return False

    async def restart_agent(self, agent_name: str, agent):
        """Restart a failed agent"""
        try:
            self.logger.warning(f"Restarting agent: {agent_name}")
            # Add restart logic here
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_name}: {str(e)}")

    async def analyze_system_performance(self):
        """Analyze overall system performance"""
        try:
            # Add performance analysis logic here
            pass
        except Exception as e:
            self.logger.error(f"Error analyzing system performance: {str(e)}")

    async def run(self):
        """Main loop for the coordinator agent"""
        self.logger.info("Starting Coordinator Agent...")
        try:
            # Start all agents
            agent_tasks = [agent.run() for agent in self.agents.values()]
            
            # Start system monitoring
            monitoring_task = self.monitor_system()
            
            # Run everything concurrently
            await asyncio.gather(*agent_tasks, monitoring_task)
            
        except Exception as e:
            self.logger.error(f"Error in coordinator main loop: {str(e)}")
            raise