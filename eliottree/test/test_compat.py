import json
from six import binary_type, text_type
from testtools import TestCase
from testtools.matchers import Equals, IsInstance

from eliottree._compat import dump_json_bytes


class DumpJsonBytesTests(TestCase):
    """
    Tests for ``eliottree._compat.dump_json_bytes``.
    """
    def test_text(self):
        """
        Text results are encoded as UTF-8.
        """
        def dump_text(obj):
            result = json.dumps(obj)
            if isinstance(result, binary_type):
                return result.decode('utf-8')
            return result

        result = dump_json_bytes(
            {'a': 42}, dumps=dump_text)
        self.assertThat(
            result,
            IsInstance(binary_type))
        self.assertThat(
            result,
            Equals(b'{"a": 42}'))

    def test_binary(self):
        """
        Binary results are left as-is.
        """
        def dump_binary(obj):
            result = json.dumps(obj)
            if isinstance(result, text_type):
                return result.encode('utf-8')
            return result

        result = dump_json_bytes(
            {'a': 42}, dumps=dump_binary)
        self.assertThat(
            result,
            IsInstance(binary_type))
        self.assertThat(
            result,
            Equals(b'{"a": 42}'))
