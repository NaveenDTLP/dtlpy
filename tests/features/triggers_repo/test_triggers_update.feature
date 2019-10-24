Feature: Triggers repository update function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "triggers_update"
        And I create a dataset with a random name
        And There is a plugin (pushed from "triggers/item") by the name of "triggers_update"
        And There is a deployment by the name of "triggers-update"
        And I create a trigger
            |name=triggers_update|filters=None|resource=Item|action=Created|active=True|executionMode=Once|

    @deployments.delete
    @plugins.delete
    Scenario: Update trigger
        When I update trigger
            |filters={"$and": [{"type": "file"}]}|resource=Item|action=Updated|active=False|
        Then I receive an updated Trigger object
        And Trigger attributes are modified
            |filters={"$and": [{"type": "file"}]}|resource=Item|action=Updated|active=False|