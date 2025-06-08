from uuid import UUID, uuid4
from typing import Dict, List, Union

from app.schemas import User, Instrument, LimitOrder, MarketOrder, Direction, UserRole, Transaction


class Storage:
    def __init__(self):
        self.users: Dict[UUID, User] = {}
        self.api_keys: Dict[str, UUID] = {}
        self.instruments: Dict[str, Instrument] = {}
        self.balances: Dict[UUID, Dict[str, int]] = {}
        self.orders: Dict[UUID, Union[LimitOrder, MarketOrder]] = {}
        self.order_books: Dict[str, Dict[Direction, List[LimitOrder]]] = {}
        self.transactions: List[Transaction] = []
        self.admin_api_key = f"key-{uuid4()}"

        admin_id = uuid4()
        admin = User(
            id=admin_id,
            name="Admin Petuh",
            role=UserRole.ADMIN,
            api_key=self.admin_api_key
        )
        self.users[admin_id] = admin
        self.api_keys[self.admin_api_key] = admin_id
        self.instruments["RUB"] = Instrument(name="Russian Ruble", ticker="RUB")


storage = Storage()