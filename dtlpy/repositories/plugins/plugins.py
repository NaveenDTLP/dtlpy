import logging

from dtlpy import entities, utilities, PlatformException
from dtlpy.repositories.plugins.package_runner.package_runner import PackageRunner
from dtlpy.repositories.plugins.plugin_uploader import PluginCreator
from dtlpy.repositories.plugins.plugin_generator import generate_plugin
from dtlpy.repositories.plugins.plugin_invoker import PluginInvoker
from dtlpy.repositories.plugins.plugin_deployer import PluginDeployer



class Plugins(object):
    """
        Plugins repository
    """

    def __init__(self, client_api, project=None):
        self.logger = logging.getLogger('dataloop.plugins')
        self.client_api = client_api
        self.project = project

    def create(self, name, package, input_parameters, output_parameters):
        """
        Create a new plugin
        :param name: plugin name
        :param input_parameters: inputs for the plugin's sessions
        :param output_parameters: outputs for the plugin's sessions
        :param package: packageId:version
        :return: plugin entity
        """
        if isinstance(input_parameters, entities.PluginInput):
            input_parameters = [input_parameters]
        if not isinstance(input_parameters, list):
            raise TypeError('must be a list of PluginInput')
        # if not all(isinstance(n, entities.PluginInput) for n in input_parameters):
        #     raise TypeError('must be a list of PluginInput')

        # input_parameters = [p.to_json for p in input_parameters]
        input_parameters.append({'path': 'package',
                                 'resource': 'package',
                                 'by': 'ref',
                                 'constValue': package})
        payload = {'name': name,
                   'pipeline': dict(),
                   'input': input_parameters,
                   'output': output_parameters,
                   'metadata': {'system': {
                       "projects": [self.project.id]
                   }}
                   }

        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/tasks',
                                                        json_req=payload)
        if success:
            plugin = entities.Plugin.from_json(client_api=self.client_api,
                                               _json=response.json())
        else:
            self.logger.exception('Platform error creating new plugin:')
            raise PlatformException(response)
        return plugin

    def get(self, plugin_id=None, plugin_name=None):
        """
        Get a Pipeline object
        :param plugin_id: optional - search by id
        :param plugin_name: optional - search by name
        :return: Pipeline object
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks/%s' % plugin_id)
            if success:
                res = response.json()
                if len(res) > 0:
                    plugin = entities.Plugin.from_json(client_api=self.client_api, _json=res)
                else:
                    plugin = None
            else:
                self.logger.exception('Platform error getting the plugin. id: %s' % plugin_id)
                raise PlatformException(response)
        elif plugin_name is not None:
            plugins = self.list()
            plugin = [plugin for plugin in plugins if plugin.name == plugin_name]
            if len(plugin) == 0:
                self.logger.info('Pipeline not found. plugin id : %s' % plugin_name)
                plugin = None
            elif len(plugin) > 1:
                self.logger.warning('More than one plugin with same name. Please "get" by id')
                raise ValueError('More than one plugin with same name. Please "get" by id')
            else:
                plugin = plugin[0]
        else:
            self.logger.exception('Must input one search parameter!')
            raise ValueError('Must input one search parameter!')
        return plugin

    def delete(self, plugin_name=None, plugin_id=None):
        """
        Delete remote item
        :param plugin_name: optional - search item by remote path
        :param plugin_id: optional - search item by id
        :return:
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin_id)
        elif plugin_name is not None:
            plugin = self.get(plugin_name=plugin_name)
            if plugin is None:
                self.logger.warning('plugin name was not found: name: %s' % plugin_name)
                raise ValueError('plugin name was not found: name: %s' % plugin_name)
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin.id)
        else:
            assert False
        return success

    def list(self):
        """
        List all plugin.
        :return: List of Pipeline objects
        """
        if self.project is None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks')
        else:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks?projects=%s' % self.project.id)

        if success:
            plugins = utilities.List(
                [entities.Plugin.from_json(client_api=self.client_api,
                                           _json=_json)
                 for _json in response.json()['items']])
            return plugins
        else:
            self.logger.exception('Platform error getting plugins')
            raise PlatformException(response)

    def edit(self, plugin, system_metadata=False):
        """
        Edit an existing plugin
        :param plugin: Plugin entity
        :param system_metadata: bool
        :return: Plugin entity
        """
        url_path = '/tasks/%s' % plugin.id
        if system_metadata:
            url_path += '?system=true'

        plugin_json = plugin.to_json()
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=plugin_json)
        if success:
            return entities.Plugin.from_json(client_api=self.client_api,
                                             _json=response.json())
        else:
            self.logger.exception('Platform error editing plugin. id: %s' % plugin.id)
            raise PlatformException(response)

    def deploy(self, plugin_id):
        """
        Deploy an existing plugin
        :param plugin_id: Id of plugin to deploy
        :return:
        """
        url_path = '/plugins/%s/deploy' % plugin_id

        success, response = self.client_api.gen_request(req_type='post',
                                                        path=url_path)
        if success:
            return response.text
        else:
            self.logger.exception('Platform error deploying plugin. id: %s' % plugin_id)
            raise PlatformException(response)

    def status(self, plugin_id):
        url_path = '/plugins/%s/status' % plugin_id
        success, response = self.client_api.gen_request(req_type='get',
                                                        path=url_path)

        if success:
            return response.text
        else:
            self.logger.exception('Platform error getting plugin status. id: %s' % plugin_id)
            raise PlatformException(response)

    def test_local_plugin(self):
        package_runner = PackageRunner()
        return package_runner.run_local_project()

    def push_local_plugin(self):
        plugin_creator = PluginCreator()
        plugin_creator.create_plugin()

    def invoke_plugin(self, input_file_path='./mock.json'):
        plugin_invoker = PluginInvoker(input_file_path)
        return plugin_invoker.invoke_plugin()

    def get_status_from_folder(self):
        import dtlpy.repositories.plugins.plugin_status as plugin_status
        plugin_status.get_status_from_folder()

    def deploy_plugin_from_folder(self):
        plugin_deployer = PluginDeployer()
        return plugin_deployer.deploy_plugin()

    def generate_local_plugin(self):
        generate_plugin()