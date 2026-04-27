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

        # Ensure order is preserved from pandas reading
        original_columns = list(df.columns)
        if self.name_column in original_columns:
            original_columns.remove(self.name_column)

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
            
            # Maintain the original order defined by the excel file
            answers = {}
            for col in original_columns:
                if col in row_dict:
                    val = row_dict[col]
                    if not pd.isna(val) and str(val).strip():
                        answers[str(col)] = str(val).strip()

            cadets.append(Cadet(name=name, interview_answers=answers))
            
        return cadets