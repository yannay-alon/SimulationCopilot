from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic

OutputType = TypeVar("OutputType")

class BaseParser(Generic[OutputType], ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes) -> OutputType:
        """Parses the given file bytes and returns the extracted data."""
        pass
