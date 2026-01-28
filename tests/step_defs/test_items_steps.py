import time

import requests
from pytest_bdd import given, scenario, then, when


@scenario("../features/items.feature", "Create item persists to database")
def test_bdd_create_item_persists():
    pass


@scenario("../features/items.feature", "Fetch item by id returns the same item")
def test_bdd_fetch_item_by_id():
    pass


@scenario("../features/items.feature", "Update item persists to database")
def test_bdd_update_item():
    pass


@scenario("../features/items.feature", "Delete item removes from database")
def test_bdd_delete_item():
    pass


@scenario("../features/items.feature", "Search items returns matching result")
def test_bdd_search_items():
    pass


@scenario("../features/items.feature", "List items supports pagination")
def test_bdd_list_items_pagination():
    pass


@scenario("../features/items.feature", "Unauthorized requests are rejected")
def test_bdd_unauthorized():
    pass


@given("the API is healthy")
def api_is_healthy(api_client):
    last_status = None
    for _ in range(10):
        try:
            resp = api_client.health()
            last_status = resp.status_code
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    assert last_status == 200


@when('I create an item with name "bdd-item" and description "from bdd"')
def create_item(api_client, cleanup_items, context):
    payload = {"name": "bdd-item", "description": "from bdd"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    context["item_id"] = resp.json()["id"]
    cleanup_items.append(context["item_id"])


@then("the item exists in the database")
def item_exists_in_db(db, context):
    row = db.fetch_one("SELECT id FROM items WHERE id = %s;", (context["item_id"],))
    assert row is not None


@given('an item exists with name "bdd-fetch" and description "from bdd"')
def given_item_for_fetch(api_client, cleanup_items, context):
    payload = {"name": "bdd-fetch", "description": "from bdd"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    context["item_id"] = resp.json()["id"]
    context["item_payload"] = payload
    cleanup_items.append(context["item_id"])


@when("I fetch the item by id")
def when_fetch_item(api_client, context):
    resp = api_client.get_item(context["item_id"])
    assert resp.status_code == 200
    context["fetch_response"] = resp.json()


@then("the response contains the same name and description")
def then_verify_fetch_response(context):
    assert context["fetch_response"]["name"] == context["item_payload"]["name"]
    assert context["fetch_response"]["description"] == context["item_payload"]["description"]


@given('an item exists with name "bdd-update" and description "before"')
def given_item_for_update(api_client, cleanup_items, context):
    payload = {"name": "bdd-update", "description": "before"}
    resp = api_client.create_item(payload)
    assert resp.status_code == 201
    context["item_id"] = resp.json()["id"]
    cleanup_items.append(context["item_id"])


@when('I update the item with name "bdd-update" and description "after"')
def when_update_item(api_client, context):
    resp = api_client.update_item(context["item_id"], {"name": "bdd-update", "description": "after"})
    assert resp.status_code == 200


@then('the item in the database has description "after"')
def then_db_has_updated_description(db, context):
    row = db.fetch_one("SELECT description FROM items WHERE id = %s;", (context["item_id"],))
    assert row is not None
    assert row[0] == "after"


@given('an item exists with name "bdd-delete" and description "to delete"')
def given_item_for_delete(api_client, cleanup_items, context):
    resp = api_client.create_item({"name": "bdd-delete", "description": "to delete"})
    assert resp.status_code == 201
    context["item_id"] = resp.json()["id"]
    cleanup_items.append(context["item_id"])


@when("I delete the item by id")
def when_delete_item(api_client, context):
    resp = api_client.delete_item(context["item_id"])
    assert resp.status_code == 204


@then("the item does not exist in the database")
def then_item_missing_in_db(db, context):
    row = db.fetch_one("SELECT id FROM items WHERE id = %s;", (context["item_id"],))
    assert row is None


@given('an item exists with name "bdd-searchable" and description "search me"')
def given_item_for_search(api_client, cleanup_items, context):
    resp = api_client.create_item({"name": "bdd-searchable", "description": "search me"})
    assert resp.status_code == 201
    context["item_id"] = resp.json()["id"]
    cleanup_items.append(context["item_id"])


@when('I search items with name "bdd-search"')
def when_search_items(api_client, context):
    resp = api_client.search_items("bdd-search")
    assert resp.status_code == 200
    context["search_results"] = resp.json()


@then("the search results include the item")
def then_search_includes_item(context):
    ids = [item["id"] for item in context["search_results"]]
    assert context["item_id"] in ids


@given("multiple items exist for pagination")
def given_items_for_pagination(api_client, cleanup_items, context):
    ids = []
    for i in range(2):
        resp = api_client.create_item({"name": f"bdd-page-{i}", "description": "page"})
        assert resp.status_code == 201
        ids.append(resp.json()["id"])
    cleanup_items.extend(ids)
    context["page_ids"] = ids


@when("I list items with limit 1 and offset 0")
def when_list_paginated(api_client, context):
    resp = requests.get(
        f"{api_client.base_url}/items",
        params={"limit": 1, "offset": 0},
        headers={"X-API-Key": api_client.api_key},
        timeout=5,
    )
    assert resp.status_code == 200
    context["page_results"] = resp.json()


@then("the response contains 1 item")
def then_page_has_one(context):
    assert len(context["page_results"]) == 1


@when("I create an item without an API key")
def when_create_without_api_key(api_client, context):
    resp = requests.post(
        f"{api_client.base_url}/items",
        json={"name": "no-auth", "description": "fail"},
        timeout=5,
    )
    context["unauth_response"] = resp


@then("the response status is 401")
def then_unauthorized(context):
    assert context["unauth_response"].status_code == 401
