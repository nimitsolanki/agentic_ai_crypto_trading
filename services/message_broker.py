# services/message_broker.py
import redis
import json
import logging
import asyncio
from typing import Dict, Callable
from datetime import datetime

class MessageBroker:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.Redis(
            host=config.get('message_broker', {}).get('host', 'localhost'),
            port=config.get('message_broker', {}).get('port', 6379),
            db=config.get('message_broker', {}).get('db', 0),
            decode_responses=True
        )
        self.subscribers = {}
        self.logger.info("Message Broker initialized")

    async def publish(self, channel: str, message: Dict):
        """Publish message to a channel"""
        try:
            message_with_timestamp = {
                **message,
                'timestamp': datetime.now().isoformat()
            }
            message_str = json.dumps(message_with_timestamp)
            result = self.redis_client.publish(channel, message_str)
            self.logger.info(f"Published message to {channel}, subscribers: {result}")
            
            # Also store in a list for history
            list_key = f"history:{channel}"
            self.redis_client.lpush(list_key, message_str)
            self.redis_client.ltrim(list_key, 0, 999)  # Keep last 1000 messages
            
        except Exception as e:
            self.logger.error(f"Error publishing to {channel}: {str(e)}")

    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel"""
        try:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            
            # Start listener if not already running
            asyncio.create_task(self._listen_to_channel(channel))
            self.logger.info(f"Subscribed to channel: {channel}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to {channel}: {str(e)}")

    async def _listen_to_channel(self, channel: str):
        """Listen to a channel for messages"""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            self.logger.info(f"Started listening to channel: {channel}")

            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    self.logger.info(f"Received message on {channel}: {data}")
                    
                    # Call all callbacks for this channel
                    for callback in self.subscribers.get(channel, []):
                        try:
                            await callback(data)
                        except Exception as e:
                            self.logger.error(f"Error in callback for {channel}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error listening to {channel}: {str(e)}")
            await asyncio.sleep(5)  # Wait before reconnecting
            await self._listen_to_channel(channel)