# utils/logger.py
import logging
import logging.config
import json
import os
from datetime import datetime

def setup_logging():
    """Set up logging configuration"""
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed'
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': f'logs/trading_{datetime.now().strftime("%Y%m%d")}.log',
                'level': 'INFO',
                'formatter': 'detailed'
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(logging_config)