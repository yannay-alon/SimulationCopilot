from pathlib import Path
from core.document_parser.base_parser import BaseParser
from core.document_parser.excel_parser import ExcelParser
from core.document_parser.word_parser import WordParser
from core.document_parser.pdf_parser import PDFParser
from utils.exceptions import FileParsingError

class DocumentParserFactory:
    @staticmethod
    def get_parser(filename: Path, name_column: str | None = None) -> BaseParser:
        match filename.suffix.lower():
            case '.xlsx':
                if name_column is None:
                    raise FileParsingError("name_column is required for Excel interview files")
                return ExcelParser(name_column=name_column)
            case '.docx':
                return WordParser()
            case '.pdf':
                return PDFParser()
            case _:
                raise FileParsingError(f"Unsupported document format: {filename}")