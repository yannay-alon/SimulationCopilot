import os
from pathlib import Path

from models.state_models import AppContext

class StorageManager:
    STORAGE_FILE = Path("storage/context_storage.json")

    @classmethod
    def save_context(cls, context: AppContext) -> None:
        try:
            with cls.STORAGE_FILE.open("w", encoding="utf-8") as file:
                file.write(context.model_dump_json(indent=4))
        except Exception as error:
            print(f"Error saving context: {error}")

    @classmethod
    def load_context(cls) -> AppContext:
        if os.path.exists(cls.STORAGE_FILE):
            try:
                with cls.STORAGE_FILE.open("r", encoding="utf-8") as file:
                    data = file.read()
                    return AppContext.model_validate_json(data)
            except Exception as error:
                print(f"Error loading context: {error}")
        return AppContext()