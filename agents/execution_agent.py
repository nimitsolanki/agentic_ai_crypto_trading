# agents/execution_agent.py
import services.exchange_service as exchange_service

class ExecutionAgent:
    def __init__(self):
        self.exchange_service = exchange_service.ExchangeService()

    def execute_trade(self, trade_signal):
        return self.exchange_service.place_order(
            trade_signal["symbol"],
            trade_signal["action"],
            trade_signal["amount"]
        )