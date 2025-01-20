# utils/config_loader.py
import os
import json
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    @staticmethod
    def load_config() -> Dict:
        """Load configuration from config files and environment variables"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load base configuration
            config_path = Path('config/config.json')
            with config_path.open('r') as f:
                config = json.load(f)
            
            # Update sensitive information from environment variables
            config['exchange'].update({
                'api_key': os.getenv('BINANCE_API_KEY'),
                'api_secret': os.getenv('BINANCE_SECRET_KEY')
            })
            
            # Add telegram configuration
            config['telegram'] = {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'notifications': {
                    'trades': True,
                    'signals': True,
                    'portfolio_updates': True
                }
            }
            
            # Validate configuration
            ConfigLoader._validate_config(config)
            
            return config
            
        except Exception as e:
            raise Exception(f"Error loading configuration: {str(e)}")
    
    @staticmethod
    def _validate_config(config: Dict):
        """Validate required configuration parameters"""
        required_env_vars = [
            ('BINANCE_API_KEY', 'Exchange API Key'),
            ('BINANCE_SECRET_KEY', 'Exchange Secret Key'),
            ('TELEGRAM_BOT_TOKEN', 'Telegram Bot Token'),
            ('TELEGRAM_CHAT_ID', 'Telegram Chat ID')
        ]
        
        missing_vars = []
        for env_var, description in required_env_vars:
            if not os.getenv(env_var):
                missing_vars.append(description)
        
        if missing_vars:
            raise ValueError(
                "Missing required environment variables:\n" + 
                "\n".join(f"- {var}" for var in missing_vars)
            )