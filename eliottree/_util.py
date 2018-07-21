from collections import namedtuple


namespace = namedtuple('namespace', ['prefix', 'name'])


def namespaced(prefix):
    """
    Create a function that creates new names in the ``prefix`` namespace.

    :rtype: Callable[[unicode], `namespace`]
    """
    return lambda name: namespace(prefix, name)


def format_namespace(ns):
    """
    Format a `namespace`.

    :rtype: unicode
    """
    if not is_namespace(ns):
        raise TypeError('Expected namespace', ns)
    return u'{}/{}'.format(ns.prefix, ns.name)


def is_namespace(x):
    """
    Is this a `namespace` instance?

    :rtype: bool
    """
    return isinstance(x, namespace)


eliot_ns = namespaced(u'eliot')
