from collections import namedtuple
import traceback
import logging
import attr

from .. import services, repositories, entities

logger = logging.getLogger("dataloop.service")


class OnResetAction:
    RERUN = 'rerun'
    FAILED = 'failed'


@attr.s
class Service(entities.BaseEntity):
    """
    Service object
    """
    # platform
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()
    version = attr.ib()

    package_id = attr.ib()
    package_revision = attr.ib()

    bot = attr.ib()
    use_user_jwt = attr.ib(repr=False)
    init_input = attr.ib()
    versions = attr.ib(repr=False)
    module_name = attr.ib()
    name = attr.ib()
    url = attr.ib()
    id = attr.ib()
    mq = attr.ib(repr=False)
    active = attr.ib()
    driver_id = attr.ib(repr=False)
    revisions = attr.ib(type=list)

    # name change
    runtime = attr.ib(repr=False)
    queue_length_limit = attr.ib()
    run_execution_as_process = attr.ib(type=bool)
    execution_timeout = attr.ib()
    drain_time = attr.ib()
    on_reset = attr.ib(type=OnResetAction)
    project_id = attr.ib()
    is_global = attr.ib()

    # SDK
    _package = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    # repositories
    _project = attr.ib(default=None, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json: dict, client_api: services.ApiClient, package=None, project=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param package:
        :param project:
        :return:
        """
        try:
            service = Service.from_json(_json=_json,
                                        client_api=client_api,
                                        package=package,
                                        project=project,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            service = traceback.format_exc()
            status = False
        return status, service

    @classmethod
    def from_json(cls, _json: dict, client_api: services.ApiClient, package=None, project=None, is_fetched=True):
        """

        :param _json:
        :param client_api:
        :param package:
        :param project:
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        versions = _json.get('versions', dict())
        runtime = _json.get("runtime", None)
        if runtime:
            runtime = KubernetesRuntime(**runtime)

        inst = cls(
            package_revision=_json.get("packageRevision", None),
            bot=_json.get("botUserName", None),
            use_user_jwt=_json.get("useUserJwt", False),
            createdAt=_json.get("createdAt", None),
            updatedAt=_json.get("updatedAt", None),
            project_id=_json.get('projectId', None),
            package_id=_json.get('packageId', None),
            driver_id=_json.get('driverId', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            revisions=_json.get('revisions', list()),
            queue_length_limit=_json.get('queueLengthLimit', None),
            active=_json.get('active', None),
            runtime=runtime,
            is_global=_json.get("global", False),
            init_input=_json.get("initParams", dict()),
            module_name=_json.get("moduleName", None),
            run_execution_as_process=_json.get('runExecutionAsProcess', False),
            execution_timeout=_json.get('executionTimeout', 60 * 60),
            drain_time=_json.get('drainTime', 60 * 10),
            on_reset=_json.get('onReset', OnResetAction.FAILED),
            name=_json.get("name", None),
            url=_json.get("url", None),
            mq=_json.get('mq', dict()),
            id=_json.get("id", None),
            versions=versions,
            client_api=client_api,
            package=package,
            project=project
        )
        inst.is_fetched = is_fetched
        inst.runtime.service = inst
        return inst

    ############
    # Entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def package(self):
        if self._package is None:
            self._package = repositories.Packages(client_api=self._client_api).get(package_id=self.package_id,
                                                                                   fetch=None)
        assert isinstance(self._package, entities.Package)
        return self._package

    @property
    def execution_url(self):
        return 'CURL -X POST' \
               '\nauthorization: Bearer <token>' \
               '\nContent-Type: application/json" -d {' \
               '\n"input": {<input json>}, ' \
               '"projectId": "{<project_id>}", ' \
               '"functionName": "<function_name>"}'

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['executions', 'services', 'triggers'])

        if self._package is None:
            services_repo = repositories.Services(client_api=self._client_api,
                                                  package=self._package,
                                                  project=self._project)
        else:
            services_repo = self._package.services

        triggers = repositories.Triggers(client_api=self._client_api,
                                         project=self._project,
                                         service=self)

        r = reps(executions=repositories.Executions(client_api=self._client_api, service=self),
                 services=services_repo, triggers=triggers)
        return r

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    ###########
    # methods #
    ###########
    def to_json(self):
        _json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Service)._project,
                attr.fields(Service)._package,
                attr.fields(Service)._client_api,
                attr.fields(Service)._repositories,
                attr.fields(Service).project_id,
                attr.fields(Service).init_input,
                attr.fields(Service).module_name,
                attr.fields(Service).bot,
                attr.fields(Service).package_id,
                attr.fields(Service).is_global,
                attr.fields(Service).use_user_jwt,
                attr.fields(Service).package_revision,
                attr.fields(Service).driver_id,
                attr.fields(Service).run_execution_as_process,
                attr.fields(Service).execution_timeout,
                attr.fields(Service).drain_time,
                attr.fields(Service).runtime,
                attr.fields(Service).queue_length_limit,
                attr.fields(Service).on_reset)
        )

        _json['projectId'] = self.project_id
        _json['packageId'] = self.package_id
        _json['initParams'] = self.init_input
        _json['moduleName'] = self.module_name
        _json['botUserName'] = self.bot
        _json['useUserJwt'] = self.use_user_jwt
        _json['global'] = self.is_global
        _json['driverId'] = self.driver_id
        _json['packageRevision'] = self.package_revision
        _json['runExecutionAsProcess'] = self.run_execution_as_process
        _json['executionTimeout'] = self.execution_timeout
        _json['drainTime'] = self.drain_time
        _json['onReset'] = self.on_reset

        if self.is_global is not None:
            _json['global'] = self.is_global

        if self.runtime:
            _json['runtime'] = self.runtime if isinstance(self.runtime, dict) else self.runtime.to_json()

        if self.queue_length_limit is not None:
            _json['queueLengthLimit'] = self.queue_length_limit

        return _json

    def update(self):
        """
        Update Service changes to platform

        :return: Service entity
        """
        return self.services.update(service=self)

    def delete(self):
        """
        Delete Service object

        :return: True
        """
        return self.services.delete(service_id=self.id)

    def status(self):
        """
        Get Service status

        :return: True
        """
        return self.services.status(service_id=self.id)

    def log(self, size=None, checkpoint=None, start=None, end=None, follow=False, text=None,
            execution_id=None, function_name=None, replica_id=None, system=False, view=True):
        """
        Get service logs

        :param text:
        :param view:
        :param system:
        :param end: iso format time
        :param start: iso format time
        :param checkpoint:
        :param follow: filters
        :param execution_id: follow
        :param function_name: execution_id
        :param replica_id: function_name
        :param size:
        :return: Service entity
        """
        return self.services.log(service=self,
                                 size=size,
                                 checkpoint=checkpoint,
                                 start=start,
                                 end=end,
                                 follow=follow,
                                 execution_id=execution_id,
                                 function_name=function_name,
                                 replica_id=replica_id,
                                 system=system,
                                 text=text,
                                 view=view)

    def open_in_web(self):
        self.services.open_in_web(service=self)

    def checkout(self):
        """
        Checkout

        :return:
        """
        return self.services.checkout(service=self)

    def pause(self):
        """
        pause

        :return:
        """
        return self.services.pause(service_id=self.id)

    def resume(self):
        """
        resume

        :return:
        """
        return self.services.resume(service_id=self.id)

    def execute(self,
                # executions info
                execution_input=None, function_name=None,
                # inputs info
                resource=None, item_id=None, dataset_id=None, annotation_id=None, project_id=None,
                # execution config
                sync=False, stream_logs=True, return_output=True):
        """
        Execute a function on an existing service

        :param function_name: function name to run
        :param project_id: resource's project
        :param execution_input: input dictionary or list of FunctionIO entities
        :param dataset_id: optional - input to function
        :param item_id: optional - input to function
        :param annotation_id: optional - input to function
        :param resource: input type.
        :param sync: wait for function to end
        :param stream_logs: prints logs of the new execution. only works with sync=True
        :param return_output: if True and sync is True - will return the output directly
        :return:
        """
        execution = self.executions.create(sync=sync,
                                           execution_input=execution_input,
                                           function_name=function_name,
                                           resource=resource,
                                           item_id=item_id,
                                           dataset_id=dataset_id,
                                           annotation_id=annotation_id,
                                           stream_logs=stream_logs,
                                           project_id=project_id,
                                           return_output=return_output)
        return execution


