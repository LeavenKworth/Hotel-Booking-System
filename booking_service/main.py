from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import pika
import os
from datetime import datetime
from booking_service.models import Booking
from admin_service.auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client.hotel_db
rabbitmq_conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
channel = rabbitmq_conn.channel()
channel.queue_declare(queue="notifications")

@app.post("/api/v1/bookings")
async def create_booking(booking: Booking, user: str = Depends(get_current_user)):

    room = await db.rooms.find_one({
        "_id": booking.room_id,
        "hotel_id": booking.hotel_id,
        "status": "Vacant",
        "start_date": {"$lte": booking.check_in},
        "end_date": {"$gte": booking.check_out},
        "capacity": {"$gte": booking.num_guests}
    })
    if not room:
        raise HTTPException(status_code=400, detail="Room not available")


    payment_success = True  # Simulate payment
    if not payment_success:
        raise HTTPException(status_code=400, detail="Payment failed")


    booking_data = booking.dict()
    booking_data["user_id"] = user
    booking_data["status"] = "Pending"
    booking_data["created_at"] = datetime.utcnow()
    result = await db.bookings.insert_one(booking_data)
    booking_data["_id"] = str(result.inserted_id)


    await db.rooms.update_one({"_id": booking.room_id}, {"$set": {"status": "Occupied"}})


    message = str({
        "user_id": user,
        "hotel_id": booking.hotel_id,
        "room_id": booking.room_id,
        "check_in": booking.check_in,
        "check_out": booking.check_out,
        "total_price": booking.total_price
    })
    channel.basic_publish(exchange="", routing_key="notifications", body=message)

    return {"message": "Booking created", "booking_id": booking_data["_id"]}