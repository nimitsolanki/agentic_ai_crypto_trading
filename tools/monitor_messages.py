# tools/monitor_messages.py
import asyncio
import redis
import json
from datetime import datetime

async def monitor_redis():
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    pubsub = r.pubsub()
    
    # Subscribe to all trading channels
    channels = [
        'market_data',
        'trading_signals',
        'trade_decisions',
        'execution_results',
        'portfolio_updates'
    ]
    
    pubsub.subscribe(*channels)
    print(f"Monitoring channels: {', '.join(channels)}")
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            channel = message['channel']
            data = json.loads(message['data'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{timestamp}] Channel: {channel}")
            print(f"Data: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(monitor_redis())