import pytest
from httpx import AsyncClient

from app import ServerApp


@pytest.fixture
def app():
    return ServerApp()


@pytest.mark.asyncio
async def test_factorial_success(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/factorial?n=5")
        assert response.status_code == 200
        assert response.json() == {"result": 120}


@pytest.mark.asyncio
async def test_fibonacci_success(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/fibonacci/10")
        assert response.status_code == 200
        assert response.json() == {"result": 55}


@pytest.mark.asyncio
async def test_mean_success(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/mean", json=[1, 2, 3, 4, 5])
        assert response.status_code == 200
        assert response.json() == {"result": 3.0}


@pytest.mark.asyncio
async def test_not_found(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/nonexistent")
        assert response.status_code == 404
        assert response.json() == {"error": "Not Found"}


@pytest.mark.asyncio
async def test_factorial_unprocessable_entity(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/factorial")
        assert response.status_code == 422
        assert response.json() == {"error": "Unprocessable Entity"}


@pytest.mark.asyncio
async def test_factorial_invalid_n(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/factorial?n=abc")
        assert response.status_code == 422
        assert response.json() == {"error": "Unprocessable Entity"}


@pytest.mark.asyncio
async def test_method_not_allowed(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/factorial?n=5")
        assert response.status_code == 405
        assert response.json() == {"error": "Method Not Allowed"}


@pytest.mark.asyncio
async def test_mean_unprocessable_entity(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/mean", json=[])
        assert response.status_code == 400
        assert response.json() == {"error": "Bad Request"}
