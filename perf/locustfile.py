import os

from locust import HttpUser, between, task


API_KEY = os.getenv("API_KEY", "local-dev-key")


class ApiUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.client.headers.update({"X-API-Key": API_KEY})

    @task(2)
    def list_items(self):
        self.client.get("/items")

    @task(1)
    def create_item(self):
        payload = {"name": "perf-item", "description": "load"}
        self.client.post("/items", json=payload)

