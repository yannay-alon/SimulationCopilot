import pandas as pd
from io import BytesIO
from core.document_parser.base_parser import BaseParser
from models.domain_models import Cadet
from utils.exceptions import FileParsingError


class ExcelParser(BaseParser[list[Cadet]]):
    def __init__(self, name_column: str):
        self.name_column = name_column

    def parse(self, file_bytes: bytes) -> list[Cadet]:
        try:
            df = pd.read_excel(BytesIO(file_bytes))
        except pd.errors.ParserError as error:
            raise FileParsingError(f"Failed to parse Excel file: {error}")

        cadets = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            if not row_dict:
                continue
            
            if self.name_column not in row_dict:
                 continue

            name = str(row_dict.pop(self.name_column)).strip()
            if not name:
                continue
            
            answers = {str(k): str(v).strip() for k, v in row_dict.items()}
            cadets.append(Cadet(name=name, interview_answers=answers))
            
        return cadets