class InstanceCatalog:
    REGULAR_XS = "regular-xs"
    REGULAR_S = "regular-s"
    REGULAR_M = "regular-m"
    REGULAR_L = "regular-l"
    REGULAR_XL = "regular-xl"
    HIGHMEM_XS = "highmem-xs"
    HIGHMEM_S = "highmem-s"
    HIGHMEM_M = "highmem-m"
    HIGHMEM_L = "highmem-l"
    HIGHMEM_XL = "highmem-xl"
    GPU_K80_S = "gpu-k80-s"


class KubernetesAutuscalerType:
    RABBITMQ = 'rabbitmq'
    CPU = 'cpu'


class KubernetesAutoscaler(entities.BaseEntity):
    MIN_REPLICA_DEFAULT = 0
    MAX_REPLICA_DEFAULT = 1
    AUTOSCALER_TYPE_DEFAULT = KubernetesAutuscalerType.RABBITMQ

    def __init__(self,
                 runtime,
                 autoscaler_type=AUTOSCALER_TYPE_DEFAULT,
                 min_replicas=MIN_REPLICA_DEFAULT,
                 max_replicas=MAX_REPLICA_DEFAULT,
                 **kwargs):
        self.autoscaler_type = kwargs.get('type', autoscaler_type)
        self.min_replicas = kwargs.get('minReplicas', min_replicas)
        self.max_replicas = kwargs.get('maxReplicas', max_replicas)
        self.runtime = runtime

    def to_json(self):
        _json = {
            'type': self.autoscaler_type,
            'minReplicas': self.min_replicas,
            'maxReplicas': self.max_replicas
        }
        return _json

    def delete(self):
        self.runtime._delete_autoscaler()

    def update(self):
        self.runtime.service.update()


