from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from app.core.mongodb import get_db
from app.models.user import User
from app.utils.security import hash_password, verify_password  # create this if not yet

router = APIRouter(prefix="/api/auth", tags=["auth"])

collection_name = "users"

class RegisterRequest(BaseModel):
    name: str
    email_address: EmailStr
    age: int
    gender: str
    role: str
    password: str

class LoginRequest(BaseModel):
    email_address: EmailStr
    password: str

@router.post("/register")
async def register_user(data: RegisterRequest, request: Request):
    db = get_db(request)
    existing = await db[collection_name].find_one({"email_address": data.email_address})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(data.password)
    user = User(
        name=data.name,
        email_address=data.email_address,
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
    return {"message": "Login successful", "user_id": str(user["_id"]), "role": user["role"]}
