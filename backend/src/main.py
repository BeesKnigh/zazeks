from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, user, game, admin, model_inference, multiplayer
from src.database.base import Base
from src.database.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rock-Paper-Scissors Game API",
    websocket_origins=["http://localhost", "http://localhost:5500", "null"]
)

origins = [
    "*",  # можно заменить на список конкретных хостов
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(game.router, prefix="/game", tags=["Game"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(model_inference.router, prefix="/model", tags=["Model"])
app.include_router(multiplayer.router)  # WebSocket‑маршруты мультиплеера

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
