class NonTextPDFError(Exception):
    """Raised when a PDF file does not contain extractable text (e.g., scanned image)."""
    pass

class FileParsingError(Exception):
    """Raised when there is a general error parsing a file."""
    pass
