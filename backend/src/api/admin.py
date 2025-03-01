from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User, Admin
from src.security import verify_password, get_password_hash
from src.config import settings

# Для аутентификации
from fastapi.security import OAuth2PasswordBearer
import jwt

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    """
    Извлекает из JWT токена username,
    проверяет, есть ли у этого пользователя запись в таблице Admin.
    Если нет, выбрасывает 403.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
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
    # Проверяем, есть ли запись в Admin
    if not user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges",
        )
    return user.admin  # возвращаем объект Admin


# ---------------- ЭНДПОИНТЫ ----------------

@router.delete("/users/{user_id}", summary="Удаление пользователя по ID")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
    return {"msg": f"User {user_id} deleted successfully"}


@router.post("/admins", summary="Добавить пользователя в таблицу админов")
def add_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)  # только существующий админ может добавлять новых админов
):
    """
    Принимает user_id, создаёт запись в таблице Admin для указанного пользователя.
    Если запись уже существует, возвращает ошибку.
    """
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


# Новый эндпоинт: удаление записи администратора по ID пользователя
@router.delete("/admins/{user_id}", summary="Удалить запись администратора по ID")
def delete_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Удаляет запись из таблицы администраторов для указанного пользователя.
    Только администратор может выполнять это действие.
    """
    admin_record = db.query(Admin).filter(Admin.user_id == user_id).first()
    if not admin_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin record not found for this user")
    db.delete(admin_record)
    db.commit()
    return {"msg": f"Admin privileges revoked for user {user_id}"}


# Новый эндпоинт: удаление записи игры по её ID
@router.delete("/games/{game_id}", summary="Удалить запись игры по ID")
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Удаляет запись об игре по ID.
    Только администратор может удалять игровые записи.
    """
    from .src.database.models import Game  # Импорт модели Game
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    db.delete(game)
    db.commit()
    return {"msg": f"Game {game_id} deleted successfully"}


# Новый эндпоинт: удаление фото профиля пользователя (обнуление поля photo)
@router.delete("/users/{user_id}/photo", summary="Удалить фото профиля пользователя")
def delete_user_photo(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Удаляет фото профиля пользователя, устанавливая поле photo в NULL.
    Только администратор может выполнять это действие.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.photo = None
    db.commit()
    db.refresh(user)
    return {"msg": f"Profile photo for user {user.username} has been removed"}


# Новый эндпоинт: смена никнейма пользователя по ID
@router.put("/users/{user_id}/username", summary="Сменить никнейм пользователя по ID")
def change_username(
    user_id: int,
    new_username: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Изменяет никнейм пользователя по ID.
    Только администратор может выполнять это действие.
    Проверяет, что новый никнейм уникален.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Проверка уникальности нового никнейма
    existing_user = db.query(User).filter(User.username == new_username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    user.username = new_username
    db.commit()
    db.refresh(user)
    return {"msg": f"Username changed successfully to {new_username}"}
