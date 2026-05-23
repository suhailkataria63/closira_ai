from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from pydantic.types import StringConstraints


Channel = Literal["whatsapp", "email", "call"]
EnquiryStatus = Literal["accepted", "created", "processed", "follow_up_scheduled", "escalated"]
FollowUpStatus = Literal["scheduled"]
NonEmptyShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
NonEmptyMessage = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=2000)]
ReasonText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)]


class EnquiryCreate(BaseModel):
    channel: Channel = Field(..., description="Inbound channel used by the customer.", examples=["whatsapp"])
    customer_name: NonEmptyShortText = Field(..., description="Customer display name.", examples=["Sarah M."])
    message: NonEmptyMessage = Field(
        ...,
        description="Raw customer enquiry text.",
        examples=["I want to book an appointment tomorrow afternoon."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "channel": "whatsapp",
                "customer_name": "Sarah M.",
                "message": "I want to book an appointment tomorrow afternoon.",
            }
        }
    }


class EnquiryCreateResponse(BaseModel):
    job_id: int
    status: Literal["accepted"]
    message: str


class FollowUpCreate(BaseModel):
    delay_minutes: int = Field(..., ge=1, le=10080, description="Delay before follow-up, in minutes.", examples=[30])
    message_template: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)] | None = Field(
        None,
        description="Optional message template for the follow-up.",
        examples=["Hi, following up on your enquiry."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "delay_minutes": 30,
                "message_template": "Hi, following up on your enquiry.",
            }
        }
    }


class FollowUpResponse(BaseModel):
    enquiry_id: int
    status: FollowUpStatus
    delay_minutes: int
    message_template: str | None


class EscalationCreate(BaseModel):
    reason: ReasonText = Field(
        ...,
        description="Reason the enquiry needs human attention.",
        examples=["Customer requested a human agent."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reason": "Customer requested a human agent.",
            }
        }
    }


class EscalationResponse(BaseModel):
    enquiry_id: int
    status: Literal["escalated"]
    reason: str


class EventResponse(BaseModel):
    event_type: str
    details: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EnquiryHistoryResponse(BaseModel):
    id: int
    channel: Channel
    customer_name: str
    message: str
    status: EnquiryStatus
    matched_sop: str | None
    suggested_response: str | None
    escalation_reason: str | None
    created_at: datetime
    timeline: list[EventResponse]


class HealthResponse(BaseModel):
    api_status: Literal["ok"]
    database_status: Literal["connected"]
