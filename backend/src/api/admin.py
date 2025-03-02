from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
import jwt

from src.database.session import get_db
from src.database.models import User, Admin, MultiplayerGame  # Обратите внимание, импортируем MultiplayerGame
from src.security import verify_password, get_password_hash
from src.config import settings
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")  # sub содержит ID пользователя
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges",
        )
    return user.admin


class AdminCreate(BaseModel):
    user_id: int


class UsernameChange(BaseModel):
    new_username: str


@router.delete("/users/{user_id}", summary="Удаление пользователя по ID")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Если пользователь имеет админские права, удаление запрещено до их отзыва
    if user.admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin user without revoking admin rights")
    
    # Удаляем все записи из таблицы MultiplayerGame, где пользователь фигурирует как player1 или player2
    games_player1 = db.query(MultiplayerGame).filter(MultiplayerGame.player1_id == user_id).all()
    for game in games_player1:
        db.delete(game)
    
    games_player2 = db.query(MultiplayerGame).filter(MultiplayerGame.player2_id == user_id).all()
    for game in games_player2:
        db.delete(game)
    
    # Если существуют иные связанные таблицы, добавьте удаление соответствующих записей здесь

    # Удаляем самого пользователя
    db.delete(user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    return {"msg": f"User {user_id} deleted successfully"}


@router.post("/admins", summary="Добавить пользователя в таблицу админов")
def add_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    user_id = admin_data.user_id
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already an admin")
    new_admin = Admin(user_id=user_id)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"msg": f"User {user_id} is now an admin"}


@router.delete("/admins/{user_id}", summary="Удалить запись администратора по ID")
def delete_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    admin_record = db.query(Admin).filter(Admin.user_id == user_id).first()
    if not admin_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin record not found for this user")
    db.delete(admin_record)
    db.commit()
    return {"msg": f"Admin privileges revoked for user {user_id}"}


@router.delete("/games/{game_id}", summary="Удалить запись игры по ID")
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    from src.database.models import Game  # Импортируем модель Game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    db.delete(game)
    db.commit()
    return {"msg": f"Game {game_id} deleted successfully"}


@router.delete("/users/{user_id}/photo", summary="Удалить фото профиля пользователя")
def delete_user_photo(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.photo = None
    db.commit()
    db.refresh(user)
    return {"msg": f"Profile photo for user {user.username} has been removed"}


@router.put("/users/{user_id}/username", summary="Сменить никнейм пользователя по ID")
def change_username(
    user_id: int,
    username_data: UsernameChange,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    new_username = username_data.new_username
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing_user = db.query(User).filter(User.username == new_username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    user.username = new_username
    db.commit()
    db.refresh(user)
    return {"msg": f"Username changed successfully to {new_username}"}
