import os
from sqlalchemy import Column, String, UUID, Enum, Integer, Float, ForeignKey, DateTime, NullPool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
import psycopg2

def create_psycopg2_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"))

engine = create_engine(
    "postgresql+psycopg2://",
    creator=create_psycopg2_connection,
    poolclass=NullPool
)


# Сессия для взаимодействия с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для SQLAlchemy моделей
Base = declarative_base()

def get_db() -> Session:
    """
    Генератор сессии БД для Dependency Injection в эндпоинтах.
    Гарантирует закрытие сессии после завершения запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Модель для баланса
class BalanceDB(Base):
    __tablename__ = "balances"

    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    ticker = Column(String(10), primary_key=True)
    amount = Column(Integer, default=0)


# Pydantic модель для баланса
class BalanceResponse(BaseModel):
    ticker: str
    amount: int