from sqlalchemy import Column, String, UUID, Enum, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum as PyEnum
import uuid
from app.schemas import OrderDirection


Base = declarative_base()


# Enums
class UserRole(str, PyEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class OrderType(str, PyEnum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, PyEnum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


# SQLAlchemy Models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)

    orders = relationship("OrderDB", back_populates="user")


class BalanceDB(Base):
    __tablename__ = "balances"

    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    ticker = Column(String(10), primary_key=True)
    amount = Column(Integer, default=0)


class InstrumentDB(Base):
    __tablename__ = "instruments"

    ticker = Column(String(10), primary_key=True, nullable=False)
    name = Column(String(100), nullable=False)


class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(10), nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    price = Column(Float)
    qty = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserDB", back_populates="orders")


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False)
    amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    order_id = Column(UUID, ForeignKey("orders.id"))


# Pydantic Models
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, example="John Doe")


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: UserRole
    api_key: str


class InstrumentCreate(BaseModel):
    name: str
    ticker: str = Field(..., pattern=r"^[A-Z]{2,10}$")


class OrderCreate(BaseModel):
    ticker: str
    type: OrderType
    direction: OrderDirection
    price: float | None = Field(None, gt=0)
    qty: int = Field(gt=0)

    @validator("price")
    def validate_price(cls, v, values):
        if values["type"] == OrderType.LIMIT and v is None:
            raise ValueError("Price is required for LIMIT orders")
        return v


class TransactionResponse(BaseModel):
    ticker: str
    amount: int
    price: float
    timestamp: datetime

class DepositRequest(BaseModel):
    user_id: uuid.UUID
    ticker: str
    amount: int = Field(..., gt=0)

class WithdrawRequest(BaseModel):
    user_id: uuid.UUID
    ticker: str
    amount: int = Field(..., gt=0)