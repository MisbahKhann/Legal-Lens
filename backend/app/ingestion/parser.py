"""
Docling integration layer for parsing PDF, DOCX, and Image legal documents.
"""

from pathlib import Path
from typing import Union, Optional, Any
from pydantic import BaseModel, ConfigDict

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
    ImageFormatOption,
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult

from app.ingestion.models import FileType
from app.ingestion.ocr import OCREngineManager, OCREngineType

import logging
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level converter cache — keyed by (use_ocr, ocr_engine).
# Docling loads several internal ML models (layout, table structure, OCR)
# on first conversion. Re-creating DocumentConverter on every upload is the
# second major contributor to the 30-minute processing wall.
# ---------------------------------------------------------------------------
_converter_cache: dict = {}
_converter_lock = threading.Lock()


def get_cached_converter(
    use_ocr: bool = True,
    ocr_engine: OCREngineType = OCREngineType.RAPIDOCR,
) -> DocumentConverter:
    """
    Returns a cached DocumentConverter for the given (use_ocr, ocr_engine) pair.
    Thread-safe: the first call for each configuration builds and caches the converter.
    """
    key = (use_ocr, ocr_engine)
    if key in _converter_cache:
        return _converter_cache[key]
    with _converter_lock:
        if key not in _converter_cache:
            logger.info(
                "Building Docling DocumentConverter (use_ocr=%s, engine=%s).",
                use_ocr,
                ocr_engine,
            )
            pdf_options = OCREngineManager.get_pipeline_options(
                use_ocr=use_ocr, ocr_engine=ocr_engine, do_table_structure=True
            )
            format_options = {
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pdf_options),
                InputFormat.DOCX: WordFormatOption(),
            }
            _converter_cache[key] = DocumentConverter(format_options=format_options)
        return _converter_cache[key]


class DoclingParseResult(BaseModel):
    """Container holding the raw Docling conversion result and parameters."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    conversion_result: ConversionResult
    file_type: FileType
    ocr_used: bool
    ocr_engine: Optional[str]


class DoclingParser:
    """Wrapper around Docling's DocumentConverter."""

    def __init__(self):
        pass

    def create_converter(
        self, use_ocr: bool = True, ocr_engine: OCREngineType = OCREngineType.RAPIDOCR
    ) -> DocumentConverter:
        """Configures a DocumentConverter instance with tailored pipeline options."""
        pdf_options = OCREngineManager.get_pipeline_options(
            use_ocr=use_ocr, ocr_engine=ocr_engine, do_table_structure=True
        )

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pdf_options),
            InputFormat.DOCX: WordFormatOption(),
        }

        return DocumentConverter(format_options=format_options)

    def parse(
        self,
        file_path: Union[str, Path],
        file_type: FileType,
        use_ocr: bool = True,
        ocr_engine: OCREngineType = OCREngineType.RAPIDOCR,
    ) -> DoclingParseResult:
        """
        Parses a document file using Docling.
        Uses a module-level cached DocumentConverter to avoid reloading Docling
        internal models (layout detection, table structure, OCR) on every call.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Target document not found at {path}")

        # Use cached converter — avoids 2-5 minute model reload on every upload.
        converter = get_cached_converter(use_ocr=use_ocr, ocr_engine=ocr_engine)
        conversion_result = converter.convert(str(path))

        actual_ocr_used = (
            use_ocr
            if file_type
            in (
                FileType.PDF,
                FileType.IMAGE_PNG,
                FileType.IMAGE_JPEG,
                FileType.IMAGE_TIFF,
                FileType.IMAGE_BMP,
            )
            else False
        )
        engine_name = ocr_engine.value if actual_ocr_used else None

        return DoclingParseResult(
            conversion_result=conversion_result,
            file_type=file_type,
            ocr_used=actual_ocr_used,
            ocr_engine=engine_name,
        )
