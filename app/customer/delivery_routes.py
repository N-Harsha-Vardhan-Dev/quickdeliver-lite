from fastapi import APIRouter, HTTPException, Request
from app.core.mongodb import get_db
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.utils.security import hash_password
from bson import ObjectId

router = APIRouter(prefix="/api/delivery", tags=["Deliveries"])
collection_name = "deliveries"

class Delivery(BaseModel):
    id: Optional[str] = None 
    name: str
    email_address: EmailStr
    password: str
    phone_number: str
    delivery_id: Optional[str] = None
    role: str = "delivery"

class LoginRequest(BaseModel):
    email_address: EmailStr
    password: str

def fix_delivery_id(delivery):
    delivery["id"] = str(delivery["_id"])
    del delivery["_id"]
    return delivery

@router.post("/create", response_model=Delivery)
async def create_delivery(delivery: Delivery, request: Request):
    """
    Create a new delivery agent.

    Args:
        delivery (Delivery): JSON body with delivery agent data.

    Returns:
        The newly created delivery agent.
    """
    db = get_db(request)
    delivery.password = hash_password(delivery.password)
    result = await db[collection_name].insert_one(delivery.dict(exclude={"id"}))
    new_delivery = await db[collection_name].find_one({"_id": result.inserted_id})
    return fix_delivery_id(new_delivery)

@router.get("/get_all", response_model=List[Delivery])
async def get_all_deliveries(request: Request):
    """
    Get a list of all registered delivery agents.

    Returns:
        A list of delivery agent objects.
    """
    db = get_db(request)
    cursor = db[collection_name].find()
    deliveries = []
    async for delivery in cursor:
        deliveries.append(fix_delivery_id(delivery))
    return deliveries

@router.get("/{delivery_id}", response_model=Delivery)
async def get_delivery_by_id(delivery_id: str, request: Request):
    """
    Retrieve a delivery agent by their MongoDB ObjectId.

    Args:
        delivery_id (str): The ObjectId of the delivery agent.

    Returns:
        The delivery agent object.

    Raises:
        HTTP 404: If no agent with the given ID is found.
    """
    db = get_db(request)
    delivery = await db[collection_name].find_one({"_id": ObjectId(delivery_id)})
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return fix_delivery_id(delivery)

@router.put("/{delivery_id}", response_model=Delivery)
async def update_delivery(delivery_id: str, delivery: Delivery, request: Request):
    """
    Update a delivery agent's details by ID.

    Args:
        delivery_id (str): The ObjectId of the delivery agent.
        delivery (Delivery): JSON body with fields to update.

    Returns:
        The updated delivery agent object.

    Raises:
        HTTP 404: If the delivery agent is not found.
    """
    db = get_db(request)
    update_data = delivery.dict(exclude_unset=True, exclude={"id"})
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
    result = await db[collection_name].update_one(
        {"_id": ObjectId(delivery_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")
    updated = await db[collection_name].find_one({"_id": ObjectId(delivery_id)})
    return fix_delivery_id(updated)

@router.delete("/{delivery_id}")
async def delete_delivery(delivery_id: str, request: Request):
    """
    Delete a delivery agent by ID.

    Args:
        delivery_id (str): The ObjectId of the delivery agent.

    Returns:
        A success message if deleted.

    Raises:
        HTTP 404: If the delivery agent is not found.
    """
    db = get_db(request)
    result = await db[collection_name].delete_one({"_id": ObjectId(delivery_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return {"message": f"Delivery {delivery_id} deleted successfully"}
