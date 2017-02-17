from functools import partial, wraps
from warnings import warn

from eliot._action import WrittenAction
from eliot._message import WrittenMessage
from eliot._parse import Task
from six import text_type, unichr
from termcolor import colored
from toolz import compose, identity, merge
from tree_format import format_tree

from eliottree import format


DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid',
    u'message_type'])


_control_equivalents = dict((i, unichr(0x2400 + i)) for i in range(0x20))
_control_equivalents[0x7f] = u'\u2421'


def _escape_control_characters(s, overrides={}):
    """
    Escape terminal control characters.
    """
    return text_type(s).translate(merge(_control_equivalents, overrides))


def _no_color(text, *a, **kw):
    """
    Colorizer that does not colorize.
    """
    return text


def some(*fs):
    """
    Create a function that returns the first non-``None`` result of applying
    the arguments to each ``fs``.
    """
    def _some(*a, **kw):
        for f in fs:
            result = f(*a, **kw)
            if result is not None:
                return result
        return None
    return _some


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
        partial(_escape_control_characters, overrides={0x0a: u'\n'}),
        partial(format.truncate_value,
                field_limit) if field_limit else identity,
        some(
            format.fields(fields),
            format.text(),
            format.binary(encoding),
            format.anything(encoding)))


def render_task_nodes_unicode(write, nodes, field_limit,
                              ignored_task_keys=None, human_readable=False,
                              colorize=False):
    """
    Render a tree of task nodes as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``text_type`` argument
    :param write: Callable to write the output.

    :type nodes: ``list`` of ``(text_type, _TaskNode)``.
    :param nodes: List of pairs of task UUID and task nodes, as obtained
        from ``Tree.nodes``.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``text_type``
    :param ignored_task_keys: Set of task key names to ignore.

    :type human_readable: ``bool``
    :param human_readable: Should this be rendered as human-readable?

    :type colorize: ``bool``
    :param colorize: Should the output be colorized?
    """
    if ignored_task_keys is None:
        ignored_task_keys = DEFAULT_IGNORED_KEYS
    colors = COLORS(colored if colorize else _no_color)
    format_value = _default_value_formatter(
        human_readable=human_readable,
        field_limit=field_limit)
    get_children = get_children_factory(
        ignored_task_keys,
        format_value)
    get_name = get_name_factory(colors)
    for root in nodes:
        write(format_tree(root, get_name, get_children))
        write(u'\n')


def render_task_nodes(write, nodes, field_limit,
                      ignored_task_keys=None, human_readable=False,
                      encoding='utf-8', colorize=False):
    """
    :type write: ``callable`` taking a single ``bytes_type`` argument
    :param write: Callable to write the output.

    :param str encoding: Encoding for data to be written to ``write``.

    :seealso: `render_task_nodes`
    """
    warn('render_task_nodes is deprecated, use eliottree.render_tasks instead',
         DeprecationWarning, 2)
    render_task_nodes_unicode(
        write=lambda value: write(value.encode(encoding)),
        nodes=nodes,
        field_limit=field_limit,
        ignored_task_keys=ignored_task_keys,
        human_readable=human_readable,
        colorize=colorize)


class Color(object):
    def __init__(self, color, attrs=[]):
        self.color = color
        self.attrs = attrs

    def __get__(self, instance, owner):
        return lambda text: instance.colored(
            text, self.color, attrs=self.attrs)


class COLORS(object):
    root = Color('white', ['bold'])
    parent = Color('magenta', [])
    success = Color('green')
    failure = Color('red')
    prop = Color('blue')

    def __init__(self, colored):
        self.colored = colored


def get_name_factory(colors):
    """
    Create a ``get_name`` function for use with `format_tree`.
    """
    def get_name(task):
        if isinstance(task, text_type):
            return _escape_control_characters(task)
        elif isinstance(task, tuple):
            name = _escape_control_characters(task[0])
            if isinstance(task[1], dict):
                return name
            elif isinstance(task[1], text_type):
                return u'{}: {}'.format(
                    colors.prop(name),
                    # No need to escape this because we assume the value
                    # formatter did that already.
                    task[1])
            else:
                return colors.root(name)
        else:
            name = _escape_control_characters(task.name)
            if task.success is True:
                return colors.success(name)
            elif task.success is False:
                return colors.failure(name)
            return name
    return get_name


def listify(f):
    """
    Convert the decorated function's result to a ``list``.
    """
    @wraps(f)
    def _wrapper(*a, **kw):
        return list(f(*a, **kw))
    return _wrapper


def get_children_factory(ignored_task_keys, format_value):
    """
    Create a ``get_children`` function for use with `format_tree`.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``text_type``
    :param ignored_task_keys: Set of task key names to ignore.

    :type format_value: ``Callable[[Any, text_type], Any]``
    :param format_value: Function to format a value for display purposes.
    """
    def items_children(items):
        for key, value in sorted(items):
            if key not in ignored_task_keys:
                if isinstance(value, dict):
                    yield key, value
                else:
                    yield key, format_value(value, key)

    @listify
    def get_children(task):
        if isinstance(task, text_type):
            return
        elif isinstance(task, tuple):
            if isinstance(task[1], dict):
                for child in items_children(task[1].items()):
                    yield child
            elif isinstance(task[1], text_type):
                # The value of Unicode values is incorporated into the name.
                return
            else:
                yield task[1]
            return
        else:
            for child in items_children(task.task.items()):
                yield child
            for child in task.children():
                yield child
    return get_children


RIGHT_DOUBLE_ARROW = u'\u21d2'


def message_name(colors, message):
    """
    Derive the name for a message.

    If the message is an action type then the ``action_type`` field is used in
    conjunction with ``task_level`` and ``action_status``. If the message is a
    message type then the ``message_type`` and ``task_level`` fields are used,
    otherwise no name will be derived.
    """
    if message is not None:
        if u'action_type' in message.contents:
            action_type = _escape_control_characters(
                message.contents.action_type)
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
            message_type = _escape_control_characters(
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
            colors.root(_escape_control_characters(node.root().task_uuid)))
    elif isinstance(node, WrittenAction):
        return message_name(colors, node.start_message)
    elif isinstance(node, WrittenMessage):
        return message_name(colors, node)
    elif isinstance(node, tuple):
        key, value = node
        if isinstance(value, (dict, list)):
            value = u''
        else:
            value = format_value(value, key)
        return u'{}: {}'.format(
            colors.prop(_escape_control_characters(key)),
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
        if isinstance(node[1], dict):
            return sorted(node[1].items())
        elif isinstance(node[1], list):
            return enumerate(node[1])
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


__all__ = ['render_task_nodes', 'render_tasks']
