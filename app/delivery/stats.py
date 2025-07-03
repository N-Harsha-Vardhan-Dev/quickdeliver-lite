from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from app.core.mongodb import get_db
from app.utils.jwt_bearer import JWTBearer

router = APIRouter(prefix="/api", tags=["Stats"])

class StatsResponse(BaseModel):
    user_id: str
    role: str
    email: str
    total_deliveries: int
    pending_deliveries: int  # <-- NEW

@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(JWTBearer())])
async def get_user_stats(request: Request, db=Depends(get_db)):
    user = request.state.user
    user_id = user["user_id"]
    role = user["role"]
    email = user["email"]

    # Determine role
    if role == "customer":
        key = "customer_id"
    elif role == "agent":
        key = "agent_id"
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    # Total deliveries
    total = await db["delivery"].count_documents({key: user_id})
    
    # Pending deliveries
    pending = await db["delivery"].count_documents({
        key: user_id,
        "status": "pending"
    })

    if total is None:
        raise HTTPException(status_code=404, detail="No deliveries found for this user")

    return StatsResponse(
        user_id=user_id,
        role=role,
        email=email,
        total_deliveries=total,
        pending_deliveries=pending
    )
