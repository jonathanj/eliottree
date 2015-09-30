import argparse
import json
import sys
from datetime import datetime
from itertools import chain, imap

from toolz import compose

from eliottree import (
    Tree, filter_by_jmespath, filter_by_uuid, render_task_nodes)


def _convert_timestamp(task):
    """
    Convert a ``timestamp`` key to a ``datetime``.
    """
    task['timestamp'] = datetime.utcfromtimestamp(task['timestamp'])
    return task


def build_task_nodes(files=None, select=None, task_uuid=None,
                     human_readable=True):
    """
    Build the task nodes given some input data, query criteria and formatting
    options.
    """
    def task_transformers():
        if human_readable:
            yield _convert_timestamp
        yield json.loads

    def filter_funcs():
        if select is not None:
            for query in select:
                yield filter_by_jmespath(query)

        if task_uuid is not None:
            yield filter_by_uuid(task_uuid)

    if not files:
        files = [sys.stdin]

    tree = Tree()
    tasks = imap(compose(*task_transformers()),
                 chain.from_iterable(files))
    return tree.nodes(tree.merge_tasks(tasks, filter_funcs()))


def display_task_tree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    nodes = build_task_nodes(
        files=args.files,
        select=args.select,
        task_uuid=args.task_uuid,
        human_readable=args.human_readable)
    render_task_nodes(
        write=sys.stdout.write,
        nodes=nodes,
        ignored_task_keys=set(args.ignored_task_keys) or None,
        field_limit=args.field_limit)


def main():
    parser = argparse.ArgumentParser(
        description='Display an Eliot log as a tree of tasks.')
    parser.add_argument('files',
                        metavar='FILE',
                        nargs='*',
                        type=argparse.FileType('r'),
                        help='''Files to process. Omit to read from stdin.''')
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
                        UTC timestamps) as human-readable''')
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
