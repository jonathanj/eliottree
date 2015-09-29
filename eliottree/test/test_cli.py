"""
Tests for the command-line itself.
"""

from unittest import TestCase
from subprocess import check_output
from tempfile import NamedTemporaryFile
from json import dumps

from .tasks import message_task


rendered_message_task = (
    'cdeb220d-7605-4d5f-8341-1a170222e308\n'
    '+-- twisted:log@1\n'
    '    |-- error: False\n'
    '    |-- message: Main loop terminated.\n'
    '    `-- timestamp: 2015-03-03 04:25:00\n\n'
)


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
        f.write(dumps(message_task))
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
        f.write(dumps(message_task))
        f.flush()
        self.assertEqual(check_output(["eliot-tree", f.name]),
                         rendered_message_task)
