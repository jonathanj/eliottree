class EliotParseError(RuntimeError):
    """
    An error occurred while parsing a particular Eliot message dictionary.
    """
    def __init__(self, message_dict, exc_info):
        self.message_dict = message_dict
        self.exc_info = exc_info
        RuntimeError.__init__(self)


class JSONParseError(RuntimeError):
    """
    An error occurred while parsing JSON text.
    """
    def __init__(self, file_name, line_number, line, exc_info):
        self.file_name = file_name
        self.line_number = line_number
        self.line = line
        self.exc_info = exc_info


__all__ = ['EliotParseError', 'JSONParseError']
