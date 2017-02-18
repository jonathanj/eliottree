from testtools import TestCase
from testtools.matchers import Is

from eliottree import format
from eliottree.test.matchers import ExactlyEquals


class BinaryTests(TestCase):
    """
    Tests for `eliottree.format.binary`.
    """
    def test_not_binary(self):
        """
        Not binary values are ignored.
        """
        self.assertThat(
            format.binary('utf-8')(u'hello'),
            Is(None))

    def test_encoding(self):
        """
        Binary values are decoded with the given encoding.
        """
        self.assertThat(
            format.binary('utf-8')(u'\N{SNOWMAN}'.encode('utf-8')),
            ExactlyEquals(u'\u2603'))

    def test_replace(self):
        """
        Replace decoding errors with the Unicode replacement character.
        """
        self.assertThat(
            format.binary('utf-32')(u'\N{SNOWMAN}'.encode('utf-8')),
            ExactlyEquals(u'\ufffd'))


class TextTests(TestCase):
    """
    Tests for `eliottree.format.text`.
    """
    def test_not_text(self):
        """
        Not text values are ignored.
        """
        self.assertThat(
            format.text()(b'hello'),
            Is(None))

    def test_text(self):
        """
        Text values are returned as is.
        """
        self.assertThat(
            format.text()(u'\N{SNOWMAN}'),
            ExactlyEquals(u'\N{SNOWMAN}'))


class FieldsTests(TestCase):
    """
    Tests for `eliottree.format.fields`.
    """
    def test_missing_mapping(self):
        """
        Values for unknown field names are ignored.
        """
        self.assertThat(
            format.fields({})(b'hello', u'a'),
            Is(None))

    def test_mapping(self):
        """
        Values for known field names are passed through their processor.
        """
        fields = {
            u'a': format.binary('utf-8'),
        }
        self.assertThat(
            format.fields(fields)(u'\N{SNOWMAN}'.encode('utf-8'), u'a'),
            ExactlyEquals(u'\N{SNOWMAN}'))


class TimestampTests(TestCase):
    """
    Tests for `eliottree.format.timestamp`.
    """
    def test_text(self):
        """
        Timestamps as text are converted to ISO 8601.
        """
        self.assertThat(
            format.timestamp()(u'1433631432'),
            ExactlyEquals(u'2015-06-06 22:57:12'))

    def test_float(self):
        """
        Timestamps as floats are converted to ISO 8601.
        """
        self.assertThat(
            format.timestamp()(1433631432.0),
            ExactlyEquals(u'2015-06-06 22:57:12'))


class AnythingTests(TestCase):
    """
    Tests for `eliottree.format.anything`.
    """
    def test_anything(self):
        """
        Convert values to Unicode via `repr`.
        """
        class _Foo(object):
            def __repr__(self):
                return 'hello'
        self.assertThat(
            format.anything('utf-8')(_Foo()),
            ExactlyEquals(u'hello'))
        self.assertThat(
            format.anything('utf-8')(42),
            ExactlyEquals(u'42'))


class TruncateTests(TestCase):
    """
    Tests for `eliottree.format.truncate_value`.
    """
    def test_under(self):
        """
        No truncation occurs if the length of the value is below the limit.
        """
        self.assertThat(
            format.truncate_value(10, u'abcdefghijklmnopqrstuvwxyz'[:5]),
            ExactlyEquals(u'abcde'))

    def test_exact(self):
        """
        No truncation occurs if the length of the value is exactly at the
        limit.
        """
        self.assertThat(
            format.truncate_value(10, u'abcdefghijklmnopqrstuvwxyz'[:10]),
            ExactlyEquals(u'abcdefghij'))

    def test_over(self):
        """
        Truncate values whose length is above the limit.
        """
        self.assertThat(
            format.truncate_value(10, u'abcdefghijklmnopqrstuvwxyz'),
            ExactlyEquals(u'abcdefghij\u2026'))

    def test_multiple_lines(self):
        """
        Truncate values that have more than a single line of text by only
        showing the first line.
        """
        self.assertThat(
            format.truncate_value(10, u'abc\ndef'),
            ExactlyEquals(u'abc\u2026'))
