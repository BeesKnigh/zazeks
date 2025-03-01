from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    photo = Column(String(255), nullable=True)
    wins = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    
    # Новые поля для онлайн статистики
    online_wins = Column(Integer, default=0)
    online_games = Column(Integer, default=0)

    # Связь с историей оффлайн игр
    games = relationship("Game", back_populates="user", cascade="all, delete-orphan")

    # Связь с админской записью (если есть)
    admin = relationship("Admin", back_populates="user", uselist=False)

    # Связи с онлайн матчами: когда пользователь является игроком 1 или игроком 2
    multiplayer_games_as_player1 = relationship("MultiplayerGame", foreign_keys="[MultiplayerGame.player1_id]", back_populates="player1")
    multiplayer_games_as_player2 = relationship("MultiplayerGame", foreign_keys="[MultiplayerGame.player2_id]", back_populates="player2")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_choice = Column(String(10), nullable=False)      # rock, paper, scissors
    computer_choice = Column(String(10), nullable=False)  # rock, paper, scissors
    result = Column(String(10), nullable=False)           # win, loss, draw
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="games")


class Admin(Base):
    """
    Запись в этой таблице означает, что User обладает правами администратора.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Связь с моделью User
    user = relationship("User", back_populates="admin")


class MultiplayerGame(Base):
    """
    Модель для хранения результатов онлайн матчей.
    Содержит идентификаторы обоих игроков, их жесты, результат матча и временную метку.
    Ожидаемые значения поля result: "player1", "player2" или "draw"
    """
    __tablename__ = "multiplayer_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player1_gesture = Column(String(10), nullable=False)
    player2_gesture = Column(String(10), nullable=False)
    result = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    player1 = relationship("User", foreign_keys=[player1_id], back_populates="multiplayer_games_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="multiplayer_games_as_player2")
