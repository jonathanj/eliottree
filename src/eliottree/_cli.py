import argparse
import codecs
import json
import os
import platform
import sys
from pprint import pformat

import iso8601
from six import PY3, binary_type, reraise
from six.moves import filter

from eliottree import (
    EliotParseError, JSONParseError, filter_by_end_date, filter_by_jmespath,
    filter_by_start_date, filter_by_uuid, render_tasks, tasks_from_iterable,
    combine_filters_and)
from eliottree._color import colored
from eliottree._theme import get_theme, apply_theme_overrides


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
        filter(combine_filters_and(*filter_funcs()), _parse(files, inventory)))


def setup_platform(colorize):
    """
    Set up any platform specifics for console output etc.
    """
    if platform.system() == 'Windows':
        # Initialise Unicode support for Windows terminals, even if they're not
        # using the Unicode codepage.
        import win_unicode_console  # noqa: E402
        import warnings  # noqa: E402
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            win_unicode_console.enable()


def display_tasks(tasks, color, colorize_tree, ascii, theme_name, ignored_fields,
                  field_limit, human_readable, utc_timestamps, theme_overrides):
    """
    Render Eliot tasks, apply any command-line-specified behaviour and render
    the task trees to stdout.
    """
    if color == 'auto':
        colorize = sys.stdout.isatty()
    else:
        colorize = color == 'always'

    setup_platform(colorize=colorize)
    write = text_writer(sys.stdout).write
    write_err = text_writer(sys.stderr).write
    if theme_name == 'auto':
        dark_background = is_dark_terminal_background(default=True)
    else:
        dark_background = theme_name == 'dark'
    theme = apply_theme_overrides(
        get_theme(
            dark_background=dark_background,
            colored=colored if colorize else None),
        theme_overrides)

    render_tasks(
        write=write,
        write_err=write_err,
        tasks=tasks,
        ignored_fields=set(ignored_fields) or None,
        field_limit=field_limit,
        human_readable=human_readable,
        colorize_tree=colorize and colorize_tree,
        ascii=ascii,
        utc_timestamps=utc_timestamps,
        theme=theme)


def _decode_command_line(value, encoding='utf-8'):
    """
    Decode a command-line argument.
    """
    if isinstance(value, binary_type):
        return value.decode(encoding)
    return value


def is_dark_terminal_background(default=True):
    """
    Does the terminal use a dark background color?

    Currently just checks the `COLORFGBG` environment variable, if it exists,
    which some terminals define as `fg:bg`.

    :rtype: bool
    """
    colorfgbg = os.environ.get('COLORFGBG', None)
    if colorfgbg is not None:
        parts = os.environ['COLORFGBG'].split(';')
        try:
            last_number = int(parts[-1])
            if 0 <= last_number <= 6 or last_number == 8:
                return True
            else:
                return False
        except ValueError:
            pass
    return default


CONFIG_PATHS = [
    os.path.expanduser('~/.config/eliot-tree/config.json'),
]


def locate_config():
    """
    Find the first config search path that exists.
    """
    return next((path for path in CONFIG_PATHS if os.path.exists(path)), None)


def read_config(path):
    """
    Read a config file from the specified path.
    """
    if path is None:
        return {}
    with open(path, 'rb') as fd:
        return json.load(fd)


CONFIG_BLACKLIST = [
    'files', 'start', 'end', 'print_default_config', 'config', 'select',
    'task_uuid']


def print_namespace(namespace):
    """
    Print an argparse namespace to stdout as JSON.
    """
    config = {k: v for k, v in vars(namespace).items()
              if k not in CONFIG_BLACKLIST}
    stdout = text_writer(sys.stdout)
    stdout.write(json.dumps(config, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description='Display an Eliot log as a tree of tasks.')
    parser.add_argument('files',
                        metavar='FILE',
                        nargs='*',
                        type=argparse.FileType('r'),
                        help='''Files to process. Omit to read from stdin.''')
    parser.add_argument('--config',
                        metavar='FILE',
                        dest='config',
                        help='''File to read configuration options from.''')
    parser.add_argument('-u', '--task-uuid',
                        dest='task_uuid',
                        metavar='UUID',
                        type=_decode_command_line,
                        help='''Select a specific task by UUID.''')
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
                        UTC timestamps) as human-readable.''')
    parser.add_argument('--local-timezone',
                        action='store_false',
                        dest='utc_timestamps',
                        help='''Convert timestamps to the local timezone.''')
    parser.add_argument('--color',
                        default='auto',
                        choices=['always', 'auto', 'never'],
                        dest='color',
                        help='''Color the output. Defaults based on whether
                        the output is a TTY.''')
    parser.add_argument('--ascii',
                        action='store_true',
                        default=False,
                        dest='ascii',
                        help='''Use ASCII for tree drawing characters.''')
    parser.add_argument('--no-color-tree',
                        action='store_false',
                        default=True,
                        dest='colorize_tree',
                        help='''Do not color the tree lines.''')
    parser.add_argument('--theme',
                        default='auto',
                        choices=['auto', 'dark', 'light'],
                        dest='theme_name',
                        help='''Select a color theme to use.'''),
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
                        AND. See <http://jmespath.org/>''')
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
    parser.add_argument('--show-default-config',
                        dest='print_default_config',
                        action='store_true',
                        help='''Show the default configuration.''')
    parser.add_argument('--show-current-config',
                        dest='print_current_config',
                        action='store_true',
                        help='''Show the current effective configuration.''')
    args = parser.parse_args()
    if args.print_default_config:
        print_namespace(parser.parse_args([]))
        return

    config = read_config(locate_config() or args.config)
    parser.set_defaults(**config)
    args = parser.parse_args()
    if args.print_current_config:
        print_namespace(args)
        return

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
            colorize_tree=args.colorize_tree,
            theme_name=args.theme_name,
            ascii=args.ascii,
            ignored_fields=args.ignored_fields,
            field_limit=args.field_limit,
            human_readable=args.human_readable,
            utc_timestamps=args.utc_timestamps,
            theme_overrides=config.get('theme_overrides'))
    except JSONParseError as e:
        stderr.write(u'JSON parse error, file {}, line {}:\n{}\n\n'.format(
            e.file_name,
            e.line_number,
            e.line))
        reraise(*e.exc_info)
    except EliotParseError as e:
        file_name, line_number = inventory.get(
            id(e.message_dict), (u'<unknown>', u'<unknown>'))
        stderr.write(
            u'Eliot message parse error, file {}, line {}:\n{}\n\n'.format(
                file_name,
                line_number,
                pformat(e.message_dict)))
        reraise(*e.exc_info)
