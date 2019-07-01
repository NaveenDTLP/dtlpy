Feature: Projects repository get function testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: Delete project by name
        Given I create a project by the name of "project_delete"
        When I delete a project by the name of "project_delete"
        Then There are no projects by the name of "project_delete"
    
    Scenario: Delete project by id
        Given I create a project by the name of "project_delete_id"
        When I delete a project by the id of "project_delete_id"
        Then There are no projects by the name of "project_delete_id"

    Scenario: Delete a non-existing project
        When I try to delete a project by the name of "Some Project Name"
        Then "NotFound" exception should be raised