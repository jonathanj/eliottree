from testtools import TestCase
from testtools.matchers import Equals

from eliottree import filter_by_jmespath, filter_by_uuid
from eliottree.test.tasks import action_task, message_task


class FilterForJmespath(TestCase):
    """
    Tests for ``eliottree.filter_by_jmespath``.
    """
    def test_no_match(self):
        """
        Return ``False`` if the jmespath does not match the input.
        """
        self.assertThat(
            filter_by_jmespath('action_type == `app:action`')(message_task),
            Equals(False))

    def test_match(self):
        """
        Return ``True`` if the jmespath does match the input.
        """
        self.assertThat(
            filter_by_jmespath('action_type == `app:action`')(action_task),
            Equals(True))


class FilterForUUID(TestCase):
    """
    Tests for ``eliottree.filter_by_uuid``.
    """
    def test_no_match(self):
        """
        Return ``False`` if the input is not the specified task UUID.
        """
        self.assertThat(
            filter_by_uuid('nope')(message_task),
            Equals(False))

    def test_match(self):
        """
        Return ``True`` if the input is the specified task UUID.
        """
        self.assertThat(
            filter_by_uuid('cdeb220d-7605-4d5f-8341-1a170222e308')(
                message_task),
            Equals(True))
