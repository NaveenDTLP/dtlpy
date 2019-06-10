import behave
import os
import json


@behave.when(u'I update ontology with labels from file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)
    context.ontology.add_labels(context.labels)
    context.recipe.ontologies.update(context.ontology)


@behave.when(u'I update ontology attributes to "{attribute1}", "{attribute2}"')
def step_impl(context, attribute1, attribute2):
    context.ontology.attributes = [attribute1, attribute2]
    context.recipe.ontologies.update(context.ontology)


@behave.when(u'I update ontology system metadata')
def step_impl(context):
    context.ontology.metadata['system']['something'] = 'value'
    context.recipe.ontologies.update(ontology=context.ontology, system_metadata=True)
