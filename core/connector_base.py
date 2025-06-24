# etl/core/connector_base.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseConnector(ABC):
    """
    An abstract base class that defines the contract for all connectors.

    Each connector plugin must inherit from this class and implement its
    abstract methods. The runner uses this common interface to orchestrate
    the ETL process for any given connector.
    """
    name: str  # Each connector must define its unique string identifier

    @abstractmethod
    def extract(self) -> str:
        """
        --- UPDATED CONTRACT ---
        The extraction phase. This method should orchestrate the capture
        and parsing of raw data from a source.

        Returns:
            A string representing the file path to the directory containing
            the structured raw JSON data artifacts.
        """
        pass

    @abstractmethod
    def transform(self, raw_data_path: str) -> Dict[str, Any]:
        """
        --- UPDATED CONTRACT ---
        The transformation phase. This method takes the raw data produced
        by the extract phase and converts it into the universal schema.

        Args:
            raw_data_path: The file path to the raw data artifacts, as
                           returned by the extract() method.

        Returns:
            A dictionary containing lists of cleaned, validated data objects,
            ready for the load phase (e.g., {'courses': [...], 'programs': [...]}).
        """
        pass

    @abstractmethod
    def load(self, norm: Dict[str, Any]) -> None:
        """
        The load phase. This method takes the cleaned, normalized data from
        the transform phase and loads it into the target database(s).
        
        Args:
            norm: The dictionary of clean data returned by the transform() method.
        """
        pass