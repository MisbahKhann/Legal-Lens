"""
Step 2 Legal Document Ingestion & OCR Pipeline package.
"""

from app.ingestion.models import (
    LegalDocument,
    LegalPage,
    LegalTextBlock,
    LegalTable,
    LegalTableCell,
    LegalSection,
    FileType,
    ProcessingStatus,
    TextBlockType,
    BoundingBox,
    ProcessingMetadata,
    DocumentMetadata,
)
from app.ingestion.file_handler import FileHandler, FileValidationResult
from app.ingestion.ocr import NativeTextDetector, OCREngineManager, OCREngineType
from app.ingestion.parser import DoclingParser, DoclingParseResult
from app.ingestion.structure import StructureExtractor
from app.ingestion.normalizer import LegalTextNormalizer
from app.ingestion.storage import DocumentStorage
from app.ingestion.pipeline import DocumentIngestionPipeline

__all__ = [
    "LegalDocument",
    "LegalPage",
    "LegalTextBlock",
    "LegalTable",
    "LegalTableCell",
    "LegalSection",
    "FileType",
    "ProcessingStatus",
    "TextBlockType",
    "BoundingBox",
    "ProcessingMetadata",
    "DocumentMetadata",
    "FileHandler",
    "FileValidationResult",
    "NativeTextDetector",
    "OCREngineManager",
    "OCREngineType",
    "DoclingParser",
    "DoclingParseResult",
    "StructureExtractor",
    "LegalTextNormalizer",
    "DocumentStorage",
    "DocumentIngestionPipeline",
]
