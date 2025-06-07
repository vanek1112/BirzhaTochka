from typing import List
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from app.database import storage
from app.schemas import (NewUser, User, UserRole, Instrument,
                         L2OrderBook, Direction, OrderStatus, Level, Transaction)

router = APIRouter()


@router.post("/api/v1/public/register", response_model=User, tags=["public"])
async def register(new_user: NewUser):
    user_id = uuid4()
    api_key = f"key-{uuid4()}"

    user = User(
        id=user_id,
        name=new_user.name,
        role=UserRole.USER,
        api_key=api_key
    )

    storage.users[user_id] = user
    storage.api_keys[api_key] = user_id
    storage.balances[user_id] = {"RUB": 0}

    return user


@router.get("/api/v1/public/instrument", response_model=List[Instrument], tags=["public"])
async def list_instruments():
    return list(storage.instruments.values())


@router.get("/api/v1/public/orderbook/{ticker}", response_model=L2OrderBook, tags=["public"])
async def get_orderbook(ticker: str, limit: int = 10):
    if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    order_book = storage.order_books.get(ticker, {Direction.BUY: [], Direction.SELL: []})

    bid_levels = {}
    ask_levels = {}

    for order in order_book[Direction.BUY]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            bid_levels[price] = bid_levels.get(price, 0) + qty

    for order in order_book[Direction.SELL]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            ask_levels[price] = ask_levels.get(price, 0) + qty

    bids = sorted([Level(price=p, qty=q) for p, q in bid_levels.items()], key=lambda x: x.price, reverse=True)[:limit]
    asks = sorted([Level(price=p, qty=q) for p, q in ask_levels.items()], key=lambda x: x.price)[:limit]

    return L2OrderBook(bid_levels=bids, ask_levels=asks)


@router.get("/api/v1/public/transactions/{ticker}", response_model=List[Transaction], tags=["public"])
async def get_transaction_history(ticker: str, limit: int = 10):
    if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    ticker_transactions = [t for t in storage.transactions if t.ticker == ticker]
    return sorted(ticker_transactions, key=lambda x: x.timestamp, reverse=True)[:limit]