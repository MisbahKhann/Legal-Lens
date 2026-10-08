"""
File handling, MIME/magic validation, integrity checks, and raw storage for uploaded legal documents.
"""

import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple, BinaryIO, Union
from pydantic import BaseModel, Field

from app.ingestion.models import FileType

MAGIC_SIGNATURES = {
    FileType.PDF: [b"%PDF-"],
    FileType.DOCX: [b"PK\x03\x04"],
    FileType.IMAGE_PNG: [b"\x89PNG\r\n\x1a\n"],
    FileType.IMAGE_JPEG: [b"\xff\xd8\xff"],
    FileType.IMAGE_TIFF: [b"II*\x00", b"MM\x00*"],
    FileType.IMAGE_BMP: [b"BM"],
}

EXTENSION_MAP = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".png": FileType.IMAGE_PNG,
    ".jpg": FileType.IMAGE_JPEG,
    ".jpeg": FileType.IMAGE_JPEG,
    ".tiff": FileType.IMAGE_TIFF,
    ".tif": FileType.IMAGE_TIFF,
    ".bmp": FileType.IMAGE_BMP,
}


class FileValidationResult(BaseModel):
    is_valid: bool
    document_id: str
    file_type: FileType
    filename: str
    file_size_bytes: int
    sha256_hash: str
    error_message: Optional[str] = None


class FileHandler:
    """Handles upload validation, format identification, integrity hashing, and file saving."""

    def __init__(self, max_file_size_bytes: int = 150 * 1024 * 1024):
        self.max_file_size_bytes = max_file_size_bytes

    def detect_file_type(self, header: bytes, filename: str) -> FileType:
        """Identifies file type using magic bytes with extension fallback."""
        for ftype, signatures in MAGIC_SIGNATURES.items():
            for sig in signatures:
                if header.startswith(sig):
                    return ftype

        ext = Path(filename).suffix.lower()
        return EXTENSION_MAP.get(ext, FileType.UNKNOWN)

    def validate_file(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        filename: Optional[str] = None,
        custom_doc_id: Optional[str] = None,
    ) -> Tuple[FileValidationResult, bytes]:
        """
        Validates the input document source. Returns validation result and raw bytes.
        """
        doc_id = custom_doc_id or str(uuid.uuid4())
        raw_bytes: bytes

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                return (
                    FileValidationResult(
                        is_valid=False,
                        document_id=doc_id,
                        file_type=FileType.UNKNOWN,
                        filename=filename or path.name,
                        file_size_bytes=0,
                        sha256_hash="",
                        error_message=f"File not found: {source}",
                    ),
                    b"",
                )
            resolved_filename = filename or path.name
            with open(path, "rb") as f:
                raw_bytes = f.read()
        elif isinstance(source, bytes):
            resolved_filename = filename or f"upload_{doc_id}.bin"
            raw_bytes = source
        elif hasattr(source, "read"):
            resolved_filename = filename or f"upload_{doc_id}.bin"
            raw_bytes = source.read()
        else:
            return (
                FileValidationResult(
                    is_valid=False,
                    document_id=doc_id,
                    file_type=FileType.UNKNOWN,
                    filename=filename or "unknown",
                    file_size_bytes=0,
                    sha256_hash="",
                    error_message="Unsupported input source type.",
                ),
                b"",
            )

        size = len(raw_bytes)
        if size == 0:
            return (
                FileValidationResult(
                    is_valid=False,
                    document_id=doc_id,
                    file_type=FileType.UNKNOWN,
                    filename=resolved_filename,
                    file_size_bytes=0,
                    sha256_hash="",
                    error_message="Uploaded file is empty (0 bytes).",
                ),
                b"",
            )

        if size > self.max_file_size_bytes:
            return (
                FileValidationResult(
                    is_valid=False,
                    document_id=doc_id,
                    file_type=FileType.UNKNOWN,
                    filename=resolved_filename,
                    file_size_bytes=size,
                    sha256_hash="",
                    error_message=f"File size ({size} bytes) exceeds limit of {self.max_file_size_bytes} bytes.",
                ),
                b"",
            )

        file_type = self.detect_file_type(raw_bytes[:32], resolved_filename)
        if file_type == FileType.UNKNOWN:
            return (
                FileValidationResult(
                    is_valid=False,
                    document_id=doc_id,
                    file_type=FileType.UNKNOWN,
                    filename=resolved_filename,
                    file_size_bytes=size,
                    sha256_hash="",
                    error_message=f"Unsupported file format for file: {resolved_filename}",
                ),
                b"",
            )

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        return (
            FileValidationResult(
                is_valid=True,
                document_id=doc_id,
                file_type=file_type,
                filename=resolved_filename,
                file_size_bytes=size,
                sha256_hash=sha256_hash,
            ),
            raw_bytes,
        )

    def save_raw_file(
        self,
        raw_bytes: bytes,
        document_id: str,
        filename: str,
        storage_dir: Union[str, Path],
    ) -> Path:
        """
        Saves original uploaded binary file to storage without modification.
        """
        target_dir = Path(storage_dir) / document_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        with open(file_path, "wb") as f:
            f.write(raw_bytes)
        return file_path
