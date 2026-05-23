from app.database import SessionLocal
from app.crud import add_event
from app.models import Enquiry
from app.sop_engine import match_sop
from app.logger import logger


def process_enquiry(enquiry_id: int) -> None:
    db = SessionLocal()
    try:
        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()

        if not enquiry:
            logger.error(
                "enquiry not found during background processing",
                extra={"event": "task_error", "enquiry_id": enquiry_id},
            )
            return

        result = match_sop(enquiry.message)

        if result.should_escalate:
            enquiry.status = "escalated"
            enquiry.matched_sop = None
            enquiry.suggested_response = None
            enquiry.escalation_reason = result.escalation_reason
            db.commit()

            add_event(db, enquiry.id, "escalation_triggered", result.escalation_reason or "No SOP matched.")
            logger.info(
                "enquiry escalated because no SOP matched",
                extra={"event": "escalation_triggered", "enquiry_id": enquiry.id},
            )
            return

        enquiry.status = "processed"
        enquiry.matched_sop = result.sop_name
        enquiry.suggested_response = result.suggested_response
        db.commit()

        add_event(db, enquiry.id, "sop_matched", f"Matched SOP: {result.sop_name}")
        add_event(db, enquiry.id, "task_processed", "Background task processed enquiry.")

        logger.info(
            "SOP matched successfully",
            extra={"event": "sop_matched", "enquiry_id": enquiry.id},
        )

    except Exception as exc:
        logger.exception(
            "background task failed",
            extra={"event": "task_failed", "enquiry_id": enquiry_id},
        )
    finally:
        db.close()
