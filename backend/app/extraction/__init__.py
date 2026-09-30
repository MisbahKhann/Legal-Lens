"""
Step 3: Deterministic Legal Information Extraction Package.
"""

from app.extraction.models import ExtractedCandidateEntity, DeterministicExtractionResult
from app.extraction.base import BaseExtractor
from app.extraction.case_citation import CaseCitationExtractor
from app.extraction.statutory import StatutoryCitationExtractor
from app.extraction.date import DateExtractor
from app.extraction.docket import DocketExtractor
from app.extraction.section import SectionExtractor
from app.extraction.exhibit import ExhibitExtractor
from app.extraction.filing_type import FilingTypeExtractor
from app.extraction.court import CourtExtractor
from app.extraction.pipeline import DeterministicExtractionPipeline

__all__ = [
    "ExtractedCandidateEntity",
    "DeterministicExtractionResult",
    "BaseExtractor",
    "CaseCitationExtractor",
    "StatutoryCitationExtractor",
    "DateExtractor",
    "DocketExtractor",
    "SectionExtractor",
    "ExhibitExtractor",
    "FilingTypeExtractor",
    "CourtExtractor",
    "DeterministicExtractionPipeline",
]
