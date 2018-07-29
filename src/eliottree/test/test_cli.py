"""
Tests for the command-line itself.
"""
from pprint import pformat
from subprocess import STDOUT, CalledProcessError, check_output
from tempfile import NamedTemporaryFile
from unittest import TestCase

from eliottree._compat import dump_json_bytes
from eliottree.test.tasks import message_task, missing_uuid_task


rendered_message_task = (
    u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
    u'\u2514\u2500\u2500 twisted:log/1 2015-03-03 04:25:00\n'
    u'    \u251c\u2500\u2500 error: False\n'
    u'    \u2514\u2500\u2500 message: Main loop terminated.\n\n'
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

    def test_json_parse_error(self):
        """
        ``eliot-tree`` displays an error containing the file name, line number
        and offending line in the event that JSON parsing fails.
        """
        f = NamedTemporaryFile()
        f.write(dump_json_bytes(message_task) + b'\n')
        f.write(b'totally not valid JSON {')
        f.flush()
        with self.assertRaises(CalledProcessError) as m:
            check_output(['eliot-tree', f.name], stderr=STDOUT)
        lines = m.exception.output.splitlines()
        first_line = lines[0].decode('utf-8')
        second_line = lines[1].decode('utf-8')
        self.assertIn('JSON parse error', first_line)
        self.assertIn(f.name, first_line)
        self.assertIn('line 2', first_line)
        self.assertEqual('totally not valid JSON {', second_line)

    def test_eliot_parse_error(self):
        """
        ``eliot-tree`` displays an error containing the original file name,
        line number and offending task in the event that parsing the message
        dict fails.
        """
        f = NamedTemporaryFile()
        f.write(dump_json_bytes(missing_uuid_task) + b'\n')
        f.flush()
        with self.assertRaises(CalledProcessError) as m:
            check_output(['eliot-tree', f.name], stderr=STDOUT)
        lines = m.exception.output.splitlines()
        first_line = lines[0].decode('utf-8')
        self.assertIn('Eliot message parse error', first_line)
        self.assertIn(f.name, first_line)
        self.assertIn('line 1', first_line)
        formatted = pformat(missing_uuid_task).encode('utf-8').splitlines()
        self.assertEqual(
            lines[1:len(formatted) + 1],
            formatted)
