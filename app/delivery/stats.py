from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from app.core.mongodb import get_db
from app.utils.jwt_bearer import JWTBearer

router = APIRouter(prefix="/api", tags=["Stats"])


class StatsResponse(BaseModel):
    user_id: str
    role: str
    email: str
    total_deliveries: int
    pending_deliveries: int

@router.get("/stats", response_model=StatsResponse)
async def get_user_stats(
    request: Request,
    db=Depends(get_db),
    user_data: dict = Depends(JWTBearer())
):
    user_id = user_data["user_id"]
    role = user_data["role"]
    email = user_data["email"]

    if role == "customer":
        key = "customer_id"
    elif role == "agent":
        key = "agent_id"
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    try:
        object_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    total = await db["delivery"].count_documents({key: object_user_id})
    pending = await db["delivery"].count_documents({key: object_user_id, "status": "pending"})

    return StatsResponse(
        user_id=user_id,
        role=role,
        email=email,
        total_deliveries=total,
        pending_deliveries=pending
    )


@router.get("/driver/{driver_id}/average-rating")
async def average_rating(driver_id: str, request: Request):
    """
    Calculate the average rating received by a driver.
    """
    db = get_db(request)
    feedbacks = await db["feedback"].find({"driver_id": ObjectId(driver_id)}).to_list(None)
    if not feedbacks:
        return {"driver_id": driver_id, "average_rating": 0, "total_feedbacks": 0}

    total = sum(fb["rating"] for fb in feedbacks)
    avg = round(total / len(feedbacks), 2)

    return {
        "driver_id": driver_id,
        "average_rating": avg,
        "total_feedbacks": len(feedbacks)
    }

@router.get("/customer/{customer_id}/feedback-summary")
async def customer_feedback_summary(customer_id: str, request: Request):
    """
    Get the number of feedbacks submitted by a customer.
    """
    db = get_db(request)
    count = await db["feedback"].count_documents({"customer_id": ObjectId(customer_id)})

    return {
        "customer_id": customer_id,
        "total_feedbacks_given": count
    }

@router.get("/driver/{driver_id}/completed-deliveries")
async def completed_deliveries(driver_id: str, request: Request):
    """
    Get the number of deliveries completed by a driver.
    """
    db = get_db(request)
    count = await db["delivery"].count_documents({
        "driver_id": ObjectId(driver_id),
        "status": "delivered"
    })

    return {
        "driver_id": driver_id,
        "completed_deliveries": count
    }

@router.get("/customer/{customer_id}/deliveries")
async def customer_delivery_count(customer_id: str, request: Request):
    """
    Get total number of deliveries made by a customer.
    """
    db = get_db(request)
    count = await db["delivery"].count_documents({"customer_id": ObjectId(customer_id)})

    return {
        "customer_id": customer_id,
        "total_deliveries": count
    }
