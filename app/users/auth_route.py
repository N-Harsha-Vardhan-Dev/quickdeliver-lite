from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Annotated
from pydantic import BaseModel, EmailStr, StringConstraints
from app.core.mongodb import get_db
from app.models.user import User
from app.utils.security import hash_password, verify_password , create_access_token # create this if not yet
from app.utils.jwt_bearer import JWTBearer
router = APIRouter(prefix="/api/auth", tags=["auth"])

collection_name = "users"

PhoneNumber = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]

class UserInfoResponse(BaseModel):
    user_id: str
    role: str
    gender: str
    name: str 
    email_address: EmailStr
    phone_number: PhoneNumber
    age: int

class RegisterRequest(BaseModel):
    name: str
    email_address: EmailStr
    age: int
    gender: str
    role: str
    password: str
    phone_number: PhoneNumber

class LoginRequest(BaseModel):
    email_address: EmailStr
    password: str

@router.post("/register")
async def register_user(data: RegisterRequest, request: Request):
    db = get_db(request)
    existing_email = await db[collection_name].find_one({"email_address": data.email_address})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_phone = await db[collection_name].find_one({"phone_number": data.phone_number})
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    hashed_pw = hash_password(data.password)
    user = User(
        name=data.name,
        email_address=data.email_address,
        phone_number=data.phone_number,
        age=data.age,
        gender=data.gender,
        role=data.role,
        hashed_password=hashed_pw,
    )
    result = await db[collection_name].insert_one(user.dict(exclude={"id"}))
    return {"message": "User registered successfully", "user_id": str(result.inserted_id)}



@router.post("/login")
async def login_user(data: LoginRequest, request: Request):
    db = get_db(request)
    user = await db[collection_name].find_one({"email_address": data.email_address})
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token_data = {
        "user_id": str(user["_id"]),
        "email" : user["email_address"],
        "role": user["role"],
        'gender' : user['gender'],
        "name": user["name"], 
        "phone_number": user["phone_number"],
        "age": user["age"]
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
        "role": user["role"]
    }

    # return {"message": "Login successful", "user_id": str(user["_id"]), "role": user["role"]}
@router.get('/me',response_model=UserInfoResponse)
async def get_profile(user_data : dict = Depends(JWTBearer())) : 
    return {
        "user_id": user_data["user_id"],
        "name": user_data["name"] , 
        "age": user_data["age"] ,
        "role": user_data["role"],
        "gender": user_data["gender"],
        "email_address": user_data["email"],  
        "phone_number": user_data["phone_number"]
    }