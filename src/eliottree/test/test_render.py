from eliot._message import WrittenMessage
from six import BytesIO, StringIO, text_type
from termcolor import colored
from testtools import ExpectedException, TestCase
from testtools.matchers import AfterPreprocessing as After
from testtools.matchers import (
    Contains, Equals, HasLength, IsDeprecated, MatchesAll, MatchesListwise,
    StartsWith)

from eliottree import (
    Tree, render_task_nodes, render_tasks, tasks_from_iterable)
from eliottree._render import (
    COLORS, HOURGLASS, RIGHT_DOUBLE_ARROW, _default_value_formatter, _no_color,
    format_node, get_children, message_fields, message_name)
from eliottree._util import eliot_ns
from eliottree.render import get_name_factory
from eliottree.test.matchers import ExactlyEquals
from eliottree.test.tasks import (
    action_task, action_task_end, action_task_end_failed, dict_action_task,
    janky_action_task, janky_message_task, list_action_task, message_task,
    multiline_action_task, nested_action_task)


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
        Format Eliot ``timestamp`` fields as human-readable if the feature was
        requested.
        """
        format_value = _default_value_formatter(
            human_readable=True, field_limit=0)
        # datetime(2015, 6, 6, 22, 57, 12)
        now = 1433631432
        self.assertThat(
            format_value(now, eliot_ns(u'timestamp')),
            ExactlyEquals(u'2015-06-06 22:57:12'))
        self.assertThat(
            format_value(str(now), eliot_ns(u'timestamp')),
            ExactlyEquals(u'2015-06-06 22:57:12'))

    def test_not_eliot_timestamp_field(self):
        """
        Do not format user fields named ``timestamp``.
        """
        format_value = _default_value_formatter(
            human_readable=True, field_limit=0)
        now = 1433631432
        self.assertThat(
            format_value(now, u'timestamp'),
            ExactlyEquals(text_type(now)))
        self.assertThat(
            format_value(text_type(now), u'timestamp'),
            ExactlyEquals(text_type(now)))

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
    def test_deprecated(self):
        """
        `render_task_nodes` is deprecated.
        """
        self.assertThat(
            lambda: render_task_nodes(lambda: None, [], field_limit=0),
            IsDeprecated(Contains('render_task_nodes is deprecated')))

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
                u'        \u2514\u2500\u2500 timestamp: 1425356802\n\n'
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
                u'        \u2514\u2500\u2500 timestamp: 2015-03-03 04:26:42\n'
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
                u'    \u251c\u2500\u2500 message: this is a\u2026\n'
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
                u'    \u251c\u2500\u2500 message: Main \u2026\n'
                u'    \u2514\u2500\u2500 timestamp: 14253\u2026\n\n'
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
                u'    \u2514\u2500\u2500 app:action:nest@1,1/started\n'
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
                u'    \u251c\u2500\u2500 er\u241bror: False\n'
                u'    \u251c\u2500\u2500 mes\u240asage: '
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
                u'\u2514\u2500\u2500 A\u241b(0@1/started\n'
                u'    \u251c\u2500\u2500 \u241b(0\n'
                u'    \u2502   \u2514\u2500\u2500 \u241b(0: nope\n'
                u'    \u251c\u2500\u2500 mes\u240asage: hello\u241b(0world\n'
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
                        C.prop('timestamp'), u'1425356802'),
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


colors = COLORS(colored)
no_colors = COLORS(_no_color)


def no_formatting(value, field_name=None):
    return text_type(value)


class MessageNameTests(TestCase):
    """
    Tests for `eliottree.render.message_name`.
    """
    def test_action_type(self):
        """
        Action types include their type name.
        """
        message = next(tasks_from_iterable([action_task])).root().start_message
        self.assertThat(
            message_name(colors, no_formatting, message),
            StartsWith(colors.parent(message.contents.action_type)))

    def test_action_task_level(self):
        """
        Action types include their task level.
        """
        message = next(tasks_from_iterable([action_task])).root().start_message
        self.assertThat(
            message_name(colors, no_formatting, message),
            Contains(message.task_level.to_string()))

    def test_action_status(self):
        """
        Action types include their status.
        """
        message = next(tasks_from_iterable([action_task])).root().start_message
        self.assertThat(
            message_name(colors, no_formatting, message),
            Contains(u'started'))

    def test_action_status_success(self):
        """
        Successful actions color their status.
        """
        message = next(tasks_from_iterable([
            action_task, action_task_end,
        ])).root().end_message
        self.assertThat(
            message_name(colors, no_formatting, message),
            Contains(colors.success(u'succeeded')))

    def test_action_status_failed(self):
        """
        Failed actions color their status.
        """
        message = next(tasks_from_iterable([
            action_task, action_task_end_failed,
        ])).root().end_message
        self.assertThat(
            message_name(colors, no_formatting, message),
            Contains(colors.failure(u'failed')))

    def test_message_type(self):
        """
        Message types include their type name.
        """
        message = WrittenMessage.from_dict(message_task)
        self.assertThat(
            message_name(colors, no_formatting, message),
            StartsWith(colors.parent(message.contents.message_type)))

    def test_message_task_level(self):
        """
        Message types include their task level.
        """
        message = WrittenMessage.from_dict(message_task)
        self.assertThat(
            message_name(colors, no_formatting, message),
            Contains(message.task_level.to_string()))

    def test_unknown(self):
        """
        None or messages with no identifiable information are rendered as
        ``<unnamed>``.
        """
        self.assertThat(
            message_name(colors, no_formatting, None),
            ExactlyEquals(u'<unnamed>'))
        message = WrittenMessage.from_dict({u'timestamp': 0})
        self.assertThat(
            message_name(colors, no_formatting, message),
            ExactlyEquals(u'<unnamed>'))


class FormatNodeTests(TestCase):
    """
    Tests for `eliottree.render.format_node`.
    """
    def format_node(self, node, format_value=None, colors=no_colors):
        if format_value is None:
            def format_value(value, field_name=None):
                return value
        return format_node(format_value, colors, node)

    def test_task(self):
        """
        `Task`'s UUID is rendered.
        """
        node = next(tasks_from_iterable([action_task]))
        self.assertThat(
            self.format_node(node),
            ExactlyEquals(node.root().task_uuid))

    def test_written_action(self):
        """
        `WrittenAction`'s start message is rendered.
        """
        tasks = tasks_from_iterable([action_task, action_task_end])
        node = next(tasks).root()
        self.assertThat(
            self.format_node(node),
            ExactlyEquals(u'{}{} {} {} {} \u29d6 {}'.format(
                node.start_message.contents.action_type,
                node.start_message.task_level.to_string(),
                RIGHT_DOUBLE_ARROW,
                node.start_message.contents.action_status,
                node.start_message.timestamp,
                node.end_message.timestamp - node.start_message.timestamp)))

    def test_tuple_list(self):
        """
        Tuples can be a key and list, in which case the value is not rendered
        here.
        """
        node = (u'a\nb\x1bc', [u'x\n', u'y\x1b', u'z'])
        self.assertThat(
            self.format_node(node, colors=colors),
            ExactlyEquals(u'{}: '.format(
                colors.prop(u'a\u240ab\u241bc'))))

    def test_tuple_dict(self):
        """
        Tuples can be a key and dict, in which case the value is not rendered
        here.
        """
        node = (u'a\nb\x1bc', {u'x\n': u'y\x1b', u'z': u'zz'})
        self.assertThat(
            self.format_node(node, colors=colors),
            ExactlyEquals(u'{}: '.format(
                colors.prop(u'a\u240ab\u241bc'))))

    def test_tuple_other(self):
        """
        Tuples can be a key and string, number, etc. rendered inline.
        """
        node = (u'a\nb\x1bc', u'hello')
        self.assertThat(
            self.format_node(node, colors=colors),
            ExactlyEquals(u'{}: {}'.format(
                colors.prop(u'a\u240ab\u241bc'),
                u'hello')))

        node = (u'a\nb\x1bc', 42)
        self.assertThat(
            self.format_node(node, colors=colors),
            ExactlyEquals(u'{}: {}'.format(
                colors.prop(u'a\u240ab\u241bc'),
                42)))

    def test_other(self):
        """
        Other types raise `NotImplementedError`.
        """
        node = object()
        with ExpectedException(NotImplementedError):
            self.format_node(node, colors=colors)


class MessageFieldsTests(TestCase):
    """
    Tests for `eliottree.render.message_fields`.
    """
    def test_empty(self):
        """
        ``None`` or empty messages result in no fields.
        """
        self.assertThat(
            message_fields(None, set()),
            Equals([]))
        message = WrittenMessage.from_dict({})
        self.assertThat(
            message_fields(message, set()),
            Equals([]))

    def test_fields(self):
        """
        Include all the message fields but not the timestamp.
        """
        message = WrittenMessage.from_dict({u'a': 1})
        self.assertThat(
            message_fields(message, set()),
            Equals([(u'a', 1)]))
        message = WrittenMessage.from_dict({u'a': 1, u'timestamp': 12345678})
        self.assertThat(
            message_fields(message, set()),
            Equals([
                (u'a', 1)]))

    def test_ignored_fields(self):
        """
        Ignore any specified fields.
        """
        message = WrittenMessage.from_dict({u'a': 1, u'b': 2})
        self.assertThat(
            message_fields(message, {u'b'}),
            Equals([(u'a', 1)]))


class GetChildrenTests(TestCase):
    """
    Tests for `eliottree.render.get_children`.
    """
    def test_task_action(self):
        """
        The root message is the only child of a `Task`.
        """
        node = next(tasks_from_iterable([action_task]))
        self.assertThat(
            get_children(set(), node),
            Equals([node.root()]))
        node = next(tasks_from_iterable([message_task]))
        self.assertThat(
            get_children(set(), node),
            Equals([node.root()]))

    def test_written_action_ignored_fields(self):
        """
        Action fields can be ignored.
        """
        task = dict(action_task)
        task.update({u'c': u'3'})
        node = next(tasks_from_iterable([task])).root()
        start_message = node.start_message
        self.assertThat(
            list(get_children({u'c'}, node)),
            Equals([
                (u'action_status', start_message.contents.action_status),
                (u'action_type', start_message.contents.action_type)]))

    def test_written_action_start(self):
        """
        The children of a `WrittenAction` begin with the fields of the start
        message.
        """
        node = next(tasks_from_iterable([
            action_task, nested_action_task, action_task_end])).root()
        start_message = node.start_message
        self.assertThat(
            list(get_children({u'foo'}, node))[:2],
            Equals([
                (u'action_status', start_message.contents.action_status),
                (u'action_type', start_message.contents.action_type)]))

    def test_written_action_children(self):
        """
        The children of a `WrittenAction` contain child actions/messages.
        """
        node = next(tasks_from_iterable([
            action_task, nested_action_task, action_task_end])).root()
        self.assertThat(
            list(get_children({u'foo'}, node))[2],
            Equals(node.children[0]))

    def test_written_action_no_children(self):
        """
        The children of a `WrittenAction` does not contain any child
        actions/messages if there aren't any.
        """
        node = next(tasks_from_iterable([action_task])).root()
        self.assertThat(
            list(get_children({u'foo'}, node)),
            HasLength(2))

    def test_written_action_no_end(self):
        """
        If the `WrittenAction` has no end message, it is excluded.
        """
        node = next(tasks_from_iterable([
            action_task, nested_action_task])).root()
        self.assertThat(
            list(get_children({u'foo'}, node))[4:],
            Equals([]))

    def test_written_action_end(self):
        """
        The last child of a `WrittenAction` is the end message.
        """
        node = next(tasks_from_iterable([
            action_task, nested_action_task, action_task_end])).root()
        self.assertThat(
            list(get_children({u'foo'}, node))[3:],
            Equals([node.end_message]))

    def test_written_message(self):
        """
        The fields of `WrittenMessage`\s are their children. Fields can also be
        ignored.
        """
        node = WrittenMessage.from_dict({u'a': 1, u'b': 2, u'c': 3})
        self.assertThat(
            get_children({u'c'}, node),
            Equals([
                (u'a', 1),
                (u'b', 2)]))

    def test_tuple_dict(self):
        """
        The key/value pairs of dicts are their children.
        """
        node = (u'key', {u'a': 1, u'b': 2, u'c': 3})
        self.assertThat(
            # The ignores intentionally do nothing.
            get_children({u'c'}, node),
            Equals([
                (u'a', 1),
                (u'b', 2),
                (u'c', 3)]))

    def test_tuple_list(self):
        """
        The indexed items of lists are their children.
        """
        node = (u'key', [u'a', u'b', u'c'])
        self.assertThat(
            # The ignores intentionally do nothing.
            get_children({2, u'c'}, node),
            After(list,
                  Equals([
                      (0, u'a'),
                      (1, u'b'),
                      (2, u'c')])))

    def test_other(self):
        """
        Other values are considered to have no children.
        """
        self.assertThat(get_children({}, None), Equals([]))
        self.assertThat(get_children({}, 42), Equals([]))
        self.assertThat(get_children({}, u'hello'), Equals([]))


class RenderTasksTests(TestCase):
    """
    Tests for `eliottree.render.render_tasks`.
    """
    def render_tasks(self, iterable, **kw):
        fd = StringIO()
        err = StringIO(u'')
        tasks = tasks_from_iterable(iterable)
        render_tasks(write=fd.write, write_err=err.write, tasks=tasks, **kw)
        if err.tell():
            return fd.getvalue(), err.getvalue()
        return fd.getvalue()

    def test_format_node_failures(self):
        """
        Catch exceptions when formatting nodes and display a message without
        interrupting the processing of tasks. List all caught exceptions to
        stderr.
        """
        def bad_format_node(*a, **kw):
            raise ValueError('Nope')
        self.assertThat(
            self.render_tasks([message_task],
                              format_node=bad_format_node),
            MatchesListwise([
                Contains(u'<node formatting exception>'),
                MatchesAll(
                    Contains(u'Traceback (most recent call last):'),
                    Contains(u'ValueError: Nope'))]))

    def test_format_value_failures(self):
        """
        Catch exceptions when formatting node values and display a message
        without interrupting the processing of tasks. List all caught
        exceptions to stderr.
        """
        def bad_format_value(*a, **kw):
            raise ValueError('Nope')
        self.assertThat(
            self.render_tasks([message_task],
                              format_value=bad_format_value),
            MatchesListwise([
                Contains(u'message: <value formatting exception>'),
                MatchesAll(
                    Contains(u'Traceback (most recent call last):'),
                    Contains(u'ValueError: Nope'))]))

    def test_tasks(self):
        """
        Render two tasks of sequential levels, by default most standard Eliot
        task keys are ignored.
        """
        self.assertThat(
            self.render_tasks([action_task, action_task_end]),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800 \u29d6 2\n'
                u'    \u2514\u2500\u2500 app:action/2 \u21d2 succeeded '
                u'1425356802\n\n'))

    def test_tasks_human_readable(self):
        """
        Render two tasks of sequential levels, by default most standard Eliot
        task keys are ignored, values are formatted to be human readable.
        """
        self.assertThat(
            self.render_tasks([action_task, action_task_end],
                              human_readable=True),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'2015-03-03 04:26:40 \u29d6 2.000s\n'
                u'    \u2514\u2500\u2500 app:action/2 \u21d2 succeeded '
                u'2015-03-03 04:26:42\n'
                u'\n'))

    def test_multiline_field(self):
        """
        When no field limit is specified for task values, multiple lines are
        output for multiline tasks.
        """
        fd = StringIO()
        tasks = tasks_from_iterable([multiline_action_task])
        render_tasks(
            write=fd.write,
            tasks=tasks)
        self.assertThat(
            fd.getvalue(),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 message: this is a\u23ce\n'
                u'        many line message\n\n'))

    def test_multiline_field_limit(self):
        """
        When a field limit is specified for task values, only the first of
        multiple lines is output.
        """
        self.assertThat(
            self.render_tasks([multiline_action_task],
                              field_limit=1000),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 message: this is a\u2026\n\n'))

    def test_field_limit(self):
        """
        Truncate task values that are longer than the field_limit if specified.
        """
        self.assertThat(
            self.render_tasks([message_task],
                              field_limit=5),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'\u2514\u2500\u2500 twisted:log/1 '
                u'14253\u2026\n'
                u'    \u251c\u2500\u2500 error: False\n'
                u'    \u2514\u2500\u2500 message: Main \u2026\n\n'))

    def test_ignored_keys(self):
        """
        Task keys can be ignored.
        """
        self.assertThat(
            self.render_tasks([action_task],
                              ignored_fields={u'action_type'}),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 action_status: started\n\n'))

    def test_task_data(self):
        """
        Task data is rendered as tree elements.
        """
        self.assertThat(
            self.render_tasks([message_task]),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-8341-1a170222e308\n'
                u'\u2514\u2500\u2500 twisted:log/1 '
                u'1425356700\n'
                u'    \u251c\u2500\u2500 error: False\n'
                u'    \u2514\u2500\u2500 message: Main loop terminated.\n\n'))

    def test_dict_data(self):
        """
        Task values that are ``dict``s are rendered as tree elements.
        """
        self.assertThat(
            self.render_tasks([dict_action_task]),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 some_data: \n'
                u'        \u2514\u2500\u2500 a: 42\n\n'))

    def test_list_data(self):
        """
        Task values that are ``list``s are rendered as tree elements.
        """
        self.assertThat(
            self.render_tasks([list_action_task]),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 some_data: \n'
                u'        \u251c\u2500\u2500 0: a\n'
                u'        \u2514\u2500\u2500 1: b\n\n'))

    def test_nested(self):
        """
        Render nested tasks in a way that visually represents that nesting.
        """
        self.assertThat(
            self.render_tasks([action_task, nested_action_task]),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 app:action/1 \u21d2 started '
                u'1425356800\n'
                u'    \u2514\u2500\u2500 app:action:nest/1/1 \u21d2 started '
                u'1425356900\n\n'))

    def test_janky_message(self):
        """
        Task names, UUIDs, keys and values in messages all have control
        characters escaped.
        """
        self.assertThat(
            self.render_tasks([janky_message_task]),
            ExactlyEquals(
                u'cdeb220d-7605-4d5f-\u241b(08341-1a170222e308\n'
                u'\u2514\u2500\u2500 M\u241b(0/1 '
                u'1425356700\n'
                u'    \u251c\u2500\u2500 er\u241bror: False\n'
                u'    \u2514\u2500\u2500 mes\u240asage: '
                u'Main loop\u241b(0terminated.\n\n'))

    def test_janky_action(self):
        """
        Task names, UUIDs, keys and values in actions all have control
        characters escaped.
        """
        self.assertThat(
            self.render_tasks([janky_action_task]),
            ExactlyEquals(
                u'f3a32bb3-ea6b-457c-\u241b(0aa99-08a3d0491ab4\n'
                u'\u2514\u2500\u2500 A\u241b(0/1 \u21d2 started '
                u'1425356800\u241b(0\n'
                u'    \u251c\u2500\u2500 \u241b(0: \n'
                u'    \u2502   \u2514\u2500\u2500 \u241b(0: nope\n'
                u'    \u2514\u2500\u2500 mes\u240asage: hello\u241b(0world\n\n'
            ))

    def test_colorize(self):
        """
        Passing ``colorize=True`` will colorize the output.
        """
        self.assertThat(
            self.render_tasks([action_task, action_task_end],
                              colorize=True),
            ExactlyEquals(
                u'\n'.join([
                    colors.root(u'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4'),
                    u'\u2514\u2500\u2500 {}/1 \u21d2 {} {} {} {}'.format(
                        colors.parent(u'app:action'),
                        colors.success(u'started'),
                        colors.timestamp(u'1425356800'),
                        HOURGLASS,
                        colors.duration(u'2')),
                    u'    \u2514\u2500\u2500 {}/2 \u21d2 {} {}'.format(
                        colors.parent(u'app:action'),
                        colors.success(u'succeeded'),
                        colors.timestamp(u'1425356802')),
                    u'\n',
                ])))
