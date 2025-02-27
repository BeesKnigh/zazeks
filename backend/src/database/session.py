from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings

# Для SQLite обязательно нужно указать параметр connect_args
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
