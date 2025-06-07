from uuid import UUID, uuid4
from typing import Dict, List, Union

from app.schemas import User, Instrument, LimitOrder, MarketOrder, Direction, UserRole, Transaction


class Storage:
    def __init__(self):
        self.users: Dict[UUID, User] = {}
        self.api_keys: Dict[str, UUID] = {}
        self.instruments: Dict[str, Instrument] = {}
        self.balances: Dict[UUID, Dict[str, int]] = {}
        self.orders: Dict[UUID, Union[LimitOrder, MarketOrder]] = {}
        self.order_books: Dict[str, Dict[Direction, List[LimitOrder]]] = {}
        self.transactions: List[Transaction] = []
        self.admin_api_key = f"key-admin-{uuid4()}"

        admin_id = uuid4()
        admin = User(
            id=admin_id,
            name="admin",
            role=UserRole.ADMIN,
            api_key=self.admin_api_key
        )
        self.users[admin_id] = admin
        self.api_keys[self.admin_api_key] = admin_id
        self.instruments["RUB"] = Instrument(name="Russian Ruble", ticker="RUB")


storage = Storage()



"""import os
import psycopg2
from pydantic import BaseModel
from sqlalchemy import Column, String, UUID, Integer, ForeignKey, NullPool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BalanceDB(Base):
    __tablename__ = "balances"

    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    ticker = Column(String(10), primary_key=True)
    amount = Column(Integer, default=0)


class BalanceResponse(BaseModel):
    ticker: str
    amount: int"""