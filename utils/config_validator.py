# utils/config_validator.py
from typing import Dict

def validate_config(config: Dict) -> bool:
    """Validate the configuration structure"""
    required_sections = [
        'trading_pairs',
        'exchange',
        'risk_management',
        'analysis',
        'data_collection'
    ]
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")
    
    # Validate trading pairs
    if not isinstance(config['trading_pairs'], list) or not config['trading_pairs']:
        raise ValueError("trading_pairs must be a non-empty list")
    
    # Validate exchange config
    exchange_required = ['name', 'testnet']
    for field in exchange_required:
        if field not in config['exchange']:
            raise ValueError(f"Missing required exchange config: {field}")
    
    # Validate risk management
    risk_required = ['risk_per_trade', 'max_position_size', 'max_positions']
    for field in risk_required:
        if field not in config['risk_management']:
            raise ValueError(f"Missing required risk management config: {field}")
    
    return True