from testtools.matchers import Equals, IsInstance, MatchesAll


def ExactlyEquals(value):
    """
    Like `Equals` but also requires that the types match.
    """
    return MatchesAll(
        IsInstance(type(value)),
        Equals(value))
