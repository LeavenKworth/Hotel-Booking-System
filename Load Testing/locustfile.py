from locust import HttpUser, task, between

class HotelUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def search_hotels(self):
        self.client.get("/api/v1/hotels/search?destination=Rome&check_in=2025-07-15&check_out=2025-07-18&guests=2")

    @task
    def create_booking(self):
        self.client.post("/api/v1/bookings", json={
            "hotel_id": "test_hotel",
            "room_id": "test_room",
            "check_in": "2025-07-15",
            "check_out": "2025-07-18",
            "num_guests": 2,
            "total_price": 200.0
        })