# agents/data_collector_agent.py
import services.exchange_service as exchange_service

class DataCollectorAgent:
    def __init__(self):
        self.exchange_service = exchange_service.ExchangeService()

    def collect_market_data(self, symbols):
        data = {}
        for symbol in symbols:
            data[symbol] = self.exchange_service.fetch_market_data(symbol)
        return data