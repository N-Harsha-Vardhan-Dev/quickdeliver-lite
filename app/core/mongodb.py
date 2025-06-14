from fastapi import FastAPI, Request
# from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient

# client = AsyncIOMotorClient(settings.MONGO_URL)
# db = client[settings.MONGO_DB]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URL,
              serverSelectionTimeoutMS=60000,  # 60 seconds
              connectTimeoutMS=60000,
              socketTimeoutMS=60000,
              tls=True)

    app.db = app.mongodb_client.get_database(settings.MONGO_DB)
    print("app.db", app.db)
    print("mongo db connected")
    yield
    print("Mongo DB disconnected")

def get_db(request: Request) :
    print("-------------------------------------------------------------------------------")
    return request.app.db