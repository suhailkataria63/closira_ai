import time

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from starlette.requests import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import Base, engine, get_db
from app.logger import logger
from app.tasks import process_enquiry

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="FastAPI prototype for customer enquiry creation, SOP processing, follow-ups, escalation, and history tracking.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Enquiries", "description": "Endpoints for enquiry lifecycle management."},
        {"name": "Health", "description": "Service and database health checks."},
    ],
)


def route_name(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "request completed",
            extra={
                "event": "request_completed",
                "enquiry_id": request.path_params.get("enquiry_id"),
                "method": request.method,
                "route": route_name(request),
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )


def get_enquiry_or_404(db: Session, enquiry_id: int) -> models.Enquiry:
    enquiry = crud.get_enquiry(db, enquiry_id)
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found.",
        )
    return enquiry


@app.post(
    "/enquiry",
    response_model=schemas.EnquiryCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new inbound customer enquiry",
    description="Submit a new customer enquiry. The enquiry is accepted and processed asynchronously using background SOP matching.",
    response_description="Acknowledgement that the enquiry was accepted and queued for processing.",
    tags=["Enquiries"],
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Enquiry accepted. Processing continues in a FastAPI background task.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Request validation failed.",
        },
    },
)
def create_enquiry(
    enquiry: schemas.EnquiryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    db_enquiry = crud.create_enquiry(db, enquiry)

    logger.info(
        "enquiry created",
        extra={"event": "enquiry_created", "enquiry_id": db_enquiry.id},
    )

    background_tasks.add_task(process_enquiry, db_enquiry.id)

    return {
        "job_id": db_enquiry.id,
        "status": "accepted",
        "message": "Enquiry received and queued for background processing.",
    }


@app.post(
    "/enquiry/{enquiry_id}/follow-up",
    response_model=schemas.FollowUpResponse,
    summary="Schedule a follow-up for an open enquiry",
    description="Create a follow-up reminder for an enquiry that is not already escalated.",
    response_description="Details of the scheduled follow-up event.",
    tags=["Enquiries"],
    responses={
        status.HTTP_200_OK: {"description": "Follow-up scheduled successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "The enquiry cannot receive a follow-up in its current state."},
        status.HTTP_404_NOT_FOUND: {"description": "No enquiry exists for the supplied id."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Request validation failed."},
    },
)
def schedule_follow_up(
    enquiry_id: int,
    follow_up: schemas.FollowUpCreate,
    db: Session = Depends(get_db),
):
    enquiry = get_enquiry_or_404(db, enquiry_id)

    if enquiry.status == "escalated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule follow-up for an escalated enquiry.",
        )

    db_follow_up = crud.schedule_follow_up(db, enquiry, follow_up)

    logger.info(
        "follow-up scheduled",
        extra={"event": "follow_up_scheduled", "enquiry_id": enquiry.id},
    )

    return {
        "enquiry_id": enquiry.id,
        "status": db_follow_up.status,
        "delay_minutes": db_follow_up.delay_minutes,
        "message_template": db_follow_up.message_template,
    }


@app.post(
    "/enquiry/{enquiry_id}/escalate",
    response_model=schemas.EscalationResponse,
    summary="Escalate an enquiry to a human agent",
    description="Mark an enquiry as escalated and record the reason so it can be handled by a human support agent.",
    response_description="Confirmation that the enquiry was escalated.",
    tags=["Enquiries"],
    responses={
        status.HTTP_200_OK: {"description": "Enquiry escalated successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "The enquiry has already been escalated."},
        status.HTTP_404_NOT_FOUND: {"description": "No enquiry exists for the supplied id."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Request validation failed."},
    },
)
def escalate_enquiry(
    enquiry_id: int,
    escalation: schemas.EscalationCreate,
    db: Session = Depends(get_db),
):
    enquiry = get_enquiry_or_404(db, enquiry_id)

    if enquiry.status == "escalated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enquiry has already been escalated.",
        )

    updated_enquiry = crud.escalate_enquiry(db, enquiry, escalation.reason)

    logger.info(
        "enquiry escalated",
        extra={"event": "escalation_triggered", "enquiry_id": enquiry.id},
    )

    return {
        "enquiry_id": updated_enquiry.id,
        "status": updated_enquiry.status,
        "reason": updated_enquiry.escalation_reason,
    }


@app.get(
    "/enquiry/{enquiry_id}/history",
    response_model=schemas.EnquiryHistoryResponse,
    summary="Get full conversation history and status timeline",
    description="Retrieve the enquiry record together with its timeline of events, SOP match status, and any escalation details.",
    response_description="The enquiry history and lifecycle timeline.",
    tags=["Enquiries"],
    responses={
        status.HTTP_200_OK: {"description": "Enquiry history returned successfully."},
        status.HTTP_404_NOT_FOUND: {"description": "No enquiry exists for the supplied id."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Request validation failed."},
    },
)
def get_enquiry_history(
    enquiry_id: int,
    db: Session = Depends(get_db),
):
    enquiry = get_enquiry_or_404(db, enquiry_id)

    return {
        "id": enquiry.id,
        "channel": enquiry.channel,
        "customer_name": enquiry.customer_name,
        "message": enquiry.message,
        "status": enquiry.status,
        "matched_sop": enquiry.matched_sop,
        "suggested_response": enquiry.suggested_response,
        "escalation_reason": enquiry.escalation_reason,
        "created_at": enquiry.created_at,
        "timeline": enquiry.events,
    }


@app.get(
    "/health",
    response_model=schemas.HealthResponse,
    summary="Check API and database health",
    description="Return the service and database connection status.",
    response_description="Service health and database availability report.",
    tags=["Health"],
    responses={
        status.HTTP_200_OK: {"description": "API and database are reachable."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database connection failed."},
    },
)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "api_status": "ok",
            "database_status": "connected",
        }
    except Exception:
        logger.exception(
            "database health check failed",
            extra={"event": "health_check_failed", "enquiry_id": None},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed.",
        )
