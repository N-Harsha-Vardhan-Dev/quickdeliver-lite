from fastapi import FastAPI, HTTPException
from app.core.mongodb import lifespan
from app.users.routes import router as users_router
from app.users.auth_route import router as auth_router

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(auth_router, tags=["auth"])
@app.get('/')
async def main_root() :
    return {"messege" : "Quick Deliver Lite Backend"}