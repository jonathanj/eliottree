from calendar import timegm
from datetime import datetime

from iso8601.iso8601 import UTC
from testtools import TestCase
from testtools.matchers import Equals

from eliottree import (
    filter_by_end_date, filter_by_jmespath, filter_by_start_date,
    filter_by_uuid)
from eliottree.test.tasks import action_task, message_task


class FilterByJmespath(TestCase):
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


class FilterByUUID(TestCase):
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


class FilterByStartDate(TestCase):
    """
    Tests for ``eliottree.filter_by_start_date``.
    """
    def test_no_match(self):
        """
        Return ``False`` if the input task's timestamp is before the start
        date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 1, 0).utctimetuple()))
        self.assertThat(
            filter_by_start_date(now)(task),
            Equals(False))

    def test_match(self):
        """
        Return ``True`` if the input task's timestamp is after the start date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 2).utctimetuple()))
        self.assertThat(
            filter_by_start_date(now)(task),
            Equals(True))

    def test_match_moment(self):
        """
        Return ``True`` if the input task's timestamp is the same as the start
        date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 1, 15).utctimetuple()))
        self.assertThat(
            filter_by_start_date(now)(task),
            Equals(True))


class FilterByEndDate(TestCase):
    """
    Tests for ``eliottree.filter_by_end_date``.
    """
    def test_no_match(self):
        """
        Return ``False`` if the input task's timestamp is after the start
        date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 2).utctimetuple()))
        self.assertThat(
            filter_by_end_date(now)(task),
            Equals(False))

    def test_no_match_moment(self):
        """
        Return ``False`` if the input task's timestamp is the same as the start
        date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 1, 15).utctimetuple()))
        self.assertThat(
            filter_by_end_date(now)(task),
            Equals(False))

    def test_match(self):
        """
        Return ``True`` if the input task's timestamp is before the start date.
        """
        now = datetime(2015, 10, 30, 22, 1, 15).replace(tzinfo=UTC)
        task = dict(
            message_task,
            timestamp=timegm(datetime(2015, 10, 30, 22, 1).utctimetuple()))
        self.assertThat(
            filter_by_end_date(now)(task),
            Equals(True))
