import platform

from eliottree._errors import EliotParseError, JSONParseError
from eliottree._parse import tasks_from_iterable
from eliottree._render import render_tasks
from eliottree.filter import (
    filter_by_end_date, filter_by_jmespath, filter_by_start_date,
    filter_by_uuid)
from eliottree.render import render_task_nodes
from eliottree.tree import Tree

if platform.system() == 'Windows':
    # Initialise Unicode support for Windows terminals, even if they're not
    # using the Unicode codepage.
    # N.B. This _must_ happen before `colorama` because win_unicode_console
    # replaces stdin/stdout while colorama wraps them.
    import win_unicode_console  # noqa: E402
    win_unicode_console.enable()
    # Initialise color support for Windows terminals.
    import colorama  # noqa: E402
    colorama.init()

__version__ = '17.1.0'


__all__ = [
    'Tree', 'render_task_nodes', 'render_task_nodes_unicode',
    'filter_by_jmespath', 'filter_by_uuid', 'filter_by_start_date',
    'filter_by_end_date', 'render_tasks', 'tasks_from_iterable',
    'EliotParseError', 'JSONParseError',
]

from ._version import get_versions  # noqa: E402
__version__ = get_versions()['version']
del get_versions
