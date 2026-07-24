from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready_with_database(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_ready_when_database_unavailable() -> None:
    class BrokenSession:
        def execute(self, _: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("offline"))

    def broken_db() -> Generator[Session, None, None]:
        yield BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_db] = broken_db
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            response = test_client.get("/api/v1/ready", headers={"X-Request-ID": "test-id"})
        assert response.status_code == 503
        assert response.json() == {
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": "The service is temporarily unavailable.",
                "details": None,
                "request_id": "test-id",
            }
        }
    finally:
        app.dependency_overrides.clear()


def test_not_found_uses_error_schema(client: TestClient) -> None:
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["request_id"]
