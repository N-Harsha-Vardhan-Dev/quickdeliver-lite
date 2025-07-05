from fastapi import FastAPI, HTTPException
from app.core.mongodb import lifespan

from app.users.routes import router as users_router
from app.users.auth_route import router as auth_router
from app.delivery.delivery import router as delivery_router
# from app.customer import delivery_routes
from app.feedback.feedback import router as feedback_router
from app.delivery.stats import router as stats_router
from app.delivery.admin import router as admin_router
app = FastAPI(lifespan=lifespan)



app.include_router(auth_router, tags=["auth"])
app.include_router(users_router, tags=["CRUD users"])

app.include_router(delivery_router)
# app.include_router(delivery_routes.router)

app.include_router(feedback_router)
app.include_router(stats_router)
app.include_router(admin_router)

@app.get('/')
async def main_root() :
    return {"messege" : "Quick Deliver Lite Backend"}