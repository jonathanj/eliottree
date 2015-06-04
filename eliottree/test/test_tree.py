from testtools import TestCase
from testtools.matchers import Equals, Is, MatchesListwise, raises

from eliottree.tree import TaskNode, Tree, task_name


message_task = {
    "task_uuid": "cdeb220d-7605-4d5f-8341-1a170222e308",
    "error": False,
    "timestamp": 1425356700,
    "message": "Main loop terminated.",
    "message_type": "twisted:log",
    "action_type": "nope",
    "task_level": [1]}

action_task = {
    "timestamp": 1425356800,
    "action_status": "started",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action",
    "task_level": [1]}

nested_action_task = {
    "timestamp": 1425356900,
    "action_status": "started",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action:nested",
    "task_level": [1, 1]}

action_task_end = {
    "timestamp": 1425356800,
    "action_status": "succeeded",
    "task_uuid": "f3a32bb3-ea6b-457c-aa99-08a3d0491ab4",
    "action_type": "app:action",
    "task_level": [2]}


class TaskNameTests(TestCase):
    """
    Tests for ``eliottree.tree.task_name``.
    """
    def test_none(self):
        """
        Cannot create a task name for ``None``.
        """
        self.assertThat(
            lambda: task_name(None),
            raises(ValueError))

    def test_message_type(self):
        """
        If the task includes a ``message_type`` key use it to construct the
        name.
        """
        self.assertThat(
            task_name(message_task),
            Equals(u'twisted:log@1/None'))

    def test_no_message_type(self):
        """
        If the task does not include a ``message_type`` key use the
        ``action_type`` and ``action_status`` keys to construct a name.
        """
        self.assertThat(
            task_name(action_task),
            Equals(u'app:action@1/started'))

    def test_levels(self):
        """
        Include the task level in the task name.
        """
        self.assertThat(
            task_name(nested_action_task),
            Equals(u'app:action:nested@1,1/started'))


class TaskNodeTests(TestCase):
    """
    Tests for ``eliottree.tree.TaskNode``.
    """
    def test_repr_root(self):
        """
        Representation of a root node.
        """
        node = TaskNode(task=None, name=u'foo')
        self.assertThat(
            repr(node),
            Equals('<TaskNode root foo children=0>'))

    def test_repr(self):
        """
        Representation of a normal task node.
        """
        node = TaskNode(task=action_task)
        self.assertThat(
            repr(node),
            Equals('<TaskNode f3a32bb3-ea6b-457c-aa99-08a3d0491ab4 '
                   'app:action@1/started children=0>'))

    def test_repr_childen(self):
        """
        Representation of a task node with children.
        """
        node = TaskNode(task=None, name=u'foo')
        node.add_child(TaskNode(task=action_task))
        self.assertThat(
            repr(node),
            Equals('<TaskNode root foo children=1>'))

    def test_first_child(self):
        """
        ``TaskNode.first_child`` returns the first child node that was added.
        """
        node = TaskNode(task=None, name=u'foo')
        child = TaskNode(task=action_task)
        child2 = TaskNode(task=action_task_end)
        node.add_child(child2)
        node.add_child(child)
        self.assertThat(
            node.first_child(),
            Equals(child2))

    def test_no_children(self):
        """
        ``TaskNode.children`` returns an empty list for a node with no children.
        """
        node = TaskNode(task=None, name=u'foo')
        self.assertThat(
            node.children(),
            Equals([]))

    def test_children(self):
        """
        ``TaskNode.children`` returns an list of child nodes sorted by their
        level regardless of the order they were added.
        """
        node = TaskNode(task=None, name=u'foo')
        child = TaskNode(task=action_task)
        child2 = TaskNode(task=action_task_end)
        node.add_child(child2)
        node.add_child(child)
        self.assertThat(
            node.children(),
            Equals([child, child2]))

    def test_nested_children(self):
        """
        ``TaskNode.children`` does not include grandchildren.
        """
        node = TaskNode(task=None, name=u'foo')
        child = TaskNode(task=action_task)
        node.add_child(child)
        child2 = TaskNode(task=nested_action_task)
        node.add_child(child2)
        self.assertThat(
            node.children(),
            Equals([child]))
        self.assertThat(
            child.children(),
            Equals([child2]))


class TreeTests(TestCase):
    """
    Tests for ``eliottree.tree.Tree``.
    """
    def test_initial(self):
        """
        The initial state of a tree is always empty.
        """
        tree = Tree()
        self.assertThat(tree.nodes(), Equals([]))


    def test_merge_tasks(self):
        """
        Merge tasks into the tree and retrieve an list of key-node
        pairs ordered by task timestamp.
        """
        tree = Tree()
        matches = tree.merge_tasks([message_task, action_task])
        self.expectThat(matches, Is(None))
        keys, nodes = zip(*tree.nodes())
        self.expectThat(
            list(keys),
            Equals(['cdeb220d-7605-4d5f-8341-1a170222e308',
                    'f3a32bb3-ea6b-457c-aa99-08a3d0491ab4']))
        self.assertThat(
            [c.task for n in nodes for c in n.children()],
            MatchesListwise([Equals(message_task),
                             Equals(action_task)]))


    def test_merge_nested_tasks(self):
        """
        Merge nested tasks into the tree and retrieve an list of key-node
        pairs ordered by task timestamp.
        """
        tree = Tree()
        matches = tree.merge_tasks([action_task_end, action_task])
        self.expectThat(matches, Is(None))
        keys, nodes = zip(*tree.nodes())
        self.expectThat(
            list(keys),
            Equals(['f3a32bb3-ea6b-457c-aa99-08a3d0491ab4']))
        self.assertThat(
            [c.task for n in nodes for c in n.children()],
            MatchesListwise([Equals(action_task),
                             Equals(action_task_end)]))


    def test_merge_tasks_filtered(self):
        """
        Merge tasks into the tree with a filter function, generating a set of
        matches that can be used to prune the tree.
        """
        tree = Tree()
        filters = [lambda task: task.get(u'action_type') == u'app:action']
        matches = tree.merge_tasks([action_task, message_task], filters)
        keys, nodes = zip(*tree.nodes(matches))
        self.expectThat(
            list(keys),
            Equals(['f3a32bb3-ea6b-457c-aa99-08a3d0491ab4']))
        self.expectThat(
            list(keys),
            Equals(list(matches)))
        self.assertThat(
            [c.task for n in nodes for c in n.children()],
            MatchesListwise([Equals(action_task)]))
