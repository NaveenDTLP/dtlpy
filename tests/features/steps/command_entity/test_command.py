import behave


@behave.when(u'Dataset is cloning')
def step_impl(context):
    context.clone_dataset = context.dataset.clone(clone_name="clone_dataset")


@behave.then(u'Cloned dataset has "{item_count}" items')
def step_impl(context, item_count):
    pages = context.dataset.items.list()
    assert pages.items_count == int(item_count)


@behave.when(u'Dataset is cloning with same name get already exist error')
def step_impl(context):
    try:
        context.clone_dataset = context.dataset.clone(clone_name=context.dataset.name)
    except context.dl.exceptions.FailedDependency as error:
        assert "Dataset with same name already exist in the specified project" in error.args[1]
        return
    assert False
