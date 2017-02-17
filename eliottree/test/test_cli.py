"""
Tests for the command-line itself.
"""
from subprocess import check_output
from tempfile import NamedTemporaryFile
from unittest import TestCase

from eliottree._compat import dump_json_bytes
from eliottree.test.tasks import message_task


rendered_message_task = (
    u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
    u'\u2514\u2500\u2500 twisted:log/1\n'
    u'    \u251c\u2500\u2500 error: False\n'
    u'    \u251c\u2500\u2500 message: Main loop terminated.\n'
    u'    \u2514\u2500\u2500 timestamp: 2015-03-03 04:25:00\n\n'
).encode('utf-8')


class EndToEndTests(TestCase):
    """
    Tests that actually run the command-line tool.
    """
    def test_stdin(self):
        """
        ``eliot-tree`` can read and render JSON messages from stdin when no
        arguments are given.
        """
        f = NamedTemporaryFile()
        f.write(dump_json_bytes(message_task))
        f.flush()
        f.seek(0, 0)
        self.assertEqual(check_output(["eliot-tree"], stdin=f),
                         rendered_message_task)

    def test_file(self):
        """
        ``eliot-tree`` can read and render JSON messages from a file on the
        command line.
        """
        f = NamedTemporaryFile()
        f.write(dump_json_bytes(message_task))
        f.flush()
        self.assertEqual(check_output(["eliot-tree", f.name]),
                         rendered_message_task)
