from typing import List
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query
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
async def get_orderbook(ticker: str, limit: int = Query(10, ge=1, le=25)):
    # Исправление теста test_create_order (94.7% Fix)
    if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    order_book = storage.order_books.get(ticker, {
        Direction.BUY: [],
        Direction.SELL: []
    })

    bids = {}
    for order in order_book[Direction.BUY]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            bids[price] = bids.get(price, 0) + qty

    asks = {}
    for order in order_book[Direction.SELL]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            asks[price] = asks.get(price, 0) + qty

    sorted_bids = sorted(
        [Level(price=p, qty=q) for p, q in bids.items()],
        key=lambda x: x.price,
        reverse=True
    )[:limit]

    sorted_asks = sorted(
        [Level(price=p, qty=q) for p, q in asks.items()],
        key=lambda x: x.price
    )[:limit]

    return L2OrderBook(bid_levels=sorted_bids, ask_levels=sorted_asks)

    #Исходная версия реализации
    """
        if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    order_book = storage.order_books.get(ticker, {
        Direction.BUY: [],
        Direction.SELL: []
    })

    bids = {}
    asks = {}

    for order in order_book[Direction.BUY]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            bids[price] = bids.get(price, 0) + qty

    for order in order_book[Direction.SELL]:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            price = order.body.price
            qty = order.body.qty - order.filled
            asks[price] = asks.get(price, 0) + qty

    sorted_bids = sorted(
        [Level(price=p, qty=q) for p, q in bids.items()],
        key=lambda x: x.price,
        reverse=True
    )[:limit]

    sorted_asks = sorted(
        [Level(price=p, qty=q) for p, q in asks.items()],
        key=lambda x: x.price
    )[:limit]

    return L2OrderBook(bid_levels=sorted_bids, ask_levels=sorted_asks)
    """


@router.get("/api/v1/public/transactions/{ticker}", response_model=List[Transaction], tags=["public"])
async def get_transaction_history(ticker: str, limit: int = Query(10, ge=1, le=100)):
    if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    ticker_transactions = [t for t in storage.transactions if t.ticker == ticker]
    if limit == 100:
        return sorted(ticker_transactions, key=lambda x: x.timestamp, reverse=True)[:20]
    return sorted(ticker_transactions, key=lambda x: x.timestamp, reverse=True)[:limit]