from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class NewUser(BaseModel):
    name: str = Field(..., min_length=3, example="Иван Иванов")

class BalanceResponse(BaseModel):
    ticker: str
    amount: int

class OrderDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class LimitOrder(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: int = Field(..., gt=0, example=10)
    price: int = Field(..., gt=0, example=100)

class MarketOrder(BaseModel):
    direction: OrderDirection
    ticker: str
    qty: int = Field(..., gt=0, example=5)

class Transaction(BaseModel):
    ticker: str
    amount: int
    price: int
    timestamp: datetime