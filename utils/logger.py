# utils/logger.py
import logging
import logging.config
import json
import os
from datetime import datetime

def setup_logging(config_path: str = 'config/logging_config.json'):
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Check if config file exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
                # Check if file is not empty
                if content.strip():
                    config = json.loads(content)
                    logging.config.dictConfig(config)
                else:
                    use_default_config()
        else:
            use_default_config()

    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        use_default_config()

def use_default_config():
    """Set up default logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
            ),
            logging.StreamHandler()
        ]
    )