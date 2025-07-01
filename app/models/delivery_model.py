from pydantic import BaseModel 

class CreateDeliveryRequest(BaseModel):
    pickup_location: str
    drop_location: str
    item_description: str
    phone_number : str
    
