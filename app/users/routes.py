from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
from typing import List
from app.core.mongodb import get_db
from app.models.user import User
from app.utils.jwt_bearer import JWTBearer

router = APIRouter(prefix="/api")
collection_name = "users"

def fix_user_id(user):
    user["id"] = str(user["_id"])
    del user["_id"]
    return user

@router.post("/create_user", response_model=User)
async def create_user(user: User, request: Request, user_data: dict = Depends(JWTBearer())):
    db = get_db(request)
    result = await db[collection_name].insert_one(user.dict(exclude={"id"}))
    inserted_user = await db[collection_name].find_one({"_id": result.inserted_id})
    return fix_user_id(inserted_user)

@router.get("/read_all_users", response_model=List[User])
async def read_all_users(request: Request, user_data: dict = Depends(JWTBearer())):
    if user_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    db = get_db(request)
    users = await db[collection_name].find().to_list(None)
    return [fix_user_id(user) for user in users]

@router.get("/user/{id}", response_model=User)
async def get_user_by_id(id: str, request: Request, user_data: dict = Depends(JWTBearer())):
    db = get_db(request)
    try:
        user = await db[collection_name].find_one({"_id": ObjectId(id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return fix_user_id(user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

@router.put("/user/{id}", response_model=User)
async def update_user(id: str, user: User, request: Request, user_data: dict = Depends(JWTBearer())):
    db = get_db(request)
    try:
        user_dict = user.dict(exclude={"id"})
        result = await db[collection_name].update_one(
            {"_id": ObjectId(id)},
            {"$set": user_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        updated_user = await db[collection_name].find_one({"_id": ObjectId(id)})
        return fix_user_id(updated_user)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

@router.delete("/user/{id}")
async def delete_user(id: str, request: Request, user_data: dict = Depends(JWTBearer())):
    db = get_db(request)
    try:
        result = await db[collection_name].delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User {id} deleted successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

@router.get("/user_by_email/{email_address}", response_model=User)
async def read_user_by_email(email_address: str, request: Request, user_data: dict = Depends(JWTBearer())):
    db = get_db(request)
    user = await db[collection_name].find_one({"email_address": email_address})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return fix_user_id(user)
