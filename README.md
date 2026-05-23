# Closira Backend Assignment

A lightweight FastAPI backend that simulates Closira's customer enquiry workflow. It accepts inbound enquiries, matches them against simple SOP rules, stores the enquiry timeline in SQLite, and supports follow-ups, escalation, history lookup, and health checks.

The project is intentionally simple: no Docker, no Celery, no Redis, no authentication, and no external database setup. The goal is to show clean backend structure and practical engineering judgment without unnecessary production infrastructure.

## Workflow

1. A customer enquiry is submitted through `POST /enquiry`.
2. The enquiry is saved in SQLite with status `created`.
3. A FastAPI `BackgroundTasks` job runs SOP matching.
4. If a keyword-based SOP matches, the enquiry becomes `processed` and stores the suggested response.
5. If no SOP matches, the enquiry is escalated automatically.
6. Follow-ups and manual escalations can be added through separate endpoints.
7. `GET /enquiry/{id}/history` returns the full enquiry record and timeline.

## Architecture Workflow

```text
Client / REST caller
        |
        v
FastAPI route handlers
        |
        v
Pydantic schemas validate request data
        |
        v
CRUD helpers persist enquiry and timeline events
        |
        v
FastAPI BackgroundTasks runs SOP processing
        |
        v
SOP engine returns a match or escalation decision
        |
        v
SQLite stores final status, suggested response, and history
```

This keeps responsibilities separated without adding heavy layers. Routes handle HTTP concerns, schemas define API contracts, CRUD functions own persistence, and the SOP engine owns matching logic.

## Tech Stack

- Python
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- FastAPI BackgroundTasks
- JSON structured logging

## Folder Structure

```text
closira_ai/
├── app/
│   ├── __init__.py
│   ├── config.py        # Environment-backed settings
│   ├── crud.py          # Database write/read helpers
│   ├── database.py      # SQLAlchemy engine and session setup
│   ├── docs.py          # OpenAPI example payloads
│   ├── logger.py        # Structured JSON logger
│   ├── main.py          # FastAPI app, routes, middleware
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── sop_engine.py    # Keyword-based SOP matching
│   └── tasks.py         # Background enquiry processing
├── .env.example
├── requirements.txt
├── tests.http
└── README.md
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: configure the database URL. SQLite is the default, so this step can be skipped for local use. The app reads environment variables from the shell; `.env.example` documents the expected value.

```bash
cp .env.example .env
export DATABASE_URL=sqlite:///./closira.db
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open the interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/enquiry` | Creates an inbound enquiry and starts background SOP processing. |
| `POST` | `/enquiry/{enquiry_id}/follow-up` | Schedules a follow-up for an enquiry that is not escalated. |
| `POST` | `/enquiry/{enquiry_id}/escalate` | Manually escalates an enquiry to a human agent. |
| `GET` | `/enquiry/{enquiry_id}/history` | Returns enquiry details, SOP result, escalation reason, and timeline events. |
| `GET` | `/health` | Checks API and database availability. |

## Example Requests

Create an enquiry:

```bash
curl -X POST http://127.0.0.1:8000/enquiry \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "whatsapp",
    "customer_name": "Sarah M.",
    "message": "I want to book an appointment tomorrow afternoon."
  }'
```

Schedule a follow-up:

```bash
curl -X POST http://127.0.0.1:8000/enquiry/1/follow-up \
  -H "Content-Type: application/json" \
  -d '{
    "delay_minutes": 30,
    "message_template": "Hi, following up on your enquiry."
  }'
```

Escalate an enquiry:

```bash
curl -X POST http://127.0.0.1:8000/enquiry/1/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Customer requested a human agent."
  }'
```

Get history:

```bash
curl http://127.0.0.1:8000/enquiry/1/history
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

## Example API Responses

Successful enquiry creation:

```json
{
  "job_id": 1,
  "status": "accepted",
  "message": "Enquiry received and queued for background processing."
}
```

Processed enquiry history:

```json
{
  "id": 1,
  "channel": "whatsapp",
  "customer_name": "Sarah M.",
  "message": "I want to book an appointment tomorrow afternoon.",
  "status": "processed",
  "matched_sop": "Booking Enquiry",
  "suggested_response": "Thanks for reaching out. We can help you schedule a booking. Please share your preferred date and time.",
  "escalation_reason": null,
  "created_at": "2026-05-23T19:30:12.541000",
  "timeline": [
    {
      "event_type": "enquiry_created",
      "details": "Inbound enquiry created.",
      "created_at": "2026-05-23T19:30:12.541000"
    },
    {
      "event_type": "sop_matched",
      "details": "Matched SOP: Booking Enquiry",
      "created_at": "2026-05-23T19:30:12.549000"
    }
  ]
}
```

Auto-escalated enquiry history:

