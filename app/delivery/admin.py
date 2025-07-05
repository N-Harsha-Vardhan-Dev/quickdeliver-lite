from fastapi import APIRouter, Request, Depends, HTTPException
from bson import ObjectId
from pydantic import BaseModel
from app.core.mongodb import get_db
from app.utils.jwt_bearer import JWTBearer

router = APIRouter(prefix="/api", tags=["Analytics"])

class AppStatsResponse(BaseModel):
    total_deliveries: int
    total_pending: int
    total_accepted: int
    total_in_transit: int
    total_delivered: int

@router.get("/app-stats", response_model=AppStatsResponse)
async def get_app_stats(db=Depends(get_db)):
    """
    Get total and categorized delivery stats across the app.

    Returns:
        AppStatsResponse: Contains total and categorized delivery counts.
    """
    total_deliveries = await db["delivery"].count_documents({})
    total_pending = await db["delivery"].count_documents({"status": "pending"})
    total_accepted = await db["delivery"].count_documents({"status": "accepted"})
    total_in_transit = await db["delivery"].count_documents({"status": "in-transit"})
    total_delivered = await db["delivery"].count_documents({"status": "delivered"})

    return AppStatsResponse(
        total_deliveries=total_deliveries,
        total_pending=total_pending,
        total_accepted=total_accepted,
        total_in_transit=total_in_transit,
        total_delivered=total_delivered
    )

@router.get("/admin/deliveries/driver/{driver_id}")
async def get_deliveries_by_driver(driver_id: str, db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all deliveries assigned to a specific driver.

    Args:
        driver_id (str): The driver's user ID.

    Returns:
        List of deliveries sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    try:
        driver_oid = ObjectId(driver_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid driver ID format")

    deliveries = await db["delivery"].find({"driver_id": driver_oid}).sort("_id", -1).to_list(None)
    for d in deliveries:
        d["id"] = str(d["_id"])
        d["driver_id"] = str(d["driver_id"])
        d["customer_id"] = str(d["customer_id"])
        d.pop("_id", None)
    return deliveries

@router.get("/admin/deliveries/customer/{customer_id}")
async def get_deliveries_by_customer(customer_id: str, db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all deliveries made by a specific customer.

    Args:
        customer_id (str): The customer's user ID.

    Returns:
        List of deliveries sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    try:
        customer_oid = ObjectId(customer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

    deliveries = await db["delivery"].find({"customer_id": customer_oid}).sort("_id", -1).to_list(None)
    for d in deliveries:
        d["id"] = str(d["_id"])
        d["driver_id"] = str(d["driver_id"])
        d["customer_id"] = str(d["customer_id"])
        d.pop("_id", None)
    return deliveries

@router.get("/admin/feedbacks/driver/{driver_id}")
async def get_feedbacks_for_driver(driver_id: str, db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all feedback entries received by a specific driver.

    Args:
        driver_id (str): The driver's user ID.

    Returns:
        List of feedbacks sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    try:
        driver_oid = ObjectId(driver_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid driver ID format")

    feedbacks = await db["feedback"].find({"driver_id": driver_oid}).sort("_id", -1).to_list(None)
    for f in feedbacks:
        f["id"] = str(f["_id"])
        f["delivery_id"] = str(f["delivery_id"])
        f["customer_id"] = str(f["customer_id"])
        f["driver_id"] = str(f["driver_id"])
        f.pop("_id", None)
        if "timestamp" in f:
            f["timestamp"] = f["timestamp"].isoformat()
    return feedbacks

@router.get("/admin/feedbacks/customer/{customer_id}")
async def get_feedbacks_for_customer(customer_id: str, db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all feedbacks submitted by a specific customer.

    Args:
        customer_id (str): The customer's user ID.

    Returns:
        List of feedbacks sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    try:
        customer_oid = ObjectId(customer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

    feedbacks = await db["feedback"].find({"customer_id": customer_oid}).sort("_id", -1).to_list(None)
    for f in feedbacks:
        f["id"] = str(f["_id"])
        f["delivery_id"] = str(f["delivery_id"])
        f["customer_id"] = str(f["customer_id"])
        f["driver_id"] = str(f["driver_id"])
        f.pop("_id", None)
        if "timestamp" in f:
            f["timestamp"] = f["timestamp"].isoformat()
    return feedbacks

@router.get("/admin/deliveries")
async def get_all_deliveries(db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all deliveries in the system.

    Returns:
        List of all deliveries sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    deliveries = await db["delivery"].find().sort("_id", -1).to_list(None)
    for d in deliveries:
        d["id"] = str(d["_id"])
        d["driver_id"] = str(d["driver_id"])
        d["customer_id"] = str(d["customer_id"])
        d.pop("_id", None)
    return deliveries

@router.get("/admin/feedbacks")
async def get_all_feedbacks(db=Depends(get_db), user=Depends(JWTBearer())):
    """
    Admin: Get all feedbacks in the system.

    Returns:
        List of all feedbacks sorted by newest first.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    feedbacks = await db["feedback"].find().sort("_id", -1).to_list(None)
    for f in feedbacks:
        f["id"] = str(f["_id"])
        f["delivery_id"] = str(f["delivery_id"])
        f["customer_id"] = str(f["customer_id"])
        f["driver_id"] = str(f["driver_id"])
        f.pop("_id", None)
        if "timestamp" in f:
            f["timestamp"] = f["timestamp"].isoformat()
    return feedbacks


