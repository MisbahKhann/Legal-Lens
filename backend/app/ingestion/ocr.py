"""
OCR backend manager and native text detection logic for Docling pipeline.
"""

from enum import Enum
from pathlib import Path
from typing import Union, Optional, Tuple
import pypdf

from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    RapidOcrOptions,
    EasyOcrOptions,
    TesseractOcrOptions,
)
from app.ingestion.models import FileType


class OCREngineType(str, Enum):
    RAPIDOCR = "RapidOCR"
    TESSERACT = "Tesseract"
    EASYOCR = "EasyOCR"
    AUTO = "AUTO"


class NativeTextDetector:
    """
    Analyzes documents to determine if native text extraction is usable
    or if OCR is required.
    """

    @staticmethod
    def analyze_pdf_native_text(
        pdf_path_or_bytes: Union[str, Path, bytes], min_char_count_per_page: int = 30
    ) -> Tuple[bool, int]:
        """
        Scans PDF pages to inspect native text density.
        Returns (has_usable_native_text: bool, page_count: int).
        """
        try:
            if isinstance(pdf_path_or_bytes, (str, Path)):
                reader = pypdf.PdfReader(str(pdf_path_or_bytes))
            else:
                import io

                reader = pypdf.PdfReader(io.BytesIO(pdf_path_or_bytes))

            page_count = len(reader.pages)
            if page_count == 0:
                return False, 0

            native_pages = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                cleaned = "".join(text.split())
                if len(cleaned) >= min_char_count_per_page:
                    native_pages += 1

            # If at least half the pages have native text, treat document as having usable native text
            has_native_text = (native_pages > 0) and (native_pages / page_count >= 0.5)
            return has_native_text, page_count
        except Exception:
            # If inspection fails, fallback to requiring OCR
            return False, 0

    @classmethod
    def should_use_ocr(
        self,
        file_type: FileType,
        file_source: Union[str, Path, bytes],
        force_ocr: bool = False,
    ) -> Tuple[bool, bool]:
        """
        Determines (should_run_ocr, has_native_text).
        - DOCX: Native text always available, OCR unnecessary.
        - IMAGES: No native text, OCR required.
        - PDF: Checked via NativeTextDetector. If native text is missing, OCR required.
        - force_ocr: forces OCR execution.
        """
        if force_ocr:
            return True, False

        if file_type == FileType.DOCX:
            return False, True

        if file_type in (
            FileType.IMAGE_PNG,
            FileType.IMAGE_JPEG,
            FileType.IMAGE_TIFF,
            FileType.IMAGE_BMP,
        ):
            return True, False

        if file_type == FileType.PDF:
            has_native, _ = self.analyze_pdf_native_text(file_source)
            should_ocr = not has_native
            return should_ocr, has_native

        return True, False


class OCREngineManager:
    """Manages Docling pipeline options and OCR engine selection."""

    @staticmethod
    def get_pipeline_options(
        use_ocr: bool = True,
        ocr_engine: OCREngineType = OCREngineType.RAPIDOCR,
        do_table_structure: bool = True,
    ) -> PdfPipelineOptions:
        """
        Configures and returns PdfPipelineOptions for Docling converter.
        """
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = use_ocr
        pipeline_options.do_table_structure = do_table_structure

        if use_ocr:
            if ocr_engine == OCREngineType.TESSERACT:
                pipeline_options.ocr_options = TesseractOcrOptions()
            elif ocr_engine == OCREngineType.EASYOCR:
                pipeline_options.ocr_options = EasyOcrOptions()
            else:
                # Default to RapidOCR
                pipeline_options.ocr_options = RapidOcrOptions()

        return pipeline_options
