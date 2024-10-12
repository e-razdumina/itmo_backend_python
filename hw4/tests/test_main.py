
from fastapi.testclient import TestClient
from hw4.demo_service.api.main import create_app

app = create_app()
client = TestClient(app)

def test_create_app():
    response = client.get("/openapi.json")
    assert response.status_code == 200  # Check if the app starts properly and OpenAPI schema is available.
