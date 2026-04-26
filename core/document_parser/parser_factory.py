from pathlib import Path
from core.document_parser.base_parser import BaseParser
from core.document_parser.excel_parser import ExcelParser
from core.document_parser.word_parser import WordParser
from core.document_parser.pdf_parser import PDFParser
from utils.exceptions import FileParsingError

class DocumentParserFactory:
    @staticmethod
    def get_parser(filename: Path, *args, **kwargs) -> BaseParser:
        match filename.suffix:
            case '.xlsx':
                return ExcelParser(*args, **kwargs)
            case '.docx':
                return WordParser(*args, **kwargs)
            case '.pdf':
                return PDFParser(*args, **kwargs)
            case _:
                raise FileParsingError(f"Unsupported document format: {filename}")