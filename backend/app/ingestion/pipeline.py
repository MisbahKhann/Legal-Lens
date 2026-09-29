"""
Unified Step 2 Document Ingestion & OCR Pipeline Orchestrator.
Coordinates file handling, format validation, native text detection,
Docling parsing, structural extraction, legal text normalization, and storage.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Optional, BinaryIO
import traceback

from app.ingestion.file_handler import FileHandler, FileValidationResult
from app.ingestion.ocr import NativeTextDetector, OCREngineType
from app.ingestion.parser import DoclingParser, DoclingParseResult
from app.ingestion.structure import StructureExtractor
from app.ingestion.normalizer import LegalTextNormalizer
from app.ingestion.storage import DocumentStorage
from app.ingestion.models import LegalDocument, ProcessingStatus, FileType


class DocumentIngestionPipeline:
    """
    Step 2 Core Ingestion & OCR Pipeline for Legal Lens Knowledge Graph System.
    Converts legal documents into standardized LegalDocument objects ready for Step 3.
    """

    def __init__(self, base_storage_dir: Union[str, Path] = "backend/storage"):
        self.file_handler = FileHandler()
        self.docling_parser = DoclingParser()
        self.structure_extractor = StructureExtractor()
        self.normalizer = LegalTextNormalizer()
        self.storage = DocumentStorage(base_dir=base_storage_dir)

    def process_document(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        filename: Optional[str] = None,
        case_id: str = "default_case",
        custom_doc_id: Optional[str] = None,
        force_ocr: bool = False,
        ocr_engine: OCREngineType = OCREngineType.RAPIDOCR
    ) -> LegalDocument:
        """
        Main entry point for document ingestion. Processes a source file and returns a LegalDocument.
        """
        # Step 1: File Detection & Integrity Validation
        val_result, raw_bytes = self.file_handler.validate_file(
            source=source,
            filename=filename,
            custom_doc_id=custom_doc_id
        )

        if not val_result.is_valid:
            raise ValueError(f"File validation failed: {val_result.error_message}")

        document_id = val_result.document_id
        resolved_filename = val_result.filename

        # Step 2: Preserve original binary file in raw storage
        raw_file_path = self.file_handler.save_raw_file(
            raw_bytes=raw_bytes,
            document_id=document_id,
            filename=resolved_filename,
            storage_dir=self.storage.get_raw_storage_dir()
        )

        # Step 3: Determine Native Text vs OCR Necessity
        should_ocr, has_native = NativeTextDetector.should_use_ocr(
            file_type=val_result.file_type,
            file_source=raw_file_path,
            force_ocr=force_ocr
        )

        try:
            # Step 4: Parse Document with Docling Converter
            parse_result: DoclingParseResult = self.docling_parser.parse(
                file_path=raw_file_path,
                file_type=val_result.file_type,
                use_ocr=should_ocr,
                ocr_engine=ocr_engine
            )

            # Step 5: Structural & Provenance Extraction
            doc: LegalDocument = self.structure_extractor.extract_structure(
                parse_result=parse_result,
                document_id=document_id,
                case_id=case_id,
                filename=resolved_filename,
                sha256_hash=val_result.sha256_hash,
                file_size_bytes=val_result.file_size_bytes,
                raw_file_path=str(raw_file_path),
                has_native_text=has_native
            )

            # Step 6: Legal Text Normalization (preserving raw text)
            doc = self.normalizer.normalize_document(doc)

            # Step 7: Update Metadata Status & Timestamps
            doc.processing_metadata.processing_status = ProcessingStatus.COMPLETED
            doc.processing_metadata.completed_at = datetime.now(timezone.utc)

            # Step 8: Persist Parsed JSON Representation
            self.storage.save_document(doc)

            return doc

        except Exception as e:
            err_msg = f"Ingestion error: {str(e)}\n{traceback.format_exc()}"
            # Log failure state and raise
            raise RuntimeError(f"Failed to process document {resolved_filename}: {str(e)}") from e
