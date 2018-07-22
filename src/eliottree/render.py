from functools import wraps
from warnings import warn

from six import text_type
from termcolor import colored
from tree_format import format_tree

from eliottree._render import (
    COLORS, DEFAULT_IGNORED_KEYS, _default_value_formatter, _no_color)
from eliottree._util import is_namespace, eliot_ns
from eliottree.format import escape_control_characters


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


def get_name_factory(colors):
    """
    Create a ``get_name`` function for use with `format_tree`.
    """
    def get_name(task):
        if isinstance(task, text_type):
            return escape_control_characters(task)
        elif isinstance(task, tuple):
            key = task[0]
            if is_namespace(key):
                key = key.name
            name = escape_control_characters(key)
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
            name = escape_control_characters(task.name)
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
                if key == u'timestamp':
                    key = eliot_ns(key)
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
                if child[0] == u'timestamp':
                    yield eliot_ns(child[0]), child[1]
                else:
                    yield child
            for child in task.children():
                yield child
    return get_children


__all__ = ['render_task_nodes']
