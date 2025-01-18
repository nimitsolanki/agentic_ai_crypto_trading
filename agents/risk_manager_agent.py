# agents/risk_manager_agent.py
class RiskManagerAgent:
    def __init__(self, risk_tolerance):
        self.risk_tolerance = risk_tolerance

    def evaluate_risk(self, trade_signal, portfolio_state):
        # Simple risk management logic
        # Need to improve this
        if portfolio_state.get_exposure() + trade_signal["risk"] > self.risk_tolerance:
            return False
        return True