from testtools import ExpectedException, TestCase
from testtools.matchers import AfterPreprocessing as After
from testtools.matchers import (
    Equals, Is, MatchesAll, MatchesListwise, MatchesPredicate,
    MatchesStructure)

from eliottree._util import format_namespace, is_namespace, namespaced


class NamespaceTests(TestCase):
    """
    Tests for `namespaced`, `format_namespace` and `is_namespace`.
    """
    def test_namespaced(self):
        """
        `namespaced` creates a function that when called produces a namespaced
        name.
        """
        self.assertThat(
            namespaced(u'foo'),
            MatchesAll(
                MatchesPredicate(callable, '%s is not callable'),
                After(
                    lambda f: f(u'bar'),
                    MatchesAll(
                        MatchesListwise([
                            Equals(u'foo'),
                            Equals(u'bar')]),
                        MatchesStructure(
                            prefix=Equals(u'foo'),
                            name=Equals(u'bar'))))))

    def test_format_not_namespace(self):
        """
        `format_namespace` raises `TypeError` if its argument is not a
        namespaced name.
        """
        with ExpectedException(TypeError):
            format_namespace(42)

    def test_format_namespace(self):
        """
        `format_namespace` creates a text representation of a namespaced name.
        """
        self.assertThat(
            format_namespace(namespaced(u'foo')(u'bar')),
            Equals(u'foo/bar'))

    def test_is_namespace(self):
        """
        `is_namespace` returns ``True`` only for namespaced names.
        """
        self.assertThat(
            is_namespace(42),
            Is(False))
        self.assertThat(
            is_namespace((u'foo', u'bar')),
            Is(False))
        self.assertThat(
            is_namespace(namespaced(u'foo')),
            Is(False))
        self.assertThat(
            is_namespace(namespaced(u'foo')(u'bar')),
            Is(True))
