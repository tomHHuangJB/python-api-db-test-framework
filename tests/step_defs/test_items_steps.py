from pytest_bdd import given, scenario, then, when


@scenario("../features/items.feature", "Create item persists to database")
def test_bdd_create_item_persists():
    pass


@given("the API is healthy")
def api_is_healthy(api_client):
    resp = api_client.health()
    assert resp.status_code == 200


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

