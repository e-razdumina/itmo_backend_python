import pytest
from hw4.demo_service.api.utils import user_service, value_error_handler
from fastapi.testclient import TestClient


def test_password_validators():
    user_svc = user_service(request=TestClient(app).request)
    valid_password = "Password123"
    invalid_password = "short"

    assert user_svc.validate_password(valid_password)
    with pytest.raises(ValueError):
        user_svc.validate_password(invalid_password)


def test_value_error_handler():
    request = TestClient(app).request
    with pytest.raises(ValueError):
        raise ValueError("This is a test error")
    response = value_error_handler(request, ValueError("This is a test error"))
    assert response.status_code == 400
    assert response.json() == {"detail": "This is a test error"}
