import httpx
import pytest

BASE_URL = "http://localhost:8000"


def test_register_user():
    response = httpx.post(f"{BASE_URL}/user-register", json={
        "username": "john_doe",
        "name": "John Doe",
        "birthdate": "1990-01-01T00:00:00",
        "password": "Secret123"
    })

    assert response.status_code == 200
    assert "uid" in response.json()


def test_get_user():
    response = httpx.post(f"{BASE_URL}/user-get", params={"id": 1})

    assert response.status_code == 200
    assert response.json()["username"] == "john_doe"
