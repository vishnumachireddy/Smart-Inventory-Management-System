import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("stocksense.database")

Base = declarative_base()

def get_effective_database_url() -> str:
    """
    Returns the configured database URL.
    In testing mode (TESTING=1), permits TEST_DATABASE_URL (or in-memory sqlite if explicitly designated for unit testing).
    In normal runtime, STRICTLY requires a valid Neon PostgreSQL connection string.
    """
    is_testing = os.getenv("TESTING", "").lower() in ("1", "true", "yes")
    
    if is_testing and settings.TEST_DATABASE_URL:
        return settings.TEST_DATABASE_URL
    if is_testing and not settings.is_neon_configured():
        # Fallback only permitted during automated unit test runs when TEST_DATABASE_URL isn't supplied
        return "sqlite:///:memory:"

    if not settings.is_neon_configured():
        raise RuntimeError(
            "\n" + "="*80 + "\n"
            "CRITICAL DATABASE CONFIGURATION ERROR:\n"
            "Neon Serverless PostgreSQL connection string is required!\n"
            "Please configure DATABASE_URL in your `.env` file with your Neon PostgreSQL connection string:\n"
            "DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ep-xyz-123456.us-east-2.aws.neon.tech/neondb?sslmode=require\n"
            "="*80 + "\n"
        )
    return settings.get_database_url()


def create_db_engine():
    db_url = get_effective_database_url()
    
    # Engine configuration tailored for serverless Neon PostgreSQL
    if "postgresql" in db_url:
        return create_engine(
            db_url,
            pool_pre_ping=True,     # Reconnect automatically after idle disconnects
            pool_recycle=60,        # Recycle connections every 60s to prevent stale serverless proxy connections
            pool_size=5,            # Keep pool lean to avoid Neon connection pooler limits
            max_overflow=10,
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 15,
                "keepalives_interval": 5,
                "keepalives_count": 3,
            }
        )
    else:
        # SQLite engine for isolated unit testing
        from sqlalchemy.pool import StaticPool
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )


try:
    engine = create_db_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except RuntimeError as err:
    # Allow import of models and tools even if env is not configured yet
    engine = None
    SessionLocal = None
    logger.warning(str(err))


def get_db():
    """FastAPI dependency to provide a transactional database session."""
    if SessionLocal is None:
        # Re-attempt creating engine in case env vars were set post-import
        eng = create_db_engine()
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    else:
        session_factory = SessionLocal

    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> tuple[bool, str]:
    """Verify connectivity to the database."""
    try:
        eng = create_db_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connected successfully to Neon PostgreSQL"
    except Exception as e:
        return False, str(e)
