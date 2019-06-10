import logging
from . import pipeline_step


class ItemsUploadStep(pipeline_step.PipelineStep):
    """
    Item upload step creator
    """

    def __init__(self, step_dict=None):
        super(ItemsUploadStep, self).__init__()
        self.name = 'ItemsUpload'
        self.logger = logging.getLogger('dataloop.pipeline.step.%s' % self.name)
        if step_dict is not None:
            self.inputs = step_dict['inputs']
            self.kwargs = step_dict['kwargs']
            self.args = step_dict['args']
            self.outputs = step_dict['outputs']
        else:
            self.inputs = [{'name': 'dataset', 'from': 'dataset', 'by': 'ref', 'type': 'object'},
                           {'name': 'filepath', 'from': 'filepath',  'by': 'ref','type': 'string'}]
            self.kwargs = dict()
            self.args = list()
            self.outputs = list()

    def execute(self, pipeline_dict):
        # input arguments for step
        for input_arg in self.inputs:
            assert input_arg['from'] in pipeline_dict, \
                '[ERROR] input argument for step is not in pipeline dictionary. arg: %s' % input_arg['from']

        # prepare
        dataset_from = [input_arg['from'] for input_arg in self.inputs if input_arg['name'] == 'dataset']
        if len(dataset_from) != 1:
            self.logger.exception('"dataset" is missing from context')
            raise ValueError('"dataset" is missing from context')
        dataset = pipeline_dict.get(dataset_from[0])

        # get input arguments
        kwargs = self.kwargs
        for input_arg in self.inputs:
            if input_arg['name'] in ['dataset']:
                continue
            # get input item 'name' from 'from'
            kwargs[input_arg['name']] = pipeline_dict[input_arg['from']]

        # run
        outputs = dataset.items.upload(**kwargs)

        # Save outputs arguments
        if not isinstance(outputs, tuple):
            # single output - put in tuple
            outputs = (outputs,)
        for i_output, output_arg in enumerate(self.outputs):
            pipeline_dict[output_arg['name']] = outputs[i_output]
        return pipeline_dict

    @staticmethod
    def get_arguments():
        import inspect
        from ... import repositories
        signature = inspect.signature(repositories.Items.upload)
        f_callargs = {
            k: v.default
            for k, v in signature.parameters.items()
            if v.default is not inspect.Parameter.empty
        }
        return f_callargs
