# main.py
import asyncio
import json
import logging
from pathlib import Path
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logging

async def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config_path = Path('config/config.json')
        with config_path.open('r') as f:
            config = json.load(f)
        
        # Initialize and run the coordinator agent
        coordinator = CoordinatorAgent(config)
        await coordinator.run()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down trading system...")