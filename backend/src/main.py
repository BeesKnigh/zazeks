from fastapi import FastAPI
from src.api import auth
from src.database.base import Base
from src.database.session import engine

# Создаем все таблицы в базе данных (если они еще не созданы)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rock-Paper-Scissors Game API")

# Подключаем эндпоинты авторизации с префиксом /auth
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
