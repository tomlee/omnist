"""Exceptions used across dataspec."""


class DataspecError(Exception):
    """Base class for all dataspec errors."""


class SchemaError(DataspecError):
    """The schema text or structure is invalid."""


class ParseError(DataspecError):
    """A document could not be read from its format (outside the supported profile)."""


class DocumentError(DataspecError):
    """A Python value is not a legal Document, or a Document operation is invalid.

    Raised by the :class:`~dataspec.document.Doc` API when an import or mutation
    would produce something outside the Document model — an unsupported Python
    type, a non-string object key, a cycle — or when an operation doesn't fit the
    node (e.g. ``get`` on a scalar).  The message carries the offending path.
    """


class DetachedNode(DocumentError):
    """A cursor was used after its node was removed from the document.

    Holding a :class:`~dataspec.document.Doc` cursor and then removing that node
    (or a node above it) leaves the cursor pointing at a subtree no longer in the
    document.  Using it raises this instead of silently editing an orphan.
    """


class WriteError(DataspecError):
    """A document cannot be represented losslessly in the target format.

    Raised only in ``strict=True`` mode.  ``.report`` holds the full
    :class:`~dataspec.report.WriteReport` of every adjustment that would have
    been needed, so callers can inspect the structured list, not just the text.
    """

    def __init__(self, message: str, report=None):
        super().__init__(message)
        self.report = report
