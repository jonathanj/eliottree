from functools import partial

from eliot._action import WrittenAction
from eliot._message import WrittenMessage
from eliot._parse import Task
from termcolor import colored
from toolz import compose, identity
from tree_format import format_tree

from eliottree import format


RIGHT_DOUBLE_ARROW = u'\u21d2'

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
            u'timestamp': format.timestamp(),
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


def message_name(colors, message, end_message=None):
    """
    Derive the name for a message.

    If the message is an action type then the ``action_type`` field is used in
    conjunction with ``task_level`` and ``action_status``. If the message is a
    message type then the ``message_type`` and ``task_level`` fields are used,
    otherwise no name will be derived.
    """
    if message is not None:
        if u'action_type' in message.contents:
            action_type = format.escape_control_characters(
                message.contents.action_type)
            if end_message:
                action_status = end_message.contents.action_status
            else:
                action_status = message.contents.action_status
            status_color = identity
            if action_status == u'succeeded':
                status_color = colors.success
            elif action_status == u'failed':
                status_color = colors.failure
            return u'{}{} {} {}'.format(
                colors.parent(action_type),
                message.task_level.to_string(),
                RIGHT_DOUBLE_ARROW,
                status_color(message.contents.action_status))
        elif u'message_type' in message.contents:
            message_type = format.escape_control_characters(
                message.contents.message_type)
            return u'{}{}'.format(
                colors.parent(message_type),
                message.task_level.to_string())
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
        return message_name(colors, node.start_message, node.end_message)
    elif isinstance(node, WrittenMessage):
        return message_name(colors, node)
    elif isinstance(node, tuple):
        key, value = node
        if isinstance(value, (dict, list)):
            value = u''
        else:
            value = format_value(value, key)
        return u'{}: {}'.format(
            colors.prop(format.escape_control_characters(key)),
            value)
    raise NotImplementedError()


def message_fields(message, ignored_fields):
    """
    Sorted fields for a `WrittenMessage`.
    """
    def _items():
        try:
            yield u'timestamp', message.timestamp
        except KeyError:
            pass
        for key, value in message.contents.items():
            if key not in ignored_fields:
                yield key, value
    return sorted(_items()) if message else []


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


def render_tasks(write, tasks, field_limit=0, ignored_fields=None,
                 human_readable=False, colorize=False):
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
    """
    if ignored_fields is None:
        ignored_fields = DEFAULT_IGNORED_KEYS
    _format_node = partial(
        format_node,
        _default_value_formatter(human_readable=human_readable,
                                 field_limit=field_limit),
        COLORS(colored if colorize else _no_color))
    _get_children = partial(get_children, ignored_fields)
    for task in tasks:
        write(format_tree(task, _format_node, _get_children))
        write(u'\n')


__all__ = ['render_tasks']
