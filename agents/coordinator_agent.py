# agents/coordinator_agent.py
from agents.data_collector_agent import DataCollectorAgent
from agents.market_analyst_agent import MarketAnalystAgent
from agents.risk_manager_agent import RiskManagerAgent
from agents.execution_agent import ExecutionAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent

class CoordinatorAgent:
    def __init__(self, symbols, risk_tolerance):
        self.symbols = symbols
        self.data_collector = DataCollectorAgent()
        self.market_analyst = MarketAnalystAgent()
        self.risk_manager = RiskManagerAgent(risk_tolerance)
        self.execution_agent = ExecutionAgent()
        self.portfolio_manager = PortfolioManagerAgent()

    def run(self):
        # Step 1: Collect market data
        market_data = self.data_collector.collect_market_data(self.symbols)

        # Step 2: Analyze market data for trade signals
        trade_signals = self.market_analyst.analyze_data(market_data)

        # Step 3: Evaluate and execute trades
        for symbol, signal in trade_signals.items():
            portfolio_state = self.portfolio_manager.get_portfolio_state()
            if self.risk_manager.evaluate_risk(signal, portfolio_state):
                executed_trade = self.execution_agent.execute_trade(signal)
                self.portfolio_manager.update_portfolio(executed_trade)