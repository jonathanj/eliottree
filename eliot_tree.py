import argparse
import json
import sys
from datetime import datetime


DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid'])


def _truncate_value(value, limit=100):
    """
    Truncate long values.
    """
    values = value.split('\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return '{}...'.format(value[:limit])
    return value


def _task_name(task):
    """
    Compute the task name for an Eliot task.
    """
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


class TaskNode(object):
    def __init__(self, task, name=None, sorter=None):
        self.task = task
        self._children = {}
        if name is None:
            name = _task_name(task)
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

    def add_child(self, node, levels=None):
        """
        Add a child ``TaskNode``.
        """
        if levels is None:
            levels = node.task['task_level']
        levels = list(levels)
        level = levels.pop(0)
        children = self._children
        if level in children:
            return children[level].add_child(node, levels)
        assert level not in children
        children[level] = node

    def children(self):
        """
        Get an ordered ``list`` of child ``TaskNode``s.
        """
        return sorted(
            self._children.values(), key=lambda n: n.task[u'task_level'])


def _indented_write(write):
    """
    Indent a write.
    """
    def _write(data):
        write('    ' + data)
    return _write


def _format_value(value):
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


def _render_task(write, task, ignored_task_keys):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param task: Eliot task ``dict`` to render.
    :param ignored_task_keys: ``set`` of task key names to ignore.
    """
    _write = _indented_write(write)
    num_items = len(task)
    for i, (key, value) in enumerate(sorted(task.items()), 1):
        if key not in ignored_task_keys:
            tree_char = '`' if i == num_items else '|'
            _value = _format_value(value)
            if isinstance(value, dict):
                write(
                    '{tree_char}-- {key}:\n'.format(
                        tree_char=tree_char,
                        key=key.encode('utf-8')))
                _render_task(_write, _value, {})
            else:
                write(
                    '{tree_char}-- {key}: {value}\n'.format(
                        tree_char=tree_char,
                        key=key.encode('utf-8'),
                        value=_truncate_value(_value)))


def _render_task_node(write, node, ignored_task_keys):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param node: ``TaskNode`` to render.
    :param ignored_task_keys: ``set`` of task key names to ignore.
    """
    _child_write = _indented_write(write)
    if node.task is not None:
        write(
            '+-- {name}\n'.format(
                # XXX: This is probably wrong in a bunch of places.
                name=node.name.encode('utf-8')))
        _render_task(_child_write, node.task, ignored_task_keys)

    for child in node.children():
        _render_task_node(_child_write, child, ignored_task_keys)


def render_task_tree(write, tasktree, ignored_task_keys=DEFAULT_IGNORED_KEYS):
    """
    Render a task tree as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param tasktree: ``list`` of ``(task_uuid, task_node)``.
    :param ignored_task_keys: ``set`` of task key names to ignore.
    """
    for task_uuid, node in tasktree:
        write('{name}\n'.format(
            # XXX: This is probably wrong in a bunch of places.
            name=node.name.encode('utf-8')))
        _render_task_node(write, node, ignored_task_keys)
        write('\n')


def merge_tasktree(tasktree, fd, process_task=None):
    """
    Merge Eliot tasks specified in ``fd`` with ``tasktree`.

    :type tasktree: ``dict``
    :type fd: ``file``-like
    :param process_task: Callable taking a single ``dict`` argument, the task
        read from ``fd``, that returns a transformed ``dict``.
    :return: Newly merged task tree.
    """
    if process_task is None:
        process_task = lambda task: task
    for line in fd:
        task = process_task(json.loads(line))
        key = task[u'task_uuid']
        node = tasktree.get(key)
        if node is None:
            node = tasktree[key] = TaskNode(None, key, task[u'timestamp'])
        node.add_child(TaskNode(task))
    return tasktree


def _convert_timestamp(task):
    """
    Convert a ``timestamp`` key to a ``datetime``.
    """
    task['timestamp'] = datetime.fromtimestamp(task['timestamp'])
    return task


def display_task_tree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    if not args.files:
        args.files.append(sys.stdin)
    process_task = None
    if args.human_readable:
        process_task = _convert_timestamp

    tasktree = {}
    for fd in args.files:
        tasktree = merge_tasktree(tasktree, fd, process_task)

    if args.task_uuid is not None:
        node = tasktree.get(args.task_uuid)
        if node is None:
            tasktree = {}
        else:
            tasktree = {args.task_uuid: node}

    tasktree = sorted(tasktree.items(), key=lambda (_, n): n.sorter)
    render_task_tree(
        write=sys.stdout.write,
        tasktree=tasktree,
        ignored_task_keys=set(args.ignored_task_keys) or DEFAULT_IGNORED_KEYS)


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
                        dest='human_readable',
                        help='''Do not format some task values (such as
                        timestamps) as human-readable''')
    args = parser.parse_args()
    display_task_tree(args)
