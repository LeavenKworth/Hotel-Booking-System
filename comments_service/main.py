from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from comments_service.models import Comment
from admin_service.auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client.hotel_db

@app.post("/api/v1/hotels/{hotel_id}/comments")
async def add_comment(hotel_id: str, comment: Comment, user: str = Depends(get_current_user)):
    comment_data = comment.dict()
    comment_data["hotel_id"] = hotel_id
    comment_data["user_id"] = user
    comment_data["date"] = datetime.utcnow().isoformat()
    result = await db.comments.insert_one(comment_data)
    comment_data["_id"] = str(result.inserted_id)
    return comment_data

@app.get("/api/v1/hotels/{hotel_id}/comments")
async def get_comments(hotel_id: str, page: int = 1, size: int = 10):
    skip = (page - 1) * size
    comments = await db.comments.find({"hotel_id": hotel_id}).skip(skip).limit(size).to_list(size)
    # Calculate rating distribution
    pipeline = [
        {"$match": {"hotel_id": hotel_id}},
        {"$group": {
            "_id": None,
            "cleanliness_avg": {"$avg": "$ratings.cleanliness"},
            "service_avg": {"$avg": "$ratings.service"},
            "facilities_avg": {"$avg": "$ratings.facilities"}
        }}
    ]
    distribution = await db.comments.aggregate(pipeline).to_list(1)
    distribution = distribution[0] if distribution else {}
    return {"comments": comments, "distribution": distribution}