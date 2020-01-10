def color_factory(colored):
    """
    Factory for making text color-wrappers.
    """
    def _color(color, attrs=[]):
        def __color(text):
            return colored(text, color, attrs=attrs)
        return __color
    return _color


class Theme(object):
    """
    Theme base class.
    """
    __slots__ = [
        'root',
        'parent',
        'success',
        'failure',
        'prop',
        'error',
        'timestamp',
        'duration',
        'tree_failed',
        'tree_color0',
        'tree_color1',
        'tree_color2',
    ]
    def __init__(self, **theme):
        super(Theme, self).__init__()
        for k, v in theme.items():
            setattr(self, k, v)


class DarkBackgroundTheme(Theme):
    """
    Color theme for dark backgrounds.
    """
    def __init__(self, colored):
        color = color_factory(colored)
        super(DarkBackgroundTheme, self).__init__(
            root=color('white', ['bold']),
            parent=color('magenta'),
            success=color('green'),
            failure=color('red'),
            prop=color('blue'),
            error=color('red', ['bold']),
            timestamp=color('white', ['dark']),
            duration=color('blue', ['dark']),
            tree_failed=color('red'),
            tree_color0=color('white', ['dark']),
            tree_color1=color('blue', ['dark']),
            tree_color2=color('magenta', ['dark']),
        )


class LightBackgroundTheme(Theme):
    """
    Color theme for light backgrounds.
    """
    def __init__(self, colored):
        color = color_factory(colored)
        super(LightBackgroundTheme, self).__init__(
            root=color('grey', ['bold']),
            parent=color('magenta'),
            success=color('green'),
            failure=color('red'),
            prop=color('blue'),
            error=color('red', ['bold']),
            timestamp=color('grey'),
            duration=color('blue', ['dark']),
            tree_failed=color('red'),
            tree_color0=color('grey', ['dark']),
            tree_color1=color('blue', ['dark']),
            tree_color2=color('magenta', ['dark']),
        )


def _no_color(text, *a, **kw):
    """
    Colorizer that does not colorize.
    """
    return text


def get_theme(dark_background, colored=None):
    """
    Create an appropriate theme.
    """
    if colored is None:
        colored = _no_color
    return DarkBackgroundTheme(colored) if dark_background else LightBackgroundTheme(colored)
