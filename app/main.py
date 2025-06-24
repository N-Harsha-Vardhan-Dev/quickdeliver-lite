from fastapi import FastAPI, HTTPException
from app.core.mongodb import lifespan
from app.users.routes import router as users_router
from app.users.auth_route import router as auth_router
from app.customer.customer_route import router as customer_route_router
from app.delivery.delivery import router as delivery_router
app = FastAPI(lifespan=lifespan)
# app.include_router(users_router)
app.include_router(auth_router, tags=["auth"])
app.include_router(customer_route_router)
app.include_router(delivery_router)

@app.get('/')
async def main_root() :
    return {"messege" : "Quick Deliver Lite Backend"}