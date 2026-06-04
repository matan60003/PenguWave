from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings

# Create the SQLAlchemy engine with a robust connection pool configuration:
# 1. pool_pre_ping=True: Executes a test query ('ping') before each checkout from the pool.
#    If a database connection has died (e.g., due to DB restart), it recycles it safely.
# 2. pool_size=5: Number of persistent connections kept in the pool.
# 3. max_overflow=10: Max temporary connections opened when load exceeds pool_size.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Factory to generate new Session objects bound to our engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency injection provider that yields a database session.
    Ensures that the session is closed at the end of the request lifecycle,
    returning it to the connection pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
