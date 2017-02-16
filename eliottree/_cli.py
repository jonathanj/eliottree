import argparse
import codecs
import json
import sys
from functools import partial
from itertools import chain
from pprint import pformat

import iso8601
from six import PY3, binary_type
from six.moves import map

from eliottree import (
    TaskMergeError, Tree, filter_by_end_date, filter_by_jmespath,
    filter_by_start_date, filter_by_uuid, render_task_nodes_unicode)


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

    if PY3:
        stderr = sys.stderr
    else:
        stderr = codecs.getwriter('utf-8')(sys.stderr)

    def _parse_file(inventory, f):
        for line_no, line in enumerate(f, 1):
            file_name = f.name
            try:
                task = json.loads(line)
                inventory[id(task)] = file_name, line_no
                yield task
            except Exception:
                if isinstance(line, binary_type):
                    line = line.decode('utf-8')
                stderr.write(
                    u'Task parsing error, file {}, line {}:\n{}\n'.format(
                        file_name, line_no, line))
                raise

    inventory = {}
    tree = Tree()
    tasks = chain.from_iterable(map(partial(_parse_file, inventory), files))
    try:
        return tree.nodes(tree.merge_tasks(tasks, filter_funcs()))
    except TaskMergeError as e:
        file_name, line_no = inventory.get(
            id(e.task), (u'<unknown>', u'<unknown>'))
        stderr.write(
            u'Task merging error, file {}, line {}:\n{}\n\n'.format(
                file_name, line_no, pformat(e.task)))
        exc_info = e.exc_info
        raise exc_info[0], exc_info[1], exc_info[2]


def display_task_tree(args):
    """
    Read the input files, apply any command-line-specified behaviour and
    display the task tree.
    """
    if PY3:
        write = sys.stdout.write
    else:
        write = codecs.getwriter('utf-8')(sys.stdout).write

    if args.color == 'auto':
        colorize = sys.stdout.isatty()
    else:
        colorize = args.color == 'always'

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
        human_readable=args.human_readable,
        colorize=colorize)


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
    parser.add_argument('--color',
                        default='auto',
                        choices=['always', 'auto', 'never'],
                        dest='color',
                        help='''Color the output. Defaults based on whether
                        the output is a TTY.''')
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
