import behave


@behave.given(u'There are no annotations')
def step_impl(context):
    assert True


@behave.when(u'I list all annotations')
def step_impl(context):
    context.annotations_list = context.item.annotations.list()


@behave.then(u'I receive a list of all annotations')
def step_impl(context):
    assert len(context.annotations_list) == len(context.annotations)


@behave.then(u'The annotations in the list equals the annotations uploaded')
def step_impl(context):
    for annotation in context.annotations_list:
        ann = {'type': annotation.type,
               'label': annotation.label,
               'attributes': annotation.attributes,
               'coordinates': annotation.coordinates}
        assert ann in context.annotations


@behave.then(u'I receive an empty annotations list')
def step_impl(context):
    assert len(context.annotations_list) == 0
