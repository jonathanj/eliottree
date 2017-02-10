from datetime import datetime

from six import PY3, BytesIO
from testtools import TestCase
from testtools.matchers import Equals, IsInstance, MatchesAll

from eliottree import Tree, render_task_nodes
from eliottree.render import _format_value
from eliottree.test.tasks import (
    action_task, action_task_end, dict_action_task, janky_action_task,
    janky_message_task, message_task, multiline_action_task,
    nested_action_task)


def ExactlyEquals(value):
    """
    Like `Equals` but also requires that the types match.
    """
    return MatchesAll(
        IsInstance(type(value)),
        Equals(value),
        first_only=True)


class FormatValueTests(TestCase):
    """
    Tests for ``eliottree.render._format_value``.
    """
    def test_datetime_human_readable(self):
        """
        Format ``datetime`` values as ISO8601.
        """
        now = datetime(2015, 6, 6, 22, 57, 12)
        self.assertThat(
            _format_value(now, human_readable=True),
            ExactlyEquals(u'2015-06-06 22:57:12'))

    def test_unicode(self):
        """
        Encode ``unicode`` values as the specified encoding.
        """
        self.assertThat(
            _format_value(u'\N{SNOWMAN}'),
            ExactlyEquals(u'\N{SNOWMAN}'))

    def test_unicode_control_characters(self):
        """
        Translate control characters to their Unicode "control picture"
        equivalent, instead of destroying a terminal.
        """
        self.assertThat(
            _format_value(u'hello\001world'),
            ExactlyEquals(u'hello\u2401world'))

    def test_bytes(self):
        """
        Assume that ``bytes`` values are UTF-8.
        """
        self.assertThat(
            _format_value(b'foo'),
            ExactlyEquals(u'foo'))
        self.assertThat(
            _format_value(b'\xe2\x98\x83'),
            ExactlyEquals(u'\N{SNOWMAN}'))

    def test_other(self):
        """
        Pass unknown values to ``repr`` while replacing encoding errors.
        """
        self.assertThat(
            _format_value(42),
            ExactlyEquals(u'42'))
        if PY3:
            self.assertThat(
                _format_value({'a': u'\N{SNOWMAN}'}),
                ExactlyEquals(u"{'a': '\N{SNOWMAN}'}"))
        else:
            self.assertThat(
                _format_value({'a': u'\N{SNOWMAN}'}),
                ExactlyEquals(u"{'a': u'\\u2603'}"))

    def test_timestamp_hint(self):
        """
        Format "timestamp" hinted data as timestamps.
        """
        # datetime(2015, 6, 6, 22, 57, 12)
        now = 1433631432
        self.assertThat(
            _format_value(now, field_hint='timestamp', human_readable=True),
            ExactlyEquals(u'2015-06-06 22:57:12'))


class RenderTaskNodesTests(TestCase):
    """
    Tests for ``eliottree.render.render_task_nodes``.
    """
    def test_tasks(self):
        """
        Render two tasks of sequential levels, by default most standard Eliot
        task keys are ignored.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([action_task, action_task_end])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    `-- timestamp: 1425356800\n'
                b'    +-- app:action@2/succeeded\n'
                b'        `-- timestamp: 1425356800\n\n'))

    def test_tasks_human_readable(self):
        """
        Render two tasks of sequential levels, by default most standard Eliot
        task keys are ignored, values are formatted to be human readable.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([action_task, action_task_end])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0,
            human_readable=True)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    `-- timestamp: 2015-03-03 04:26:40\n'
                b'    +-- app:action@2/succeeded\n'
                b'        `-- timestamp: 2015-03-03 04:26:40\n\n'))

    def test_multiline_field(self):
        """
        When no field limit is specified for task values, multiple lines are
        output for multiline tasks.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([multiline_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    |-- message: this is a\n'
                b'        many line message\n'
                b'    `-- timestamp: 1425356800\n\n'))

    def test_multiline_field_limit(self):
        """
        When a field limit is specified for task values, only the first of
        multiple lines is output.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([multiline_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=1000)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    |-- message: this is a [...]\n'
                b'    `-- timestamp: 1425356800\n\n'))

    def test_field_limit(self):
        """
        Truncate task values that are longer than the field_limit if specified.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=5)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                b'+-- twisted:log@1\n'
                b'    |-- error: False\n'
                b'    |-- message: Main  [...]\n'
                b'    `-- timestamp: 14253 [...]\n\n'))

    def test_ignored_keys(self):
        """
        Task keys can be ignored.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0,
            ignored_task_keys=set(['task_level']))
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    |-- action_status: started\n'
                b'    |-- action_type: app:action\n'
                b'    |-- task_uuid: f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'    `-- timestamp: 1425356800\n\n'))

    def test_task_data(self):
        """
        Task data is rendered as tree elements.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                b'+-- twisted:log@1\n'
                b'    |-- error: False\n'
                b'    |-- message: Main loop terminated.\n'
                b'    `-- timestamp: 1425356700\n\n'))

    def test_dict_data(self):
        """
        Task values that are ``dict``s are rendered as tree elements.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([dict_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    |-- some_data:\n'
                b'        `-- a: 42\n'
                b'    `-- timestamp: 1425356800\n\n'))

    def test_nested(self):
        """
        Render nested tasks in a way that visually represents that nesting.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([action_task, nested_action_task])
        render_task_nodes(fd.write, tree.nodes(), 0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                b'+-- app:action@1/started\n'
                b'    `-- timestamp: 1425356800\n'
                b'    +-- app:action:nested@1,1/started\n'
                b'        `-- timestamp: 1425356900\n\n'))

    def test_janky_message(self):
        """
        Task names, UUIDs, keys and values in messages all have control
        characters escaped.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([janky_message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'cdeb220d-7605-4d5f-\xe2\x90\x9b(08341-1a170222e308\n'
                b'+-- M\xe2\x90\x9b(0@1\n'
                b'    |-- error: False\n'
                b'    |-- message: Main loop\xe2\x90\x9b(0terminated.\n'
                b'    `-- timestamp: 1425356700\n\n'))

    def test_janky_action(self):
        """
        Task names, UUIDs, keys and values in actions all have control
        characters escaped.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([janky_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                b'f3a32bb3-ea6b-457c-\xe2\x90\x9b(0aa99-08a3d0491ab4\n'
                b'+-- A\xe2\x90\x9b(0@1/started\xe2\x90\x9b(0\n'
                b'    |-- \xe2\x90\x9b(0:\n'
                b'        `-- \xe2\x90\x9b(0: nope\n'
                b'    |-- message: hello\xe2\x90\x9b(0world\n'
                b'    `-- timestamp: 1425356800\xe2\x90\x9b(0\n\n'))