```json
{
  "id": 2,
  "channel": "email",
  "customer_name": "Amit K.",
  "message": "Can someone help me with a custom partnership request?",
  "status": "escalated",
  "matched_sop": null,
  "suggested_response": null,
  "escalation_reason": "No SOP matched the inbound message.",
  "created_at": "2026-05-23T19:35:00.100000",
  "timeline": [
    {
      "event_type": "enquiry_created",
      "details": "Inbound enquiry created.",
      "created_at": "2026-05-23T19:35:00.100000"
    },
    {
      "event_type": "escalation_triggered",
      "details": "No SOP matched the inbound message.",
      "created_at": "2026-05-23T19:35:00.112000"
    }
  ]
}
```

## SOP Matching

The SOP engine uses simple keyword matching to keep the assignment transparent and easy to review.

| SOP | Keywords | Outcome |
|---|---|---|
| Booking Enquiry | booking, book, appointment, schedule, reservation | Stores a booking-focused suggested response. |
| Pricing Question | price, pricing, cost, quote, charges, plan | Stores a pricing-focused suggested response. |
| Complaint | complaint, unhappy, issue, problem, bad, refund | Stores a complaint acknowledgement response. |
| After Hours Message | urgent, emergency, after hours, asap | Stores an urgent-request acknowledgement response. |

If no SOP matches, the enquiry is escalated automatically with the reason `No SOP matched the inbound message.`

## Logging

Logs are emitted as JSON and include:

- `timestamp`
- `level`
- `event`
- `enquiry_id`
- `method`
- `route`
- `status_code`
- `duration_ms`

The request logging middleware records every API request with method, route, status code, and duration. Domain events such as `enquiry_created`, `sop_matched`, and `escalation_triggered` include `enquiry_id` where available.

Startup log:

```json
{
  "timestamp": "2026-05-23 19:30:00,100",
  "level": "INFO",
  "event": "app_started",
  "enquiry_id": null,
  "database_connected": true,
  "environment_loaded": true,
  "message": "app started"
}
```

SOP match log:

```json
{
  "timestamp": "2026-05-23 19:30:12,549",
  "level": "INFO",
  "event": "sop_matched",
  "enquiry_id": 1
}
```

Request log:

```json
{
  "timestamp": "2026-05-23 19:30:12,555",
  "level": "INFO",
  "event": "request_completed",
  "enquiry_id": "1",
  "method": "GET",
  "route": "/enquiry/{enquiry_id}/history",
  "status_code": 200,
  "duration_ms": 2.73,
  "message": "request completed"
}
```

## BackgroundTasks vs Celery

FastAPI `BackgroundTasks` is used because this is a local assignment prototype. It keeps the runtime simple while still showing asynchronous-style processing after the API accepts an enquiry.

Celery would be better for production workloads that need durable queues, retries, distributed workers, scheduled jobs, and Redis or RabbitMQ. For this assignment, Celery would add operational complexity without improving the core demonstration.

## SQLite vs PostgreSQL

SQLite is the default because it requires no external setup and makes the project easy to run during review.

PostgreSQL would be the stronger production choice for higher concurrency, stronger operational tooling, migrations, backups, and multi-user workloads. The code keeps `DATABASE_URL` configurable so the storage layer can evolve without changing route logic.

## Project Assumptions

- Enquiry volume is small enough for a local prototype.
- SOP matching can be keyword-based for assignment review.
- Background processing only needs to demonstrate asynchronous-style behavior.
- Follow-up execution is out of scope; the API records follow-up intent.
- Human-agent workflows are represented by escalation status and reason.
- Environment configuration is provided through shell variables.

## Why This Structure Scales Reasonably For SMB Workflows

Small and medium businesses often need clear, auditable workflows before they need distributed infrastructure. This project keeps the core workflow easy to inspect: every enquiry has a status, every major action creates a timeline event, and logs expose request and domain activity.

The file structure can grow gradually. More SOP rules can be added in `sop_engine.py`, persistence logic can stay in `crud.py`, API contracts can evolve in `schemas.py`, and heavier infrastructure such as PostgreSQL, migrations, or a real queue can be introduced later without rewriting the route layer.

## Known Limitations

- No authentication or authorization.
- No database migrations.
- No production-grade task queue or retry mechanism.
- Follow-ups are stored but not executed by a scheduler.
- SOP matching is keyword-based, not AI-powered.
- SQLite is not intended for high-concurrency production traffic.

## Future Improvements

- Add Alembic migrations.
- Add automated tests with pytest and FastAPI `TestClient`.
- Add authentication for staff-only operations.
- Replace keyword SOP matching with an AI or rules service.
- Add a real scheduler for follow-up execution.
- Move to PostgreSQL for production deployment.
- Add CI checks for linting and tests.

## Testing

Use `tests.http` with the VS Code REST Client extension, or run the `curl` commands above after starting the server.
