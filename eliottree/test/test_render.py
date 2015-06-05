from StringIO import StringIO

from testtools import TestCase
from testtools.matchers import Equals

from eliottree import Tree, render_task_nodes
from eliottree.test.tasks import (
    action_task, action_task_end, message_task, nested_action_task)


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
                '    +-- app:action@1/started\n'
                '        `-- timestamp: 1425356800\n'
                '    +-- app:action@2/succeeded\n'
                '        `-- timestamp: 1425356800\n\n'))


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
                '    +-- twisted:log@1/None\n'
                '        |-- error: False\n'
                '        |-- message: Main  [...]\n'
                '        |-- message_type: twist [...]\n'
                '        `-- timestamp: 14253 [...]\n\n'))


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
                '    +-- app:action@1/started\n'
                '        |-- action_status: started\n'
                '        |-- action_type: app:action\n'
                '        |-- task_uuid: f3a32bb3-ea6b-457c-aa99-08a3d0491ab4\n'
                '        `-- timestamp: 1425356800\n\n'))


    def test_task_data(self):
        """
        Custom task data is rendered as tree elements.
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
                '    +-- twisted:log@1/None\n'
                '        |-- error: False\n'
                '        |-- message: Main loop terminated.\n'
                '        |-- message_type: twisted:log\n'
                '        `-- timestamp: 1425356700\n\n'))


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
                '    +-- app:action@1/started\n'
                '        `-- timestamp: 1425356800\n'
                '        +-- app:action:nested@1,1/started\n'
                '            `-- timestamp: 1425356900\n\n'))
