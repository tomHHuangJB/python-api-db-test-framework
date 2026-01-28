Feature: Items API

  Scenario: Create item persists to database
    Given the API is healthy
    When I create an item with name "bdd-item" and description "from bdd"
    Then the item exists in the database

