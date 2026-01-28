Feature: Items API

  @smoke @critical
  Scenario: Create item persists to database
    Given the API is healthy
    When I create an item with name "bdd-item" and description "from bdd"
    Then the item exists in the database

  @smoke
  Scenario: Fetch item by id returns the same item
    Given an item exists with name "bdd-fetch" and description "from bdd"
    When I fetch the item by id
    Then the response contains the same name and description

  @regression
  Scenario: Update item persists to database
    Given an item exists with name "bdd-update" and description "before"
    When I update the item with name "bdd-update" and description "after"
    Then the item in the database has description "after"

  @regression
  Scenario: Delete item removes from database
    Given an item exists with name "bdd-delete" and description "to delete"
    When I delete the item by id
    Then the item does not exist in the database

  @regression
  Scenario: Search items returns matching result
    Given an item exists with name "bdd-searchable" and description "search me"
    When I search items with name "bdd-search"
    Then the search results include the item

  @regression
  Scenario: List items supports pagination
    Given multiple items exist for pagination
    When I list items with limit 1 and offset 0
    Then the response contains 1 item

  @smoke @critical
  Scenario: Unauthorized requests are rejected
    When I create an item without an API key
    Then the response status is 401
