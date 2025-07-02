from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from models import Room, Hotel
from auth import create_access_token, get_current_user

load_dotenv()
app = FastAPI()
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client.hotel_db
redis_client = Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/token")

@app.post("/api/v1/admin/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/hotels", response_model=Hotel)
async def add_hotel(hotel: Hotel, user: str = Depends(get_current_user)):
    hotel_data = hotel.dict()
    hotel_data["updated_at"] = datetime.utcnow()
    result = await db.hotels.insert_one(hotel_data)
    hotel_data["_id"] = str(result.inserted_id)
    redis_client.setex(f"hotel:{hotel_data['_id']}", 3600, str(hotel_data))
    return hotel_data

@app.post("/api/v1/hotels/rooms", response_model=Room)
async def add_room(room: Room, user: str = Depends(get_current_user)):
    room_data = room.dict()
    room_data["updated_at"] = datetime.utcnow()
    result = await db.rooms.insert_one(room_data)
    room_data["_id"] = str(result.inserted_id)
    redis_client.setex(f"hotel:{room.hotel_id}", 3600, str(room_data))
    return room_data

@app.put("/api/v1/hotels/rooms/{room_id}")
async def update_room(room_id: str, room: Room, user: str = Depends(get_current_user)):
    result = await db.rooms.update_one(
        {"_id": room_id, "hotel_id": room.hotel_id},
        {"$set": {**room.dict(), "updated_at": datetime.utcnow()}}
    )
    if result.modified_count:
        redis_client.setex(f"hotel:{room.hotel_id}", 3600, str(room.dict()))
        return {"message": "Room updated successfully"}
    raise HTTPException(status_code=404, detail="Room not found")

