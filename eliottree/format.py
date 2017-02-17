from datetime import datetime

from six import binary_type, text_type


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


def timestamp():
    """
    Create a formatter for POSIX timestamp values.
    """
    def _format_timestamp_value(value, field_name=None):
        result = datetime.utcfromtimestamp(float(value)).isoformat(' ')
        if isinstance(result, binary_type):
            result = result.decode('ascii')
        return result
    return _format_timestamp_value


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
