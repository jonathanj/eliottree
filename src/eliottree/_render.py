import sys
import traceback
from functools import partial

from eliot._action import WrittenAction
from eliot._message import WrittenMessage
from eliot._parse import Task
from six import text_type
from termcolor import colored
from toolz import compose, excepts, identity
from tree_format import format_tree

from eliottree import format
from eliottree._util import eliot_ns, format_namespace, is_namespace


RIGHT_DOUBLE_ARROW = u'\N{RIGHTWARDS DOUBLE ARROW}'
HOURGLASS = u'\N{WHITE HOURGLASS}'

DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid',
    u'message_type'])


class Color(object):
    def __init__(self, color, attrs=[]):
        self.color = color
        self.attrs = attrs

    def __get__(self, instance, owner):
        return lambda text: instance.colored(
            text, self.color, attrs=self.attrs)


class COLORS(object):
    root = Color('white', ['bold'])
    parent = Color('magenta')
    success = Color('green')
    failure = Color('red')
    prop = Color('blue')
    error = Color('red', ['bold'])
    timestamp = Color('white', ['dark'])
    duration = Color('blue', ['dark'])

    def __init__(self, colored):
        self.colored = colored


def _no_color(text, *a, **kw):
    """
    Colorizer that does not colorize.
    """
    return text


def _default_value_formatter(human_readable, field_limit, encoding='utf-8'):
    """
    Create a value formatter based on several user-specified options.
    """
    fields = {}
    if human_readable:
        fields = {
            eliot_ns(u'timestamp'): format.timestamp(
                include_microsecond=False),
            eliot_ns(u'duration'): format.duration(),
        }
    return compose(
        # We want tree-format to handle newlines.
        partial(format.escape_control_characters, overrides={0x0a: u'\n'}),
        partial(format.truncate_value,
                field_limit) if field_limit else identity,
        format.some(
            format.fields(fields),
            format.text(),
            format.binary(encoding),
            format.anything(encoding)))


def message_name(colors, format_value, message, end_message=None):
    """
    Derive the name for a message.

    If the message is an action type then the ``action_type`` field is used in
    conjunction with ``task_level`` and ``action_status``. If the message is a
    message type then the ``message_type`` and ``task_level`` fields are used,
    otherwise no name will be derived.
    """
    if message is not None:
        timestamp = colors.timestamp(
            format_value(
                message.timestamp, field_name=eliot_ns('timestamp')))
        if u'action_type' in message.contents:
            action_type = format.escape_control_characters(
                message.contents.action_type)
            duration = u''
            if end_message:
                duration_seconds = end_message.timestamp - message.timestamp
                duration = u' {} {}'.format(
                    HOURGLASS,
                    colors.duration(
                        format_value(
                            duration_seconds,
                            field_name=eliot_ns('duration'))))
                action_status = end_message.contents.action_status
            else:
                action_status = message.contents.action_status
            status_color = identity
            if action_status == u'succeeded':
                status_color = colors.success
            elif action_status == u'failed':
                status_color = colors.failure
            return u'{}{} {} {} {}{}'.format(
                colors.parent(action_type),
                message.task_level.to_string(),
                RIGHT_DOUBLE_ARROW,
                status_color(message.contents.action_status),
                timestamp,
                duration)
        elif u'message_type' in message.contents:
            message_type = format.escape_control_characters(
                message.contents.message_type)
            return u'{}{} {}'.format(
                colors.parent(message_type),
                message.task_level.to_string(),
                timestamp)
    return u'<unnamed>'


def format_node(format_value, colors, node):
    """
    Format a node for display purposes.

    Different representations exist for the various types of node:
        - `eliot._parse.Task`: A task UUID.
        - `eliot._action.WrittenAction`: An action's type, level and status.
        - `eliot._message.WrittenMessage`: A message's type and level.
        - ``tuple``: A field name and value.
    """
    if isinstance(node, Task):
        return u'{}'.format(
            colors.root(
                format.escape_control_characters(node.root().task_uuid)))
    elif isinstance(node, WrittenAction):
        return message_name(
            colors,
            format_value,
            node.start_message,
            node.end_message)
    elif isinstance(node, WrittenMessage):
        return message_name(
            colors,
            format_value,
            node)
    elif isinstance(node, tuple):
        key, value = node
        if isinstance(value, (dict, list)):
            value = u''
        else:
            value = format_value(value, key)
        if is_namespace(key):
            key = format_namespace(key)
        return u'{}: {}'.format(
            colors.prop(format.escape_control_characters(key)),
            value)
    raise NotImplementedError()


