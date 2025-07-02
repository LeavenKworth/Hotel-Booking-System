# Hotel Booking System 🏨

A scalable, cloud-deployable hotel booking platform inspired by Hotels.com. Built as part of the SE4458 Software Architecture & Design of Modern Large-Scale Systems course project.

---

## 📚 Features

### 🔐 Hotel Admin Service
- Authenticated hotel administrators can add/update room availability.
- Admins are notified if hotel capacity falls below 20% for the coming month.

### 🔍 Hotel Search Service
- Search hotels by location, dates, and number of people.
- Logged-in clients receive 15% discount on prices.
- “Show on Map” feature displays results visually.

### 🛏️ Booking Service
- Users can book rooms directly from hotel detail page.
- Room capacity is adjusted upon booking (no payment integration).

### 💬 Comments Service
- Hotel comments and ratings are shown with service-specific distribution charts.
- Stored in a NoSQL database for scalability.

### 🔔 Notification Service
- Nightly tasks notify admins of low capacity.
- Push reservation details from queue to admins.

### 🤖 AI Agent Service
- A chat-based AI assistant helps users with hotel search and booking.
- Uses backend APIs for real-time suggestions and confirmations.

---

## 🏗️ Architecture

- **Microservices:** Each domain (Search, Booking, Notification, etc.) is a separate REST service.
- **API Gateway:** Central point to route requests to services.
- **Queues:** RabbitMQ / Azure Messaging for async communication.
- **Databases:** SQL for transactional data, NoSQL for comments, Redis for hotel caching.
- **Cloud Hosting:** Azure App Services / GCP / AWS (as chosen by implementers).

---

## ⚙️ Tech Stack

| Component        | Technology Used      |
|------------------|----------------------|
| Backend APIs     | Python FastAPI|
| Frontend         | Basic HTML |
| DB (Hotel/Booking)| MySQL |
| DB (Comments)    | MongoDB |
| Caching          | Redis |
| Messaging Queue  | RabbitMQ |
| AI Agent         | OpenAI API  Langchain |
| Containerization | Docker |
