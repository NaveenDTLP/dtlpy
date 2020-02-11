import behave


@behave.when(u'I list all code bases')
def step_impl(context):
    context.codebase_list = context.project.codebases.list()


@behave.then(u'I receive a list of "{codebase_count}" code bases')
def step_impl(context, codebase_count):
    assert len(context.codebase_list.items) == int(codebase_count)


@behave.given(u'There are "{codebases_num}" code bases')
def step_impl(context, codebases_num):
    context.codebase_list = context.project.codebases.list()
    assert len(context.codebase_list.items) == int(codebases_num)
