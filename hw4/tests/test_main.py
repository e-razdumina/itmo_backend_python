from fastapi.testclient import TestClient
from demo_service.api.main import create_app
from http import HTTPStatus

# Create the FastAPI app
app = create_app()


def test_create_app():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == HTTPStatus.OK
    assert response.json()
