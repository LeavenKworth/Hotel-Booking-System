from apscheduler.schedulers.asyncio import AsyncIOScheduler
from motor.motor_asyncio import AsyncIOMotorClient
import pika
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
import asyncio

load_dotenv()

mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client.hotel_db
rabbitmq_conn = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
channel = rabbitmq_conn.channel()
channel.queue_declare(queue="notifications")

scheduler = AsyncIOScheduler()

async def check_low_capacity():
    next_month = datetime.utcnow() + timedelta(days=30)
    hotels = await db.hotels.find().to_list(None)
    for hotel in hotels:
        rooms = await db.rooms.find({
            "hotel_id": hotel["_id"],
            "status": "Vacant",
            "start_date": {"$lte": next_month.isoformat()},
            "end_date": {"$gte": datetime.utcnow().isoformat()}
        }).to_list(None)
        total_rooms = await db.rooms.count_documents({"hotel_id": hotel["_id"]})
        if total_rooms and len(rooms) / total_rooms < 0.2:
            message = f"Low capacity alert for {hotel['name']}: {len(rooms)}/{total_rooms} rooms available"
            channel.basic_publish(exchange="", routing_key="notifications", body=message)

async def process_reservations():
    bookings = await db.bookings.find({"status": "Pending"}).to_list(None)
    for booking in bookings:
        hotel = await db.hotels.find_one({"_id": booking["hotel_id"]})
        message = json.dumps({
            "user_id": booking["user_id"],
            "hotel_name": hotel["name"],
            "check_in": booking["check_in"],
            "check_out": booking["check_out"],
            "total_price": booking["total_price"]
        })
        channel.basic_publish(exchange="", routing_key="notifications", body=message)
        await db.bookings.update_one({"_id": booking["_id"]}, {"$set": {"status": "Confirmed"}})

scheduler.add_job(check_low_capacity, "interval", days=1)
scheduler.add_job(process_reservations, "interval", days=1)

async def main():
    scheduler.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
