from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User, Game
from src.api.user import get_current_user  # или ваш метод получения текущего пользователя

router = APIRouter()

# ---------- Pydantic-схемы ----------

class GameCreate(BaseModel):
    """Схема для создания записи об игре"""
    user_choice: str  # 'rock', 'paper', 'scissors'
    computer_choice: str  # 'rock', 'paper', 'scissors'
    result: str  # 'win', 'loss', 'draw'

class GameResponse(BaseModel):
    """Схема для ответа при получении игры"""
    id: int
    user_id: int
    user_choice: str
    computer_choice: str
    result: str

    class Config:
        orm_mode = True

# ---------- ЭНДПОИНТЫ ----------

@router.post("/", response_model=GameResponse, summary="Сохранить игру в историю")
def create_game(
    game_data: GameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Сохраняет информацию об одной сыгранной игре.
    Также можно обновить статистику пользователя (games_played, wins).
    """

    # Создаем запись об игре
    new_game = Game(
        user_id=current_user.id,
        user_choice=game_data.user_choice,
        computer_choice=game_data.computer_choice,
        result=game_data.result
    )
    db.add(new_game)

    # Обновляем статистику пользователя
    current_user.games_played += 1
    if game_data.result == "win":
        current_user.wins += 1

    db.commit()
    db.refresh(new_game)
    db.refresh(current_user)

    return new_game  # FastAPI преобразует в GameResponse


@router.get("/{game_id}", response_model=GameResponse, summary="Получить игру по ID")
def get_game_by_id(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает информацию об игре с указанным ID (если игра принадлежит текущему пользователю
    или если требуется доп. логика для админа).
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    # Если вы хотите запретить другим пользователям смотреть чужие игры,
    # можно добавить проверку
    if game.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    return game


@router.get("/user/{user_id}", summary="Получить все игры пользователя по ID")
def get_all_games_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает список всех игр для пользователя с указанным ID.
    Если нужно, проверяем права: либо сам пользователь, либо админ.
    """
    if current_user.id != user_id:
        # Можно дополнительно проверить, есть ли у current_user роль "admin"
        # Для простоты примера бросаем 403
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    games = db.query(Game).filter(Game.user_id == user_id).all()
    return games  # Список игр (можно вернуть pydantic-модель, если хотите структурированный ответ)


@router.put("/add-win/{user_id}", summary="Начисление очков победы по ID")
def add_win(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Увеличивает счетчик побед у пользователя (с учетом проверки прав, если нужно).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Проверка прав - например, только сам пользователь или администратор может это делать
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    user.wins += 1
    db.commit()
    db.refresh(user)
    return {"msg": f"User {user.username} now has {user.wins} wins."}
