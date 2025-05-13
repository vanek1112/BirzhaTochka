from fastapi import APIRouter, HTTPException, Path, Depends, HTTPException
from sqlalchemy.orm import sessionmaker, Session
from app.database import get_db
from app.models import UserDB, InstrumentDB, TransactionDB
from app.schemas import NewUser
from app.services.auth import generate_api_key
from app.services.orderbook import OrderBook
from app.database import SessionLocal

router = APIRouter()
orderbook = OrderBook()  # In-memory хранилище


@router.post("/api/v1/public/register")
async def register(user_data: NewUser):
    db = SessionLocal()

    # Генерация ключа
    raw_key, hashed_key = generate_api_key()

    # Сохранение пользователя
    new_user = UserDB(
        name=user_data.name,
        api_key=hashed_key
    )

    try:
        db.add(new_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка регистрации")
    finally:
        db.close()

    return {"api_key": raw_key}  # Возвращаем исходный ключ клиенту


@router.get("/api/v1/public/orderbook/{ticker}")
async def get_orderbook(
        ticker: str = Path(..., description="Тикер инструмента"),
        limit: int = 10
):
    if limit > 25:
        raise HTTPException(status_code=400, detail="Лимит не может превышать 25")

    return orderbook.get_l2_data(ticker, limit)

@router.get("/api/v1/public/instrument")
async def list_instruments(db: Session = Depends(get_db)):
    instruments = db.query(InstrumentDB).all()
    return [{"name": i.name, "ticker": i.ticker} for i in instruments]

@router.get("/api/v1/public/transactions/{ticker}")
async def get_transactions(ticker: str, db: Session = Depends(get_db)):
    transactions = db.query(TransactionDB).filter(TransactionDB.ticker == ticker).all()
    return transactions