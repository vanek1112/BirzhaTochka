from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from uuid import UUID
from app.models import UserDB, InstrumentDB, BalanceDB
from sqlalchemy.orm import Session
from app.routes.user import get_current_user

router = APIRouter(prefix="/api/v1/admin")


def verify_admin(user: UserDB = Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/user/{user_id}")
async def delete_user(
        user_id: UUID,
        db: Session = Depends(get_db),
        _: UserDB = Depends(verify_admin)
):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"status": "deleted"}


@router.post("/balance/deposit")
async def deposit_balance(
        deposit_data: dict,  # Модель Body_deposit_api_v1_admin_balance_deposit_post
        db: Session = Depends(get_db),
        _: UserDB = Depends(verify_admin)
):
    user = db.query(UserDB).filter(UserDB.id == deposit_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    balance = db.query(BalanceDB).filter(
        BalanceDB.user_id == deposit_data["user_id"],
        BalanceDB.ticker == deposit_data["ticker"]
    ).first()

    if not balance:
        balance = BalanceDB(
            user_id=deposit_data["user_id"],
            ticker=deposit_data["ticker"],
            amount=deposit_data["amount"]
        )
        db.add(balance)
    else:
        balance.amount += deposit_data["amount"]

    db.commit()
    return {"status": "success"}


@router.delete("/instrument/{ticker}")
async def delete_instrument(
        ticker: str,
        db: Session = Depends(get_db),
        _: UserDB = Depends(verify_admin)
):
    instrument = db.query(InstrumentDB).filter(InstrumentDB.ticker == ticker).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    db.delete(instrument)
    db.commit()
    return {"status": "deleted"}