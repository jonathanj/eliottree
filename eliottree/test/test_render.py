from datetime import datetime
from StringIO import StringIO

from testtools import TestCase
from testtools.matchers import Equals

from eliottree import Tree, render_task_nodes
from eliottree.render import _format_value
from eliottree.test.tasks import (
    action_task, action_task_end, dict_action_task, message_task,
    multiline_action_task, nested_action_task)


class FormatValueTests(TestCase):
    """
    Tests for ``eliottree.render._format_value``.
    """
    def test_datetime(self):
        """
        Format ``datetime`` values as ISO8601.
        """
        now = datetime(2015, 6, 6, 22, 57, 12)
        self.assertThat(
            _format_value(now, 'utf-8'),
            Equals('2015-06-06 22:57:12'))
        self.assertThat(
            _format_value(now, 'utf-16'),
            Equals('\xff\xfe2\x000\x001\x005\x00-\x000\x006\x00-\x000\x006'
                   '\x00 \x002\x002\x00:\x005\x007\x00:\x001\x002\x00'))

    def test_unicode(self):
        """
        Encode ``unicode`` values as the specified encoding.
        """
        self.assertThat(
            _format_value(u'\N{SNOWMAN}', 'utf-8'),
            Equals('\xe2\x98\x83'))
        self.assertThat(
            _format_value(u'\N{SNOWMAN}', 'utf-16'),
            Equals('\xff\xfe\x03&'))

    def test_str(self):
        """
        Assume that ``str`` values are UTF-8.
        """
        self.assertThat(
            _format_value('foo', 'utf-8'),
            Equals('foo'))
        self.assertThat(
            _format_value('\xe2\x98\x83', 'utf-8'),
            Equals('\xe2\x98\x83'))
        self.assertThat(
            _format_value('\xff\xfe\x03&', 'utf-8'),
            Equals('\xef\xbf\xbd\xef\xbf\xbd\x03&'))

    def test_other(self):
        """
        Pass unknown values to ``repr`` and encode as ``utf-8`` while replacing
        encoding errors.
        """
        self.assertThat(
            _format_value(42, 'utf-8'),
            Equals('42'))
        self.assertThat(
            _format_value({u'a': u'\N{SNOWMAN}'}, 'utf-8'),
            Equals("{u'a': u'\\u2603'}"))
        self.assertThat(
            _format_value({u'a': u'\N{SNOWMAN}'}, 'utf-16'),
            Equals("\xff\xfe{\x00u\x00'\x00a\x00'\x00:\x00 \x00u\x00'"
                   "\x00\\\x00u\x002\x006\x000\x003\x00'\x00}\x00"))


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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    `-- timestamp: 1425356800\n'
                '    +-- app:action@2/succeeded\n'
                '        `-- timestamp: 1425356800\n\n'))

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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    |-- message: this is a\n'
                '        many line message\n'
                '    `-- timestamp: 1425356800\n\n'))

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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    |-- message: this is a [...]\n'
                '    `-- timestamp: 1425356800\n\n'))

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
            Equals(
                'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                '+-- twisted:log@1\n'
                '    |-- error: False\n'
                '    |-- message: Main  [...]\n'
                '    `-- timestamp: 14253 [...]\n\n'))

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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    |-- action_status: started\n'
                '    |-- action_type: app:action\n'
                '    |-- task_uuid: f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '    `-- timestamp: 1425356800\n\n'))

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
            Equals(
                'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                '+-- twisted:log@1\n'
                '    |-- error: False\n'
                '    |-- message: Main loop terminated.\n'
                '    `-- timestamp: 1425356700\n\n'))

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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    |-- some_data:\n'
                '        `-- a: 42\n'
                '    `-- timestamp: 1425356800\n\n'))

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
            Equals(
                'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '+-- app:action@1/started\n'
                '    `-- timestamp: 1425356800\n'
                '    +-- app:action:nested@1,1/started\n'
                '        `-- timestamp: 1425356900\n\n'))
