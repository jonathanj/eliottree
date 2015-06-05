from collections import OrderedDict, defaultdict


def task_name(task):
    """
    Compute the task name for an Eliot task.
    """
    if task is None:
        raise ValueError('Cannot compute the task name for {!r}'.format(task))
    level = u','.join(map(unicode, task[u'task_level']))
    message_type = task.get('message_type', None)
    if message_type is not None:
        status = None
    elif message_type is None:
        message_type = task['action_type']
        status = task['action_status']
    return u'{message_type}@{level}/{status}'.format(
        message_type=message_type,
        level=level,
        status=status)


class _TaskNode(object):
    """
    A node representing an Eliot task and it's child tasks.

    :type task: ``dict``
    :ivar task: Eliot task.

    :type name: ``unicode``
    :ivar name: Node name; this will be derived from the task if it is not
        specified.

    :type _children: ``OrderedDict`` of ``_TaskNode``
    :ivar _children: Child nodes, see ``_TaskNode.children``
    """
    def __init__(self, task, name=None):
        self.task = task
        self._children = OrderedDict()
        if name is None:
            name = task_name(task)
        self.name = name

    def __repr__(self):
        """
        Human-readable representation of the node.
        """
        if self.task is None:
            task_uuid = 'root'
        else:
            # XXX: This is probably wrong in a bunch of places.
            task_uuid = self.task[u'task_uuid'].encode('utf-8')
        return '<{type} {task_uuid} {name} children={children}>'.format(
            type=type(self).__name__,
            task_uuid=task_uuid,
            # XXX: This is probably wrong in a bunch of places.
            name=self.name.encode('utf-8'),
            children=len(self._children))

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
        _add_child(self, node.task['task_level'])

    def first_child(self):
        """
        First child ``_TaskNode``.
        """
        # XXX: The code assumes this is the first node by timestamp (?), but
        # that may not always be true.
        return next(self._children.itervalues())

    def children(self):
        """
        Get a ``list`` of child ``_TaskNode``s ordered by task level.
        """
        return sorted(
            self._children.values(), key=lambda n: n.task[u'task_level'])


class Tree(object):
    """
    Eliot task tree.

    :ivar _nodes: Internal tree storage, use ``Tree.nodes`` or
        ``Tree.matching_nodes`` to obtain the tree nodes.
    """
    def __init__(self):
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
        if uuids:
            nodes = ((k, self._nodes[k]) for k in uuids)
        else:
            nodes = self._nodes.iteritems()
        return sorted(nodes,
                      key=lambda (_, n): n.first_child().task[u'timestamp'])

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
        matches = defaultdict(set)
        if filter_funcs is None:
            filter_funcs = []
        filter_funcs = list(filter_funcs)
        for task in tasks:
            key = task[u'task_uuid']
            node = tasktree.get(key)
            if node is None:
                node = tasktree[key] = _TaskNode(task=None, name=key)
            node.add_child(_TaskNode(task))
            for i, fn in enumerate(filter_funcs):
                if fn(task):
                    matches[i].add(key)
        if not matches:
            return None
        return set.intersection(*matches.values())


__all__ = ['Tree']
