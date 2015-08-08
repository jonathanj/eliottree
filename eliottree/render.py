from datetime import datetime


DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid',
    u'message_type'])


def _format_value(value, encoding):
    """
    Format a value for a task tree.
    """
    if isinstance(value, datetime):
        return value.isoformat(' ').encode(encoding)
    elif isinstance(value, unicode):
        return value.encode(encoding)
    elif isinstance(value, str):
        # We guess bytes values are UTF-8.
        return value.decode('utf-8', 'replace').encode(encoding)
    return repr(value).decode('utf-8', 'replace').encode(encoding)


def _indented_write(write):
    """
    Wrap ``write`` to instead write indented bytes.
    """
    def _write(data):
        write('    ' + data)
    return _write


def _truncate_value(value, limit):
    """
    Truncate values longer than ``limit``.
    """
    values = value.split('\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return '{} [...]'.format(value[:limit])
    return value


def _render_task(write, task, ignored_task_keys, field_limit, encoding):
    """
    Render a single ``_TaskNode`` as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``bytes`` argument
    :param write: Callable to write the output.

    :type task: ``dict`` of ``unicode``:``Any``
    :param task: Task ``dict`` to render.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``unicode``
    :param ignored_task_keys: Set of task key names to ignore.

    :type encoding: ``bytes``
    :param encoding: Encoding to use when rendering.
    """
    _write = _indented_write(write)
    num_items = len(task)
    for i, (key, value) in enumerate(sorted(task.items()), 1):
        if key not in ignored_task_keys:
            tree_char = '`' if i == num_items else '|'
            key = key.encode(encoding)
            if isinstance(value, dict):
                write(
                    '{tree_char}-- {key}:\n'.format(
                        tree_char=tree_char,
                        key=key))
                _render_task(write=_write,
                             task=value,
                             ignored_task_keys={},
                             field_limit=field_limit,
                             encoding=encoding)
            else:
                _value = _format_value(value, encoding)
                if field_limit:
                    first_line = _truncate_value(_value, field_limit)
                else:
                    lines = _value.splitlines() or [u'']
                    first_line = lines.pop(0)
                write(
                    '{tree_char}-- {key}: {value}\n'.format(
                        tree_char=tree_char,
                        key=key,
                        value=first_line))
                if not field_limit:
                    for line in lines:
                        _write(line + '\n')


def _render_task_node(write, node, field_limit, ignored_task_keys, encoding):
    """
    Render a single ``_TaskNode`` as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``bytes`` argument
    :param write: Callable to write the output.

    :type node: ``_TaskNode)``
    :param node: ``_TaskNode`` to render.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``unicode``
    :param ignored_task_keys: Set of task key names to ignore.

    :type encoding: ``bytes``
    :param encoding: Encoding to use when rendering.
    """
    _child_write = _indented_write(write)
    write(
        '+-- {name}\n'.format(
            name=node.name.encode(encoding)))
    _render_task(
        write=_child_write,
        task=node.task,
        field_limit=field_limit,
        ignored_task_keys=ignored_task_keys,
        encoding=encoding)

    for child in node.children():
        _render_task_node(
            write=_child_write,
            node=child,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys,
            encoding=encoding)


def render_task_nodes(write, nodes, field_limit, ignored_task_keys=None,
                      encoding='utf-8'):
    """
    Render a tree of task nodes as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``bytes`` argument
    :param write: Callable to write the output.

    :type nodes: ``list`` of ``(unicode, _TaskNode)``.
    :param nodes: List of pairs of task UUID and task nodes, as obtained
        from ``Tree.nodes``.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``unicode``
    :param ignored_task_keys: Set of task key names to ignore.

    :type encoding: ``bytes``
    :param encoding: Encoding to use when rendering.
    """
    if ignored_task_keys is None:
        ignored_task_keys = DEFAULT_IGNORED_KEYS
    for task_uuid, node in nodes:
        write('{name}\n'.format(
            name=node.task['task_uuid'].encode(encoding)))
        _render_task_node(
            write=write,
            node=node,
            field_limit=field_limit,
            ignored_task_keys=ignored_task_keys,
            encoding=encoding)
        write('\n')


__all__ = ['render_task_nodes']
