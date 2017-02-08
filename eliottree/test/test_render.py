from datetime import datetime

from six import PY3, StringIO
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
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([action_task, action_task_end])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    `-- timestamp: 1425356800\n'
                u'    +-- app:action@2/succeeded\n'
                u'        `-- timestamp: 1425356800\n\n'))

    def test_tasks_human_readable(self):
        """
        Render two tasks of sequential levels, by default most standard Eliot
        task keys are ignored, values are formatted to be human readable.
        """
        fd = StringIO()
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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    `-- timestamp: 2015-03-03 04:26:40\n'
                u'    +-- app:action@2/succeeded\n'
                u'        `-- timestamp: 2015-03-03 04:26:40\n\n'))

    def test_multiline_field(self):
        """
        When no field limit is specified for task values, multiple lines are
        output for multiline tasks.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([multiline_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    |-- message: this is a\n'
                u'        many line message\n'
                u'    `-- timestamp: 1425356800\n\n'))

    def test_multiline_field_limit(self):
        """
        When a field limit is specified for task values, only the first of
        multiple lines is output.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([multiline_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=1000)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    |-- message: this is a [...]\n'
                u'    `-- timestamp: 1425356800\n\n'))

    def test_field_limit(self):
        """
        Truncate task values that are longer than the field_limit if specified.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=5)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'+-- twisted:log@1\n'
                u'    |-- error: False\n'
                u'    |-- message: Main  [...]\n'
                u'    `-- timestamp: 14253 [...]\n\n'))

    def test_ignored_keys(self):
        """
        Task keys can be ignored.
        """
        fd = StringIO()
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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    |-- action_status: started\n'
                u'    |-- action_type: app:action\n'
                u'    |-- task_uuid: f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'    `-- timestamp: 1425356800\n\n'))

    def test_task_data(self):
        """
        Task data is rendered as tree elements.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'+-- twisted:log@1\n'
                u'    |-- error: False\n'
                u'    |-- message: Main loop terminated.\n'
                u'    `-- timestamp: 1425356700\n\n'))

    def test_dict_data(self):
        """
        Task values that are ``dict``s are rendered as tree elements.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([dict_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    |-- some_data:\n'
                u'        `-- a: 42\n'
                u'    `-- timestamp: 1425356800\n\n'))

    def test_nested(self):
        """
        Render nested tasks in a way that visually represents that nesting.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([action_task, nested_action_task])
        render_task_nodes(fd.write, tree.nodes(), 0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'+-- app:action@1/started\n'
                u'    `-- timestamp: 1425356800\n'
                u'    +-- app:action:nested@1,1/started\n'
                u'        `-- timestamp: 1425356900\n\n'))

    def test_janky_message(self):
        """
        Task names, UUIDs, keys and values in messages all have control
        characters escaped.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([janky_message_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-\u241b(08341-1a170222e308\n'
                u'+-- M\u241b(0@1\n'
                u'    |-- error: False\n'
                u'    |-- message: Main loop\u241b(0terminated.\n'
                u'    `-- timestamp: 1425356700\n\n'))

    def test_janky_action(self):
        """
        Task names, UUIDs, keys and values in actions all have control
        characters escaped.
        """
        fd = StringIO()
        tree = Tree()
        tree.merge_tasks([janky_action_task])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-\u241b(0aa99-08a3d0491ab4\n'
                u'+-- A\u241b(0@1/started\u241b(0\n'
                u'    |-- \u241b(0:\n'
                u'        `-- \u241b(0: nope\n'
                u'    |-- message: hello\u241b(0world\n'
                u'    `-- timestamp: 1425356800\u241b(0\n\n'))
