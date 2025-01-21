# tools/strategy_monitor.py
import asyncio
import json
from datetime import datetime
import redis
from tabulate import tabulate

async def monitor_trading_activity():
    """Monitor real-time trading activity and performance"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    pubsub = r.pubsub()
    
    channels = ['trading_signals', 'trade_decisions', 'execution_results']
    pubsub.subscribe(*channels)
    
    signals = []
    trades = []
    
    print("🔄 Monitoring Trading Activity...")
    
    while True:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            data = json.loads(message['data'])
            channel = message['channel']
            
            if channel == 'trading_signals':
                print("\n🎯 New Trading Signal:")
                print(f"Symbol: {data['symbol']}")
                print(f"Direction: {data['direction']}")
                print(f"Confidence: {data['confidence']:.2%}")
                
            elif channel == 'execution_results':
                print("\n✅ Trade Executed:")
                print(f"Symbol: {data['symbol']}")
                print(f"Price: {data['execution_price']}")
                print(f"Size: {data['executed_quantity']}")
                
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(monitor_trading_activity())