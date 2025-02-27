from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
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
    Если нет, выбрасываем 403.
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
        # admin здесь фактически не используем,
        # но наличие зависимости гарантирует, что только админ сможет вызвать эндпоинт
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
