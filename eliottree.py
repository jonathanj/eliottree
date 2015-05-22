import argparse
import json
import sys
from datetime import datetime



DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid'])



def _truncateValue(value, limit=100):
    """
    Truncate long values.
    """
    values = value.split('\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return '{}...'.format(value[:limit])
    return value



def _taskName(task):
    """
    Compute the task name for an Eliot task.
    """
    level = u','.join(map(unicode, task[u'task_level']))
    messageType = task.get('message_type', None)
    if messageType is not None:
        status = None
    elif messageType is None:
        messageType = task['action_type']
        status = task['action_status']
    return u'{messageType}@{level}/{status}'.format(
        messageType=messageType,
        level=level,
        status=status)



class TaskNode(object):
    def __init__(self, task, name=None, sorter=None):
        self.task = task
        self._children = {}
        if name is None:
            name = _taskName(task)
        self.name = name
        self.sorter = sorter


    def __repr__(self):
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


    def addChild(self, node, levels=None):
        """
        Add a child ``TaskNode``.
        """
        if levels is None:
            levels = node.task['task_level']
        levels = list(levels)
        level = levels.pop(0)
        children = self._children
        if level in children:
            return children[level].addChild(node, levels)
        assert level not in children
        children[level] = node


    def children(self):
        """
        Get an ordered ``list`` of child ``TaskNode``s.
        """
        return sorted(
            self._children.values(), key=lambda n: n.task[u'task_level'])



def _indentedWrite(write):
    """
    Indent a write.
    """
    def _write(data):
        write('    ' + data)
    return _write



def _formatValue(value):
    """
    Format a value for a task tree.
    """
    if isinstance(value, datetime):
        return value.isoformat(' ')
    elif isinstance(value, unicode):
        # XXX: This is probably wrong in a bunch of places.
        return value.encode('utf-8')
    elif isinstance(value, dict):
        return value
    # XXX: This is probably wrong in a bunch of places.
    return str(value)



def _renderTask(write, task, ignoredTaskKeys):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param task: Eliot task ``dict`` to render.
    :param ignoredTaskKeys: ``set`` of task key names to ignore.
    """
    _write = _indentedWrite(write)
    numItems = len(task)
    for i, (key, value) in enumerate(sorted(task.items()), 1):
        if key not in ignoredTaskKeys:
            treeChar = '`' if i == numItems else '|'
            _value = _formatValue(value)
            if isinstance(value, dict):
                write(
                    '{treeChar}-- {key}:\n'.format(
                        treeChar=treeChar,
                        key=key.encode('utf-8')))
                _renderTask(_write, _value, {})
            else:
                write(
                    '{treeChar}-- {key}: {value}\n'.format(
                        treeChar=treeChar,
                        key=key.encode('utf-8'),
                        value=_truncateValue(_value)))



def _renderTaskNode(write, node, ignoredTaskKeys):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param node: ``TaskNode`` to render.
    :param ignoredTaskKeys: ``set`` of task key names to ignore.
    """
    _childWrite = _indentedWrite(write)
    if node.task is not None:
        write(
            '+-- {name}\n'.format(
                # XXX: This is probably wrong in a bunch of places.
                name=node.name.encode('utf-8')))
        _renderTask(_childWrite, node.task, ignoredTaskKeys)

    for child in node.children():
        _renderTaskNode(_childWrite, child, ignoredTaskKeys)



def renderTaskTree(write, tasktree, ignoredTaskKeys=DEFAULT_IGNORED_KEYS):
    """
    Render a task tree as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param tasktree: ``list`` of ``(task_uuid, task_node)``.
    :param ignoredTaskKeys: ``set`` of task key names to ignore.
    """
    for task_uuid, node in tasktree:
        write('{name}\n'.format(
            # XXX: This is probably wrong in a bunch of places.
            name=node.name.encode('utf-8')))
        _renderTaskNode(write, node, ignoredTaskKeys)
        write('\n')



def mergeTasktree(tasktree, fd, processTask=None):
    """
    Merge Eliot tasks specified in ``fd`` with ``tasktree`.

    :type tasktree: ``dict``
    :type fd: ``file``-like
    :param processTask: Callable taking a single ``dict`` argument, the task
        read from ``fd``, that returns a transformed ``dict``.
    :return: Newly merged task tree.
    """
    if processTask is None:
        processTask = lambda task: task
    for line in fd:
        task = processTask(json.loads(line))
        key = task[u'task_uuid']
        node = tasktree.get(key)
        if node is None:
            node = tasktree[key] = TaskNode(None, key, task[u'timestamp'])
        node.addChild(TaskNode(task))
    return tasktree



def _convertTimestamp(task):
    """
    Convert a ``timestamp`` key to a ``datetime``.
    """
    task['timestamp'] = datetime.fromtimestamp(task['timestamp'])
    return task



def displayTaskTree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    if not args.files:
        args.files.append(sys.stdin)
    processTask = None
    if args.human_readable:
        processTask = _convertTimestamp

    tasktree = {}
    for fd in args.files:
        tasktree = mergeTasktree(tasktree, fd, processTask)

    if args.task_uuid is not None:
        node = tasktree.get(args.task_uuid)
        if node is None:
            tasktree = {}
        else:
            tasktree = {args.task_uuid: node}

    tasktree = sorted(tasktree.items(), key=lambda (_, n): n.sorter)
    renderTaskTree(
        write=sys.stdout.write,
        tasktree=tasktree,
        ignoredTaskKeys=set(args.ignored_task_keys) or DEFAULT_IGNORED_KEYS)


def main():
    parser = argparse.ArgumentParser(
        description='Display an Eliot log as a tree of tasks.')
    parser.add_argument('files',
                        metavar='FILE',
                        nargs='*',
                        type=argparse.FileType('r'),
                        help='''Files to process''')
    parser.add_argument('-u', '--task-uuid',
                        dest='task_uuid',
                        metavar='UUID',
                        help='''Select a specific task by UUID''')
    parser.add_argument('-i', '--ignore-task-key',
                        action='append',
                        default=[],
                        dest='ignored_task_keys',
                        metavar='KEY',
                        help='''Ignore a task key, use multiple times to ignore
                        multiple keys. Defaults to ignoring most Eliot standard
                        keys.''')
    parser.add_argument('--raw',
                        action='store_false',
                        #default=True,
                        #const=False,
                        dest='human_readable',
                        help='''Do not format some task values (such as
                        timestamps) as human-readable''')
    args = parser.parse_args()
    displayTaskTree(args)
