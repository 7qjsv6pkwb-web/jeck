from fastapi.testclient import TestClient

from app.main import app


def test_list_executor_handlers():
    client = TestClient(app)
    response = client.get("/v1/executor/handlers")
    assert response.status_code == 200
    body = response.json()
    handlers = body["handlers"]
    assert handlers == sorted(handlers)
    assert "artifact.store" in handlers
    assert "stub.echo" in handlers
