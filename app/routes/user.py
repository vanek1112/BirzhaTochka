from datetime import datetime
from typing import Union, List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from app.database import storage
from app.schemas import (CreateOrderResponse, Ok, LimitOrderBody, MarketOrderBody, LimitOrder, MarketOrder, OrderStatus)
from app.services.auth import get_current_user
from app.services.orderbook import matching_engine

router = APIRouter()


@router.post("/api/v1/order", response_model=CreateOrderResponse, tags=["order"])
async def create_order(
        body: Union[LimitOrderBody, MarketOrderBody],
        user_id: UUID = Depends(get_current_user)
):
    if body.ticker not in storage.instruments:
        raise HTTPException(status_code=404, detail="Instrument not found")

    order_id = uuid4()
    timestamp = datetime.now()

    if isinstance(body, MarketOrderBody):
        order = MarketOrder(
            id=order_id,
            status=OrderStatus.NEW,
            user_id=user_id,
            timestamp=timestamp,
            body=body
        )
    else:
        order = LimitOrder(
            id=order_id,
            status=OrderStatus.NEW,
            user_id=user_id,
            timestamp=timestamp,
            body=body,
            filled=0
        )

    storage.orders[order_id] = order

    try:
        await matching_engine.process_order(order, user_id)
    except Exception as e:
        del storage.orders[order_id]
        raise e

    return CreateOrderResponse(order_id=order_id)


@router.get("/api/v1/order", response_model=List[Union[LimitOrder, MarketOrder]], tags=["order"])
async def list_orders(user_id: UUID = Depends(get_current_user)):
    user_orders = [
        order for order in storage.orders.values()
        if order.user_id == user_id and order.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]
    ]
    return user_orders


@router.get("/api/v1/order/{order_id}", response_model=Union[LimitOrder, MarketOrder], tags=["order"])
async def get_order(order_id: UUID, user_id: UUID = Depends(get_current_user)):
    order = storage.orders.get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your order")

    return order


@router.delete("/api/v1/order/{order_id}", response_model=Ok, tags=["order"])
async def cancel_order(order_id: UUID, user_id: UUID = Depends(get_current_user)):
    order = storage.orders.get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your order")

    if order.status not in [OrderStatus.NEW, OrderStatus.PARTIALLY_EXECUTED]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    if isinstance(order, LimitOrder):
        ticker = order.body.ticker
        if ticker in storage.order_books and order in storage.order_books[ticker][order.body.direction]:
            storage.order_books[ticker][order.body.direction].remove(order)

    order.status = OrderStatus.CANCELLED

    return Ok()