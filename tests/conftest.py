import json
import os

import allure
import pytest

from tests.clients import db_client
from tests.clients.api_client import ApiClient


@pytest.fixture(scope="session")
def api_client():
    return ApiClient()


@pytest.fixture(scope="session")
def db():
    return db_client


@pytest.fixture()
def cleanup_items(db):
    created_ids = []
    yield created_ids
    for item_id in created_ids:
        db.execute("DELETE FROM items WHERE id = %s;", (item_id,))


@pytest.fixture()
def context():
    return {}


def _attach_api_response(api_client):
    resp = api_client.last_response
    if not resp:
        return
    req = resp.request
    request_payload = {
        "method": req.method,
        "url": req.url,
        "headers": dict(req.headers or {}),
        "body": req.body.decode() if hasattr(req.body, "decode") else req.body,
    }
    response_payload = {
        "status_code": resp.status_code,
        "headers": dict(resp.headers or {}),
        "body": resp.text,
    }
    allure.attach(
        json.dumps(request_payload, indent=2),
        "api_request.json",
        allure.attachment_type.JSON,
    )
    allure.attach(
        json.dumps(response_payload, indent=2),
        "api_response.json",
        allure.attachment_type.JSON,
    )


def _attach_db_query(db):
    query, params = db.last_query()
    if not query:
        return
    payload = {"query": query, "params": params}
    allure.attach(json.dumps(payload, indent=2), "db_query.json", allure.attachment_type.JSON)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    attach_on_pass = os.getenv("ALLURE_ATTACH_ON_PASS", "true").lower() == "true"
    if rep.passed and not attach_on_pass:
        return
    api_client = item.funcargs.get("api_client")
    if api_client:
        _attach_api_response(api_client)
    db = item.funcargs.get("db")
    if db:
        _attach_db_query(db)
