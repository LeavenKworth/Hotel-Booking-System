from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis
from fastapi.security import OAuth2PasswordBearer
import os
from datetime import datetime
from search_service.models import SearchQuery
from admin_service.auth import get_current_user
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client.hotel_db
redis_client = Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{os.getenv('API_GATEWAY_URL')}/api/v1/admin/token", auto_error=False)

@app.get("/api/v1/hotels/search")
async def search_hotels(query: SearchQuery = Depends(), token: str = Depends(oauth2_scheme)):
    cache_key = f"search:{query.destination}:{query.check_in}:{query.check_out}:{query.guests}"
    cached = redis_client.get(cache_key)
    if cached:
        return {"results": eval(cached)}  # Use proper serialization in production

    check_in = datetime.fromisoformat(query.check_in)
    check_out = datetime.fromisoformat(query.check_out)
    rooms = await db.rooms.find({
        "status": "Vacant",
        "capacity": {"$gte": query.guests},
        "start_date": {"$lte": check_in.isoformat()},
        "end_date": {"$gte": check_out.isoformat()},
        "hotel_id": {"$in": await db.hotels.find({"location": query.destination}).distinct("_id")}
    }).to_list(10)  # Pagination: limit to 10

    is_authenticated = bool(token)
    results = []
    for room in rooms:
        price = room["price"] * 0.85 if is_authenticated else room["price"]
        hotel = await db.hotels.find_one({"_id": room["hotel_id"]})
        results.append({
            "hotel_id": hotel["_id"],
            "hotel_name": hotel["name"],
            "room_type": room["type"],
            "price": price,
            "coordinates": hotel.get("coordinates")
        })

    redis_client.setex(cache_key, 3600, str(results))
    return {"results": results}