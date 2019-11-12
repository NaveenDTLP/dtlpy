import logging
import math
import copy
import attr

from .. import entities, services, miscellaneous, exceptions

logger = logging.getLogger(name=__name__)


@attr.s
class PagedEntities:
    """
    Pages object
    """
    # api
    _client_api = attr.ib(type=services.ApiClient)

    # params
    page_offset = attr.ib()
    page_size = attr.ib()
    filters = attr.ib()
    items_repository = attr.ib()
    item_entity = attr.ib(default=entities.Item)
    has_next_page = attr.ib(default=False)
    total_pages_count = attr.ib(default=0)
    items_count = attr.ib(default=0)

    # items list
    items = attr.ib(default=miscellaneous.List())

    def process_result(self, result):
        if 'page_offset' in result:
            self.page_offset = result['page_offset']
        if 'page_size' in result:
            self.page_size = result['page_size']
        if 'hasNextPage' in result:
            self.has_next_page = result['hasNextPage']
        if 'totalItemsCount' in result:
            self.items_count = result['totalItemsCount']
        if 'totalPagesCount' in result:
            self.total_pages_count = result['totalPagesCount']
        if 'items' in result:
            if self.filters.resource == 'items':
                items = miscellaneous.List(
                    [self.item_entity.from_json(client_api=self._client_api,
                                                _json=_json,
                                                dataset=self.items_repository.dataset)
                     for _json in result['items']])
            elif self.filters.resource == 'annotations':
                items = self.load_annotations(result=result)
            else:
                raise exceptions.PlatformException('400', 'Unknown page entity type')
        else:
            items = list()
        return items

    def __iter__(self):
        self.page_offset = 0
        self.has_next_page = True
        while self.has_next_page:
            items = self.get_page()
            yield items
            self.page_offset += 1

    def __reversed__(self):
        self.page_offset = self.total_pages_count - 1
        while True:
            items = self.get_page()
            yield items
            if self.page_offset == 0:
                break
            self.page_offset -= 1

    def get_page(self, page_offset=None, page_size=None):
        filters = copy.copy(self.filters)
        filters.page = self.page_offset
        filters.page_size = self.page_size
        if page_offset is not None:
            filters.page = page_offset
        if page_size is not None:
            filters.page_size = page_size
        result = self.items_repository.get_list(filters=filters)
        items = self.process_result(result)
        return items

    def print(self):
        self.items.print()

    def next_page(self):
        """
        Brings the next page of items from host

        :return:
        """
        self.page_offset += 1
        self.items = self.get_page()

    def prev_page(self):
        """
        Brings the previous page of items from host

        :return:
        """
        self.page_offset -= 1
        self.items = self.get_page()

    def go_to_page(self, page=0):
        """
        Brings specified page of items from host

        :param page: page number
        :return:
        """
        self.page_offset = page
        self.items = self.get_page()

    def load_annotations(self, result):
        items = dict()
        annotations = [None] * len(result['items'])
        for i_json, _json in enumerate(result['items']):
            if _json['itemId'] not in items:
                items[_json['itemId']] = self.items_repository.get(item_id=_json['itemId'])
            annotations[i_json] = self.item_entity.from_json(item=items[_json['itemId']], _json=_json)
        return miscellaneous.List(annotations)

    def all(self):
        page_offset = 0
        page_size = 100
        total_pages = math.ceil(self.items_count / page_size)
        total_items = list()
        jobs = list()
        while True:
            if len(total_items) < 50 and page_offset <= total_pages:
                jobs.append(self._client_api.thread_pool.apply_async(self.get_page, kwds={'page_offset': page_offset,
                                                                                          'page_size': page_size}))
                page_offset += 1
            for i_job, job in enumerate(jobs):
                if job.ready():
                    for item in job.get():
                        yield item
                    jobs.remove(job)
            if len(jobs) == 0:
                break
