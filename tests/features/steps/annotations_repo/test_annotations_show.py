import behave, os
import numpy as np
import random


@behave.when(u'I show items annotations with param "{annotation_format}"')
def step_impl(context, annotation_format):
    context.item = context.item.update()
    context.mask = context.item.annotations.show(height=768, width=1536, annotation_format=annotation_format)


@behave.then(u'I receive annotations mask and it is equal to mask in "{should_be_path}"')
def step_impl(context, should_be_path):
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)
    if not np.array_equal(context.mask, np.load(should_be_path)):
        np.save(should_be_path.replace('.npy', '_wrong.npy'), context.mask)
        assert False

@behave.when(u'Every annotation has an object id')
def step_impl(context):
    context.annotaitons = context.item.annotations.list()
    types = ['ellipse', 'segment', 'box', 'polyline', 'point']
    for ann in context.annotaitons:
        ann.object_id = types.index(ann.type) + 1
    context.annotaitons = context.annotaitons.update()