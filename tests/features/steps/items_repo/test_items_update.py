import behave
from dtlpy import entities
import os


@behave.when(u'I update items name to "{name}"')
def step_impl(context, name):
    context.item.filename = name
    context.item_update = context.dataset.items.update(item=context.item)


@behave.then(u'I receive an Item object with name "{name}"')
def step_impl(context, name):
    assert type(context.item_update) == entities.Item
    assert context.item_update.filename == name


@behave.then(u'Only name attributes was changed')
def step_impl(context):
    item_get_json = context.item_get.to_json()
    original_item_json = context.item.to_json()
    item_get_json.pop('filename')
    original_item_json.pop('filename')
    item_get_json.pop('name')
    original_item_json.pop('name')
    item_get_json.pop('metadata')
    original_item_json.pop('metadata')

    assert item_get_json == original_item_json


@behave.then(u'Item in host was changed to "{name}"')
def step_impl(context, name):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert context.item_get.filename == name


@behave.given(u'And There is an item by the name of "{name}"')
def step_impl(context, name):
    local_path = '0000000162.jpg'
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    context.item = context.dataset.items.upload(
        filepath=local_path,
        remote_path=None,
        uploaded_filename=name,
        callback=None,
        upload_options=None,
    )


@behave.then(u'PageEntity has directory item "{dir_name}"')
def step_impl(context, dir_name):
    page = context.dataset.items.list()
    dir_exist = False
    for item in page.items:
        if item.filename == dir_name:
            dir_exist = True
            break
    assert dir_exist is True


@behave.when(u'I update item system metadata with system_metadata="{param}"')
def step_impl(context, param):
    system_metadata = param == "True"
    context.original_item_json = context.item.to_json()
    context.item.metadata['system']['modified'] = 'True'
    context.item_update = context.dataset.items.update(context.item, system_metadata)


@behave.then(u'Then I receive an Item object')
def step_impl(context):
    assert type(context.item_update) == entities.Item


@behave.then(u'Item in host has modified metadata')
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert 'modified' in context.item_get.metadata['system']


@behave.then(u'Only metadata was changed')
def step_impl(context):
    item_get_json = context.item_get.to_json()
    item_get_json.pop('metadata')
    context.original_item_json.pop('metadata')

    assert item_get_json == context.original_item_json


@behave.then(u'Item in host was not changed')
def step_impl(context):
    context.item_get = context.dataset.items.get(item_id=context.item.id)
    assert 'modified' not in context.item_get.metadata['system']
