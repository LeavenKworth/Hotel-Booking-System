from pydantic import BaseModel
from typing import Optional, Dict

class Hotel(BaseModel):
    _id: Optional[str] = None
    name: str
    location: str
    coordinates: Dict
    image: Optional[str] = None

class Room(BaseModel):
    _id: Optional[str] = None
    hotel_id: str
    type: str
    status: str
    price: float
    start_date: str
    end_date: str
    capacity: int
