from typing import Optional, List
from pydantic import BaseModel, EmailStr
from enum import Enum

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"

class RoleEnum(str, Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"  # optional, if you want admin control

class User(BaseModel):
    id: Optional[str] = None
    name: str
    email_address: EmailStr
    age: int
    gender: Optional[GenderEnum] = GenderEnum.prefer_not_to_say
    role: RoleEnum = RoleEnum.customer  # default role
    hashed_password: Optional[str] = None
    other_names: Optional[List[str]] = []
