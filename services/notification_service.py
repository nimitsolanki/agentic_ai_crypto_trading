# services/notification_service.py
import logging
from typing import Dict
import telegram
import asyncio
from datetime import datetime

class TelegramNotificationService:
    def __init__(self, config: Dict):
        self.config = config
        self.bot = telegram.Bot(token=config['telegram']['bot_token'])
        self.chat_id = config['telegram']['chat_id']
        self.logger = logging.getLogger(__name__)

    async def send_message(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            self.logger.error(f"Error sending telegram message: {str(e)}")

    async def send_trade_notification(self, trade_data: Dict):
        """Send formatted trade notification"""
        try:
            emoji = "🟢" if trade_data['side'] == 'BUY' else "🔴"
            message = (
                f"{emoji} <b>Trade Executed</b>\n\n"
                f"Symbol: {trade_data['symbol']}\n"
                f"Side: {trade_data['side']}\n"
                f"Price: {trade_data['price']:.2f}\n"
                f"Quantity: {trade_data['quantity']:.4f}\n"
                f"Total: ${(trade_data['price'] * trade_data['quantity']):.2f}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.send_message(message)
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {str(e)}")

    async def send_signal_notification(self, signal_data: Dict):
        """Send trading signal notification"""
        try:
            emoji = "📈" if signal_data['direction'] == 'BUY' else "📉"
            message = (
                f"{emoji} <b>Trading Signal</b>\n\n"
                f"Symbol: {signal_data['symbol']}\n"
                f"Signal: {signal_data['signal_type']}\n"
                f"Direction: {signal_data['direction']}\n"
                f"Confidence: {signal_data['confidence']:.2%}\n"
                f"Price: {signal_data['price']:.2f}"
            )
            await self.send_message(message)
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {str(e)}")