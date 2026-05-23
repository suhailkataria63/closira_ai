from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


Channel = Literal["whatsapp", "email", "call"]


class EnquiryCreate(BaseModel):
    channel: Channel = Field(..., examples=["whatsapp"])
    customer_name: str = Field(..., min_length=1, examples=["Sarah M."])
    message: str = Field(..., min_length=1, examples=["I want to book an appointment tomorrow."])


class EnquiryCreateResponse(BaseModel):
    job_id: int
    status: str
    message: str


class FollowUpCreate(BaseModel):
    delay_minutes: int = Field(..., gt=0, examples=[30])
    message_template: str | None = Field(None, examples=["Hi, following up on your enquiry."])


class FollowUpResponse(BaseModel):
    enquiry_id: int
    status: str
    delay_minutes: int
    message_template: str | None


class EscalationCreate(BaseModel):
    reason: str = Field(..., min_length=1, examples=["Customer requested a human agent."])


class EscalationResponse(BaseModel):
    enquiry_id: int
    status: str
    reason: str


class EventResponse(BaseModel):
    event_type: str
    details: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EnquiryHistoryResponse(BaseModel):
    id: int
    channel: str
    customer_name: str
    message: str
    status: str
    matched_sop: str | None
    suggested_response: str | None
    escalation_reason: str | None
    created_at: datetime
    timeline: list[EventResponse]


class HealthResponse(BaseModel):
    api_status: str
    database_status: str
