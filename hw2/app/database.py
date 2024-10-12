import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError


SQLALCHEMY_DATABASE_URL = "postgresql://myuser:mypassword@db/online_store"

engine = None
retry_attempts = 10

for attempt in range(retry_attempts):
    try:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=50,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        break
    except OperationalError:
        print("Database not ready, retrying in 2 seconds...")
        time.sleep(30)
else:
    raise Exception("Could not connect to the database after 10 retries.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
