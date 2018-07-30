from datetime import datetime

from six import binary_type, text_type, unichr
from toolz import merge


_control_equivalents = dict((i, unichr(0x2400 + i)) for i in range(0x20))
_control_equivalents[0x7f] = u'\u2421'


def escape_control_characters(s, overrides={}):
    """
    Replace terminal control characters with their Unicode control character
    equivalent.
    """
    return text_type(s).translate(merge(_control_equivalents, overrides))


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


def binary(encoding):
    """
    Create a formatter for ``binary_type`` values.

    :param str encoding: Encoding to assume for values.
    """
    def _format_bytes_value(value, field_name=None):
        if isinstance(value, binary_type):
            return value.decode(encoding, 'replace')
    return _format_bytes_value


def text():
    """
    Create a formatter for ``text_type`` values.
    """
    def _format_text_value(value, field_name=None):
        if isinstance(value, text_type):
            return value
    return _format_text_value


def fields(format_mapping):
    """
    Create a formatter that performs specific formatting based on field names.

    :type format_mapping: ``Dict[text_type, Callable[[Any, text_type], Any]]``
    """
    def _format_field_value(value, field_name=None):
        f = format_mapping.get(field_name, None)
        if f is None:
            return None
        return f(value, field_name)
    return _format_field_value


def timestamp(include_microsecond=True):
    """
    Create a formatter for POSIX timestamp values.
    """
    def _format_timestamp_value(value, field_name=None):
        result = datetime.utcfromtimestamp(float(value))
        if not include_microsecond:
            result = result.replace(microsecond=0)
        result = result.isoformat(' ')
        if isinstance(result, binary_type):
            result = result.decode('ascii')
        return result
    return _format_timestamp_value


def duration():
    """
    Create a formatter for duration values specified as seconds.
    """
    def _format_duration(value, field_name=None):
        return u'{:.3f}s'.format(value)
    return _format_duration


def anything(encoding):
    """
    Create a formatter for any value using `repr`.

    :param str encoding: Encoding to assume for a `binary_type` result.
    """
    def _format_other_value(value, field_name=None):
        result = repr(value)
        if isinstance(result, binary_type):
            result = result.decode(encoding, 'replace')
        return result
    return _format_other_value


def truncate_value(limit, value):
    """
    Truncate ``value`` to a maximum of ``limit`` characters.
    """
    values = value.split(u'\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return u'{}\u2026'.format(value[:limit])
    return value


__all__ = [
    'escape_control_characters', 'some', 'binary', 'text', 'fields',
    'timestamp', 'anything', 'truncate_value']
