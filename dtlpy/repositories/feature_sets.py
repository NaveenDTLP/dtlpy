import logging
from .. import exceptions, entities, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class FeatureSets:
    """
    Feature Sets repository
    """
    URL = '/features/sets'

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._project = project
        self._client_api = client_api

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Datasets repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    ###########
    # methods #
    ###########
    @_api_reference.add(path='/features/sets', method='get')
    def list(self):
        """
        List of features

        :return: List of features
        :rtype: list
        """

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=self.URL)
        if not success:
            raise exceptions.PlatformException(response)

        features = miscellaneous.List([entities.FeatureSet.from_json(_json=_json,
                                                                     client_api=self._client_api) for _json in
                                       response.json()])
        return features

    @_api_reference.add(path='/features/sets/{id}', method='get')
    def get(self, feature_set_name: str = None, feature_set_id: str = None) -> entities.Feature:
        """
        Get Feature Set object

        :param str feature_set_name: name of the feature set
        :param str feature_set_id: id of the feature set
        :return: Feature object
        """
        if feature_set_id is not None:
            success, response = self._client_api.gen_request(req_type="GET",
                                                             path="{}/{}".format(self.URL, feature_set_id))
            if not success:
                raise exceptions.PlatformException(response)
            feature_set = entities.FeatureSet.from_json(client_api=self._client_api,
                                                        _json=response.json())
        elif feature_set_name is not None:
            if not isinstance(feature_set_name, str):
                raise exceptions.PlatformException(
                    error='400',
                    message='feature_set_name must be string')

            feature_sets = [feature_set for feature_set in self.list() if feature_set.name == feature_set_name]
            if len(feature_sets) == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message='Feature set not found. name: {!r}'.format(feature_set_name))
            elif len(feature_sets) > 1:
                # more than one matching project
                raise exceptions.PlatformException(
                    error='404',
                    message='More than one feature_set with same name. Please "get" by id')
            else:
                feature_set = feature_sets[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs, feature_set_name or feature_set_id')
        return feature_set

    @_api_reference.add(path='/features/sets', method='post')
    def create(self, name: str,
               size: int,
               set_type: str,
               data_type: entities.FeatureDataType,
               entity_type: entities.FeatureEntityType,
               project_id: str = None,
               tags: list = None,
               org_id: str = None):
        """
        Create a new Feature Set

        :param str name: the Feature name
        :param int size: the set size
        :param str set_type: string of the feature type: 2d, 3d, modelFC, TSNE,PCA,FFT
        :param entity_type: the entity that feature vector is linked to. Use the enum dl.FeatureEntityType
        :param str project_id: the Id of the project where feature set will be created
        :param list tags: optional tag per feature  - matched by index
        :param str org_id: the Id of the org where feature set will be created
        :param data_type: the type of feature vectors that relate to this set. Use the enum dl.FeatureDataType
        :return: Feature Set object
        """
        if tags is None:
            tags = list()
        if project_id is None:
            if self._project is None:
                raise ValueError('Must input a project id')
            else:
                project_id = self._project.id

        payload = {'name': name,
                   'size': size,
                   'tags': tags,
                   'type': set_type,
                   'project': project_id,
                   'entityType': entity_type}
        if org_id is not None:
            payload['org'] = org_id
        if data_type is not None:
            payload['dataType'] = data_type
        success, response = self._client_api.gen_request(req_type="post",
                                                         json_req=payload,
                                                         path=self.URL)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.FeatureSet.from_json(client_api=self._client_api,
                                             _json=response.json()[0])

    @_api_reference.add(path='/features/sets/{id}', method='delete')
    def delete(self, feature_set_id: str):
        """
        Delete feature vector

        :param str feature_set_id: feature set id to delete
        :return: success
        :rtype: bool
        """

        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="{}/{}".format(self.URL, feature_set_id))

        # check response
        if success:
            logger.debug("Feature Set deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Item]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.FeatureSet._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items
