"""
Document storage layer managing preserved raw upload binaries and parsed
JSON LegalDocument representations.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from app.ingestion.models import LegalDocument


class DocumentStorage:
    """Manages raw document storage and JSON serialization/deserialization for LegalDocument."""

    def __init__(self, base_dir: Union[str, Path] = "backend/storage"):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw"
        self.parsed_dir = self.base_dir / "parsed"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)

    def get_raw_storage_dir(self) -> Path:
        return self.raw_dir

    def get_parsed_storage_dir(self) -> Path:
        return self.parsed_dir

    def save_document(self, document: LegalDocument) -> Path:
        """Serializes and saves a LegalDocument instance as JSON."""
        file_path = self.parsed_dir / f"{document.document_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(document.model_dump_json(indent=2))
        return file_path

    def load_document(self, document_id: str) -> Optional[LegalDocument]:
        """Loads and deserializes a LegalDocument by document_id."""
        file_path = self.parsed_dir / f"{document_id}.json"
        if not file_path.is_file():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LegalDocument.model_validate(data)

    def has_document(self, document_id: str) -> bool:
        """Checks whether a parsed LegalDocument exists in storage."""
        return (self.parsed_dir / f"{document_id}.json").is_file()

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists summaries of all parsed documents currently stored."""
        documents = []
        for file_path in self.parsed_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                documents.append(
                    {
                        "document_id": data.get("document_id"),
                        "filename": data.get("filename"),
                        "file_type": data.get("file_type"),
                        "sha256_hash": data.get("sha256_hash"),
                        "page_count": len(data.get("pages", [])),
                        "created_at": data.get("processing_metadata", {}).get(
                            "started_at"
                        ),
                    }
                )
            except Exception:
                continue
        return documents
