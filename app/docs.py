ENQUIRY_CREATE_RESPONSE_EXAMPLE = {
    "job_id": 1,
    "status": "accepted",
    "message": "Enquiry received and queued for background processing.",
}

FOLLOW_UP_RESPONSE_EXAMPLE = {
    "enquiry_id": 1,
    "status": "scheduled",
    "delay_minutes": 30,
    "message_template": "Hi, following up on your enquiry.",
}

ESCALATION_RESPONSE_EXAMPLE = {
    "enquiry_id": 1,
    "status": "escalated",
    "reason": "Customer requested a human agent.",
}

PROCESSED_HISTORY_RESPONSE_EXAMPLE = {
    "id": 1,
    "channel": "whatsapp",
    "customer_name": "Sarah M.",
    "message": "I want to book an appointment tomorrow afternoon.",
    "status": "processed",
    "matched_sop": "Booking Enquiry",
    "suggested_response": (
        "Thanks for reaching out. We can help you schedule a booking. "
        "Please share your preferred date and time."
    ),
    "escalation_reason": None,
    "created_at": "2026-05-23T19:30:12.541000",
    "timeline": [
        {
            "event_type": "enquiry_created",
            "details": "Inbound enquiry created.",
            "created_at": "2026-05-23T19:30:12.541000",
        },
        {
            "event_type": "sop_matched",
            "details": "Matched SOP: Booking Enquiry",
            "created_at": "2026-05-23T19:30:12.549000",
        },
    ],
}

AUTO_ESCALATED_HISTORY_RESPONSE_EXAMPLE = {
    "id": 2,
    "channel": "email",
    "customer_name": "Amit K.",
    "message": "Can someone help me with a custom partnership request?",
    "status": "escalated",
    "matched_sop": None,
    "suggested_response": None,
    "escalation_reason": "No SOP matched the inbound message.",
    "created_at": "2026-05-23T19:35:00.100000",
    "timeline": [
        {
            "event_type": "enquiry_created",
            "details": "Inbound enquiry created.",
            "created_at": "2026-05-23T19:35:00.100000",
        },
        {
            "event_type": "escalation_triggered",
            "details": "No SOP matched the inbound message.",
            "created_at": "2026-05-23T19:35:00.112000",
        },
    ],
}
