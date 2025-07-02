from pydantic import BaseModel

class Booking(BaseModel):
    _id: str | None = None
    hotel_id: str
    room_id: str
    check_in: str
    check_out: str
    num_guests: int
    total_price: float