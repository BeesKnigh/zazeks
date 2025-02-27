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
    # Добавьте другие поля, если нужно обновлять больше данных

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

@router.get("/leaderboard", summary="Получить лидерборд")
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.wins.desc()).all()
    result = []
    for u in users:
        result.append({
            "username": u.username,
            "photo": u.photo,
            "wins": u.wins
        })
    return result

@router.get("/{user_id}", summary="Получить всю информацию о пользователе по ID")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает информацию о пользователе по его ID (кроме пароля).
    По умолчанию доступ только авторизованным пользователям.
    При необходимости можно добавить проверку прав (admin / тот же user).
    """
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


@router.put("/{user_id}", summary="Полностью заменить профиль пользователя (PUT)")
def update_user_profile(
    user_id: int,
    user_data: UserProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Полностью заменяет профиль пользователя (PUT).
    Можно сменить username, photo и т.д.
    По умолчанию разрешаем только самому пользователю
    (либо администратору, если такое предусмотрено).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Если у вас нет роли "admin", то проверяем, тот ли это пользователь
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

    # Обновляем поля (username, photo) — только если они переданы
    if user_data.username is not None:
        # Убедитесь, что не нарушаете уникальность username,
        # если пользователь меняет имя на уже существующее.
        # Для упрощения примера опускаем эту проверку.
        user.username = user_data.username

    if user_data.photo is not None:
        user.photo = user_data.photo

    db.commit()
    db.refresh(user)
    return {
        "msg": "User updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "photo": user.photo
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
    - Пользователь (или админ, если у вас есть такая логика)
      может поменять пароль, зная старый пароль.
    - Если текущий пользователь не совпадает с логином,
      бросаем 403 (если нет admin-ролей).
    """
    user = db.query(User).filter(User.username == data.login).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Проверка прав: если текущий пользователь != data.login
    # (и при условии, что у нас нет понятия admin),
    # то запрещаем смену пароля:
    if current_user.username != data.login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )

    # Проверяем старый пароль
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid old password"
        )

    # Устанавливаем новый пароль
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    db.refresh(user)
    return {"msg": "Password changed successfully"}