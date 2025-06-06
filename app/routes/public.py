from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.database import get_db
from app.models import UserDB, InstrumentDB, TransactionDB, UserRole
from app.schemas import NewUser
from app.services.auth import generate_api_key
from app.services.orderbook import OrderBook


router = APIRouter()
orderbook = OrderBook()


@router.post("/api/v1/public/register")
async def register(user_data: NewUser):
    db = SessionLocal()

    raw_key, hashed_key = generate_api_key()

    new_user = UserDB(
        name=user_data.name,
        api_key=hashed_key,
        role=UserRole.USER
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка регистрации")
    finally:
        db.close()

    return {
        "id": str(new_user.id),
        "name": new_user.name,
        "role": new_user.role.value,
        "api_key": raw_key
    }


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