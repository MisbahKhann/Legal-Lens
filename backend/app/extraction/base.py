"""
Base Extractor abstract interface for Step 3 deterministic extraction modules.
"""

from abc import ABC, abstractmethod
from typing import List

from app.ingestion.models import LegalDocument
from app.extraction.models import ExtractedCandidateEntity


class BaseExtractor(ABC):
    """
    Abstract base interface for all deterministic legal information extractors.
    Subclasses implement extraction logic for specific legal entity categories.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns unique identifier/name for this extractor."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Returns target extraction category (e.g. case_citation, date, court_name)."""
        pass

    @abstractmethod
    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        """
        Executes deterministic extraction on a standardized LegalDocument.

        Args:
            document: LegalDocument produced by Step 2 ingestion pipeline.

        Returns:
            List of candidate entities extracted from the document.
        """
        pass
