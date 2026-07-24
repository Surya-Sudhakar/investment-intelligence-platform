import json
import logging
from datetime import UTC, datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    def __init__(self, service: str, environment: str, json_logs: bool) -> None:
        super().__init__()
        self.service = service
        self.environment = environment
        self.json_logs = json_logs

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self.service,
            "environment": self.environment,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "route", "status_code", "duration_ms", "error_type"):
            value = getattr(record, key, None)
            if value is not None:
                data[key] = value
        if self.json_logs:
            return json.dumps(data, default=str)
        context = " ".join(f"{key}={value}" for key, value in data.items() if key != "message")
        return f"{context} message={data['message']}"


def configure_logging(service: str, environment: str, level: str, json_logs: bool) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter(service, environment, json_logs))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
