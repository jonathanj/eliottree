import jmespath


def filter_by_jmespath(query):
    """
    A factory function producing a filter function for filtering a task by
    a jmespath query expression.
    """
    def _filter(task):
        return bool(expn.search(task))
    expn = jmespath.compile(query)
    return _filter


def filter_by_uuid(task_uuid):
    """
    A factory function producing a filter function for filtering tasks by their
    UUID.
    """
    return filter_by_jmespath('task_uuid == `{}`'.format(task_uuid))


__all__ = ['filter_by_jmespath', 'filter_by_uuid']
