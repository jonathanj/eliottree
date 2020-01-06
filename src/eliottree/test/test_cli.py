"""
Tests for the command-line itself.
"""
import os
import six
import tempfile
from collections import namedtuple
from subprocess import PIPE, CalledProcessError, Popen
from unittest import TestCase

from eliottree._compat import dump_json_bytes
from eliottree.test.tasks import message_task, missing_uuid_task


rendered_message_task = (
    u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
    u'\u2514\u2500\u2500 twisted:log/1 2015-03-03 04:25:00Z\n'
    u'    \u251c\u2500\u2500 error: False\n'
    u'    \u2514\u2500\u2500 message: Main loop terminated.\n\n'
).replace('\n', os.linesep).encode('utf-8')


def bytes_hex(a):
    """
    Encode `bytes` into hex on Python 2 or 3.
    """
    if hasattr(a, 'hex'):
        return a.hex()
    return a.encode('hex')


class NamedTemporaryFile(object):
    """
    Similar to `tempfile.NamedTemporaryFile` except less buggy and with a
    Python context manager interface.
    """
    def __init__(self):
        # See https://stackoverflow.com/a/58955530/81065
        self.name = os.path.join(tempfile.gettempdir(), bytes_hex(os.urandom(24)))
        self._fd = open(self.name, 'wb+')
        self.write = self._fd.write
        self.flush = self._fd.flush
        self.seek = self._fd.seek

    def close(self):
        self._fd.close()
        if os.path.exists(self.name):
            os.unlink(self.name)

    def __enter__(self):
        return self._fd

    def __exit__(self, type, value, traceback):
        self.flush()
        self.close()


def check_output(args, stdin=None):
    """
    Similar to `subprocess.check_output` but include separated stdout and
    stderr in the `CalledProcessError` exception.
    """
    kwargs = {}
    pipes = Popen(
        args,
        stdin=PIPE if stdin is not None else None,
        stdout=PIPE,
        stderr=PIPE,
        **kwargs)
    stdout, stderr = pipes.communicate(
        six.ensure_binary(stdin) if stdin is not None else None)
    if pipes.returncode != 0:
        output = namedtuple('Output', ['stdout', 'stderr'])(
            six.ensure_binary(stdout),
            six.ensure_binary(stderr))
        raise CalledProcessError(pipes.returncode, args, output)
    return six.ensure_binary(stdout)


class EndToEndTests(TestCase):
    """
    Tests that actually run the command-line tool.
    """
    def test_stdin(self):
        """
        ``eliot-tree`` can read and render JSON messages from stdin when no
        arguments are given.
        """
        with NamedTemporaryFile() as f:
            f.write(dump_json_bytes(message_task))
            f.flush()
            f.seek(0, 0)
            self.assertEqual(check_output(["eliot-tree"], stdin=f.read()),
                             rendered_message_task)

    def test_file(self):
        """
        ``eliot-tree`` can read and render JSON messages from a file on the
        command line.
        """
        with NamedTemporaryFile() as f:
            f.write(dump_json_bytes(message_task))
            f.flush()
            self.assertEqual(check_output(["eliot-tree", f.name]),
                             rendered_message_task)

    def test_json_parse_error(self):
        """
        ``eliot-tree`` displays an error containing the file name, line number
        and offending line in the event that JSON parsing fails.
        """
        with NamedTemporaryFile() as f:
            f.write(dump_json_bytes(message_task) + b'\n')
            f.write(b'totally not valid JSON {')
            f.flush()
            with self.assertRaises(CalledProcessError) as m:
                check_output(['eliot-tree', '--color=never', f.name])
            lines = m.exception.output.stderr.splitlines()
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
        with NamedTemporaryFile() as f:
            f.write(dump_json_bytes(missing_uuid_task) + b'\n')
            f.flush()
            with self.assertRaises(CalledProcessError) as m:
                check_output(['eliot-tree', f.name])
            lines = m.exception.output.stderr.splitlines()
            first_line = lines[0].decode('utf-8')
            self.assertIn('Eliot message parse error', first_line)
            self.assertIn(f.name, first_line)
            self.assertIn('line 1', first_line)
