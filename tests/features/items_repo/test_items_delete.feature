Feature: Items repository delete function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "items_delete"
        And I create a dataset by the name of "Dataset"

    Scenario: Delete item by name
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I delete an item by the name of "/test_item.jpg"
        Then There are no items
    
    Scenario: Delete item by id
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I delete an item by the id of "/test_item.jpg"
        Then There are no items

    Scenario: Delete a non-existing item by name
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I try to delete an item by the name of "Some_item_name"
        Then "NotFound" exception should be raised
        And No item was deleted

    Scenario: Delete a non-existing item by id
        Given There are no items
        And I upload an item by the name of "/test_item.jpg"
        When I try to delete an item by the id of "Some_id"
        Then "InternalServerError" exception should be raised
        And No item was deleted

    Scenario: Finally
        Given Clean up "items_delete"