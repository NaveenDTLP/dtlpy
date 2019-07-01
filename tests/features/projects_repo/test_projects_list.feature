Feature: Projects repository list function testing

    Background: Background name
        Given Platform Interface is initialized as dlp and Environment is set to development

    Scenario: List all projects when projects exist
        Given I create a project by the name of "projects_list"
        When I list all projects
        Then The project in the projects list equals the project I created

    Scenario: Finally
        Given Remove cookie