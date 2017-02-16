from six import BytesIO, text_type
from termcolor import colored
from testtools import TestCase

from eliottree import Tree, render_task_nodes
from eliottree.render import COLORS, _default_value_formatter, get_name_factory
from eliottree.test.matchers import ExactlyEquals
from eliottree.test.tasks import (
    action_task, action_task_end, dict_action_task, janky_action_task,
    janky_message_task, message_task, multiline_action_task,
    nested_action_task)


class DefaultValueFormatterTests(TestCase):
    """
    Tests for ``eliottree.render._default_value_formatter``.
    """
    def test_unicode(self):
        """
        Pass ``unicode`` values straight through.
        """
        format_value = _default_value_formatter(
            human_readable=False, field_limit=0)
        self.assertThat(
            format_value(u'\N{SNOWMAN}'),
            ExactlyEquals(u'\N{SNOWMAN}'))

    def test_unicode_control_characters(self):
        """
        Translate control characters to their Unicode "control picture"
        equivalent, instead of destroying a terminal.
        """
        format_value = _default_value_formatter(
            human_readable=False, field_limit=0)
        self.assertThat(
            format_value(u'hello\001world'),
            ExactlyEquals(u'hello\u2401world'))

    def test_bytes(self):
        """
        Decode ``bytes`` values as the specified encoding.
        """
        format_value = _default_value_formatter(
            human_readable=False, field_limit=0, encoding='utf-8')
        self.assertThat(
            format_value(b'foo'),
            ExactlyEquals(u'foo'))
        self.assertThat(
            format_value(b'\xe2\x98\x83'),
            ExactlyEquals(u'\N{SNOWMAN}'))

    def test_anything(self):
        """
        Pass unknown values to ``repr``.
        """
        class _Thing(object):
            def __repr__(self):
                return 'Hello'
        format_value = _default_value_formatter(
            human_readable=False, field_limit=0)
        self.assertThat(
            format_value(_Thing()),
            ExactlyEquals(u'Hello'))

    def test_timestamp_field(self):
        """
        Format ``timestamp`` fields as human-readable if the feature was
        requested.
        """
        format_value = _default_value_formatter(
            human_readable=True, field_limit=0)
        # datetime(2015, 6, 6, 22, 57, 12)
        now = 1433631432
        self.assertThat(
            format_value(now, u'timestamp'),
            ExactlyEquals(u'2015-06-06 22:57:12'))
        self.assertThat(
            format_value(str(now), u'timestamp'),
            ExactlyEquals(u'2015-06-06 22:57:12'))

    def test_timestamp_field_not_human(self):
        """
        Do not format ``timestamp`` fields as human-readable if the feature was
        not requested.
        """
        format_value = _default_value_formatter(
            human_readable=False, field_limit=0)
        # datetime(2015, 6, 6, 22, 57, 12)
        now = 1433631432
        self.assertThat(
            format_value(now, u'timestamp'),
            ExactlyEquals(text_type(now)))


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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 timestamp: 1425356800\n'
                u'    \u2514\u2500\u2500 app:action@2/succeeded\n'
                u'        \u2514\u2500\u2500 timestamp: 1425356800\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 timestamp: 2015-03-03 04:26:40\n'
                u'    \u2514\u2500\u2500 app:action@2/succeeded\n'
                u'        \u2514\u2500\u2500 timestamp: 2015-03-03 04:26:40\n'
                u'\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 message: this is a\u23ce\n'
                u'    \u2502   many line message\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356800\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 message: this is a [...]\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356800\n\n'
                .encode('utf-8')))

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
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'\u2514\u2500\u2500 twisted:log@1\n'
                u'    \u251c\u2500\u2500 error: False\n'
                u'    \u251c\u2500\u2500 message: Main  [...]\n'
                u'    \u2514\u2500\u2500 timestamp: 14253 [...]\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 action_status: started\n'
                u'    \u251c\u2500\u2500 action_type: app:action\n'
                u'    \u251c\u2500\u2500 task_uuid: '
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356800\n\n'
                .encode('utf-8')))

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
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'\u2514\u2500\u2500 twisted:log@1\n'
                u'    \u251c\u2500\u2500 error: False\n'
                u'    \u251c\u2500\u2500 message: Main loop terminated.\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356700\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 some_data\n'
                u'    \u2502   \u2514\u2500\u2500 a: 42\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356800\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action@1/started\n'
                u'    \u251c\u2500\u2500 timestamp: 1425356800\n'
                u'    \u2514\u2500\u2500 app:action:nested@1,1/started\n'
                u'        \u2514\u2500\u2500 timestamp: 1425356900\n\n'
                .encode('utf-8')))

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
                u'cdeb220d-7605-4d5f-\u241b(08341-1a170222e308\n'
                u'\u2514\u2500\u2500 M\u241b(0@1\n'
                u'    \u251c\u2500\u2500 error: False\n'
                u'    \u251c\u2500\u2500 message: '
                u'Main loop\u241b(0terminated.\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356700\n\n'
                .encode('utf-8')))

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
                u'f3a32bb3-ea6b-457c-\u241b(0aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 A\u241b(0@1/started\u241b(0\n'
                u'    \u251c\u2500\u2500 \u241b(0\n'
                u'    \u2502   \u2514\u2500\u2500 \u241b(0: nope\n'
                u'    \u251c\u2500\u2500 message: hello\u241b(0world\n'
                u'    \u2514\u2500\u2500 timestamp: 1425356800\u241b(0\n\n'
                .encode('utf-8')))

    def test_colorize(self):
        """
        Passing ``colorize=True`` will colorize the output.
        """
        fd = BytesIO()
        tree = Tree()
        tree.merge_tasks([action_task, action_task_end])
        render_task_nodes(
            write=fd.write,
            nodes=tree.nodes(),
            field_limit=0,
            colorize=True)
        C = COLORS(colored)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'\n'.join([
                    C.root(u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4'),
                    u'\u2514\u2500\u2500 {}'.format(
                        C.success(u'app:action@1/started')),
                    u'    \u251c\u2500\u2500 {}: {}'.format(
                        C.prop(u'timestamp'), u'1425356800'),
                    u'    \u2514\u2500\u2500 {}'.format(
                        C.success(u'app:action@2/succeeded')),
                    u'        \u2514\u2500\u2500 {}: {}'.format(
                        C.prop('timestamp'), u'1425356800'),
                    u'\n',
                ]).encode('utf-8')))


