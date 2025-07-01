from typing import Optional, List, Annotated
from pydantic import BaseModel, EmailStr, StringConstraints
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
    phone_number: Annotated[str, StringConstraints(pattern=r"^\d{10}$")]
    age: int
    gender: Optional[GenderEnum] = GenderEnum.prefer_not_to_say
    role: RoleEnum = RoleEnum.customer  # default role
    hashed_password: Optional[str] = None