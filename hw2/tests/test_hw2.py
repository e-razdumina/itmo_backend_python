from http import HTTPStatus
from typing import Any
from uuid import uuid4
import websockets
import asyncio

import pytest
from faker import Faker
import httpx
import re

faker = Faker()

API_BASE_URL = "http://localhost:8000"
CHAT_BASE_URL = "ws://localhost:8000/chat"


@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=API_BASE_URL)


@pytest.fixture(scope="session")
def existing_empty_cart_id(client) -> int:
    return client.post("/cart").json()["id"]


@pytest.fixture(scope="session")
def existing_items(client) -> list[int]:
    items = [
        {
            "name": f"Тестовый товар {i}",
            "price": faker.pyfloat(positive=True, min_value=10.0, max_value=500.0),
        }
        for i in range(10)
    ]
    return [client.post("/item", json=item).json()["id"] for item in items]


@pytest.fixture(scope="session", autouse=True)
def existing_not_empty_carts(client, existing_items: list[int]) -> list[int]:
    carts = []

    for i in range(20):
        cart_id: int = client.post("/cart").json()["id"]
        for item_id in faker.random_elements(existing_items, unique=False, length=i):
            client.post(f"/cart/{cart_id}/add/{item_id}")

        carts.append(cart_id)

    return carts


@pytest.fixture(scope="session")
def existing_not_empty_cart_id(client, existing_empty_cart_id: int, existing_items: list[int]) -> int:
    for item_id in faker.random_elements(existing_items, unique=False, length=3):
        client.post(f"/cart/{existing_empty_cart_id}/add/{item_id}")

    return existing_empty_cart_id


@pytest.fixture()
def existing_item(client) -> dict[str, Any]:
    return client.post(
        "/item",
        json={
            "name": f"Тестовый товар {uuid4().hex}",
            "price": faker.pyfloat(min_value=10.0, max_value=100.0),
        },
    ).json()


@pytest.fixture()
def deleted_item(client, existing_item: dict[str, Any]) -> dict[str, Any]:
    item_id = existing_item["id"]
    client.delete(f"/item/{item_id}")

    existing_item["deleted"] = True
    return existing_item


@pytest.mark.xfail()
def test_post_cart(client) -> None:
    response = client.post("/cart")

    assert response.status_code == HTTPStatus.CREATED
    assert "location" in response.headers
    assert "id" in response.json()


@pytest.mark.parametrize(
    ("cart", "not_empty"),
    [
        ("existing_empty_cart_id", False),
        ("existing_not_empty_cart_id", True),
    ],
)
def test_get_cart(request, client, cart: int, not_empty: bool) -> None:
    cart_id = request.getfixturevalue(cart)

    response = client.get(f"/cart/{cart_id}")

    assert response.status_code == HTTPStatus.OK
    response_json = response.json()

    len_items = len(response_json["items"])
    assert len_items > 0 if not_empty else len_items == 0

    if not_empty:
        price = 0

        for item in response_json["items"]:
            item_id = item["item_id"]
            price += client.get(f"/item/{item_id}").json()["price"] * item["quantity"]

        assert response_json["price"] == pytest.approx(price, 1e-8)
    else:
        assert response_json["price"] == 0.0


@pytest.mark.parametrize(
    ("query", "status_code"),
    [
        ({}, HTTPStatus.OK),
        ({"offset": 1, "limit": 2}, HTTPStatus.OK),
        ({"min_price": 1000.0}, HTTPStatus.OK),
        ({"max_price": 20.0}, HTTPStatus.OK),
        ({"min_quantity": 1}, HTTPStatus.OK),
        ({"max_quantity": 0}, HTTPStatus.OK),
        ({"offset": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"limit": 0}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"limit": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"min_price": -1.0}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"max_price": -1.0}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"min_quantity": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"max_quantity": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
    ],
)
def test_get_cart_list(client, query: dict[str, Any], status_code: int):
    response = client.get("/cart", params=query)

    assert response.status_code == status_code

    if status_code == HTTPStatus.OK:
        data = response.json()

        assert isinstance(data, list)

        if "min_price" in query:
            assert all(item["price"] >= query["min_price"] for item in data)

        if "max_price" in query:
            assert all(item["price"] <= query["max_price"] for item in data)

        quantity = sum(
            sum(item["quantity"] for item in cart["items"]) for cart in data
        )

        if "min_quantity" in query:
            assert quantity >= query["min_quantity"]

        if "max_quantity" in query:
            assert quantity <= query["max_quantity"]


def test_post_item(client) -> None:
    item = {"name": "test item", "price": 9.99}
    response = client.post("/item", json=item)

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()
    assert item["price"] == data["price"]
    assert item["name"] == data["name"]


def test_get_item(client, existing_item: dict[str, Any]) -> None:
    item_id = existing_item["id"]

    response = client.get(f"/item/{item_id}")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == existing_item


@pytest.mark.parametrize(
    ("query", "status_code"),
    [
        ({"offset": 2, "limit": 5}, HTTPStatus.OK),
        ({"min_price": 5.0}, HTTPStatus.OK),
        ({"max_price": 100.0}, HTTPStatus.OK),
        ({"show_deleted": True}, HTTPStatus.OK),
        ({"offset": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"limit": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"limit": 0}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"min_price": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"max_price": -1}, HTTPStatus.UNPROCESSABLE_ENTITY),
    ],
)
def test_get_item_list(client, query: dict[str, Any], status_code: int) -> None:
    response = client.get("/item", params=query)

    assert response.status_code == status_code

    if status_code == HTTPStatus.OK:
        data = response.json()

        assert isinstance(data, list)

        if "min_price" in query:
            assert all(item["price"] >= query["min_price"] for item in data)

        if "max_price" in query:
            assert all(item["price"] <= query["max_price"] for item in data)


