from datetime import datetime

from six import PY3, binary_type, text_type, unichr


DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid',
    u'message_type'])


def _format_value_raw(value):
    """
    Format a value.
    """
    if isinstance(value, datetime):
        if PY3:
            return value.isoformat(' ')
        else:
            return value.isoformat(' ').decode('ascii')
    return None


def _format_value_hint(value, hint):
    """
    Format a value given a rendering hint.
    """
    if hint == u'timestamp':
        return _format_value_raw(datetime.utcfromtimestamp(value))
    return None


controlEquivalents = dict((i, unichr(0x2400 + i)) for i in range(0x20))
controlEquivalents[0x0a] = u'\n'
controlEquivalents[0x7f] = u'\u2421'


def _escape_control_characters(s):
    """
    Escape terminal control characters.
    """
    return text_type(s).translate(controlEquivalents)


def _format_value(value, field_hint=None, human_readable=False):
    """
    Format a value for a task tree.
    """
    if isinstance(value, binary_type):
        # We guess bytes values are UTF-8.
        value = value.decode('utf-8', 'replace')

    if isinstance(value, text_type):
        return _escape_control_characters(value)

    if human_readable:
        formatted = _format_value_raw(value)
        if formatted is None:
            formatted = _format_value_hint(value, field_hint)
        if formatted is not None:
            return formatted
    result = repr(value)
    if isinstance(result, binary_type):
        result = result.decode('utf-8', 'replace')
    return result


def _indented_write(write):
    """
    Wrap ``write`` to instead write indented text.
    """
    def _write(data):
        write(u'    ' + data)
    return _write


def _truncate_value(value, limit):
    """
    Truncate values longer than ``limit``.
    """
    values = value.split(u'\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return u'{} [...]'.format(value[:limit])
    return value


def _render_task(write, task, ignored_task_keys, field_limit, human_readable):
    """
    Render a single ``_TaskNode`` as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``text_type`` argument
    :param write: Callable to write the output.

    :type task: ``dict`` of ``text_type``:``Any``
    :param task: Task ``dict`` to render.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``text_type``
    :param ignored_task_keys: Set of task key names to ignore.

    :type human_readable: ``bool``
    :param human_readable: Should this be rendered as human-readable?
    """
    _write = _indented_write(write)
    num_items = len(task)
    for i, (key, value) in enumerate(sorted(task.items()), 1):
        if key not in ignored_task_keys:
            tree_char = u'`' if i == num_items else u'|'
            if isinstance(value, dict):
                write(
                    u'{tree_char}-- {key}:\n'.format(
                        tree_char=tree_char,
                        key=_escape_control_characters(key)))
                _render_task(write=_write,
                             task=value,
                             ignored_task_keys={},
                             field_limit=field_limit,
                             human_readable=human_readable)
            else:
                _value = _format_value(value,
                                       field_hint=key,
                                       human_readable=human_readable)
                if field_limit:
                    first_line = _truncate_value(_value, field_limit)
                else:
                    lines = _value.splitlines() or [u'']
                    first_line = lines.pop(0)
                assert isinstance(first_line, text_type)
                write(
                    u'{tree_char}-- {key}: {value}\n'.format(
                        tree_char=tree_char,
                        key=_escape_control_characters(key),
                        value=first_line))
                if not field_limit:
                    for line in lines:
                        _write(line + u'\n')


def _render_task_node(write, node, field_limit, ignored_task_keys,
                      human_readable):
    """
    Render a single ``_TaskNode`` as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``text_type`` argument
    :param write: Callable to write the output.

    :type node: ``_TaskNode)``
    :param node: ``_TaskNode`` to render.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``text_type``
    :param ignored_task_keys: Set of task key names to ignore.

    :type human_readable: ``bool``
    :param human_readable: Should this be rendered as human-readable?
    """
    _child_write = _indented_write(write)
    write(u'+-- {name}\n'.format(name=_escape_control_characters(node.name)))
    _render_task(
        write=_child_write,
        task=node.task,
        field_limit=field_limit,
        ignored_task_keys=ignored_task_keys,
        human_readable=human_readable)

    for child in node.children():
        _render_task_node(
            write=_child_write,
            node=child,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys,
            human_readable=human_readable)


def render_task_nodes(write, nodes, field_limit, ignored_task_keys=None,
                      human_readable=False):
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
    """
    if ignored_task_keys is None:
        ignored_task_keys = DEFAULT_IGNORED_KEYS
    for task_uuid, node in nodes:
        write(u'{name}\n'.format(
            name=_escape_control_characters(node.task['task_uuid'])))
        _render_task_node(
            write=write,
            node=node,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys,
            human_readable=human_readable)
        write(u'\n')


__all__ = ['render_task_nodes']
