import pytest
from hw4.demo_service.core.users import UserService, UserInfo, UserEntity, UserRole, password_is_longer_than_8
from pydantic import SecretStr
from datetime import datetime


@pytest.fixture
def user_service():
    # Initialize UserService with password validators
    return UserService(password_validators=[password_is_longer_than_8])


def test_register_user_success(user_service):
    user_info = UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("validPassword123")
    )
    user_entity = user_service.register(user_info)

    assert user_entity.uid == 1
    assert user_entity.info.username == "john_doe"
    assert user_entity.info.role == UserRole.USER


def test_register_username_taken(user_service):
    user_info = UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("validPassword123")
    )
    user_service.register(user_info)

    # Attempt to register with the same username
    with pytest.raises(ValueError, match="username is already taken"):
        user_service.register(user_info)


def test_register_invalid_password(user_service):
    # Create a user with a short password (invalid)
    user_info = UserInfo(
        username="jane_doe",
        name="Jane Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("short")
    )

    # Expect ValueError due to invalid password
    with pytest.raises(ValueError, match="invalid password"):
        user_service.register(user_info)


def test_get_user_by_username(user_service):
    user_info = UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("validPassword123")
    )
    user_service.register(user_info)

    user = user_service.get_by_username("john_doe")
    assert user is not None
    assert user.info.username == "john_doe"


def test_get_user_by_id(user_service):
    user_info = UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("validPassword123")
    )
    user_entity = user_service.register(user_info)

    user = user_service.get_by_id(user_entity.uid)
    assert user is not None
    assert user.uid == 1
    assert user.info.username == "john_doe"


def test_get_nonexistent_user(user_service):
    user = user_service.get_by_username("nonexistent_user")
    assert user is None

    user_by_id = user_service.get_by_id(999)
    assert user_by_id is None


def test_grant_admin_success(user_service):
    user_info = UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=datetime(1990, 1, 1),
        password=SecretStr("validPassword123")
    )
    user_entity = user_service.register(user_info)

    # Grant admin role to the user
    user_service.grant_admin(user_entity.uid)

    user = user_service.get_by_id(user_entity.uid)
    assert user.info.role == UserRole.ADMIN


def test_grant_admin_nonexistent_user(user_service):
    # Attempt to grant admin to a non-existent user
    with pytest.raises(ValueError, match="user not found"):
        user_service.grant_admin(999)


def test_password_is_longer_than_8():
    assert password_is_longer_than_8("validPassword123")
    assert not password_is_longer_than_8("short")
