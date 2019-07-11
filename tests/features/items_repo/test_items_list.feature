Feature: Items repository list function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "items_list"
        And I create a dataset by the name of "Dataset"

    Scenario: List dataset items
        Given There is an item
        When I list items
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And Item in PageEntity items equals item uploaded

    Scenario: List dataset items - with size
        Given There are "10" items
        When I list items with size of "5"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items has next page
        And PageEntity next page items has length of "5"
        And PageEntity items does not have next page

    Scenario: List dataset items - with offset
        Given There are "10" items
        When I list items with offset of "1" and size of "5"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items does not have next page

    Scenario: List dataset items - with query - filename
        Given There are "10" items
        And There is one item by the name of "test_name"
        When I list items with query filename="/test_name"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And PageEntity item received equal to item uploaded with name "test_name"

    Scenario: List dataset items - with query - filepath
        Given There are "5" items
        And There are "5" items in remote path "/folder"
        When I list items with query filename="/folder/*"
        Then I receive a PageEntity object
        And PageEntity items has length of "5"
        And PageEntity items received have "/folder" in the filename

    Scenario: List dataset items - with query - mimetypes png
        Given There are "5" .jpg items
        And There is one .png item
        When I list items with query mimetypes="*png"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And And PageEntity item received equal to .png item uploadede

    Scenario: List dataset items - with query - mimetypes video
        Given There are "5" .jpg items
        And There is one .mp4 item
        When I list items with query mimetypes="video*"
        Then I receive a PageEntity object
        And PageEntity items has length of "1"
        And And PageEntity item received equal to .mp4 item uploadede

    Scenario: Finally
        Given Clean up