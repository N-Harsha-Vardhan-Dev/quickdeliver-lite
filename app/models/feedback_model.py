from pydantic import BaseModel, Field
from pydantic.types import StringConstraints
from typing import Optional, Annotated
from datetime import datetime

class Feedback(BaseModel):
    id: Optional[str] = None
    delivery_id: str
    customer_id: str
    driver_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[Annotated[str, StringConstraints(max_length=200)]] = ""
    timestamp: datetime = Field(default_factory=datetime.now())