def message_fields(message, ignored_fields):
    """
    Sorted fields for a `WrittenMessage`.
    """
    def _items():
        for key, value in message.contents.items():
            if key not in ignored_fields:
                yield key, value

    def _sortkey(x):
        k = x[0]
        return format_namespace(k) if is_namespace(k) else k
    return sorted(_items(), key=_sortkey) if message else []


def get_children(ignored_fields, node):
    """
    Retrieve the child nodes for a node.

    The various types of node have different concepts of children:
        - `eliot._parse.Task`: The root ``WrittenAction``.
        - `eliot._action.WrittenAction`: The start message fields, child
          ``WrittenAction`` or ``WrittenMessage``s, and end ``WrittenMessage``.
        - `eliot._message.WrittenMessage`: Message fields.
        - ``tuple``: Contained values for `dict` and `list` types.
    """
    if isinstance(node, Task):
        return [node.root()]
    elif isinstance(node, WrittenAction):
        return filter(None,
                      message_fields(node.start_message, ignored_fields) +
                      list(node.children) +
                      [node.end_message])
    elif isinstance(node, WrittenMessage):
        return message_fields(node, ignored_fields)
    elif isinstance(node, tuple):
        value = node[1]
        if isinstance(value, dict):
            return sorted(value.items())
        elif isinstance(value, list):
            return enumerate(value)
    return []


def track_exceptions(f, caught, default=None):
    """
    Decorate ``f`` with a function that traps exceptions and appends them to
    ``caught``, returning ``default`` in their place.
    """
    def _catch(_):
        caught.append(sys.exc_info())
        return default
    return excepts(Exception, f, _catch)


def render_tasks(write, tasks, field_limit=0, ignored_fields=None,
                 human_readable=False, colorize=False, write_err=None,
                 format_node=format_node, format_value=None):
    """
    Render Eliot tasks as an ASCII tree.

    :type write: ``Callable[[text_type], None]``
    :param write: Callable used to write the output.
    :type tasks: ``Iterable``
    :param tasks: Iterable of parsed Eliot tasks, as returned by
    `eliottree.tasks_from_iterable`.
    :param int field_limit: Length at which to begin truncating, ``0`` means no
    truncation.
    :type ignored_fields: ``Set[text_type]``
    :param ignored_fields: Set of field names to ignore, defaults to ignoring
    most Eliot metadata.
    :param bool human_readable: Render field values as human-readable?
    :param bool colorize: Colorized the output?
    :type write_err: Callable[[`text_type`], None]
    :param write_err: Callable used to write errors.
    :param format_node: See `format_node`.
    :type format_value: Callable[[Any], `text_type`]
    :param format_value: Callable to format a value.
    """
    if ignored_fields is None:
        ignored_fields = DEFAULT_IGNORED_KEYS
    colors = COLORS(colored if colorize else _no_color)
    caught_exceptions = []
    if format_value is None:
        format_value = _default_value_formatter(
            human_readable=human_readable,
            field_limit=field_limit)
    _format_value = track_exceptions(
        format_value,
        caught_exceptions,
        u'<value formatting exception>')
    _format_node = track_exceptions(
        partial(format_node, _format_value, colors),
        caught_exceptions,
        u'<node formatting exception>')
    _get_children = partial(get_children, ignored_fields)
    for task in tasks:
        write(format_tree(task, _format_node, _get_children))
        write(u'\n')

    if write_err and caught_exceptions:
        write_err(
            colors.error(
                u'Exceptions ({}) occurred during processing:\n'.format(
                    len(caught_exceptions))))
        for exc in caught_exceptions:
            for line in traceback.format_exception(*exc):
                if not isinstance(line, text_type):
                    line = line.decode('utf-8')
                write_err(line)
            write_err(u'\n')


__all__ = ['render_tasks']
