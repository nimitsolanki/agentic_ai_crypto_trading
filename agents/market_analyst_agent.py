# agents/market_analyst_agent.py
import utils.indicators as indicators

class MarketAnalystAgent:
    def __init__(self):
        pass

    def analyze_data(self, market_data):
        signals = {}
        for symbol, data in market_data.items():
            signals[symbol] = indicators.calculate_signals(data)
        return signals