
from fastapi import APIRouter, HTTPException, Request, Body
from typing import List
from app.customer import Customer
from app.core.mongodb import get_db
from app.utils.security import hash_password, verify_password
from bson import ObjectId


router = APIRouter(prefix="/api/customers", tags=["customers"])
collection_name = "customers"

# Utility: Fix MongoDB _id to id
def fix_customer_id(customer):
    customer["id"] = str(customer["_id"])
    del customer["_id"]
    return customer       

@router.post("/create_user", response_model=Customer)
async def create_user(user: Customer, request: Request):
    db = get_db(request)
    existing_customer = await db[collection_name].find_one({"email_address": user.email_address})
    if existing_customer:   
        raise HTTPException(status_code=400, detail="Email already registered")
    customer_data = user.dict(exclude={"id"})
    customer_data["role"] = "customer"
    result = await db[collection_name].insert_one(customer_data)
    new_customer = await db[collection_name].find_one({"_id": result.inserted_id})
    return fix_customer_id(new_customer)  
                                  
# POST - Register a new customer
@router.post("/register", response_model=Customer)
async def register_customer(customer: Customer, request: Request):
    db = get_db(request)

    # Check if email already exists
    existing_customer = await db[collection_name].find_one({"email_address": customer.email_address})
    if existing_customer:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    customer_data = customer.dict(exclude={"id"})
    customer_data["password"] = hash_password(customer.password)

    # Insert into DB
    result = await db[collection_name].insert_one(customer_data)
    new_customer = await db[collection_name].find_one({"_id": result.inserted_id})
    return fix_customer_id(new_customer)

@router.get("/", response_model=List[Customer])
async def get_all_customers(request: Request):
    db = get_db(request)
    customers_cursor = db[collection_name].find()
    customers = []
    async for customer in customers_cursor:
        customers.append(fix_customer_id(customer))
    return customers

@router.get("/{customer_id}", response_model=Customer)
async def get_customer_by_id(customer_id: str, request: Request):
    db = get_db(request)
    customer = await db[collection_name].find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return fix_customer_id(customer)
 
# PUT - Update customer details
@router.put("/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: Customer, request: Request):
    db = get_db(request)
    update_data = customer.dict(exclude_unset=True, exclude={"id"})
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
    result = await db[collection_name].update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    updated_customer = await db[collection_name].find_one({"_id": ObjectId(customer_id)})
    return fix_customer_id(updated_customer)

@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: str, request: Request):
    db = get_db(request)
    result = await db[collection_name].delete_one({"_id": ObjectId(customer_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": f"Customer {customer_id} deleted successfully"}

    
# GET - Fetch customer by email
@router.get("/by_email/{email_address}", response_model=Customer)
async def get_customer_by_email(email_address: str, request: Request):
    db = get_db(request)
    customer = await db[collection_name].find_one({"email_address": email_address})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return fix_customer_id(customer)
