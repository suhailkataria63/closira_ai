import logging
import sys
from pythonjsonlogger import jsonlogger

from app.config import settings


class LogContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        defaults = {
            "event": "application_log",
            "enquiry_id": None,
            "method": None,
            "route": None,
            "status_code": None,
            "duration_ms": None,
            "database_connected": None,
            "environment_loaded": None,
        }
        for key, value in defaults.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("closira_backend")
    logger.setLevel(settings.log_level.upper())
    logger.propagate = False

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(LogContextFilter())
    formatter = jsonlogger.JsonFormatter(
        (
            "%(asctime)s %(levelname)s %(event)s %(enquiry_id)s %(method)s "
            "%(route)s %(status_code)s %(duration_ms)s %(database_connected)s "
            "%(environment_loaded)s %(message)s"
        ),
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()
