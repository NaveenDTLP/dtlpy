import behave


@behave.when(u"I list triggers")
def step_impl(context):
    context.trigger_list = context.service.triggers.list()


@behave.then(u'I receive a Trigger list of "{count}" objects')
def step_impl(context, count):
    assert context.trigger_list.items_count == int(count)
    if int(count) > 0:
        for page in context.trigger_list:
            for trigger in page:
                assert isinstance(trigger, context.dl.entities.Trigger)
