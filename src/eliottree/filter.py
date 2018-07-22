from datetime import datetime

import jmespath
from iso8601.iso8601 import UTC


def filter_by_jmespath(query):
    """
    Produce a function for filtering a task by a jmespath query expression.
    """
    def _filter(task):
        return bool(expn.search(task))
    expn = jmespath.compile(query)
    return _filter


def filter_by_uuid(task_uuid):
    """
    Produce a function for filtering tasks by their UUID.
    """
    return filter_by_jmespath(u'task_uuid == `{}`'.format(task_uuid))


def _parse_timestamp(timestamp):
    """
    Parse a timestamp into a UTC L{datetime}.
    """
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=UTC)


def filter_by_start_date(start_date):
    """
    Produce a function for filtering by task timestamps after (or on) a certain
    date and time.
    """
    def _filter(task):
        return _parse_timestamp(task[u'timestamp']) >= start_date
    return _filter


def filter_by_end_date(end_date):
    """
    Produce a function for filtering by task timestamps before a certain date
    and time.
    """
    def _filter(task):
        return _parse_timestamp(task[u'timestamp']) < end_date
    return _filter


__all__ = [
    'filter_by_jmespath', 'filter_by_uuid', 'filter_by_start_date',
    'filter_by_end_date',
]
