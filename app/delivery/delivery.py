from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
from pydantic import BaseModel, EmailStr
from app.models.delivery import CreateDeliveryRequest
from app.core.mongodb import get_db
from app.utils import jwt_bearer
from app.utils.jwt_bearer import JWTBearer


router = APIRouter(prefix='/api/deliveries', tags=['Delivery'])

collection_name = "delivery"

class StatusUpdate(BaseModel) : 
    status : str

transitions = {
    "accepted" : "in-transit",
    "in-transit" : "delivered"
}
#week 2

@router.post('/', dependencies= [Depends(JWTBearer)])
async def create_delivery(data : CreateDeliveryRequest, request: Request, user_data : dict = Depends(JWTBearer())) : 
    """
    Create a new delivery request by a customer.

    Requires:
        - Authenticated user with role 'customer'.
        - JSON body with {pickup location, drop location, item description, and phone number.}

    Returns:
        - Success message with delivery ID if created.
        - 401 if non-customer tries to create.
    """
    if user_data['role'] != 'customer' : 
        raise HTTPException(status_code=401, detail="Customers can only create delvieries")
    
    db = get_db(request)

    new_delivery = {
        "customer_id" : ObjectId(user_data['user_id']),
        "partner_id" : None,
        "pickup_location" : data.pickup_location, 
        "drop_location" : data.drop_location, 
        "item_description" : data.item_description,
        "phone_number": data.phone_number,
        "status" : 'pending', 
        "delivery_charge" : None,
        "requested_at" : datetime.now(),
        "accepted_at" : None,
        "delivered_at" : None, 
        "is_cancelled" : False
    }

    result = await db[collection_name].insert_one(new_delivery)

    return {"message" : "Delivery Created", "delivery_id": str(result.inserted_id)}


@router.get('/pending') 
async def list_pending_deliveries(request: Request) : 
    """
    List all pending delivery requests available for agents to accept.

    Returns:
        - List of deliveries with pickup/drop locations, description, and requested time.
    """
    db = get_db(request)

    deliveries_list = db[collection_name].find({"status" : "pending"}).sort({"requested" : -1})
    deliveries = []

    async for delivery in deliveries_list : 
        deliveries.append(
            {
                "id" : str(delivery['_id']), 
                "pickup_location" : delivery['pickup_location'], 
                "drop_location" : delivery['drop_location'], 
                "item_description" : delivery['item_description'], 
                "phone_number": delivery.get('phone_number'),
                "requested_at" : delivery["requested_at"]
            }
        )
    
    return {"Pending deliveries" : deliveries}

# week 3 

@router.post('/{delivery_id}/accept', dependencies= [Depends(JWTBearer)])
async def accept_delivery(delivery_id : str, request :Request, user : dict = Depends(JWTBearer()) ) : 
    """
    Allows a delivery agent to accept a pending delivery.

    Requires:
        - Authenticated user with role 'agent'.
        - Path parameter: delivery_id.

    Returns:
        - Success message if accepted.
        - 403 if not an agent or already accepted.
        - 404 if delivery not found.
    """
    if user['role'] != "agent" : 
        raise HTTPException(status_code=403, detail= "only delivery agents can accept deliveries")
    
    db = get_db(request)
    delivery = await db[collection_name].find_one({"_id": ObjectId(delivery_id)})

    if not delivery : 
        raise HTTPException(status_code=404, detail="Delivery not found")
    print(delivery)
    if delivery['status'] != "pending"  :
        raise HTTPException(status_code=400, detail="Delivery already accepted")
    
    update_result = await db[collection_name].update_one(
        {"_id" : ObjectId(delivery_id)}, 
        {
            "$set" : {
                "partner_id" : ObjectId(user["user_id"]),
                "status"  : "accepted", 
                "accepted_at" : datetime.now()
            }
        }
        )

    if update_result.modified_count == 1 : 
        return {"message": "Delivery accepted"}
    else : 
        raise HTTPException(status_code=500, detail="Failed to accepted reqeust")
    