class KubernetesRabbitmqAutoscaler(KubernetesAutoscaler):
    QUEUE_LENGTH_DEFAULT = 1000

    def __init__(self,
                 runtime,
                 min_replicas=KubernetesAutoscaler.MIN_REPLICA_DEFAULT,
                 max_replicas=KubernetesAutoscaler.MAX_REPLICA_DEFAULT,
                 queue_length=QUEUE_LENGTH_DEFAULT,
                 **kwargs):
        super().__init__(min_replicas=min_replicas, max_replicas=max_replicas, runtime=runtime,
                         autoscaler_type=KubernetesAutuscalerType.RABBITMQ, **kwargs)
        self.queue_length = kwargs.get('queueLength', queue_length)

    def to_json(self):
        _json = super().to_json()
        _json['queueLength'] = self.queue_length
        return _json


class RuntimeType:
    KUBERNETES = 'kubernetes'


class ServiceRuntime(entities.BaseEntity):
    def __init__(self, service=None, service_type=RuntimeType.KUBERNETES):
        self.service_type = service_type
        self.service = service
        self._autoscaler_delete_mode = False

    def update(self, service=None):
        if service is None and self.service is None:
            raise Exception('Cannot update without a service attribute or service param. Please set service')
        self.service.update()

    def _delete_autoscaler(self):
        self._autoscaler_delete_mode = True
        self.autoscaler = None
        self.service.update()


class KubernetesRuntime(ServiceRuntime):
    DEFAULT_POD_TYPE = InstanceCatalog.REGULAR_S
    DEFAULT_NUM_REPLICAS = 1
    DEFAULT_CONCURRENCY = 6

    def __init__(self,
                 service=None,
                 pod_type=DEFAULT_POD_TYPE,
                 num_replicas=DEFAULT_NUM_REPLICAS,
                 concurrency=DEFAULT_CONCURRENCY,
                 runner_image=None,
                 autoscaler=None,
                 **kwargs):

        super().__init__(service_type=RuntimeType.KUBERNETES, service=service)
        self.pod_type = kwargs.get('podType', pod_type)
        self.num_replicas = kwargs.get('numReplicas', num_replicas)
        self.concurrency = kwargs.get('concurrency', concurrency)
        self.runner_image = kwargs.get('runnerImage', runner_image)
        self._proxy_image = kwargs.get('proxyImage', None)

        self.autoscaler = kwargs.get('autoscaler', autoscaler)
        if self.autoscaler is not None and isinstance(self.autoscaler, dict):
            if self.autoscaler['type'] == KubernetesAutuscalerType.RABBITMQ:
                self.autoscaler = KubernetesRabbitmqAutoscaler(**self.autoscaler, runtime=self)
            else:
                raise NotImplementedError(
                    'Unknown kubernetes autoscaler type: {}'.format(self.autoscaler['type']))

    def to_json(self):
        _json = {
            'podType': self.pod_type,
            'numReplicas': self.num_replicas,
            'concurrency': self.concurrency
        }

        if self.runner_image is not None:
            _json['runnerImage'] = self.runner_image

        if self._proxy_image is not None:
            _json['proxyImage'] = self._proxy_image

        if self.autoscaler is not None:
            _json['autoscaler'] = self.autoscaler.to_json()
        elif self._autoscaler_delete_mode:
            _json['autoscaler'] = None
            self._autoscaler_delete_mode = False

        return _json
