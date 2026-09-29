"""
Standardized Data Models for Step 2 Legal Document Ingestion & OCR Pipeline.
Preserves page boundaries, bounding boxes, raw text, normalized text, source provenance,
tables, section structures, and processing metadata.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.schema.provenance import Provenance


class FileType(str, Enum):
    """Supported document formats."""
    PDF = "PDF"
    DOCX = "DOCX"
    IMAGE_PNG = "IMAGE_PNG"
    IMAGE_JPEG = "IMAGE_JPEG"
    IMAGE_TIFF = "IMAGE_TIFF"
    IMAGE_BMP = "IMAGE_BMP"
    UNKNOWN = "UNKNOWN"


class ProcessingStatus(str, Enum):
    """Lifecycle status of document processing."""
    PENDING = "PENDING"
    PARSING = "PARSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


class TextBlockType(str, Enum):
    """Types of extracted document text blocks."""
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    LIST_ITEM = "LIST_ITEM"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    CAPTION = "CAPTION"
    TABLE_CELL = "TABLE_CELL"
    CODE = "CODE"
    OTHER = "OTHER"


class BoundingBox(BaseModel):
    """
    Coordinates representing bounding box location on a page.
    Default coordinate system is TOPLEFT origin.
    """
    l: float = Field(..., description="Left offset")
    t: float = Field(..., description="Top offset")
    r: float = Field(..., description="Right offset")
    b: float = Field(..., description="Bottom offset")
    page_number: int = Field(..., ge=1, description="1-indexed page number")
    coord_origin: str = Field(default="TOPLEFT", description="TOPLEFT or BOTTOMLEFT")


class LegalTableCell(BaseModel):
    """Representation of an individual table cell."""
    row_index: int = Field(..., ge=0)
    col_index: int = Field(..., ge=0)
    row_span: int = Field(default=1, ge=1)
    col_span: int = Field(default=1, ge=1)
    text: str = Field(default="")
    is_header: bool = Field(default=False)


class LegalTable(BaseModel):
    """Extracted tabular structure from a document page."""
    table_id: str = Field(..., description="Unique table identifier")
    page_number: int = Field(..., ge=1)
    num_rows: int = Field(..., ge=0)
    num_cols: int = Field(..., ge=0)
    cells: List[LegalTableCell] = Field(default_factory=list)
    csv_content: str = Field(default="")
    markdown_content: str = Field(default="")
    bbox: Optional[BoundingBox] = Field(default=None)
    caption: Optional[str] = Field(default=None)


class LegalTextBlock(BaseModel):
    """Atomic text element preserving raw text, normalized text, page info, and provenance."""
    block_id: str = Field(..., description="Unique block identifier within document")
    block_type: TextBlockType = Field(default=TextBlockType.PARAGRAPH)
    raw_text: str = Field(..., description="Verbatim raw extracted text")
    normalized_text: str = Field(default="", description="Cleaned/normalized text for downstream NLP")
    page_number: int = Field(..., ge=1)
    level: Optional[int] = Field(default=None, description="Heading level (1..6) or list indent level")
    bbox: Optional[BoundingBox] = Field(default=None)
    provenance: Optional[Provenance] = Field(default=None, description="Source provenance trace")


class LegalPage(BaseModel):
    """Per-page container keeping page boundaries and extracted content separate."""
    page_number: int = Field(..., ge=1)
    width: Optional[float] = Field(default=None)
    height: Optional[float] = Field(default=None)
    raw_text: str = Field(default="", description="Aggregated raw text for page")
    normalized_text: str = Field(default="", description="Aggregated normalized text for page")
    has_native_text: bool = Field(default=True)
    ocr_applied: bool = Field(default=False)
    blocks: List[LegalTextBlock] = Field(default_factory=list)
    tables: List[LegalTable] = Field(default_factory=list)


class LegalSection(BaseModel):
    """Hierarchical structural document sections (e.g. Headings, Clauses, Orders)."""
    section_id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title or heading")
    level: int = Field(default=1, ge=1)
    page_start: int = Field(..., ge=1)
    page_end: int = Field(..., ge=1)
    block_ids: List[str] = Field(default_factory=list)
    subsections: List["LegalSection"] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Metadata extracted from file or document header."""
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    creation_date: Optional[str] = Field(default=None)
    language: str = Field(default="en")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class ProcessingMetadata(BaseModel):
    """Processing audit trail and execution status."""
    document_id: str
    filename: str
    file_type: FileType
    page_count: int = 0
    ocr_used: bool = False
    ocr_engine: Optional[str] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_errors: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)


class LegalDocument(BaseModel):
    """
    Standardized internal representation of a legal document for Step 2 Ingestion.
    Consumed by Step 3 (Entity & Relationship Extraction).
    """
    document_id: str
    case_id: str = Field(default="case_default", description="Associated case identifier")
    filename: str
    file_type: FileType
    raw_file_path: Optional[str] = Field(default=None, description="Path to preserved raw uploaded file")
    sha256_hash: str
    file_size_bytes: int
    document_metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    processing_metadata: ProcessingMetadata
    pages: List[LegalPage] = Field(default_factory=list)
    sections: List[LegalSection] = Field(default_factory=list)

    @property
    def full_raw_text(self) -> str:
        """Helper to retrieve raw text across all pages while preserving page breaks."""
        return "\n\n".join(f"--- Page {p.page_number} ---\n{p.raw_text}" for p in self.pages)

    @property
    def full_normalized_text(self) -> str:
        """Helper to retrieve normalized text across all pages."""
        return "\n\n".join(f"--- Page {p.page_number} ---\n{p.normalized_text}" for p in self.pages)


LegalSection.model_rebuild()
