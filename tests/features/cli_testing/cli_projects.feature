#noinspection CucumberUndefinedStep
Feature: Cli Projects

    Background: background
        Given Platform Interface is initialized as dlp and Environment is set according to git branch
        And I am logged in
        And I have context random number

    @testrail-C4523069
    Scenario: Projects list
        When I perform command:
            |projects|ls|
        Then I succeed

    @testrail-C4523069
    Scenario: Projects Create
        When I perform command:
            |projects|create|-p|to-delete-test-<random>_cli_project|
        Then I succeed
        And There is a project by the name of "to-delete-test-<random>_cli_project"
        And "to-delete-test-<random>_cli_project" in output

    @testrail-C4523069
    Scenario: Finally
        Given I delete the project by the name of "to-delete-test-<random>_cli_project"