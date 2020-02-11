import attr
from .. import entities, services, miscellaneous, exceptions, repositories


@attr.s
class Trigger:
    """
    Trigger Entity
    """
    #######################
    # Platform attributes #
    #######################
    id = attr.ib()
    url = attr.ib(repr=False)
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()
    name = attr.ib()
    active = attr.ib()
    scope = attr.ib()

    ###################
    # spec attributes #
    ###################
    resource = attr.ib()
    actions = attr.ib()
    execution_mode = attr.ib(repr=False)
    # name change
    function_name = attr.ib()
    service_id = attr.ib()
    webhook_id = attr.ib()

    ########
    # temp #
    ########
    special = attr.ib(repr=False)

    ##############################
    # different name in platform #
    ##############################
    filters = attr.ib()
    project_id = attr.ib()
    _spec = attr.ib()

    ##################
    # SDK attributes #
    ##################
    _service = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _op_type = attr.ib(default='service')

    # noinspection PyShadowingBuiltins
    @classmethod
    def from_json(cls, _json, client_api, project, service=None):
        spec = _json.get('spec', dict())
        operation = spec.get('operation', dict())
        filters = spec.get('filter', dict())
        op_type = operation.get('type', None)

        if op_type == 'function':
            service_id = operation.get('serviceId', None)
            webhook_id = None
        elif op_type == 'webhook':
            webhook_id = operation.get('webhookId', None)
            service_id = None
        else:
            raise exceptions.PlatformException('400', 'unknown trigger operation type: {}'.format(op_type))

        return cls(
            execution_mode=spec.get('executionMode', None),
            project_id=_json.get('projectId', None),
            updatedAt=_json.get('updatedAt', None),
            createdAt=_json.get('createdAt', None),
            resource=spec.get('resource', None),
            creator=_json.get('creator', None),
            special=_json.get('special', None),
            actions=spec.get('actions', None),
            active=_json.get('active', None),
            function_name=operation.get('functionName', None),
            scope=_json.get('scope', None),
            name=_json.get('name', None),
            service_id=service_id,
            url=_json.get('url', None),
            webhook_id=webhook_id,
            client_api=client_api,
            filters=filters,
            project=project,
            service=service,
            id=_json['id'],
            op_type=op_type,
            spec=spec,
        )

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def service(self):
        if self._service is None:
            self.get_service()
            if self._service is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "service".')
        assert isinstance(self._service, entities.Service)
        return self._service

    def get_service(self, dummy=False):
        if self._service is None:
            if dummy:
                self._service = entities.Service.dummy(service_id=self.service_id, client_api=self._client_api)
            else:
                self._service = self.project.services.get(service_id=self.service_id)

    def get_project(self, dummy=False):
        if self._project is None:
            if dummy:
                self._project = entities.Project.dummy(project_id=self.project_id, client_api=self._client_api)
            else:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id)

    ###########
    # functions #
    ###########
    def print(self):
        miscellaneous.List([self]).print()

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Trigger)._client_api,
                                                              attr.fields(Trigger).project_id,
                                                              attr.fields(Trigger)._project,
                                                              attr.fields(Trigger)._service,
                                                              attr.fields(Trigger).special,
                                                              attr.fields(Trigger).filters,
                                                              attr.fields(Trigger)._op_type,
                                                              attr.fields(Trigger)._spec,
                                                              attr.fields(Trigger).resource,
                                                              attr.fields(Trigger).actions,
                                                              attr.fields(Trigger).service_id,
                                                              attr.fields(Trigger).webhook_id,
                                                              attr.fields(Trigger).execution_mode,
                                                              attr.fields(Trigger).function_name
                                                              ))

        # rename
        _json['projectId'] = self.project_id
        operation = {
            'type': self._op_type,
            'functionName': self.function_name
        }

        if self._op_type == 'function':
            operation['serviceId'] = self.service_id
        elif self._op_type == 'webhook':
            operation['webhookId'] = self.webhook_id

        _json['spec'] = {
            'filter': self.filters,
            'executionMode': self.execution_mode,
            'resource': self.resource,
            'actions': self.actions,
            'operation': operation,
        }

        return _json

    def delete(self):
        """
        Delete Trigger object

        :return: True
        """
        return self.project.triggers.delete(trigger_id=self.id)

    def update(self):
        """

        :return: Trigger entity
        """
        return self.project.triggers.update(trigger=self)
