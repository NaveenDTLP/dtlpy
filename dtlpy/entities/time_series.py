import attr
from .. import utilities


@attr.s
class TimeSeries:
    """
    Session object
    """
    # platform
    id = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    esIndex = attr.ib()
    esInstance = attr.ib()
    owner = attr.ib()
    name = attr.ib()
    # params
    # entities
    project = attr.ib()

    @classmethod
    def from_json(cls, _json, project):
        """
        Build a TimeSeries entity object from a json

        :param _json: _json response form host
        :param project: project id
        :return: Session object
        """
        return cls(
            esIndex=_json['esIndex'],
            esInstance=_json['esInstance'],
            owner=_json['owner'],
            project=project,
            id=_json['id'],
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            name=_json['name']
        )

    def print(self):
        utilities.List([self]).print()

    def add(self, data):
        self.project.times_series.add(series=self, data=data)

    def delete(self):
        self.project.times_series.delete(series=self)

    def table(self, filters=None):
        return self.project.times_series.get_table(series=self, filters=filters)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(TimeSeries).project))
