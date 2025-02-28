import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Определяем абсолютный путь к директории, где находится данный файл (backend/src/database)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Формируем абсолютный путь к файлу базы данных (база будет храниться в папке database)
DATABASE_PATH = os.path.join(BASE_DIR, "test.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Создаем движок подключения к SQLite (параметр connect_args обязателен для SQLite)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
