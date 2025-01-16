# agents/portfolio_manager_agent.py
import models.portfolio_state as portfolio_state

class PortfolioManagerAgent:
    def __init__(self):
        self.portfolio = portfolio_state.PortfolioState()

    def update_portfolio(self, executed_trade):
        self.portfolio.update(executed_trade)

    def get_portfolio_state(self):
        return self.portfolio.get_state()