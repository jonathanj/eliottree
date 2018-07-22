import sys

from eliot._parse import Parser

from eliottree._errors import EliotParseError


def tasks_from_iterable(iterable):
    """
    Parse an iterable of Eliot message dictionaries into tasks.

    :type iterable: ``Iterable[Dict]``
    :param iterable: Iterable of serialized Eliot message dictionaries.
    :rtype: ``Iterable``
    :return: Iterable of parsed Eliot tasks, suitable for use with
    `eliottree.render_tasks`.
    """
    parser = Parser()
    for message_dict in iterable:
        try:
            completed, parser = parser.add(message_dict)
            for task in completed:
                yield task
        except Exception:
            raise EliotParseError(message_dict, sys.exc_info())
    for task in parser.incomplete_tasks():
        yield task


__all__ = ['tasks_from_iterable']
