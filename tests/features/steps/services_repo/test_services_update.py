import behave
import json


@behave.then(u"Service attributes are modified")
def step_impl(context):
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "revision":
            if param[1] != "None":
                revision = int(param[1])
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])

    assert context.trigger_update.revision == revision
    assert context.trigger_update.config == config
    assert context.trigger_update.runtime == runtime


@behave.then(u"I receive an updated Service object")
def step_impl(context):
    assert isinstance(context.service_update, context.dl.entities.Service)


@behave.when(u'I change service "{attribute}" to "{value}"')
def step_impl(context, attribute, value):
    if attribute in ['gpu', 'image']:
        context.service.runtime[attribute] = value
    elif attribute in ['numReplicas', 'concurrency']:
        setattr(context.service.runtime, attribute, int(value))
    elif attribute in ['config']:
        context.service.config = json.loads(value)
    elif attribute in ['packageRevision']:
        setattr(context.service, attribute, int(value))
    else:
        setattr(context.service, attribute, value)


@behave.when(u'I update service')
def step_impl(context):
    context.service_update = context.service.update()


@behave.then(u'Service received equals service changed except for "{updated_attribute}"')
def step_impl(context, updated_attribute):
    updated_to_json = context.service_update.to_json()
    origin_to_json = context.service.to_json()
    if 'runtime' in updated_attribute:
        attribute = updated_attribute.split('.')[-1]
        updated_to_json['runtime'].pop(attribute, None)
        origin_to_json['runtime'].pop(attribute, None)
    else:
        updated_to_json.pop(updated_attribute, None)
        origin_to_json.pop(updated_attribute, None)

    updated_to_json.pop('updatedAt', None)
    origin_to_json.pop('updatedAt', None)

    updated_to_json.pop('version', None)
    origin_to_json.pop('version', None)

    updated_to_json.pop('revisions', None)
    origin_to_json.pop('revisions', None)

    assert len(context.service_update.revisions) == len(context.service.revisions) + 1
    assert updated_to_json == origin_to_json
