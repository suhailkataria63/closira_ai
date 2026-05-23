import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./closira.db")
    app_name: str = os.getenv("APP_NAME", "Closira Enquiry Handling Backend")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def database_connect_args(self) -> dict[str, bool]:
        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}


settings = Settings()
