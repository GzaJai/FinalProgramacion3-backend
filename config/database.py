import os
import logging
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from models.base_model import base

from models.user import User
from models.category import CategoryModel
from models.client import ClientModel
from models.product import ProductModel
from models.address import AddressModel
from models.order import OrderModel
from models.bill import BillModel
from models.order_detail import OrderDetailModel
from models.review import ReviewModel


# Get logger (logging is configured in main.py)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path, override=False)

# Database URL (Railway provides this automatically)
DATABASE_URL = os.getenv('DATABASE_URL')

# Fix Railway's "postgres://" -> "postgresql://" for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback to individual variables for local development
if not DATABASE_URL:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# High-performance connection pool configuration
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '50'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '100'))
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '10'))
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# Create engine with optimized connection pooling for high concurrency
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    echo=False,
    future=True,
)

# SessionLocal class for creating new sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    Creates a new session for each request and closes it when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    try:
        base.metadata.create_all(engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def drop_database():
    """Drop all tables in the database."""
    try:
        base.metadata.drop_all(engine)
        logger.info("Tables dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise


def check_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection established.")
        return True
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return False