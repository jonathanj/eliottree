import argparse
import codecs
import json
import sys
from pprint import pformat

import iso8601
from six import PY3, binary_type, reraise
from six.moves import filter
from toolz import compose

from eliottree import (
    EliotParseError, JSONParseError, filter_by_end_date, filter_by_jmespath,
    filter_by_start_date, filter_by_uuid, render_tasks, tasks_from_iterable)


def text_writer(fd):
    """
    File writer that accepts Unicode to write.
    """
    if PY3:
        return fd
    return codecs.getwriter('utf-8')(fd)


def text_reader(fd):
    """
    File reader that returns Unicode from reading.
    """
    if PY3:
        return fd
    return codecs.getreader('utf-8')(fd)


def parse_messages(files=None, select=None, task_uuid=None, start=None,
                   end=None):
    """
    Parse message dictionaries from inputs into Eliot tasks, filtering by any
    provided criteria.
    """
    def filter_funcs():
        if task_uuid is not None:
            yield filter_by_uuid(task_uuid)
        if start:
            yield filter_by_start_date(start)
        if end:
            yield filter_by_end_date(end)
        if select is not None:
            for query in select:
                yield filter_by_jmespath(query)

    def _parse(files, inventory):
        for file in files:
            file_name = getattr(file, 'name', '<unknown>')
            for line_number, line in enumerate(file, 1):
                try:
                    task = json.loads(line)
                    inventory[id(task)] = file_name, line_number
                    yield task
                except Exception:
                    raise JSONParseError(
                        file_name,
                        line_number,
                        line.rstrip(u'\n'),
                        sys.exc_info())

    if not files:
        files = [text_reader(sys.stdin)]
    inventory = {}
    return inventory, tasks_from_iterable(
        filter(compose(*filter_funcs()), _parse(files, inventory)))


def display_tasks(tasks, color, ignored_fields, field_limit, human_readable):
    """
    Render Eliot tasks, apply any command-line-specified behaviour and render
    the task trees to stdout.
    """
    write = text_writer(sys.stdout).write
    write_err = text_writer(sys.stderr).write
    if color == 'auto':
        colorize = sys.stdout.isatty()
    else:
        colorize = color == 'always'
    render_tasks(
        write=write,
        write_err=write_err,
        tasks=tasks,
        ignored_fields=set(ignored_fields) or None,
        field_limit=field_limit,
        human_readable=human_readable,
        colorize=colorize)


def _decode_command_line(value, encoding='utf-8'):
    """
    Decode a command-line argument.
    """
    if isinstance(value, binary_type):
        return value.decode(encoding)
    return value


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
                        type=_decode_command_line,
                        help='''Select a specific task by UUID''')
    parser.add_argument('-i', '--ignore-task-key',
                        action='append',
                        default=[],
                        dest='ignored_fields',
                        metavar='KEY',
                        type=_decode_command_line,
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
                        type=_decode_command_line,
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
    stderr = text_writer(sys.stderr)
    try:
        inventory, tasks = parse_messages(
            files=args.files,
            select=args.select,
            task_uuid=args.task_uuid,
            start=args.start,
            end=args.end)
        display_tasks(
            tasks=tasks,
            color=args.color,
            ignored_fields=args.ignored_fields,
            field_limit=args.field_limit,
            human_readable=args.human_readable)
    except JSONParseError as e:
        stderr.write('JSON parse error, file {}, line {}:\n{}\n\n'.format(
            e.file_name,
            e.line_number,
            e.line))
        reraise(*e.exc_info)
    except EliotParseError as e:
        file_name, line_number = inventory.get(
            id(e.message_dict), (u'<unknown>', u'<unknown>'))
        stderr.write(
            'Eliot message parse error, file {}, line {}:\n{}\n\n'.format(
                file_name,
                line_number,
                pformat(e.message_dict)))
        reraise(*e.exc_info)
