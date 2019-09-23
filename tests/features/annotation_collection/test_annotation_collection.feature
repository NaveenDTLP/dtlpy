Feature: Annotations collection testing

    Background: Initiate Platform Interface
        Given Platform Interface is initialized as dlp and Environment is set to development
        And There is a project by the name of "Project_test_annotation_collection"
        And I create a dataset with a random name

   Scenario: Update - image
       Given Classes in file: "classes_new.json" are uploaded to test Dataset
       And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
       And Item is annotated with annotations in file: "annotations_new.json"
       And I get item annotation collection
       And I change all image annotations label to "ball"
       When I update annotation collection
       Then Image annotations in host have label "ball"

    Scenario: Update - video
        Given Labels in file: "video_classes.json" are uploaded to test Dataset
        And Item in path "sample_video.mp4" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "video_annotations.json"
        And I get item annotation collection
        And I change all annotations label to "ball"
        When I update annotation collection
        Then Annotations in host have label "ball"

    Scenario: Delete
        Given Classes in file: "classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        And Item is annotated with annotations in file: "assets_split/annotation_collection/annotations_new.json"
        And I get item annotation collection
        When I delete annotation collection
        Then Item in host has no annotations

    Scenario: Upload - image
        Given Classes in file: "assets_split/annotation_collection/classes_new.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/0000000162.jpg" is uploaded to "Dataset"
        And I create item annotation collection
        And I add a few annotations to image
        When I upload annotation collection
        Then Annotations in host equal annotations uploded

    Scenario: Upload - video
        Given Labels in file: "assets_split/annotation_collection/video_classes.json" are uploaded to test Dataset
        And Item in path "assets_split/annotation_collection/sample_video.mp4" is uploaded to "Dataset"
        And I create item annotation collection
        And I add a few annotations to video
        And I add a few frames to annotations
        When I upload annotation collection
        Then Annotations in host equal annotations uploded

