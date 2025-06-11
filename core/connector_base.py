from abc import ABC, abstractmethod

class BaseConnector(ABC):
    name: str

    @abstractmethod
    def extract(self) -> dict:
        """Dump raw JSON or HTML."""
        ...

    @abstractmethod
    def transform(self, raw: dict) -> dict:
        """Normalize & validate against schemas/…"""
        ...

    @abstractmethod
    def load(self, norm: dict) -> None:
        """Insert into DB (SCD-2 for programs, upsert for courses)."""
        ...
