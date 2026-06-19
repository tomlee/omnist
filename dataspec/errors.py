"""Exceptions used across dataspec."""


class DataspecError(Exception):
    """Base class for all dataspec errors."""


class SchemaError(DataspecError):
    """The schema text or structure is invalid."""


class ParseError(DataspecError):
    """A document could not be read from its format (outside the supported profile)."""


class WriteError(DataspecError):
    """A document cannot be represented losslessly in the target format.

    Raised only in ``strict=True`` mode.  ``.report`` holds the full
    :class:`~dataspec.report.WriteReport` of every adjustment that would have
    been needed, so callers can inspect the structured list, not just the text.
    """

    def __init__(self, message: str, report=None):
        super().__init__(message)
        self.report = report
