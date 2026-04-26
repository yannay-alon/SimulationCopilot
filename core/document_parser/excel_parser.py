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
        except (pd.errors.ParserError, ValueError) as error:
            raise FileParsingError(f"Failed to parse Excel file: {error}")
        except Exception as error:
            raise FileParsingError(f"Unexpected Excel parsing error: {error}")

        cadets = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            if not row_dict:
                continue
            
            if self.name_column not in row_dict:
                continue

            raw_name = row_dict.pop(self.name_column)
            if pd.isna(raw_name):
                continue

            name = str(raw_name).strip()
            if not name or name.lower() == "nan":
                continue
            
            answers = {
                str(key): str(value).strip()
                for key, value in row_dict.items()
                if not pd.isna(value) and str(value).strip()
            }
            cadets.append(Cadet(name=name, interview_answers=answers))
            
        return cadets