from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from app.core.mongodb import get_db
from app.utils.jwt_bearer import JWTBearer

router = APIRouter(prefix="/api", tags=["Stats"])

@router.get("/driver/{driver_id}/average-rating")
async def average_rating(driver_id: str, request: Request):
    """
    Calculate the average rating received by a specific driver based on feedback.

    Args:
        driver_id (str): The driver's user ID.

    Returns:
        dict: Contains driver_id, average_rating, and total_feedbacks.
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
    Retrieve the number of feedback entries submitted by a customer.

    Args:
        customer_id (str): The customer's user ID.

    Returns:
        dict: Contains customer_id and total_feedbacks_given.
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
    Get the number of completed and pending deliveries for a specific driver.

    Args:
        driver_id (str): The driver's user ID.

    Returns:
        dict: Completed and pending delivery counts for the driver.
    """
    db = get_db(request)
    delivered = await db["delivery"].count_documents({"driver_id": ObjectId(driver_id), "status": "delivered"})
    pending = await db["delivery"].count_documents({"driver_id": ObjectId(driver_id), "status": "pending"})

    return {
        "driver_id": driver_id,
        "completed_deliveries": delivered,
        "pending_deliveries": pending
    }

@router.get("/customer/{customer_id}/deliveries")
async def customer_delivery_count(customer_id: str, request: Request):
    """
    Retrieve detailed delivery status counts for a specific customer.

    Args:
        customer_id (str): The customer's user ID.

    Returns:
        dict: Contains total, pending, accepted, in-transit, and completed deliveries.
    """
    db = get_db(request)
    oid = ObjectId(customer_id)
    total = await db["delivery"].count_documents({"customer_id": oid})
    pending = await db["delivery"].count_documents({"customer_id": oid, "status": "pending"})
    accepted = await db["delivery"].count_documents({"customer_id": oid, "status": "accepted"})
    in_transit = await db["delivery"].count_documents({"customer_id": oid, "status": "in-transit"})
    completed = await db["delivery"].count_documents({"customer_id": oid, "status": "delivered"})

    return {
        "customer_id": customer_id,
        "total_deliveries": total,
        "pending": pending,
        "accepted": accepted,
        "in_transit": in_transit,
        "completed": completed
    }
