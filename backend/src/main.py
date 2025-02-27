# src/main.py

from fastapi import FastAPI
from src.api import auth, user, game, admin
from src.database.base import Base
from src.database.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rock-Paper-Scissors Game API")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(game.router, prefix="/game", tags=["Game"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

for r in app.routes:
    print(r.path, r.name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)





