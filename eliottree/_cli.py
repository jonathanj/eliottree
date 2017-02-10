import argparse
import codecs
import json
import sys
from itertools import chain

import iso8601
from six import PY3
from six.moves import map

from eliottree import (
    Tree, filter_by_end_date, filter_by_jmespath, filter_by_start_date,
    filter_by_uuid, render_task_nodes_unicode)


def build_task_nodes(files=None, select=None, task_uuid=None, start=None,
                     end=None):
    """
    Build the task nodes given some input data, query criteria and formatting
    options.
    """
    def filter_funcs():
        if start:
            yield filter_by_start_date(start)
        if end:
            yield filter_by_end_date(end)

        if select is not None:
            for query in select:
                yield filter_by_jmespath(query)

        if task_uuid is not None:
            yield filter_by_uuid(task_uuid)

    if not files:
        if PY3:
            files = [sys.stdin]
        else:
            files = [codecs.getreader('utf-8')(sys.stdin)]

    tree = Tree()
    tasks = map(json.loads, chain.from_iterable(files))
    return tree.nodes(tree.merge_tasks(tasks, filter_funcs()))


def display_task_tree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    if PY3:
        write = sys.stdout.write
    else:
        write = codecs.getwriter('utf-8')(sys.stdout).write

    nodes = build_task_nodes(
        files=args.files,
        select=args.select,
        task_uuid=args.task_uuid,
        start=args.start,
        end=args.end)
    render_task_nodes_unicode(
        write=write,
        nodes=nodes,
        ignored_task_keys=set(args.ignored_task_keys) or None,
        field_limit=args.field_limit,
        human_readable=args.human_readable)


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
    parser.add_argument('--start',
                        dest='start',
                        type=iso8601.parse_date,
                        help='''Select tasks whose timestamp occurs after (or
                        on) an ISO8601 date.''')
    parser.add_argument('--end',
                        dest='end',
                        type=iso8601.parse_date,
                        help='''Select tasks whose timestamp occurs before an
                        ISO8601 date.''')
    args = parser.parse_args()
    display_task_tree(args)
