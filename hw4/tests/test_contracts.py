import pytest
from datetime import datetime
from pydantic import SecretStr
from demo_service.api.contracts import RegisterUserRequest, UserResponse
from demo_service.core.users import UserInfo, UserEntity, UserRole


def test_register_user_request():
    request_data = {
        "username": "john_doe",
        "name": "John Doe",
        "birthdate": "1990-01-01T00:00:00",
        "password": "Secret123"
    }
    request = RegisterUserRequest(**request_data)
    assert request.username == "john_doe"
    assert request.name == "John Doe"
    assert request.password.get_secret_value() == "Secret123"


def test_user_response_from_entity(mock_user_entity):
    user_entity = mock_user_entity

    response = UserResponse.from_user_entity(user_entity)

    assert response.uid == user_entity.uid
    assert response.username == user_entity.info.username
    assert response.name == user_entity.info.name
    assert response.birthdate == user_entity.info.birthdate
    assert response.role == user_entity.info.role


@pytest.fixture
def mock_user_entity():
    user_info = UserInfo(
        username="admin",
        name="Admin User",
        birthdate=datetime(1970, 1, 1),
        role=UserRole.ADMIN,
        password=SecretStr("superSecretAdminPassword123")
    )

    user_entity = UserEntity(
        uid=1,
        info=user_info
    )

    return user_entity
