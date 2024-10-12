from locust import HttpUser, task, between, events
from uuid import uuid4
from faker import Faker
import websockets
import asyncio
import json
import httpx

faker = Faker()
API_BASE_URL = "http://localhost:8000"


class FastAPIUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def create_cart(self):
        # Create a new cart
        response = self.client.post("/cart")
        if response.status_code == 201:
            cart_id = response.json()["id"]

    @task
    def add_items_to_cart(self):
        # Add items to cart
        items = [{"name": f"Item {i}", "price": faker.pyfloat(min_value=10.0, max_value=100.0)} for i in range(5)]
        for item in items:
            response = self.client.post("/item", json=item)
            if response.status_code == 201:
                item_id = response.json()["id"]
                cart_response = self.client.post("/cart")
                if cart_response.status_code == 201:
                    cart_id = cart_response.json()["id"]
                    self.client.post(f"/cart/{cart_id}/add/{item_id}")

    @task
    def get_cart_list(self):
        # Retrieve a list of carts
        response = self.client.get("/cart", params={"offset": 0, "limit": 5})
        if response.status_code == 200:
            carts = response.json()

    @task
    def get_items(self):
        # Retrieve a list of items
        self.client.get("/item", params={"offset": 0, "limit": 10})

    @task
    def delete_item(self):
        # Create and delete an item
        item_data = {"name": "Item to delete", "price": 9.99}
        response = self.client.post("/item", json=item_data)
        if response.status_code == 201:
            item_id = response.json()["id"]
            self.client.delete(f"/item/{item_id}")


# Event listener to track test start and stop events
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test stopped")
