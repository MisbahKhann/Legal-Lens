"""
Deterministic Extraction Pipeline Orchestrator (Step 3).
Executes all candidate extractors in a unified, modular pass over a LegalDocument.
"""

from typing import List, Optional
from collections import Counter

from app.ingestion.models import LegalDocument
from app.extraction.base import BaseExtractor
from app.extraction.models import (
    ExtractedCandidateEntity,
    DeterministicExtractionResult,
)
from app.extraction.case_citation import CaseCitationExtractor
from app.extraction.statutory import StatutoryCitationExtractor
from app.extraction.date import DateExtractor
from app.extraction.docket import DocketExtractor
from app.extraction.section import SectionExtractor
from app.extraction.exhibit import ExhibitExtractor
from app.extraction.filing_type import FilingTypeExtractor
from app.extraction.court import CourtExtractor


class DeterministicExtractionPipeline:
    """
    Main orchestrator for Step 3 Deterministic Legal Information Extraction.
    Combines rule-based candidate extractors without invoking LLMs or GLiNER-Relex.
    """

    def __init__(self, extractors: Optional[List[BaseExtractor]] = None):
        if extractors is not None:
            self.extractors = extractors
        else:
            self.extractors = [
                CaseCitationExtractor(),
                StatutoryCitationExtractor(),
                DateExtractor(),
                DocketExtractor(),
                SectionExtractor(),
                ExhibitExtractor(),
                FilingTypeExtractor(),
                CourtExtractor(),
            ]

    def extract_candidates(
        self, document: LegalDocument
    ) -> DeterministicExtractionResult:
        """
        Executes all registered deterministic extractors on the given LegalDocument.

        Args:
            document: LegalDocument produced by Step 2 Ingestion.

        Returns:
            DeterministicExtractionResult containing structured collection of candidate entities.
        """
        all_candidates: List[ExtractedCandidateEntity] = []

        for extractor in self.extractors:
            try:
                extracted = extractor.extract(document)
                all_candidates.extend(extracted)
            except Exception as exc:
                # Conservative error handling per extractor
                print(f"Warning: Extractor '{extractor.name}' failed with error: {exc}")

        # Summary counts per category
        category_counts = dict(Counter(c.category for c in all_candidates))

        return DeterministicExtractionResult(
            document_id=document.document_id,
            case_id=document.case_id,
            candidates=all_candidates,
            summary_counts=category_counts,
        )