class GetNameFactoryTests(TestCase):
    """
    Tests for `eliottree.render.get_name_factory` output.
    """
    def test_text(self):
        """
        Text leaves are their own name.
        """
        get_name = get_name_factory(None)
        self.assertThat(
            get_name(u'hello'),
            ExactlyEquals(u'hello'))
        self.assertThat(
            get_name(u'hello\x1b'),
            ExactlyEquals(u'hello\u241b'))

    def test_tuple_dict(self):
        """
        Tuples whose value is a dict use the name in the first position of the
        tuple.
        """
        get_name = get_name_factory(None)
        self.assertThat(
            get_name((u'key\x1bname', {})),
            ExactlyEquals(u'key\u241bname'))

    def test_tuple_unicode(self):
        """
        Tuples whose value is unicode are a key/value pair.
        """
        C = COLORS(colored)
        get_name = get_name_factory(C)
        self.assertThat(
            get_name((u'key\x1bname', u'hello')),
            ExactlyEquals(u'{}: hello'.format(C.prop(u'key\u241bname'))))

    def test_tuple_root(self):
        """
        Tuples that are neither unicode nor a dict are assumed to be a root
        node.
        """
        C = COLORS(colored)
        get_name = get_name_factory(C)
        self.assertThat(
            get_name((u'key\x1bname', None)),
            ExactlyEquals(C.root(u'key\u241bname')))

    def test_node(self):
        """
        Task nodes use their own name.
        """
        tree = Tree()
        tree.merge_tasks([action_task])
        node = tree.nodes()[0][1]
        C = COLORS(colored)
        get_name = get_name_factory(C)
        self.assertThat(
            get_name(node),
            ExactlyEquals(node.name))

    def test_node_success(self):
        """
        Task nodes indicating success are colored.
        """
        tree = Tree()
        tree.merge_tasks([action_task])
        node = tree.nodes()[0][1].copy()
        node.success = True
        C = COLORS(colored)
        get_name = get_name_factory(C)
        self.assertThat(
            get_name(node),
            ExactlyEquals(C.success(node.name)))

    def test_node_failure(self):
        """
        Task nodes indicating failure are colored.
        """
        tree = Tree()
        tree.merge_tasks([action_task])
        node = tree.nodes()[0][1].copy()
        node.success = False
        C = COLORS(colored)
        get_name = get_name_factory(C)
        self.assertThat(
            get_name(node),
            ExactlyEquals(C.failure(node.name)))
