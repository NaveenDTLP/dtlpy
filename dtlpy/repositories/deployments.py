import logging
import os
import json
from .plugins_assets import deployment_json_local_path

from .. import utilities, exceptions, entities, repositories

logger = logging.getLogger(name=__name__)


class Deployments:
    def __init__(self, client_api, project=None, plugin=None):
        self._client_api = client_api
        self._plugin = plugin
        self._project = project

    @property
    def plugin(self):
        assert isinstance(self._plugin, entities.Plugin)
        return self._plugin

    @property
    def project(self):
        if self._project is None:
            # try to get checked out project
            try:
                projects = repositories.Projects(client_api=self._client_api)
                self._project = projects.get()
            except Exception:
                # try to get from plugin
                if self.plugin is not None:
                    try:
                        self._project = self.plugin.project
                    except Exception:
                        logging.warning('please checkout a project or use project deployment repository'
                                        'for this action')
        return self._project

    def get(self, deployment_name=None, deployment_id=None):
        """
        Get deployment

        :param deployment_name: optional - search by name
        :param deployment_id: optional - search by id
        :return: Deployment object
        """
        if deployment_id is not None:
            success, response = self._client_api.gen_request(
                req_type="get",
                path="/deployments/{}".format(deployment_id)
            )
            # exception handling
            if not success:
                raise exceptions.PlatformException(response)
            # return entity
            if self.plugin is None:
                logging.warning('Getting deployment with project entity will return deployment object with no plugin.\n'
                                'to properly get deployment use plugin.deployments.get() method')
            deployment = entities.Deployment.from_json(client_api=self._client_api,
                                                       _json=response.json(),
                                                       plugin=self.plugin)
        elif deployment_name is not None:
            deployments = self.list()
            deployment = [deployment for deployment in deployments if deployment.name == deployment_name]
            if not deployment:
                # empty list
                raise exceptions.PlatformException('404', 'Deployment not found. Name: {}'.format(deployment_name))
            elif len(deployment) > 1:
                # more than one deployment
                logger.warning('More than one deployment with same name. Please "get" by id')
                raise exceptions.PlatformException('400', 'More than one deployment with same name.')
            else:
                deployment = deployment[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must choose by "deployment_id" or "deployment_name"')

        assert isinstance(deployment, entities.Deployment)
        return deployment

    def list(self):
        """
        List project deployments
        :return:
        """
        url_path = '/deployments'

        if self.project is not None:
            url_path += '?projects={}'.format(self.project.id)
        elif self.plugin is not None and self.plugin.project is not None:
            url_path += '?projects={}'.format(self.plugin.project.id)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        # return triggers list
        if self.plugin is None:
            logging.warning('Listing deployments with project entity will return deployment objects with no plugin.\n'
                            'to properly list deployments use plugin.deployments.list() method')
        deployments = utilities.List()
        for deployment in response.json()['items']:
            deployments.append(entities.Deployment.from_json(client_api=self._client_api,
                                                             _json=deployment,
                                                             plugin=self.plugin))
        return deployments

    def create(self, deployment_name=None, plugin=None, revision=None, config=None, runtime=None):
        """
        Create deployment entity
        :param runtime:
        :param config:
        :param revision: optional - int - plugin revision - default=latest
        :param plugin:
        :param deployment_name:
        :return:
        """
        if plugin is None:
            if self.plugin is None:
                raise exceptions.PlatformException('400', 'Please provide param plugin')
            else:
                plugin = self.plugin

        if deployment_name is None:
            deployment_name = 'default_deployment'

        if config is None:
            config = dict()

        # payload
        payload = {'name': deployment_name,
                   'project': self.project.id,
                   'pluginId': plugin.id,
                   'config': config}

        # revision
        if isinstance(revision, int):
            payload['pluginRevision'] = revision

        if runtime is not None:
            payload['runtime'] = runtime
        else:
            payload['runtime'] = {'gpu': False,
                                  'numReplicas': 1}

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/deployments',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Deployment.from_json(_json=response.json(),
                                             client_api=self._client_api,
                                             plugin=plugin)

    def delete(self, deployment_name=None, deployment_id=None):
        """
        Delete Deployment object

        :param deployment_id:
        :param deployment_name:
        :return: True
        """
        # get bby name
        if deployment_id is None:
            if deployment_name is None:
                raise exceptions.PlatformException('400', 'Must provide either deployment id or deployment name')
            else:
                deployments = self.list()
                for deployment in deployments:
                    if deployment.name == deployment_name:
                        deployment_id = deployment.id
        # delete by id
        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/deployments/{}".format(deployment_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, deployment):
        """
        Update Deployment changes to platform
        :param deployment: Deployment entity
        :return: Deployment entity
        """
        assert isinstance(deployment, entities.Deployment)

        # payload
        payload = deployment.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/deployments/{}'.format(deployment.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        if self.plugin is not None:
            plugin = self.plugin
        else:
            plugin = deployment._plugin

        return entities.Deployment.from_json(_json=response.json(),
                                             client_api=self._client_api,
                                             plugin=plugin)

    def deploy(self, deployment_name=None, plugin=None, revision=None, config=None, runtime=None):
        """
        Deploy deployment

        :param deployment_name:
        :param plugin:
        :param revision:
        :param config:
        :param runtime:
        :return:
        """
        deployments = {deployment.name: deployment for deployment in self.project.deployments.list()}
        if deployment_name in deployments:
            deployment = deployments[deployment_name]
            if runtime is not None:
                deployment.runtime = runtime
            if config is not None:
                deployment.config = config
            if revision is not None:
                deployment.pluginRevision = revision
            return self.update(deployment=deployment)
        else:
            return self.create(deployment_name=deployment_name,
                               plugin=plugin,
                               revision=revision,
                               config=config,
                               runtime=runtime)

    def deploy_from_local_folder(self):
        """
        Deploy from local folder
        :return:
        """
        cwd = os.getcwd()

        if 'deployment.json' in os.listdir(cwd):
            with open(os.path.join(cwd, 'deployment.json'), 'r') as f:
                deployment_json = json.load(f)
        else:
            raise exceptions.PlatformException('400', 'Could not find deployment.json in path: {}'.format(cwd))

        deployment_json = deployment_json[0]
        deployment_triggers = deployment_json.get('triggers', list())

        # get attributes
        plugin_name = deployment_json.get('plugin', None)
        plugins = repositories.Plugins(client_api=self._client_api, project=self.project)
        if plugin_name is None:
            plugin = plugins.get()
        else:
            plugin = plugins.get(plugin_name=plugin_name)
        name = deployment_json.get('name', None)
        revision = deployment_json.get('revision', plugin.version)
        config = deployment_json.get('config', dict())
        runtime = deployment_json.get('runtime', dict())

        deployment = self.deploy(deployment_name=name, plugin=plugin, revision=revision, runtime=runtime, config=config)

        triggers = repositories.Triggers(client_api=self._client_api, project=self.project)
        for trigger in deployment_triggers:
            name = trigger.get('name', None)
            filters = trigger.get('filters', dict())
            resource = trigger['resource']
            actions = trigger.get('actions', list())
            active = trigger.get('active', True)
            # noinspection PyPep8Naming
            executionMode = trigger.get('executionMode', None)

            triggers.create(deployment_id=deployment.id, name=name, filters=filters,
                            resource=resource, actions=actions, active=active, executionMode=executionMode)

        logging.debug('Successfully deployed!')
        return deployment

    def deploy_pipeline(self, deployment_json_path=None, project=None):
        """
        Deploy pipeline
    
        :param project:
        :param deployment_json_path:
        :return: True
        """
        # project
        if project is None:
            project = self.project.projects.get()

        # get deployment file
        if deployment_json_path is None:
            deployment_json_path = os.getcwd()

        if not deployment_json_path.endswith('.json'):
            deployment_json_path = os.path.join(deployment_json_path, 'deployment.json')
            if not os.path.isfile(deployment_json_path):
                raise exceptions.PlatformException('404', 'File not exist: {}'.format(deployment_json_path))

        # get existing project's deployments and triggers
        project_triggers = {trigger.name: trigger for trigger in project.triggers.list()}
        project_deployments = {deployment.name: deployment for deployment in project.deployments.list()}
        project_plugins = {plugin.name: plugin for plugin in project.plugins.list()}

        # load file
        with open(deployment_json_path, 'r') as f:
            deployment_json = json.load(f)

        # build
        for deployment_input in deployment_json:
            # get plugin
            if deployment_input['plugin'] in project_plugins:
                plugin = project_plugins[deployment_input['plugin']]
            else:
                raise exceptions.PlatformException('404', 'Plugin not found, plugin name: {}'.format(
                    deployment_input['plugin']))

            # create or update deployment
            if deployment_input['name'] in project_deployments:
                deployment = project_deployments[deployment_input['name']]
                deployment.runtime = deployment_input.get('runtime', deployment.runtime)
                deployment.config = deployment_input.get('config', deployment.config)
                deployment = project.deployments.update(deployment=deployment)
                project_deployments[deployment.name] = deployment

            else:
                deployment = project.deployments.create(plugin=plugin,
                                                        deployment_name=deployment_input['name'],
                                                        runtime=deployment_input.get('runtime', None),
                                                        config=deployment_input.get('config', None))
                project_deployments[deployment.name] = deployment

            # create or update triggers
            if 'triggers' in deployment_input:
                for trigger_input in deployment_input['triggers']:
                    if trigger_input['name'] in project_triggers:
                        trigger = project_triggers[trigger_input['name']]
                        trigger.resource = trigger_input.get('resource', trigger.resource)
                        trigger.active = trigger_input.get('active', trigger.active)
                        trigger.actions = trigger_input.get('actions', trigger.actions)
                        trigger.filters = trigger_input.get('filters', trigger.filters)
                        trigger.executionMode = trigger_input.get('executionMode', trigger.executionMode)
                        if deployment.id not in trigger.deploymentIds:
                            trigger.deploymentIds.append(deployment.id)
                        trigger = trigger.update()
                        project_triggers[trigger.name] = trigger
                    else:
                        trigger = project.triggers.create(deployment_ids=[deployment.id],
                                                          resource=trigger_input.get('resource', None),
                                                          active=trigger_input.get('active', None),
                                                          actions=trigger_input.get('actions', None),
                                                          filters=trigger_input.get('filters', None),
                                                          executionMode=trigger_input.get('executionMode', None))
                        project_triggers[trigger.name] = trigger

        print('File deployed successfully!')
        return True

    def tear_down(self, deployment_json_path=None, project=None):
        """
        Tear down a pipeline
    
        :param project:
        :param deployment_json_path:
        :return:
        """
        # project
        if project is None:
            project = self.project.projects.get()

        # get deployment file
        if deployment_json_path is None:
            deployment_json_path = os.getcwd()

        if not deployment_json_path.endswith('.json'):
            deployment_json_path = os.path.join(deployment_json_path, 'deployment.json')
            if not os.path.isfile(deployment_json_path):
                raise exceptions.PlatformException('404', 'File not exist: {}'.format(deployment_json_path))

        # get existing project's deployments and triggers
        project_triggers = {trigger.name: trigger for trigger in project.triggers.list()}
        project_deployments = {deployment.name: deployment for deployment in project.deployments.list()}

        with open(deployment_json_path, 'r') as f:
            deployment_json = json.load(f)

        # tear down
        for deployment_input in deployment_json:
            # delete deployment
            if deployment_input['name'] in project_deployments:
                deployment = project_deployments[deployment_input['name']]
                deployment.delete()

            # delete triggers
            if 'triggers' in deployment_input:
                for trigger_input in deployment_input['triggers']:
                    if trigger_input['name'] in project_triggers:
                        trigger = project_triggers[trigger_input['name']]
                        trigger.delete()

        print('File torn down successfully!')
        return True

    @staticmethod
    def generate_deployments_json(path=None):

        if path is None:
            path = os.getcwd()

        path = os.path.join(path, 'deployment.json')

        with open(deployment_json_local_path, 'r') as f:
            deployment_file = json.load(f)

        with open(path, 'w+') as f:
            json.dump(deployment_file, f)

        return path
