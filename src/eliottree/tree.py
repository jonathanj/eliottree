import sys
from warnings import warn

from six import text_type as unicode
from six import PY2


def task_name(task):
    """
    Compute the task name for an Eliot task.

    If we can't find a ``message_type`` or an ``action_type`` field to use to
    derive the name, then return ``None``.
    """
    if task is None:
        raise ValueError('Cannot compute task name', task)
    level = u','.join(map(unicode, task[u'task_level']))
    message_type = task.get('message_type', None)
    if message_type is not None:
        status = u''
    elif message_type is None:
        message_type = task.get('action_type', None)
        if message_type is None:
            return None
        status = u'/' + task['action_status']
    return u'{message_type}@{level}{status}'.format(
        message_type=message_type,
        level=level,
        status=status)


class _TaskNode(object):
    """
    A node representing an Eliot task and its child tasks.

    :type task: ``dict``
    :ivar task: Eliot task.

    :type name: ``unicode``
    :ivar name: Node name; this will be derived from the task if it is not
        specified.

    :type _children: ``dict`` of ``_TaskNode``
    :ivar _children: Child nodes, see ``_TaskNode.children``
    """

    _DEFAULT_TASK_NAME = u'<UNNAMED TASK>'

    def __init__(self, task, name=None):
        if task is None:
            raise ValueError('Missing eliot task')
        self.task = task
        self._children = dict()
        if name is None:
            name = task_name(task) or self._DEFAULT_TASK_NAME
        self.name = name
        self.success = None

    def __repr__(self):
        """
        Human-readable representation of the node.
        """
        task_uuid = self.task[u'task_uuid']
        name = self.name
        if PY2:
            # XXX: This is probably wrong in a bunch of places.
            task_uuid = task_uuid.encode('utf-8')
            name = name.encode('utf-8')
        return '<{type} {task_uuid!r} {name!r} children={children}>'.format(
            type=type(self).__name__,
            task_uuid=task_uuid,
            name=name,
            children=len(self._children))

    def copy(self):
        """
        Make a shallow copy of this node.
        """
        return type(self)(self.task, self.name)

    def add_child(self, node):
        """
        Add a child node.

        :type node: ``_TaskNode``
        :param node: Child node to add to the tree, if the child has multiple
            levels it may be added as a grandchild.
        """
        def _add_child(parent, levels):
            levels = list(levels)
            level = levels.pop(0)
            children = parent._children
            if level in children:
                _add_child(children[level], levels)
            else:
                children[level] = node
                action_status = node.task.get('action_status')
                if action_status == u'succeeded':
                    node.success = parent.success = True
                elif action_status == u'failed':
                    node.success = parent.success = False
        _add_child(self, node.task['task_level'])

    def children(self):
        """
        Get a ``list`` of child ``_TaskNode``s ordered by task level.
        """
        return sorted(
            self._children.values(), key=lambda n: n.task[u'task_level'])


def missing_start_task(task_missing_parent):
    """
    Create a fake start task for an existing task that happens to be missing
    one.
    """
    return {
        u'action_type': u'<missing start task>',
        u'action_status': u'started',
        u'timestamp': task_missing_parent[u'timestamp'],
        u'task_uuid': task_missing_parent[u'task_uuid'],
        u'task_level': [1]}


class TaskMergeError(RuntimeError):
    """
    An exception occured while trying to merge a task into the tree.
    """
    def __init__(self, task, exc_info):
        self.task = task
        self.exc_info = exc_info
        RuntimeError.__init__(self)


class Tree(object):
    """
    Eliot task tree.

    :ivar _nodes: Internal tree storage, use ``Tree.nodes`` or
        ``Tree.matching_nodes`` to obtain the tree nodes.
    """
    def __init__(self):
        warn('Tree is deprecated, use eliottree.tasks_from_iterable instead',
             DeprecationWarning, 2)
        self._nodes = {}

    def nodes(self, uuids=None):
        """
        All top-level nodes in the tree.

        :type uuids: ``set`` of ``unicode``
        :param uuids: Set of task UUIDs to include, or ``None`` for no
            filtering.

        :rtype: ``iterable`` of 2-``tuple``s
        :return: Iterable of key and node pairs for top-level nodes, sorted by
            timestamp.
        """
        if uuids is not None:
            nodes = ((k, self._nodes[k]) for k in uuids)
        else:
            nodes = self._nodes.items()
        return sorted(nodes, key=lambda x: x[1].task[u'timestamp'])

    def merge_tasks(self, tasks, filter_funcs=None):
        """
        Merge tasks into the tree.

        :type tasks: ``iterable`` of ``dict``
        :param tasks: Iterable of task dicts.

        :type filter_funcs: ``iterable`` of 1-argument ``callable``s returning
            ``bool``
        :param filter_funcs: Iterable of predicate functions that given a task
            determine whether to keep it.

        :return: ``set`` of task UUIDs that match all of the filter functions,
            can be passed to ``Tree.matching_nodes``, or ``None`` if no filter
            functions were specified.
        """
        tasktree = self._nodes
        if filter_funcs is None:
            filter_funcs = []
        filter_funcs = list(filter_funcs)
        matches = dict((i, set()) for i, _ in enumerate(filter_funcs))

        def _merge_one(task, create_missing_tasks):
            key = task[u'task_uuid']
            node = tasktree.get(key)
            if node is None:
                if task[u'task_level'] != [1]:
                    if create_missing_tasks:
                        n = tasktree[key] = _TaskNode(
                            task=missing_start_task(task))
                        n.add_child(_TaskNode(task))
                    else:
                        return task
                else:
                    node = tasktree[key] = _TaskNode(task=task)
            else:
                node.add_child(_TaskNode(task))
            for i, fn in enumerate(filter_funcs):
                if fn(task):
                    matches[i].add(key)
            return None

        def _merge(tasks, create_missing_tasks=False):
            pending = []
            for task in tasks:
                try:
                    result = _merge_one(task, create_missing_tasks)
                    if result is not None:
                        pending.append(result)
                except Exception:
                    raise TaskMergeError(task, sys.exc_info())
            return pending

        pending = _merge(tasks)
        if pending:
            pending = _merge(pending, True)
            if pending:
                raise RuntimeError('Some tasks have no start parent', pending)
        if not matches:
            return None
        return set.intersection(*matches.values())


__all__ = ['Tree']
