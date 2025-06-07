"""from sqlalchemy.orm import Session
from app.models import BalanceDB
from uuid import UUID

def update_balance(
    user_id: UUID,
    ticker: str,
    amount: int,
    db: Session,
    is_deposit: bool = True  # True для пополнения, False для списания
) -> None:
    balance = db.query(BalanceDB).filter(
        BalanceDB.user_id == user_id,
        BalanceDB.ticker == ticker
    ).first()

    if not balance:
        if is_deposit:
            balance = BalanceDB(user_id=user_id, ticker=ticker, amount=amount)
            db.add(balance)
        else:
            raise ValueError("Недостаточно средств")
    else:
        if is_deposit:
            balance.amount += amount
        else:
            if balance.amount < amount:
                raise ValueError("Недостаточно средств")
            balance.amount -= amount

    db.commit()"""