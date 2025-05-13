from collections import defaultdict, deque
from typing import Dict, Deque
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas import LimitOrder, MarketOrder


class OrderBook:
    def __init__(self):
        self.bids: Dict[int, Deque[LimitOrder]] = defaultdict(deque)  # Цена -> ордера на покупку
        self.asks: Dict[int, Deque[LimitOrder]] = defaultdict(deque)  # Цена -> ордера на продажу

    def add_order(self, order: LimitOrder):
        """Добавление лимитного ордера в стакан."""
        if order.direction == "BUY":
            self.bids[order.price].append(order)
        else:
            self.asks[order.price].append(order)

    def get_l2_data(self, ticker: str, limit: int = 10) -> dict:
        """Формирование L2 стакана для тикера."""
        sorted_bids = sorted(self.bids.items(), reverse=True)[:limit]
        sorted_asks = sorted(self.asks.items())[:limit]

        return {
            "bid_levels": [{"price": p, "qty": sum(o.qty for o in orders)} for p, orders in sorted_bids],
            "ask_levels": [{"price": p, "qty": sum(o.qty for o in orders)} for p, orders in sorted_asks]
        }

    def execute_market_order(self, order: MarketOrder, db: Session):
        if order.direction == "BUY":
            best_ask = min(self.asks.keys()) if self.asks else None
            if not best_ask:
                raise HTTPException(400, "No asks available")
            self._execute_trade(order, best_ask, db)
        else:
            best_bid = max(self.bids.keys()) if self.bids else None
            if not best_bid:
                raise HTTPException(400, "No bids available")
            self._execute_trade(order, best_bid, db)