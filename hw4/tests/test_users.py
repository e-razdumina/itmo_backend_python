from fastapi.testclient import TestClient
from demo_service.api.main import create_app
import pytest
import uuid
from demo_service.core.users import UserService, UserInfo, UserRole, password_is_longer_than_8
from pydantic import SecretStr
from datetime import datetime
from http import HTTPStatus


# Create the FastAPI app
app = create_app()


@pytest.fixture
def valid_user_data():
    return {
        "username": f"john_doe_{uuid.uuid4()}",
        "name": "John Doe",
        "birthdate": "1990-01-01T00:00:00",
        "password": "Secret123"
    }


@pytest.fixture
def invalid_user_data():
    return {
        "username": "",
        "name": "",
        "birthdate": "invalid_date",
        "password": ""
    }


@pytest.fixture
def admin_credentials():
    return {
        "username": "admin",
        "password": "superSecretAdminPassword123"
    }


@pytest.fixture
def non_admin_credentials():
    return {
        "username": f"john_doe_{uuid.uuid4()}",
        "password": "Secret123"
    }


@pytest.fixture
def user_service():
    return UserService(password_validators=[password_is_longer_than_8])


def test_register_user_success(valid_user_data):
    with TestClient(app) as client:
        response = client.post("/user-register", json=valid_user_data)
        assert response.status_code == HTTPStatus.OK
        assert "uid" in response.json()


def test_register_user_failure(invalid_user_data):
    with TestClient(app) as client:
        response = client.post("/user-register", json=invalid_user_data)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "detail" in response.json()


def test_get_user_with_both_id_and_username(admin_credentials):
    with TestClient(app) as client:
        response = client.post("/user-get", auth=(admin_credentials["username"], admin_credentials["password"]),
                               params={"id": 1, "username": "admin"})
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "both id and username are provided"}


def test_get_user_with_neither_id_nor_username(admin_credentials):
    with TestClient(app) as client:
        response = client.post("/user-get", auth=(admin_credentials["username"], admin_credentials["password"]))
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "neither id nor username are provided"}


def test_get_user_not_found(admin_credentials):
    with TestClient(app) as client:
        response = client.post("/user-get", auth=(admin_credentials["username"], admin_credentials["password"]),
                               params={"id": 9999})
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("credentials_fixture, expected_status", [
    ("non_admin_credentials", HTTPStatus.UNAUTHORIZED),
    ("admin_credentials", HTTPStatus.OK)
])
def test_get_user_by_username(credentials_fixture, expected_status, request, valid_user_data):
    credentials = request.getfixturevalue(credentials_fixture)

    with TestClient(app) as client:
        response = client.post("/user-register", json=valid_user_data)
        assert response.status_code == HTTPStatus.OK

        response = client.post("/user-get", auth=(credentials["username"], credentials["password"]),
                               params={"username": valid_user_data["username"]})

        assert response.status_code == expected_status
        if response.status_code == HTTPStatus.OK:
            assert response.json()["username"] == valid_user_data["username"]


def test_promote_user_as_admin(admin_credentials):
    with TestClient(app) as client:
        response = client.post("/user-promote", auth=(admin_credentials["username"], admin_credentials["password"]),
                               params={"id": 1})
        assert response.status_code == HTTPStatus.OK


def test_promote_user_as_non_admin(non_admin_credentials, valid_user_data):
    with TestClient(app) as client:
        client.post("/user-register", json=valid_user_data)
    with TestClient(app) as client:
        response = client.post("/user-promote", auth=(valid_user_data["username"], valid_user_data["password"]),
                               params={"id": 1})
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_user_register_username_taken(user_service):
    user_info = UserInfo(username="john_doe", name="John Doe", birthdate=datetime.now(),
                         role=UserRole.USER, password=SecretStr("Secret123"))
    user_service.register(user_info)
    with pytest.raises(ValueError, match="username is already taken"):
        user_service.register(user_info)


def test_user_register_invalid_password(user_service):
    user_info = UserInfo(username="john_doe", name="John Doe", birthdate=datetime.now(),
                         role=UserRole.USER, password=SecretStr("short"))
    with pytest.raises(ValueError, match="invalid password"):
        user_service.register(user_info)


def test_grant_admin_user_not_found(user_service):
    with pytest.raises(ValueError, match="user not found"):
        user_service.grant_admin(9999)


def test_requires_admin_non_admin(non_admin_credentials, valid_user_data):
    with TestClient(app) as client:
        client.post("/user-register", json=valid_user_data)

        response = client.post("/user-promote", auth=(valid_user_data["username"], valid_user_data["password"]),
                               params={"id": 1})

        assert response.status_code == HTTPStatus.FORBIDDEN
