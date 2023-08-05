


class DictLoadError(Exception):
    """Exception for any file-loading or parsing error when parsing files for dictionaries with different
    libraries (eg. PyYaml).
    """

    def __init__(
        self,
        message: str,
        position: int = None,
        document: str = None,
        line_number: int = None,
        column_number: int = None,
    ):
        """Create new DictLoadException
        Args:
            message: an error message from the parsing library describing the nature of the parsing error.
            document: full or parts of the documents parsed into a dict (actual content depends on parsing library)
            position: character position where the parsing error occurred, counting from document start
            line_number: line number in the read file where the parsing error occurred
            column_number: column number in the line where the parsing error occurred
        """

        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        self.message = message
        self.document = document
        self.position = position
        self.line_number = line_number
        self.column_number = column_number
