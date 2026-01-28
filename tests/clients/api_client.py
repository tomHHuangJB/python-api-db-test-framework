import os

import requests


class ApiClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.api_key = api_key or os.getenv("API_KEY", "local-dev-key")
        self.last_response = None

    def _headers(self):
        return {"X-API-Key": self.api_key}

    def health(self):
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        self.last_response = resp
        return resp

    def create_item(self, payload: dict):
        resp = requests.post(
            f"{self.base_url}/items",
            json=payload,
            headers=self._headers(),
            timeout=5,
        )
        self.last_response = resp
        return resp

    def list_items(self):
        resp = requests.get(f"{self.base_url}/items", headers=self._headers(), timeout=5)
        self.last_response = resp
        return resp

    def search_items(self, name: str):
        resp = requests.get(
            f"{self.base_url}/items/search",
            params={"name": name},
            headers=self._headers(),
            timeout=5,
        )
        self.last_response = resp
        return resp

    def get_item(self, item_id: int):
        resp = requests.get(f"{self.base_url}/items/{item_id}", headers=self._headers(), timeout=5)
        self.last_response = resp
        return resp

    def update_item(self, item_id: int, payload: dict):
        resp = requests.put(
            f"{self.base_url}/items/{item_id}",
            json=payload,
            headers=self._headers(),
            timeout=5,
        )
        self.last_response = resp
        return resp

    def delete_item(self, item_id: int):
        resp = requests.delete(
            f"{self.base_url}/items/{item_id}",
            headers=self._headers(),
            timeout=5,
        )
        self.last_response = resp
        return resp
