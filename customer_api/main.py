from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Customer API", version="1.0.0")

customers: Dict[str, dict] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class CustomerStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACTIVE|INACTIVE|SUSPENDED)$")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/customers", status_code=201)
def create_customer(payload: CustomerCreate):
    customer_id = str(uuid4())
    customer = {
        "id": customer_id,
        "name": payload.name,
        "email": payload.email.lower(),
        "phone": payload.phone,
        "status": "ACTIVE",
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    customers[customer_id] = customer
    return customer


@app.get("/customers")
def list_customers(
    email: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    result = list(customers.values())

    if email:
        result = [c for c in result if c["email"] == email.lower()]

    if status:
        result = [c for c in result if c["status"] == status.upper()]

    return result


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    customer = customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.get("/customers/search")
def search_customer_by_email(email: str):
    email = email.lower()
    matches = [c for c in customers.values() if c["email"] == email]
    if not matches:
        raise HTTPException(status_code=404, detail="Customer not found")
    return matches[0]


@app.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate):
    customer = customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if payload.name is not None:
        customer["name"] = payload.name
    if payload.email is not None:
        customer["email"] = payload.email.lower()
    if payload.phone is not None:
        customer["phone"] = payload.phone

    customer["updated_at"] = utc_now()
    customers[customer_id] = customer
    return customer


@app.patch("/customers/{customer_id}/status")
def update_customer_status(customer_id: str, payload: CustomerStatusUpdate):
    customer = customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer["status"] = payload.status
    customer["updated_at"] = utc_now()
    customers[customer_id] = customer
    return {"id": customer_id, "status": customer["status"], "updated_at": customer["updated_at"]}


@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: str):
    if customer_id not in customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    del customers[customer_id]
    return None