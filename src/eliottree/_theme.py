NO_COLOR = (None,)
DEFAULT_THEME = {
    # Task root.
    'root': NO_COLOR,
    # Action / message node.
    'parent': NO_COLOR,
    # Action / message task level.
    'task_level': NO_COLOR,
    # Action success status.
    'status_success': NO_COLOR,
    # Action failure status.
    'status_failure': NO_COLOR,
    # Task timestamp.
    'timestamp': NO_COLOR,
    # Action / message property key.
    'prop_key': NO_COLOR,
    # Action / message property value.
    'prop_value': NO_COLOR,
    # Task duration.
    'duration': NO_COLOR,
    # Tree color for failed tasks.
    'tree_failed': NO_COLOR,
    # Cycled tree colors.
    'tree_color0': NO_COLOR,
    'tree_color1': NO_COLOR,
    'tree_color2': NO_COLOR,
    # Processing error.
    'error': NO_COLOR,
}


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
    __slots__ = DEFAULT_THEME.keys()

    def __init__(self, color, **theme):
        super(Theme, self).__init__()
        self.color = color
        _theme = dict(DEFAULT_THEME)
        _theme.update(theme)
        for k, v in _theme.items():
            if not isinstance(v, (tuple, list)):
                raise TypeError(
                    'Theme color must be a tuple or list of values', k, v)
            setattr(self, k, color(*v))


class DarkBackgroundTheme(Theme):
    """
    Color theme for dark backgrounds.
    """
    def __init__(self, colored):
        super(DarkBackgroundTheme, self).__init__(
            color=color_factory(colored),
            root=('white', ['bold']),
            parent=('magenta',),
            status_success=('green',),
            status_failure=('red',),
            prop_key=('blue',),
            error=('red', ['bold']),
            timestamp=('white', ['dark']),
            duration=('blue', ['dark']),
            tree_failed=('red',),
            tree_color0=('white', ['dark']),
            tree_color1=('blue', ['dark']),
            tree_color2=('magenta', ['dark']),
        )


class LightBackgroundTheme(Theme):
    """
    Color theme for light backgrounds.
    """
    def __init__(self, colored):
        super(LightBackgroundTheme, self).__init__(
            color=color_factory(colored),
            root=('grey', ['bold']),
            parent=('magenta',),
            status_success=('green',),
            status_failure=('red',),
            prop_key=('blue',),
            error=('red', ['bold']),
            timestamp=('grey',),
            duration=('blue', ['dark']),
            tree_failed=('red',),
            tree_color0=('grey', ['dark']),
            tree_color1=('blue', ['dark']),
            tree_color2=('magenta', ['dark']),
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


def apply_theme_overrides(theme, overrides):
    """
    Apply overrides to a theme.
    """
    if overrides is None:
        return theme

    for key, args in overrides.items():
        setattr(theme, key, theme.color(*args))
    return theme