@pytest.mark.parametrize(
    ("body", "status_code"),
    [
        ({}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"price": 9.99}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"name": "new name", "price": 9.99}, HTTPStatus.OK),
    ],
)
def test_put_item(client, existing_item: dict[str, Any], body: dict[str, Any], status_code: int) -> None:
    item_id = existing_item["id"]
    response = client.put(f"/item/{item_id}", json=body)

    assert response.status_code == status_code

    if status_code == HTTPStatus.OK:
        new_item = existing_item.copy()
        new_item.update(body)
        assert response.json() == new_item


@pytest.mark.parametrize(
    ("item", "body", "status_code"),
    [
        ("deleted_item", {}, HTTPStatus.NOT_MODIFIED),
        ("deleted_item", {"price": 9.99}, HTTPStatus.NOT_MODIFIED),
        ("deleted_item", {"name": "new name", "price": 9.99}, HTTPStatus.NOT_MODIFIED),
        ("existing_item", {}, HTTPStatus.OK),
        ("existing_item", {"price": 9.99}, HTTPStatus.OK),
        ("existing_item", {"name": "new name", "price": 9.99}, HTTPStatus.OK),
        (
                "existing_item",
                {"name": "new name", "price": 9.99, "odd": "value"},
                HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
                "existing_item",
                {"name": "new name", "price": 9.99, "deleted": True},
                HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
    ],
)
def test_patch_item(request, client, item: str, body: dict[str, Any], status_code: int) -> None:
    item_data: dict[str, Any] = request.getfixturevalue(item)
    item_id = item_data["id"]
    response = client.patch(f"/item/{item_id}", json=body)

    assert response.status_code == status_code

    if status_code == HTTPStatus.OK:
        patch_response_body = response.json()

        response = client.get(f"/item/{item_id}")
        patched_item = response.json()

        assert patched_item == patch_response_body


def test_delete_item(client, existing_item: dict[str, Any]) -> None:
    item_id = existing_item["id"]

    response = client.delete(f"/item/{item_id}")
    assert response.status_code == HTTPStatus.OK

    response = client.get(f"/item/{item_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = client.delete(f"/item/{item_id}")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_chat_room():
    chat_room_name = "room1"

    # Regular expression to match the format "{username} :: {message}"
    message_pattern = re.compile(r"(\w+) :: (.+)")

    # Connect two users to the same chat room
    async with websockets.connect(f"{CHAT_BASE_URL}/{chat_room_name}") as ws_user1, \
            websockets.connect(f"{CHAT_BASE_URL}/{chat_room_name}") as ws_user2:

        # User 1 sends a message
        await ws_user1.send("Hello from user 1")

        # Both users should receive the message
        received_message_1 = await ws_user1.recv()
        received_message_2 = await ws_user2.recv()

        # Check if the message format is correct for both users
        for received_message in [received_message_1, received_message_2]:
            match = message_pattern.match(received_message)
            assert match is not None, f"Message format is incorrect: {received_message}"

            username, message = match.groups()
            assert message == "Hello from user 1", f"Expected 'Hello from user 1', got '{message}'"

        # User 2 sends a message
        await ws_user2.send("Hello from user 2")

        # Both users should receive the message
        received_message_1 = await ws_user1.recv()
        received_message_2 = await ws_user2.recv()

        # Check if the message format is correct for both users
        for received_message in [received_message_1, received_message_2]:
            match = message_pattern.match(received_message)
            assert match is not None, f"Message format is incorrect: {received_message}"

            username, message = match.groups()
            assert message == "Hello from user 2", f"Expected 'Hello from user 2', got '{message}'"


@pytest.mark.asyncio
async def test_chat_room_isolated():
    # Two users in different rooms shouldn't receive each other's messages
    async with websockets.connect(f"{CHAT_BASE_URL}/roomA") as ws_user1, \
            websockets.connect(f"{CHAT_BASE_URL}/roomB") as ws_user2:

        # User 1 sends a message in room A
        await ws_user1.send("Message from user 1 in room A")

        # User 2 sends a message in room B
        await ws_user2.send("Message from user 2 in room B")

        # Try to receive from user1's WebSocket and expect a timeout
        try:
            user1_received = await asyncio.wait_for(ws_user1.recv(), timeout=1)
            print(f"User 1 received: {user1_received}")

        except asyncio.TimeoutError:
            print("User 1 did not receive a message, as expected")

        # Try to receive from user2's WebSocket and expect a timeout
        try:
            user2_received = await asyncio.wait_for(ws_user2.recv(), timeout=1)
            print(f"User 2 received: {user2_received}")
        except asyncio.TimeoutError:
            print("User 2 did not receive a message, as expected")

        # Ensure User 1 did not receive User 2's message
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(ws_user1.recv(), timeout=1)

        # Ensure User 2 did not receive User 1's message
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(ws_user2.recv(), timeout=1)


@pytest.mark.asyncio
async def test_high_load_cart_requests():
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        tasks = []
        # Simulate 100 concurrent POST requests to create carts
        for _ in range(100):
            tasks.append(client.post("/cart"))

        # Await all the requests
        responses = await asyncio.gather(*tasks)

        # Check that all responses are successful
        assert all(response.status_code == 201 for response in responses)
