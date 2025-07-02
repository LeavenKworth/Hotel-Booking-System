from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import httpx
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType

load_dotenv()

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hotel_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


app = FastAPI()

client = AsyncIOMotorClient(MONGO_URI)
db = client["hotel_db"]

class ChatRequest(BaseModel):
    message: str



async def search_hotels(input_str: str) -> str:
    """
    input_str : "Search hotels in Rome from 2025-07-15 to 2025-07-18 for 2 adults"
    """
    try:
        pattern = r"(?:search|find|book).*hotel.*in\s+(\w+).*from\s+(\d{4}-\d{2}-\d{2}).*to\s+(\d{4}-\d{2}-\d{2}).*for\s+(\d+)\s*(?:adult|guest)"
        match = re.match(pattern, input_str.lower())
        if not match:
            return "Invalid search query format."

        destination, check_in, check_out, guests = match.groups()

        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(
                f"{API_GATEWAY_URL}/api/v1/hotels/search",
                params={
                    "destination": destination,
                    "check_in": check_in,
                    "check_out": check_out,
                    "guests": int(guests)
                }
            )
            if response.status_code == 200:
                hotels = response.json().get("results", [])
                if not hotels:
                    return "No hotels found for your criteria."
                return f"Hotels found: {hotels}"
            return f"Search API error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Search error: {str(e)}"

async def book_hotel(input_str: str) -> str:
    """
    input_str : "Book hotel Hilton from 2025-07-15 to 2025-07-18 for 2 adults"
    """
    try:
        pattern = r"(?:book|reserve).*hotel\s+(\w+).*from\s+(\d{4}-\d{2}-\d{2}).*to\s+(\d{4}-\d{2}-\d{2}).*for\s+(\d+)\s*(?:adult|guest)"
        match = re.match(pattern, input_str.lower())
        if not match:
            return "Invalid booking query format."

        hotel_name, check_in, check_out, guests = match.groups()

        hotel = await db.hotels.find_one({"name": {"$regex": hotel_name, "$options": "i"}})
        if not hotel:
            return "Hotel not found."

        room = await db.rooms.find_one({"hotel_id": hotel["_id"], "status": "Vacant"})
        if not room:
            return "No available rooms."

        async with httpx.AsyncClient() as client_http:
            response = await client_http.post(
                f"{API_GATEWAY_URL}/api/v1/bookings",
                json={
                    "hotel_id": str(hotel["_id"]),
                    "room_id": str(room["_id"]),
                    "check_in": check_in,
                    "check_out": check_out,
                    "num_guests": int(guests),
                    "total_price": room["price"]
                }
            )
            if response.status_code == 200:
                return "Booking created successfully!"
            return f"Booking API error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Booking error: {str(e)}"


import asyncio
from functools import wraps

def async_to_sync(func):
    @wraps(func)
    def sync_func(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return sync_func

tools = [
    Tool(
        name="SearchHotels",
        func=async_to_sync(search_hotels),
        description="Search hotels by destination, date range and number of guests. Input format: Search hotels in <destination> from <YYYY-MM-DD> to <YYYY-MM-DD> for <number> adults"
    ),
    Tool(
        name="BookHotel",
        func=async_to_sync(book_hotel),
        description="Book a hotel room. Input format: Book hotel <hotel_name> from <YYYY-MM-DD> to <YYYY-MM-DD> for <number> adults"
    )
]

llm = ChatOpenAI(temperature=0, model="gpt-4")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

@app.post("/api/v1/ai/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required.")

    try:

        response = await asyncio.to_thread(agent.invoke, user_message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
