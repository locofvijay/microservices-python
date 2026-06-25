from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Order API", version="1.0.0")

orders: Dict[str, dict] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderItem(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    items: List[OrderItem]
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(CREATED|CONFIRMED|SHIPPED|DELIVERED|CANCELLED)$")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders", status_code=201)
def create_order(payload: OrderCreate):
    order_id = str(uuid4())
    total_amount = round(
        sum(item.quantity * item.unit_price for item in payload.items),
        2
    )

    order = {
        "id": order_id,
        "customer_id": payload.customer_id,
        "items": [item.model_dump() for item in payload.items],
        "total_amount": total_amount,
        "status": "CREATED",
        "notes": payload.notes,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    orders[order_id] = order
    return order


@app.get("/orders")
def list_orders(customer_id: Optional[str] = Query(default=None)):
    result = list(orders.values())
    if customer_id:
        result = [o for o in result if o["customer_id"] == customer_id]
    return result


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"id": order_id, "status": order["status"]}


@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: str, payload: OrderStatusUpdate):
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order["status"] = payload.status
    order["updated_at"] = utc_now()
    orders[order_id] = order
    return {"id": order_id, "status": order["status"], "updated_at": order["updated_at"]}


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    del orders[order_id]
    return None