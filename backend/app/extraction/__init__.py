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

# Step 4 AI Entity & Relationship Extraction exports
from app.extraction.ai_models import (
    CandidateEntity,
    CandidateRelation,
    AIExtractionResult,
    CombinedExtractionResult
)
from app.extraction.chunker import DocumentChunker, DocumentChunk
from app.extraction.gliner_relex import GLiNERRelexExtractor
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.extraction.ai_evaluator import AIEvaluator, EvaluationReport, EvaluationMetric

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
    "CandidateEntity",
    "CandidateRelation",
    "AIExtractionResult",
    "CombinedExtractionResult",
    "DocumentChunker",
    "DocumentChunk",
    "GLiNERRelexExtractor",
    "AIExtractionPipeline",
    "AIEvaluator",
    "EvaluationReport",
    "EvaluationMetric",
]

