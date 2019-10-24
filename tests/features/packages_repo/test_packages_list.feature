Feature: Packages repository List method

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "packages_list"
        And I create a dataset with a random name

    Scenario: List all versions when 0 exist
        Given There are "0" packages
        When I list all packages
        Then I receive a list of "0" packages

    Scenario: List all packages when 1 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list"
        When I pack directory by name "package1_name"
        When I list all packages
        Then I receive a list of "1" packages

    Scenario: List all packages when 2 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list"
        And I pack directory by name "package2_name"
        When I list all packages
        Then I receive a list of "2" packages

    Scenario: List all versions when 3 exist
        Given There is a Package directory with a python file in path "packages_assets/packages_list"
        And There are "2" packages
        When I pack directory by name "package_name3"
        When I list all packages
        Then I receive a list of "3" packages

