from dataclasses import dataclass


@dataclass
class SOPResult:
    sop_name: str | None
    suggested_response: str | None
    should_escalate: bool
    escalation_reason: str | None = None


SOP_RULES = [
    {
        "name": "Booking Enquiry",
        "keywords": ["booking", "book", "appointment", "schedule", "reservation"],
        "response": "Thanks for reaching out. We can help you schedule a booking. Please share your preferred date and time.",
    },
    {
        "name": "Pricing Question",
        "keywords": ["price", "pricing", "cost", "quote", "charges", "plan"],
        "response": "Thanks for your interest. We will share the relevant pricing details and help you choose the right plan.",
    },
    {
        "name": "Complaint",
        "keywords": ["complaint", "unhappy", "issue", "problem", "bad", "refund"],
        "response": "Sorry for the inconvenience. Your concern has been noted and our team will review it shortly.",
    },
    {
        "name": "After Hours Message",
        "keywords": ["urgent", "emergency", "after hours", "asap"],
        "response": "We have received your urgent request. Our team will prioritize this and respond as soon as possible.",
    },
]


def match_sop(message: str) -> SOPResult:
    normalized_message = message.lower()

    for rule in SOP_RULES:
        if any(keyword in normalized_message for keyword in rule["keywords"]):
            return SOPResult(
                sop_name=rule["name"],
                suggested_response=rule["response"],
                should_escalate=False,
            )

    return SOPResult(
        sop_name=None,
        suggested_response=None,
        should_escalate=True,
        escalation_reason="No SOP matched the inbound message.",
    )
