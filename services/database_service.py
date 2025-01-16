# services/database_service.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict
import logging

class DatabaseService:
    def __init__(self, config: Dict):
        self.engine = create_engine(config['database']['url'])
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger(__name__)

    def store_market_data(self, data: Dict):
        session = self.Session()
        try:
            # Implement storage logic
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database error: {str(e)}")
        finally:
            session.close()