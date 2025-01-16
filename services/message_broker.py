# services/message_broker.py
import redis
import json
from typing import Dict, Callable
import logging

class MessageBroker:
    def __init__(self, config: Dict):
        self.redis_client = redis.Redis(
            host=config['message_broker']['host'],
            port=config['message_broker']['port'],
            db=config['message_broker']['db']
        )
        self.logger = logging.getLogger(__name__)

    async def publish(self, channel: str, message: Dict):
        try:
            self.redis_client.publish(channel, json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error publishing message: {str(e)}")

    async def subscribe(self, channel: str, callback: Callable):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message['type'] == 'message':
                await callback(json.loads(message['data']))