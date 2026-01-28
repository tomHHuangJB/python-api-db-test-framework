import json
from pathlib import Path

import pytest
import requests

from tests.utils.allure_helpers import attach_json, attach_text

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str):
    return json.loads((DATA_DIR / name).read_text())


@pytest.mark.parametrize("payload", _load_json("items_valid.json"))
def test_create_items_valid(api_client, db, cleanup_items, payload):
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    item_id = resp.json()["id"]
    cleanup_items.append(item_id)

    row = db.fetch_one("SELECT id, name, description FROM items WHERE id = %s;", (item_id,))
    assert row is not None
    assert row[0] == item_id
    assert row[1] == payload["name"]
    assert row[2] == payload["description"]


@pytest.mark.parametrize("payload", _load_json("items_invalid.json"))
def test_create_items_invalid(api_client, payload):
    resp = api_client.create_item(payload)
    assert resp.status_code == 422


@pytest.mark.smoke
def test_health(api_client):
    resp = api_client.health()
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.smoke
def test_create_item_and_db_validation(api_client, db, cleanup_items):
    payload = {"name": "gamma", "description": "from test"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    item_id = resp.json()["id"]
    cleanup_items.append(item_id)

    row = db.fetch_one("SELECT id, name, description FROM items WHERE id = %s;", (item_id,))
    assert row is not None
    assert row[0] == item_id
    assert row[1] == payload["name"]
    assert row[2] == payload["description"]


@pytest.mark.negative
def test_create_item_missing_api_key(api_client):
    resp = requests.post(
        f"{api_client.base_url}/items",
        json={"name": "no-auth", "description": "fail"},
        timeout=5,
    )
    assert resp.status_code == 401


@pytest.mark.negative
def test_create_item_invalid_api_key():
    from tests.clients.api_client import ApiClient

    client = ApiClient(api_key="wrong-key")
    resp = client.create_item({"name": "no-auth", "description": "fail"})
    assert resp.status_code == 401


@pytest.mark.negative
def test_update_nonexistent_item(api_client):
    resp = api_client.update_item(999999, {"name": "missing", "description": "none"})
    assert resp.status_code == 404


@pytest.mark.negative
def test_delete_nonexistent_item(api_client):
    resp = api_client.delete_item(999999)
    assert resp.status_code == 404


@pytest.mark.security
def test_injection_like_payload_is_safely_stored(api_client, db, cleanup_items):
    payload = {"name": "x'); DROP TABLE items; --", "description": "inj"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    item_id = resp.json()["id"]
    cleanup_items.append(item_id)

    row = db.fetch_one("SELECT name FROM items WHERE id = %s;", (item_id,))
    assert row is not None
    assert row[0] == payload["name"]

    count = db.fetch_value("SELECT COUNT(*) FROM items;")
    assert count is not None


def test_search_items_by_name(api_client, db, cleanup_items):
    payload = {"name": "searchable-name", "description": "search me"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    item_id = resp.json()["id"]
    cleanup_items.append(item_id)

    resp = api_client.search_items("searchable")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert item_id in ids


def test_api_and_db_counts_match(api_client, db):
    resp = api_client.list_items()
    assert resp.status_code == 200
    api_count = len(resp.json())
    db_count = db.fetch_value("SELECT COUNT(*) FROM items;")
    assert api_count == db_count


def test_delete_item_and_db_validation(api_client, db):
    row = db.fetch_one(
        "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
        ("temp", "to delete"),
    )
    item_id = row[0]

    resp = api_client.delete_item(item_id)
    assert resp.status_code == 204

    row = db.fetch_one("SELECT id FROM items WHERE id = %s;", (item_id,))
    assert row is None


def test_allure_custom_attachment_example():
    attach_json("sample_payload", {"name": "demo", "description": "custom attachment"})
    attach_text("sample_note", "This is an example of a custom attachment.")
