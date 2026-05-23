from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created")
    matched_sop: Mapped[str | None] = mapped_column(String(100), nullable=True)
    suggested_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list["EnquiryEvent"]] = relationship(
        "EnquiryEvent",
        back_populates="enquiry",
        cascade="all, delete-orphan",
    )


class EnquiryEvent(Base):
    __tablename__ = "enquiry_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    enquiry: Mapped["Enquiry"] = relationship("Enquiry", back_populates="events")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enquiry_id: Mapped[int] = mapped_column(ForeignKey("enquiries.id"), nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
