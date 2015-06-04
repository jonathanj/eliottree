import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from itertools import chain, imap

import jmespath

from eliottree.tree import TaskNode, Tree

DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid'])


def compose(*fs):
    """
    Create a function composition.

    :param fs: Iterable of 1-argument functions to compose. Functions are
        composed from last to first.
    :return: I{callable} taking 1 argument
    """
    return reduce(lambda f, g: lambda x: f(g(x)), fs)



def _truncate_value(value, limit):
    """
    Truncate long values.
    """
    values = value.split('\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return '{} [...]'.format(value[:limit])
    return value


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


def _render_task(write, task, ignored_task_keys, field_limit):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param task: Eliot task ``dict`` to render.
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.
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
                _render_task(_write, _value, {}, field_limit)
            else:
                if field_limit:
                    first_line = _truncate_value(_value, field_limit)
                else:
                    lines = _value.splitlines() or [u'']
                    first_line = lines.pop(0)
                write(
                    '{tree_char}-- {key}: {value}\n'.format(
                        tree_char=tree_char,
                        key=key.encode('utf-8'),
                        value=first_line))
                if not field_limit:
                    for line in lines:
                        _write(line + '\n')


def _render_task_node(write, node, field_limit, ignored_task_keys):
    """
    Render a single ``TaskNode`` as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param node: ``TaskNode`` to render.
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.
    :param ignored_task_keys: ``set`` of task key names to ignore.
    """
    _child_write = _indented_write(write)
    if node.task is not None:
        write(
            '+-- {name}\n'.format(
                # XXX: This is probably wrong in a bunch of places.
                name=node.name.encode('utf-8')))
        _render_task(
            write=_child_write,
            task=node.task,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys)

    for child in node.children():
        _render_task_node(
            write=_child_write,
            node=child,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys)


def render_task_tree(write, tasktree, field_limit,
                     ignored_task_keys=DEFAULT_IGNORED_KEYS):
    """
    Render a task tree as an ``ASCII`` tree.

    :param write: Callable taking a single ``bytes`` argument to write the
        output.
    :param tasktree: ``list`` of ``(task_uuid, task_node)``.
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.
    :param ignored_task_keys: ``set`` of task key names to ignore.
    """
    for task_uuid, node in tasktree:
        write('{name}\n'.format(
            # XXX: This is probably wrong in a bunch of places.
            name=node.name.encode('utf-8')))
        _render_task_node(
            write=write,
            node=node,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys)
        write('\n')


def _convert_timestamp(task):
    """
    Convert a ``timestamp`` key to a ``datetime``.
    """
    task['timestamp'] = datetime.fromtimestamp(task['timestamp'])
    return task


def _filter_by_jmespath(query):
    """
    A factory function producting a filter function for filtering a task by
    a jmespath query expression.
    """
    expn = jmespath.compile(query)
    def _filter(task):
        return bool(expn.search(task))
    return _filter


def display_task_tree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    def task_transformers():
        if args.human_readable:
            yield _convert_timestamp
        yield json.loads

    def filter_funcs():
        if args.select:
            for query in args.select:
                yield _filter_by_jmespath(query)

        if args.task_uuid:
            yield _filter_by_jmespath(
                'task_uuid == `{}`'.format(args.task_uuid))

    if not args.files:
        args.files.append(sys.stdin)

    tree = Tree()
    tasks = imap(compose(*task_transformers()),
                 chain.from_iterable(args.files))
    tasktree = tree.nodes(tree.merge_tasks(tasks, filter_funcs()))
    render_task_tree(
        write=sys.stdout.write,
        tasktree=tasktree,
        ignored_task_keys=set(args.ignored_task_keys) or DEFAULT_IGNORED_KEYS,
        field_limit=args.field_limit)


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
    parser.add_argument('-l', '--field-limit',
                        metavar='LENGTH',
                        type=int,
                        default=100,
                        dest='field_limit',
                        help='''Limit the length of field values to LENGTH or a
                        newline, whichever comes first. Use a length of 0 to
                        output the complete value.''')
    parser.add_argument('--select',
                        action='append',
                        metavar='QUERY',
                        dest='select',
                        help='''Select tasks to be displayed based on a jmespath
                        query, can be specified multiple times to mimic logical
                        AND. If any child task is selected the entire top-level
                        task is selected. See <http://jmespath.org/>''')
    args = parser.parse_args()
    display_task_tree(args)
