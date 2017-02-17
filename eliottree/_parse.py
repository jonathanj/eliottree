from eliot._parse import Parser


def tasks_from_iterable(iterable):
    """
    Parse an iterable of Eliot message dictionaries into tasks.

    :type iterable: ``Iterable[Dict]``
    :param iterable: Iterable of serialized Eliot message dictionaries.
    :rtype: ``Iterable``
    :return: Iterable of parsed Eliot tasks, suitable for use with
    `eliottree.render_tasks`.
    """
    return Parser.parse_stream(iterable)


__all__ = ['tasks_from_iterable']
