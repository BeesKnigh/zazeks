from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    photo = Column(String(255))  # URL фотографии профиля
    wins = Column(Integer, default=0)
    games_played = Column(Integer, default=0)

    # Связь с историей игр
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_choice = Column(String(10), nullable=False)      # rock, paper, scissors
    computer_choice = Column(String(10), nullable=False)    # rock, paper, scissors
    result = Column(String(10), nullable=False)             # win, loss, draw
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", back_populates="games")
