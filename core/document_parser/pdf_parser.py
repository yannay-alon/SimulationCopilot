import fitz  # PyMuPDF

from core.document_parser.base_parser import BaseParser
from utils.exceptions import NonTextPDFError, FileParsingError


class PDFParser(BaseParser[str]):
    def parse(self, file_bytes: bytes) -> str:
        try:
            document = fitz.Document(filetype="pdf", stream=file_bytes)
        except Exception as error:
            raise FileParsingError(f"Failed to parse PDF file: {error}")

        text_parts = [page.get_text() for page in document]
        full_text = "\n".join(text_parts).strip()

        if len(full_text) < 50 and len(document) > 0:
            raise NonTextPDFError("The uploaded PDF appears to be scanned or contains no extractable text.")

        return full_text
