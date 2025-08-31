"""
Database configuration and initialization
"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

logger = logging.getLogger('juniorgpt.database')

# Create declarative base
Base = declarative_base()

class Database:
    """Database manager class"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.session = None
        
    def init_app(self, database_url: str, echo: bool = False):
        """Initialize database with Flask app or standalone"""
        try:
            # Handle SQLite special configuration
            if database_url.startswith('sqlite'):
                # Ensure directory exists
                db_path = database_url.replace('sqlite:///', '')
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    
                # SQLite specific engine configuration
                self.engine = create_engine(
                    database_url,
                    echo=echo,
                    poolclass=StaticPool,
                    connect_args={
                        'check_same_thread': False,
                        'timeout': 20
                    },
                    pool_pre_ping=True
                )
            else:
                # PostgreSQL/MySQL configuration
                self.engine = create_engine(
                    database_url,
                    echo=echo,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
            
            # Create session factory
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            
            logger.info(f"Database initialized: {database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_all(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_all(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_scoped_session(self):
        """Get scoped session for thread-safe operations"""
        return self.Session()
    
    def close(self):
        """Close database connections"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")

# Global database instance
db = Database()

def init_db(database_url: str, echo: bool = False):
    """Initialize database"""
    db.init_app(database_url, echo)
    
    # Import all models to ensure they're registered
    from . import conversation, agent, team
    
    # Create tables
    db.create_all()
    
    return db