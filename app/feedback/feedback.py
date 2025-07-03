from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
from app.core.mongodb import get_db
from app.utils.jwt_bearer import JWTBearer 
from app.models.feedback_model import Feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])
collection_name = "feedback"
delivery_collection = "delivery"

def fix_feedback_id(feedback):
    feedback["id"] = str(feedback["_id"])
    del feedback["_id"]
    return feedback

def fix_feedback_id(feedback):
    feedback["id"] = str(feedback["_id"])
    del feedback["_id"]
    feedback["delivery_id"] = str(feedback["delivery_id"])
    feedback["customer_id"] = str(feedback["customer_id"])
    feedback["driver_id"] = str(feedback["driver_id"])
    feedback["timestamp"] = feedback["timestamp"].isoformat()
    return feedback

@router.post("/submit", response_model=Feedback)
async def submit_feedback(feedback: Feedback, request: Request, user_data: dict = Depends(JWTBearer())):
    """
    Submit feedback for a delivered order.

    Requirements:
    - Only authenticated users with role 'customer' can submit.
    - The delivery must exist and be marked as 'Delivered'.
    - Only one feedback is allowed per delivery.

    Returns:
        The newly created feedback document.
    """
    if user_data.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only customers can submit feedback")

    db = get_db(request)

    # Convert delivery_id to ObjectId
    try:
        delivery_oid = ObjectId(feedback.delivery_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid delivery_id format")

    # Find the delivery
    delivery = await db[delivery_collection].find_one({"_id": delivery_oid})
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if delivery.get("status") != "delivered":
        raise HTTPException(status_code=400, detail="Cannot submit feedback until delivery is marked as 'Delivered'")

    if str(delivery.get("customer_id")) != str(user_data.get("user_id")):
        raise HTTPException(status_code=403, detail="You can only submit feedback for your own delivery")

    # Check for existing feedback with ObjectId
    existing = await db[collection_name].find_one({"delivery_id": delivery_oid})
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted for this delivery")

    # Prepare and insert feedback document
    feedback_data = feedback.dict(exclude={"id"})
    feedback_data["delivery_id"] = delivery_oid
    feedback_data["customer_id"] = ObjectId(delivery.get("customer_id"))
    feedback_data["driver_id"] = ObjectId(delivery.get("driver_id"))
    feedback_data["timestamp"] = datetime.now()

    result = await db[collection_name].insert_one(feedback_data)
    new_feedback = await db[collection_name].find_one({"_id": result.inserted_id})

    return fix_feedback_id(new_feedback)



@router.get("/driver/{driver_id}")
async def get_feedback_by_driver(driver_id: str, request: Request):
    """
    Retrieve all feedback entries associated with a specific driver.

    Args:
        driver_id: The driver's user ID.

    Returns:
        List of feedback objects given to the driver.
    """
    db = get_db(request)
    feedbacks = await db[collection_name].find({"driver_id": ObjectId(driver_id)}).to_list(None)
    l = []
    for fb in feedbacks:
        fb["id"] = str(fb["_id"])
        del fb["_id"]
        fb["delivery_id"] = str(fb["delivery_id"])
        fb["customer_id"] = str(fb["customer_id"])
        fb["driver_id"] = str(fb["driver_id"])
        fb["timestamp"] = fb["timestamp"].isoformat() if isinstance(fb["timestamp"], datetime) else fb["timestamp"]
        l.append(fb)
    return l

@router.get("/customer/{customer_id}")
async def get_feedback_by_customer(customer_id: str, request: Request):
    """
    Retrieve all feedback submitted by a specific customer.

    Args:
        customer_id: The customer's user ID.

    Returns:
        List of feedback entries submitted by the customer.
    """
    db = get_db(request)
    feedbacks = await db[collection_name].find({"customer_id": ObjectId(customer_id)}).to_list(None)
    l = []
    for fb in feedbacks:
        fb["id"] = str(fb["_id"])
        del fb["_id"]
        fb["delivery_id"] = str(fb["delivery_id"])
        fb["customer_id"] = str(fb["customer_id"])
        fb["driver_id"] = str(fb["driver_id"])
        fb["timestamp"] = fb["timestamp"].isoformat() if isinstance(fb["timestamp"], datetime) else fb["timestamp"]
        l.append(fb)
    return l

@router.get("/delivery/{delivery_id}")
async def get_feedback_by_delivery(delivery_id: str, request: Request):
    """
    Retrieve feedback associated with a specific delivery.

    Args:
        delivery_id: The ObjectId of the delivery.

    Returns:
        The feedback entry for the delivery.

    Raises:
        404 if no feedback is found.
    """
    db = get_db(request)

    # Convert to ObjectId
    try:
        delivery_oid = ObjectId(delivery_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid delivery_id format")

    feedback = await db["feedback"].find_one({"delivery_id": delivery_oid})
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Fix feedback fields
    feedback["id"] = str(feedback["_id"])
    del feedback["_id"]
    feedback["delivery_id"] = str(feedback["delivery_id"])
    feedback["customer_id"] = str(feedback["customer_id"])
    feedback["driver_id"] = str(feedback["driver_id"])
    feedback["timestamp"] = feedback["timestamp"].isoformat() if isinstance(feedback["timestamp"], datetime) else feedback["timestamp"]

    return feedback
