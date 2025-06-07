import asyncio
from typing import Union
from uuid import UUID
from fastapi import HTTPException
from datetime import datetime
from app.database import storage, Storage
from app.schemas import Direction, OrderStatus, Transaction, LimitOrder, MarketOrder

class MatchingEngine:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.lock = asyncio.Lock()

    async def process_order(self, order: Union[LimitOrder, MarketOrder], user_id: UUID):
        async with self.lock:
            ticker = order.body.ticker

            if ticker not in self.storage.order_books:
                self.storage.order_books[ticker] = {
                    Direction.BUY: [],
                    Direction.SELL: []
                }

            if order.body.direction == Direction.BUY:
                required_rub = order.body.qty * (
                    order.body.price if isinstance(order, LimitOrder) else self._get_best_ask_price(ticker))
                if self.storage.balances.get(user_id, {}).get("RUB", 0) < required_rub:
                    raise HTTPException(status_code=400, detail="Insufficient RUB balance")
            else:
                if self.storage.balances.get(user_id, {}).get(ticker, 0) < order.body.qty:
                    raise HTTPException(status_code=400, detail=f"Insufficient {ticker} balance")

            if isinstance(order, MarketOrder):
                await self._execute_market_order(order, user_id)
            else:
                await self._execute_limit_order(order, user_id)

    def _get_best_ask_price(self, ticker: str) -> int:
        asks = self.storage.order_books.get(ticker, {}).get(Direction.SELL, [])
        if not asks:
            raise HTTPException(status_code=400, detail="No sell orders available")
        return min(asks, key=lambda x: x.body.price).body.price

    def _get_best_bid_price(self, ticker: str) -> int:
        bids = self.storage.order_books.get(ticker, {}).get(Direction.BUY, [])
        if not bids:
            raise HTTPException(status_code=400, detail="No buy orders available")
        return max(bids, key=lambda x: x.body.price).body.price

    async def _execute_market_order(self, order: MarketOrder, user_id: UUID):
        ticker = order.body.ticker
        remaining_qty = order.body.qty

        if order.body.direction == Direction.BUY:
            opposite_orders = sorted(
                self.storage.order_books[ticker][Direction.SELL],
                key=lambda x: x.body.price
            )
        else:
            opposite_orders = sorted(
                self.storage.order_books[ticker][Direction.BUY],
                key=lambda x: x.body.price,
                reverse=True
            )

        for opposite_order in opposite_orders[:]:
            if remaining_qty <= 0:
                break

            match_qty = min(remaining_qty, opposite_order.body.qty - opposite_order.filled)
            match_price = opposite_order.body.price

            await self._execute_trade(
                order.user_id,
                opposite_order.user_id,
                ticker,
                match_qty,
                match_price,
                order.body.direction
            )

            opposite_order.filled += match_qty
            remaining_qty -= match_qty

            if opposite_order.filled >= opposite_order.body.qty:
                opposite_order.status = OrderStatus.EXECUTED
                self.storage.order_books[ticker][opposite_order.body.direction].remove(opposite_order)
            else:
                opposite_order.status = OrderStatus.PARTIALLY_EXECUTED

        if remaining_qty == 0:
            order.status = OrderStatus.EXECUTED
        else:
            raise HTTPException(status_code=400, detail="Not enough liquidity for market order")

    async def _execute_limit_order(self, order: LimitOrder, user_id: UUID):
        ticker = order.body.ticker

        if order.body.direction == Direction.BUY:
            opposite_orders = [
                o for o in self.storage.order_books[ticker][Direction.SELL]
                if o.body.price <= order.body.price
            ]
            opposite_orders.sort(key=lambda x: x.body.price)
        else:
            opposite_orders = [
                o for o in self.storage.order_books[ticker][Direction.BUY]
                if o.body.price >= order.body.price
            ]
            opposite_orders.sort(key=lambda x: x.body.price, reverse=True)

        remaining_qty = order.body.qty

        for opposite_order in opposite_orders[:]:
            if remaining_qty <= 0:
                break

            match_qty = min(remaining_qty, opposite_order.body.qty - opposite_order.filled)
            match_price = opposite_order.body.price

            await self._execute_trade(
                order.user_id,
                opposite_order.user_id,
                ticker,
                match_qty,
                match_price,
                order.body.direction
            )

            opposite_order.filled += match_qty
            order.filled += match_qty
            remaining_qty -= match_qty

            if opposite_order.filled >= opposite_order.body.qty:
                opposite_order.status = OrderStatus.EXECUTED
                self.storage.order_books[ticker][opposite_order.body.direction].remove(opposite_order)
            else:
                opposite_order.status = OrderStatus.PARTIALLY_EXECUTED

        if order.filled >= order.body.qty:
            order.status = OrderStatus.EXECUTED
        elif order.filled > 0:
            order.status = OrderStatus.PARTIALLY_EXECUTED
            self.storage.order_books[ticker][order.body.direction].append(order)
        else:
            self.storage.order_books[ticker][order.body.direction].append(order)

    async def _execute_trade(
            self,
            buyer_id: UUID,
            seller_id: UUID,
            ticker: str,
            qty: int,
            price: int,
    ):
        total_rub = qty * price

        self.storage.balances[buyer_id]["RUB"] -= total_rub
        self.storage.balances[buyer_id][ticker] = self.storage.balances[buyer_id].get(ticker, 0) + qty


        self.storage.balances[seller_id]["RUB"] = self.storage.balances[seller_id].get("RUB", 0) + total_rub
        self.storage.balances[seller_id][ticker] -= qty

        transaction = Transaction(
            ticker=ticker,
            amount=qty,
            price=price,
            timestamp=datetime.now()
        )
        self.storage.transactions.append(transaction)

matching_engine = MatchingEngine(storage)