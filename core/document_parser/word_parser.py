import docx
from io import BytesIO
from core.document_parser.base_parser import BaseParser
from utils.exceptions import FileParsingError

class WordParser(BaseParser[str]):
    def parse(self, file_bytes: bytes) -> str:
        try:
            document = docx.Document(BytesIO(file_bytes))
        except Exception as error:
            raise FileParsingError(f"Failed to parse DOCX file: {error}")

        full_text = "\n".join([paragraph.text for paragraph in document.paragraphs])
        return full_text.strip()