@router.get('/my')
async def get_my_deliveries(request : Request, user = Depends(JWTBearer())) : 
    """
    Get all deliveries assigned to the currently logged-in delivery agent.

    Requires:
        - Authenticated user with role 'agent'.

    Returns:
        - List of deliveries with status, pickup/drop locations, and request time.
    """
    if user['role'] != 'agent' : 
        raise HTTPException(status_code=403, detail="Only driver can see their deliveries")
    
    db = get_db(request)
    result = db[collection_name].find({"partner_id" : ObjectId(user["user_id"])})
    # print(result)
    deliveries = []

    async for delivery in result : 
        deliveries.append({
            "id" : str(delivery['_id']), 
            "pickup_location" : delivery['pickup_location'],
            "drop_location" : delivery['drop_location'], 
            "status" : delivery['status'], 
            "phone_number": delivery.get('phone_number'),
            'requested_at' : delivery['requested_at']
        })
    
    return {"my deliveries": deliveries}



#week 4 

@router.patch('/{delivery_id}/status')
async def update_delivery_status(delivery_id : str, data : StatusUpdate, request:Request, user = Depends(JWTBearer())) : 
    """
    Update the delivery status from 'accepted' to 'in-transit', or 'in-transit' to 'delivered'.

    Requires:
        - Authenticated user with role 'agent'.
        - Path parameter: delivery_id.
        - JSON body with the next valid status.

    Returns:
        - Success message if status is updated.
        - 403 if unauthorized or not assigned to delivery.
        - 400 if invalid status transition.
    """
    if user['role'] != 'agent' :
        raise HTTPException(status_code=403, detail="Only delivery agents can update status")
    
    db = get_db(request)
    delivery = await db[collection_name].find_one({"_id" : ObjectId(delivery_id)})

    if not delivery : 
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    if str(delivery["partner_id"]) != user["user_id"] : 
        raise HTTPException(status_code=403, detail="You are assigned to this delivery")
    
    current_status = delivery['status']
    next_status = data.status

    if current_status not in transitions or transitions[current_status] != next_status : 
        raise HTTPException(status_code=400, detail=f"Invalid status trasition from {current_status} to {next_status}")
    
    update_data = {"status"  : next_status}
    if next_status == "delivered" :
        update_data['delivered_at'] = datetime.now()

    result =  await db[collection_name].update_one(
        {"_id" : ObjectId(delivery_id) },
        { "$set" : update_data }
    )
    
    if result.modified_count == 1 : 
        return {"message" : f"Status updated to {next_status}"}
    else : 
        raise HTTPException(status_code=500, detail="Failed to update status")
    

@router.get("/customer")
async def view_customer_deliveries(
    request: Request,
    user: dict = Depends(JWTBearer())
):
    """
    View all deliveries requested by the logged-in customer.

    Requires:
        - Authenticated user with role 'customer'.

    Returns:
        - List of all deliveries with status, timestamps, and location info.
    """
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can see their deliveries")
    
    db = get_db(request)
    print("user_id type:", type(user["user_id"]), "value:", user["user_id"])
    cursor = db[collection_name].find({"customer_id" : ObjectId(user["user_id"])})
    print(type(ObjectId(user["user_id"])))
    deliveries = []
    async for delivery in cursor:
        deliveries.append({
            "id": str(delivery["_id"]),
            "pickup_location": delivery["pickup_location"],
            "drop_location": delivery["drop_location"],
            "status": delivery["status"],
            "phone_number": delivery.get("phone_number"),
            "requested_at": delivery["requested_at"],
            "delivered_at": delivery.get("delivered_at")

        })

    return {"deliveries": deliveries}

#  create a rpoute to view all deliveries for a customer
@router.get("/{delivery_id}")
async def view_delivery_by_id(
    delivery_id: str,
    request: Request,
    user: dict = Depends(JWTBearer())
):
    """
    View a specific delivery by ID for the logged-in customer.

    Requires:
        - Authenticated user with role 'customer'.
        - Path parameter: delivery_id.

    Returns:
        - Delivery details if found.
        - 403 if not a customer.
        - 404 if delivery not found.
    """
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can view their deliveries")

    db = get_db(request)
    delivery = await db[collection_name].find_one({"_id": ObjectId(delivery_id), "customer_id": ObjectId(user["user_id"])})

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {
        "id": str(delivery["_id"]),
        "pickup_location": delivery["pickup_location"],
        "drop_location": delivery["drop_location"],
        "status": delivery["status"],
        "phone_number": delivery.get("phone_number"),
        "requested_at": delivery["requested_at"],
        "delivered_at": delivery.get("delivered_at")
    }