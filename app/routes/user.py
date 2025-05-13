from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import get_db
from app.models import BalanceDB, OrderDB, UserDB, OrderCreate, OrderStatus, InstrumentDB, OrderType
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter()


def get_current_user(api_key: str = Header(..., alias="Authorization"), db: Session = Depends(get_db)):
    if not api_key.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    raw_key = api_key.split(" ")[1]
    user = db.query(UserDB).filter(UserDB.api_key == raw_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/api/v1/balance")
async def get_balance(
        user: UserDB = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> dict:
    balances = db.query(BalanceDB).filter(BalanceDB.user_id == user.id).all()
    return {b.ticker: b.amount for b in balances}


@router.post("/api/v1/order")
async def create_order(
        order_data: OrderCreate,
        user: UserDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Проверка инструмента
    instrument = db.query(InstrumentDB).filter(InstrumentDB.ticker == order_data.ticker).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    # Создание ордера
    new_order = OrderDB(
        user_id=user.id,
        ticker=order_data.ticker,
        type=order_data.type,
        price=order_data.price,
        qty=order_data.qty,
        status=OrderStatus.NEW
    )

    db.add(new_order)
    db.commit()

    # Логика исполнения ордера (упрощённо)
    if order_data.type == OrderType.MARKET:
        # Исполнение по рыночной цене (заглушка)
        pass

    return {"order_id": new_order.id}


@router.get("/api/v1/order")
async def list_orders(
        user: UserDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    orders = db.query(OrderDB).filter(
        OrderDB.user_id == user.id,
        OrderDB.status.in_([OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED])
    ).all()
    return orders


@router.delete("/api/v1/order/{order_id}")
async def cancel_order(
        order_id: UUID,
        user: UserDB = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    order = db.query(OrderDB).filter(
        OrderDB.id == order_id,
        OrderDB.user_id == user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = OrderStatus.CANCELLED
    db.commit()
    return {"status": "cancelled"}