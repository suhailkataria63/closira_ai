# Closira Backend Assignment

A lightweight FastAPI backend that simulates Closira's customer enquiry-handling workflow.

## Objective

This project accepts inbound customer enquiries, processes them asynchronously using SOP keyword matching, stores enquiry history in SQLite, supports follow-ups and escalation, and exposes a health check endpoint.

## Tech Stack

- Python
- FastAPI
- SQLite
- SQLAlchemy
- FastAPI BackgroundTasks
- Pydantic
- JSON structured logging

## Why FastAPI BackgroundTasks instead of Celery?

For this assignment, FastAPI BackgroundTasks is used because the requirement is to simulate asynchronous enquiry processing in a lightweight prototype. Celery is better for production workloads with retries, queues, distributed workers, and Redis/RabbitMQ, but it adds extra setup complexity. Since this assignment values clarity and ownership over production-level infrastructure, BackgroundTasks is the faster and cleaner choice.

## Why SQLite instead of PostgreSQL?

SQLite is used because this is a small prototype with local setup requirements. It avoids external database setup and makes the project easy to run and review. PostgreSQL would be a better choice for production because of stronger concurrency, scalability, and multi-tenant support.

## Folder Structure

```text
closira_ai_support_assignment/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── sop_engine.py
│   ├── tasks.py
│   └── logger.py
├── tests.http
├── requirements.txt
├── README.md
└── .gitignore
```

## Setup Instructions

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

### 4. Open API documentation

Visit:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/enquiry` | Create inbound enquiry and trigger async processing |
| POST | `/enquiry/{id}/follow-up` | Schedule follow-up |
| POST | `/enquiry/{id}/escalate` | Escalate enquiry to human agent |
| GET | `/enquiry/{id}/history` | Get enquiry history and timeline |
| GET | `/health` | API and database health check |

### Example Request Payloads

Create enquiry:
```json
{
  "channel": "whatsapp",
  "customer_name": "Sarah M.",
  "message": "I want to book an appointment for tomorrow."
}
```

Follow-up request:
```json
{
  "delay_minutes": 30,
  "message_template": "Hi, following up on your enquiry."
}
```

Escalation request:
```json
{
  "reason": "Customer requested a human agent."
}
```

## SOP Matching Logic

The backend uses simple keyword logic to match enquiries to hardcoded SOPs:

| SOP | Example Keywords |
|---|---|
| Booking enquiry | booking, appointment, schedule |
| Pricing question | price, pricing, cost, quote |
| Complaint | complaint, unhappy, issue, problem |
| After-hours message | urgent, emergency, after hours |

If no SOP matches, the enquiry is automatically escalated.

## Known Limitations

- No authentication.
- No real AI model integration.
- BackgroundTasks do not provide production-grade queueing or retries.
- SQLite is not ideal for high-concurrency production use.
- Follow-up scheduling is stored but not executed by a real scheduler.

## Testing

Use the included `tests.http` file in VS Code with the REST Client extension.
