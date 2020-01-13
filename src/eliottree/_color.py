import colored as _colored


attr_codes = {
    'bold': 1,
    'dim': 2,
    'underlined': 4,
    'blink': 5,
    'reverse': 7,
    'hidden': 8,
    'reset': 0,
    'res_bold': 21,
    'res_dim': 22,
    'res_underlined': 24,
    'res_blink': 25,
    'res_reverse': 27,
    'res_hidden': 28,
}


def colored(text, fg=None, bg=None, attrs=None):
    """
    Wrap text in terminal color codes.

    Intended to mimic the API of `termcolor`.
    """
    if attrs is None:
        attrs = []
    return u'{}{}{}{}{}'.format(
        _colored.fg(fg) if fg is not None else u'',
        _colored.bg(bg) if bg is not None else u'',
        text,
        u''.join(_colored.attr(attr_codes.get(attr, attr)) for attr in attrs),
        _colored.attr(0))


def color_factory(colored):
    """
    Factory for making text color-wrappers.
    """
    def _color(fg, bg=None, attrs=[]):
        def __color(text):
            return colored(text, fg, bg, attrs=attrs)
        return __color
    return _color
