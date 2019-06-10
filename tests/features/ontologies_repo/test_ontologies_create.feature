Feature: Ontologies repository create function testing

    Background: Initiate Platform Interface and create a project
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There are no projects
        And There is a project by the name of "Project"
        And I create a dataset by the name of "Dataset"

    Scenario: Create ontology
        When I create a new ontology with labels from file "labels.json"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Create ontology - no project id
        When I create a new ontology with no projectIds, with labels from file "labels.json"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    Scenario: Create ontology with attributes
        When I create a new ontology with labels from file "labels.json" and attributes "['attr1', 'attr2']"
        And I update dataset ontology to the one created
        Then Dataset ontology in host equal ontology uploaded

    # not working properly
    # Scenario: Create ontology - other project id
    #     Given There is another project by the name of "other_project"
    #     When I create a new ontology with labels and project id of "other_project" from file "labels.json"
    #     And I try to update dataset ontology to the one created
    #     Then "Forbidden" exception should be raised

    Scenario: Create ontology - wrong project id
        When I try create a new ontology with labels and "some_project_id" from file "labels.json"
        Then "Forbidden" exception should be raised
    
    Scenario: Create ontology - invalid labels
        When I try to create a new ontology with labels "[{'tag': 'vehicle', 'color': '#14638f'}]"
        Then "BadRequest" exception should be raised


