import json

from six import text_type


def dump_json_bytes(obj, dumps=json.dumps):
    """
    Serialize ``obj`` to JSON formatted UTF-8 encoded ``bytes``.
    """
    result = dumps(obj)
    if isinstance(result, text_type):
        return result.encode('utf-8')
    return result
