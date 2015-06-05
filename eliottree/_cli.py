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
    task['timestamp'] = datetime.fromtimestamp(task['timestamp'])
    return task


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
                yield filter_by_jmespath(query)

        if args.task_uuid:
            yield filter_by_uuid(args.task_uuid)

    if not args.files:
        args.files.append(sys.stdin)

    tree = Tree()
    tasks = imap(compose(*task_transformers()),
                 chain.from_iterable(args.files))
    render_task_nodes(
        write=sys.stdout.write,
        nodes=tree.nodes(tree.merge_tasks(tasks, filter_funcs())),
        ignored_task_keys=set(args.ignored_task_keys) or None,
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
