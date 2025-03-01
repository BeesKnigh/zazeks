from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, constr
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User, MultiplayerGame
from src.api.user import get_current_user

router = APIRouter()

class MultiplayerGameCreate(BaseModel):
    player1_id: int
    player2_id: int
    player1_gesture: constr(min_length=1)
    player2_gesture: constr(min_length=1)
    result: str  # Ожидаемые значения: "player1", "player2", "draw"

@router.post("/result", summary="Сохранить результат онлайн матча")
def save_multiplayer_result(
    game: MultiplayerGameCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, что текущий пользователь участвует в матче
    if current_user.id not in [game.player1_id, game.player2_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to save this game result"
        )

    # Проверяем корректность значения результата
    if game.result not in ["player1", "player2", "draw"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid result value"
        )

    # Создаем запись о матче
    new_game = MultiplayerGame(
        player1_id=game.player1_id,
        player2_id=game.player2_id,
        player1_gesture=game.player1_gesture.lower(),
        player2_gesture=game.player2_gesture.lower(),
        result=game.result,
        timestamp=datetime.utcnow()
    )
    db.add(new_game)

    # Обновляем онлайн-статистику для обоих игроков
    player1 = db.query(User).filter(User.id == game.player1_id).first()
    player2 = db.query(User).filter(User.id == game.player2_id).first()
    if not player1 or not player2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both players not found"
        )

    # Увеличиваем количество онлайн игр для обоих игроков
    player1.online_games = (player1.online_games or 0) + 1
    player2.online_games = (player2.online_games or 0) + 1

    # Увеличиваем счет побед для победителя (если не ничья)
    if game.result == "player1":
        player1.online_wins = (player1.online_wins or 0) + 1
    elif game.result == "player2":
        player2.online_wins = (player2.online_wins or 0) + 1

    db.commit()
    db.refresh(new_game)
    return {"msg": "Multiplayer game result saved successfully", "game_id": new_game.id}
