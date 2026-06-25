from datetime import datetime, timezone
from typing import Dict, Optional, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Notification API", version="1.0.0")

notifications: Dict[str, dict] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


ChannelType = Literal["email", "sms", "push"]
DeliveryStatus = Literal["PENDING", "DELIVERED", "FAILED"]


class NotificationCreate(BaseModel):
    channel: ChannelType
    recipient: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=1000)
    simulate_failure: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/notifications/send", status_code=201)
def send_notification(payload: NotificationCreate):
    notification_id = str(uuid4())

    status: DeliveryStatus = "FAILED" if payload.simulate_failure else "DELIVERED"

    notification = {
        "id": notification_id,
        "channel": payload.channel,
        "recipient": payload.recipient,
        "message": payload.message,
        "status": status,
        "attempt_count": 1,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    notifications[notification_id] = notification
    return notification


@app.get("/notifications")
def list_notifications(status: Optional[str] = Query(default=None)):
    result = list(notifications.values())
    if status:
        result = [n for n in result if n["status"] == status.upper()]
    return result


@app.get("/notifications/{notification_id}")
def get_notification(notification_id: str):
    notification = notifications.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@app.get("/notifications/{notification_id}/status")
def get_notification_status(notification_id: str):
    notification = notifications.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "id": notification_id,
        "status": notification["status"],
        "attempt_count": notification["attempt_count"],
    }


@app.post("/notifications/{notification_id}/retry")
def retry_failed_notification(notification_id: str):
    notification = notifications.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification["status"] != "FAILED":
        return {
            "id": notification_id,
            "status": notification["status"],
            "message": "Notification is not failed, retry not needed",
        }

    notification["attempt_count"] += 1
    notification["status"] = "DELIVERED"
    notification["updated_at"] = utc_now()
    notifications[notification_id] = notification

    return {
        "id": notification_id,
        "status": notification["status"],
        "attempt_count": notification["attempt_count"],
    }