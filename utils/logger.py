# utils/logger.py
import logging
import logging.config
import json
import os
from datetime import datetime

def setup_logging(config_path: str = 'config/logging_config.json'):
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )