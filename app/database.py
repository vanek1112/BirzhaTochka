from sqlalchemy import Column, String, UUID, Enum, Integer, Float, ForeignKey, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
import os
import ssl


DB_HOST = "rc1a-8mmdgrpd32sl3pug.mdb.yandexcloud.net"
DB_PORT = 6432
DB_NAME = "tochka"
DB_USER = "chernov"
DB_PASSWORD = "chernov1112"
SSL_CERT = "C:\\Users\chern\.postgresql\\root.crt"

# Получение URL БД из переменных окружения (для гибкости)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SSL-конфигурация
ssl_context = ssl.create_default_context(cafile=SSL_CERT)
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Создание движка БД
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "sslmode": "verify-full",
        "sslrootcert": SSL_CERT,
        "target_session_attrs": "read-write",
        "ssl": ssl_context
    },
    pool_pre_ping=True
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


# Добавим модель для баланса
class BalanceDB(Base):
    __tablename__ = "balances"

    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    ticker = Column(String(10), primary_key=True)
    amount = Column(Integer, default=0)


# Pydantic модель для баланса
class BalanceResponse(BaseModel):
    ticker: str
    amount: int