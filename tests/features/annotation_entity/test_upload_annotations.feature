Feature: Upload annotation testing

    Background: Initiate Platform Interface
      Given Platform Interface is initialized as dlp and Environment is set to development
      And There is a project by the name of "upload_annotations"
      And I create a dataset by the name of "Dataset"

    Scenario: Upload image annotations from file
          Given Classes in file: "assets_split/annotations_upload/classes_new.json" are uploaded to test Dataset
          And Dataset ontology has attributes "attr1" and "attr2"
          And Item in path "assets_split/annotations_upload/0000000162.jpg" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/annotations_new.json"
          Then Item annotations in host equal annotations in file "assets_split/annotations_upload/annotations_new.json"

    Scenario: Upload video annotations from file
          Given Classes in file: "assets_split/annotations_upload/video_classes.json" are uploaded to test Dataset
          And Item in path "assets_split/annotations_upload/sample_video.mp4" is uploaded to "Dataset"
          When Item is annotated with annotations in file: "assets_split/annotations_upload/video_annotations.json"
          Then Item video annotations in host equal annotations in file "assets_split/annotations_upload/video_annotations.json"

    Scenario: Finally
        Given Clean up



