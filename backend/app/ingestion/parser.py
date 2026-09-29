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
        self,
        use_ocr: bool = True,
        ocr_engine: OCREngineType = OCREngineType.RAPIDOCR
    ) -> DocumentConverter:
        """Configures a DocumentConverter instance with tailored pipeline options."""
        pdf_options = OCREngineManager.get_pipeline_options(
            use_ocr=use_ocr,
            ocr_engine=ocr_engine,
            do_table_structure=True
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
        ocr_engine: OCREngineType = OCREngineType.RAPIDOCR
    ) -> DoclingParseResult:
        """
        Parses a document file using Docling.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Target document not found at {path}")

        converter = self.create_converter(use_ocr=use_ocr, ocr_engine=ocr_engine)
        conversion_result = converter.convert(str(path))

        actual_ocr_used = use_ocr if file_type in (FileType.PDF, FileType.IMAGE_PNG, FileType.IMAGE_JPEG, FileType.IMAGE_TIFF, FileType.IMAGE_BMP) else False
        engine_name = ocr_engine.value if actual_ocr_used else None

        return DoclingParseResult(
            conversion_result=conversion_result,
            file_type=file_type,
            ocr_used=actual_ocr_used,
            ocr_engine=engine_name
        )
