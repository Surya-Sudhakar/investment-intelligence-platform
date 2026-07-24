class AppException(Exception):
    def __init__(
        self, code: str, message: str, status_code: int, details: object | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class DatabaseUnavailableError(AppException):
    def __init__(self) -> None:
        super().__init__("DATABASE_UNAVAILABLE", "The service is temporarily unavailable.", 503)
