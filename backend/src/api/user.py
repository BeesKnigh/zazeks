# src/api/user.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from src.database.session import get_db
from src.database.models import User
from src.security import verify_password, get_password_hash
from src.config import settings
import jwt
import base64
import imghdr

router = APIRouter()

# Используем OAuth2PasswordBearer, указывая эндпоинт логина:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------------------------
# Вспомогательные схемы (Pydantic)
# ---------------------------

class UserProfile(BaseModel):
    """Схема для полного обновления профиля (с нуля)."""
    username: Optional[str] = None
    photo: Optional[str] = None
    # Если нужно обновлять больше данных, можно добавить поля

class PasswordChange(BaseModel):
    """Схема для смены пароля по логину."""
    login: str
    old_password: str
    new_password: str

# ---------------------------
# Вспомогательные функции
# ---------------------------

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Извлекает текущего пользователя из JWT-токена.
    - Декодирует токен, получает username (sub).
    - Ищет пользователя в базе по username.
    - Если что-то не так, выбрасывает исключение HTTP 401.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
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

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

# ---------------------------
# Эндпоинты
# ---------------------------

@router.get("/leaderboard/offline", summary="Получить оффлайн лидерборд (игры против бота)")
def get_offline_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.wins.desc()).all()
    result = []
    for u in users:
        result.append({
            "username": u.username,
            "photo": u.photo,
            "wins": u.wins
        })
    return result

@router.get("/leaderboard/online", summary="Получить онлайн лидерборд (игры против игроков)")
def get_online_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.online_wins.desc()).all()
    result = []
    for u in users:
        result.append({
            "username": u.username,
            "photo": u.photo,
            "online_wins": u.online_wins
        })
    return result

@router.get("/{user_id}", summary="Получить всю информацию о пользователе по ID")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает информацию о пользователе по его ID.
    Теперь доступ разрешён только владельцу аккаунта.
    """
    # Если ID запрашиваемого пользователя не совпадает с текущим пользователем — запрещаем
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this profile"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "username": user.username,
        "photo": user.photo,
        "wins": user.wins,
        "games_played": user.games_played,
        "online_wins": user.online_wins,
        "online_games": user.online_games,
    }

@router.get("/{user_id}/avatar", summary="Получить аватар пользователя по ID")
def get_user_avatar(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает аватар (URL) пользователя по его ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"photo": user.photo}

MAX_IMAGE_SIZE_MB = 5  # Максимальный размер 5MB
ALLOWED_IMAGE_TYPES = {"jpeg", "png"}  # Разрешённые форматы

@router.put("/{user_id}", summary="Полностью заменить профиль пользователя (PUT)")
def update_user_profile(
        user_id: int,
        user_data: UserProfile,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Полностью заменяет профиль пользователя (PUT), включая обновление фото.
    По умолчанию разрешаем только самому пользователю.
    Добавлены проверки:
    - Формат фото: только PNG или JPEG
    - Размер фото: не более 5MB
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Проверяем, может ли текущий пользователь обновлять этот профиль
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

    # Проверка фото (если передано)
    if user_data.photo is not None:
        try:
            # Убираем "data:image/png;base64," из строки base64
            header, encoded = user_data.photo.split(",", 1)

            # Декодируем base64
            decoded_img = base64.b64decode(encoded)

            # Проверяем размер (в байтах)
            if len(decoded_img) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image size exceeds 5MB"
                )

            # Определяем формат файла (png, jpeg)
            img_format = imghdr.what(None, decoded_img)
            if img_format not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PNG and JPG images are allowed"
                )

            # Если всё ок, сохраняем фото в БД
            user.photo = user_data.photo

        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )

    # Обновляем другие данные, если переданы
    if user_data.username is not None:
        user.username = user_data.username

    db.commit()
    db.refresh(user)
    return {
        "msg": "User updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "photo": user.photo,
            "wins": user.wins,
            "games_played": user.games_played,
            "online_wins": user.online_wins,
            "online_games": user.online_games,
        }
    }

@router.put("/change-password", summary="Изменить пароль по логину")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Смена пароля по логину:
    - Пользователь (или админ) может поменять пароль, зная старый пароль.
    - Если текущий пользователь не совпадает с логином, бросаем 403.
    """
    user = db.query(User).filter(User.username == data.login).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if current_user.username != data.login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid old password"
        )

    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    db.refresh(user)
    return {"msg": "Password changed successfully"}
