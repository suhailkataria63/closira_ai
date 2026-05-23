from sqlalchemy.orm import Session
from app import models, schemas


def add_event(db: Session, enquiry_id: int, event_type: str, details: str) -> models.EnquiryEvent:
    event = models.EnquiryEvent(
        enquiry_id=enquiry_id,
        event_type=event_type,
        details=details,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_enquiry(db: Session, enquiry: schemas.EnquiryCreate) -> models.Enquiry:
    db_enquiry = models.Enquiry(
        channel=enquiry.channel,
        customer_name=enquiry.customer_name,
        message=enquiry.message,
        status="created",
    )
    db.add(db_enquiry)
    db.commit()
    db.refresh(db_enquiry)
    add_event(db, db_enquiry.id, "enquiry_created", "Inbound enquiry created.")
    return db_enquiry


def get_enquiry(db: Session, enquiry_id: int) -> models.Enquiry | None:
    return db.query(models.Enquiry).filter(models.Enquiry.id == enquiry_id).first()


def schedule_follow_up(
    db: Session,
    enquiry: models.Enquiry,
    follow_up: schemas.FollowUpCreate,
) -> models.FollowUp:
    db_follow_up = models.FollowUp(
        enquiry_id=enquiry.id,
        delay_minutes=follow_up.delay_minutes,
        message_template=follow_up.message_template,
    )
    enquiry.status = "follow_up_scheduled"
    db.add(db_follow_up)
    db.commit()
    db.refresh(db_follow_up)
    add_event(
        db,
        enquiry.id,
        "follow_up_scheduled",
        f"Follow-up scheduled after {follow_up.delay_minutes} minutes.",
    )
    return db_follow_up


def escalate_enquiry(
    db: Session,
    enquiry: models.Enquiry,
    reason: str,
) -> models.Enquiry:
    enquiry.status = "escalated"
    enquiry.escalation_reason = reason
    db.commit()
    db.refresh(enquiry)
    add_event(db, enquiry.id, "escalation_triggered", reason)
    return enquiry
