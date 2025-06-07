from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.database import storage
from app.schemas import Ok, DepositBody, WithdrawBody, User, Instrument, OrderStatus, LimitOrder, Direction
from app.services.auth import get_admin_user


router = APIRouter()

@router.delete("/api/v1/admin/user/{user_id}", response_model=User, tags=["admin", "user"])
async def delete_user(user_id: UUID, admin_id: UUID = Depends(get_admin_user)):
    user = storage.users.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_orders = [o for o in storage.orders.values() if o.user_id == user_id]
    for order in user_orders:
        if order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            order.status = OrderStatus.CANCELLED
            if isinstance(order, LimitOrder):
                ticker = order.body.ticker
                if ticker in storage.order_books and order in storage.order_books[ticker][order.body.direction]:
                    storage.order_books[ticker][order.body.direction].remove(order)

    del storage.users[user_id]
    del storage.api_keys[user.api_key]
    if user_id in storage.balances:
        del storage.balances[user_id]

    return user


@router.post("/api/v1/admin/instrument", response_model=Ok, tags=["admin"])
async def add_instrument(instrument: Instrument, admin_id: UUID = Depends(get_admin_user)):
    if instrument.ticker in storage.instruments:
        raise HTTPException(status_code=400, detail="Instrument already exists")

    storage.instruments[instrument.ticker] = instrument
    storage.order_books[instrument.ticker] = {Direction.BUY: [], Direction.SELL: []}

    return Ok()


@router.delete("/api/v1/admin/instrument/{ticker}", response_model=Ok, tags=["admin"])
async def delete_instrument(ticker: str, admin_id: UUID = Depends(get_admin_user)):
    if ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    if ticker == "RUB":
        raise HTTPException(status_code=400, detail="Cannot delete RUB")

    # Cancel all orders for this instrument
    for order in list(storage.orders.values()):
        if order.body.ticker == ticker and order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
            order.status = OrderStatus.CANCELLED

    del storage.instruments[ticker]
    if ticker in storage.order_books:
        del storage.order_books[ticker]

    return Ok()


@router.post("/api/v1/admin/balance/deposit", response_model=Ok, tags=["admin", "balance"])
async def deposit(body: DepositBody, admin_id: UUID = Depends(get_admin_user)):
    if body.user_id not in storage.users:
        raise HTTPException(status_code=404, detail="User not found")

    if body.ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    if body.user_id not in storage.balances:
        storage.balances[body.user_id] = {}

    storage.balances[body.user_id][body.ticker] = storage.balances[body.user_id].get(body.ticker, 0) + body.amount

    return Ok()


@router.post("/api/v1/admin/balance/withdraw", response_model=Ok, tags=["admin", "balance"])
async def withdraw(body: WithdrawBody, admin_id: UUID = Depends(get_admin_user)):
    if body.user_id not in storage.users:
        raise HTTPException(status_code=404, detail="User not found")

    if body.ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    current_balance = storage.balances.get(body.user_id, {}).get(body.ticker, 0)

    if current_balance < body.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    storage.balances[body.user_id][body.ticker] = current_balance - body.amount

    return Ok()