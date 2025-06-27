from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.mongodb import get_db
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.utils.security import hash_password, verify_password
from bson import ObjectId
from app.utils.jwt_bearer import JWTBearer
from app.utils.security import create_access_token
from app.customer import delivery_routes
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

@router.post("/register", response_model=Delivery)
async def register_delivery(delivery: Delivery, request: Request):
    db = get_db(request)
    existing = await db[collection_name].find_one({"email_address": delivery.email_address})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    delivery_data = delivery.dict(exclude={"id"})
    delivery_data["password"] = hash_password(delivery.password)

    result = await db[collection_name].insert_one(delivery_data)
    new_delivery = await db[collection_name].find_one({"_id": result.inserted_id})
    return Delivery(
        id=str(new_delivery["_id"]),
        name=new_delivery["name"],
        email_address=new_delivery["email_address"],
        password=new_delivery["password"],
        delivery_id=new_delivery.get("delivery_id", ""),
        role=new_delivery.get("role", "delivery")
    )

@router.post("/login")
async def login_delivery(data: LoginRequest, request: Request):
    db = get_db(request)
    delivery = await db[collection_name].find_one({"email_address": data.email_address})
    if not delivery or not verify_password(data.password, delivery["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(delivery["_id"]), "role": delivery.get("role", "delivery")})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/", response_model=List[Delivery])
async def get_all_deliveries(request: Request, token: str = Depends(JWTBearer())):
    db = get_db(request)
    cursor = db[collection_name].find()
    deliveries = []
    async for delivery in cursor:
        deliveries.append(fix_delivery_id(delivery))
    return deliveries

@router.get("/{delivery_id}", response_model=Delivery)
async def get_delivery_by_id(delivery_id: str, request: Request, token: str = Depends(JWTBearer())):
    db = get_db(request)
    delivery = await db[collection_name].find_one({"_id": ObjectId(delivery_id)})
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return fix_delivery_id(delivery)

@router.put("/{delivery_id}", response_model=Delivery)
async def update_delivery(delivery_id: str, delivery: Delivery, request: Request, token: str = Depends(JWTBearer())):
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

@router.delete("/{delivery_id}", status_code=204)
async def delete_delivery(delivery_id: str, request: Request, token: str = Depends(JWTBearer())):
    db = get_db(request)
    result = await db[collection_name].delete_one({"_id": ObjectId(delivery_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return {"message": f"Delivery {delivery_id} deleted successfully"}