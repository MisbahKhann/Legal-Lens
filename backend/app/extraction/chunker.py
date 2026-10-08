"""
Document Chunker module for Step 4 AI Extraction pipeline.
Splits LegalDocument into structured chunks based on pages, sections, and paragraphs
while preserving document ID, page numbers, section information, original text, and character offsets.
"""

from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field

from app.ingestion.models import LegalDocument, LegalPage, LegalTextBlock, LegalSection


class DocumentChunk(BaseModel):
    """
    Representation of a localized text chunk from a LegalDocument.
    Preserves exact document ID, page number, section metadata, and character offsets.
    """

    chunk_id: str = Field(..., description="Unique chunk identifier.")
    document_id: str = Field(..., description="Source legal document ID.")
    case_id: Optional[str] = Field(default=None, description="Associated case ID.")
    page_number: int = Field(
        ..., ge=1, description="1-indexed page number of the chunk."
    )
    section_id: Optional[str] = Field(
        default=None, description="Section ID or heading if known."
    )
    section_title: Optional[str] = Field(
        default=None, description="Section title if known."
    )
    text: str = Field(..., description="Chunk text content for model inference.")
    start_char_offset: int = Field(
        ..., ge=0, description="Start character offset within page or source text."
    )
    end_char_offset: int = Field(
        ..., ge=0, description="End character offset within page or source text."
    )
    block_ids: List[str] = Field(
        default_factory=list, description="IDs of LegalTextBlocks contained in chunk."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional chunking metadata."
    )


class DocumentChunker:
    """
    Splits LegalDocument into optimal semantic chunks (pages/sections/paragraphs)
    for model inference without losing spatial or textual provenance.
    """

    def __init__(
        self,
        max_chunk_chars: int = 1500,
        min_chunk_chars: int = 100,
        overlap_chars: int = 0,
    ):
        """
        Args:
            max_chunk_chars: Maximum recommended character length per chunk (default 1500).
            min_chunk_chars: Minimum character length below which small blocks are merged (default 100).
            overlap_chars: Overlap character length between chunks (default 0 to avoid duplication).
        """
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_document(self, document: LegalDocument) -> List[DocumentChunk]:
        """
        Main entrypoint: Chunks an entire LegalDocument into page-aware DocumentChunks.

        Args:
            document: Processed LegalDocument from Step 2.

        Returns:
            List of DocumentChunk instances.
        """
        chunks: List[DocumentChunk] = []

        # Map block_id to section information if sections exist
        block_section_map: Dict[str, LegalSection] = {}
        self._map_block_sections(document.sections, block_section_map)

        for page in document.pages:
            page_chunks = self.chunk_page(
                document_id=document.document_id,
                case_id=document.case_id,
                page=page,
                block_section_map=block_section_map,
            )
            chunks.extend(page_chunks)

        return chunks

    def chunk_page(
        self,
        document_id: str,
        case_id: Optional[str],
        page: LegalPage,
        block_section_map: Optional[Dict[str, LegalSection]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk a single LegalPage into DocumentChunks based on text blocks or raw text.
        """
        block_section_map = block_section_map or {}
        chunks: List[DocumentChunk] = []

        # If page has structured blocks, combine blocks up to max_chunk_chars
        if page.blocks:
            curr_text_parts: List[str] = []
            curr_block_ids: List[str] = []
            curr_section_id: Optional[str] = None
            curr_section_title: Optional[str] = None
            chunk_idx = 0
            page_char_counter = 0

            for block in page.blocks:
                block_text = block.normalized_text.strip() or block.raw_text.strip()
                if not block_text:
                    continue

                section = block_section_map.get(block.block_id)
                sec_id = section.section_id if section else None
                sec_title = section.title if section else None

                # Check if current accumulated text + new block exceeds max_chunk_chars
                curr_length = sum(len(p) for p in curr_text_parts) + len(
                    curr_text_parts
                )
                if (
                    curr_length + len(block_text) > self.max_chunk_chars
                    and curr_text_parts
                ):
                    # Flush current chunk
                    combined_text = "\n".join(curr_text_parts)
                    start_offset = page_char_counter - len(combined_text)
                    end_offset = page_char_counter
                    chunk_id = f"chunk_{document_id}_p{page.page_number}_{chunk_idx}"

                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            case_id=case_id,
                            page_number=page.page_number,
                            section_id=curr_section_id,
                            section_title=curr_section_title,
                            text=combined_text,
                            start_char_offset=max(0, start_offset),
                            end_char_offset=start_offset + len(combined_text),
                            block_ids=list(curr_block_ids),
                        )
                    )
                    chunk_idx += 1
                    curr_text_parts = []
                    curr_block_ids = []

                curr_text_parts.append(block_text)
                curr_block_ids.append(block.block_id)
                page_char_counter += len(block_text) + 1
                if sec_id:
                    curr_section_id = sec_id
                    curr_section_title = sec_title

            # Flush remaining accumulated text
            if curr_text_parts:
                combined_text = "\n".join(curr_text_parts)
                start_offset = page_char_counter - len(combined_text)
                chunk_id = f"chunk_{document_id}_p{page.page_number}_{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        case_id=case_id,
                        page_number=page.page_number,
                        section_id=curr_section_id,
                        section_title=curr_section_title,
                        text=combined_text,
                        start_char_offset=max(0, start_offset),
                        end_char_offset=max(0, start_offset) + len(combined_text),
                        block_ids=list(curr_block_ids),
                    )
                )

        else:
            # Fallback for page with only raw_text or normalized_text
            text = page.normalized_text.strip() or page.raw_text.strip()
            if not text:
                return []

            paragraphs = text.split("\n\n")
            chunk_idx = 0
            current_offset = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_start = text.find(para, current_offset)
                if para_start == -1:
                    para_start = current_offset
                para_end = para_start + len(para)
                current_offset = para_end

                chunk_id = f"chunk_{document_id}_p{page.page_number}_{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        case_id=case_id,
                        page_number=page.page_number,
                        section_id=None,
                        section_title=None,
                        text=para,
                        start_char_offset=para_start,
                        end_char_offset=para_end,
                        block_ids=[],
                    )
                )
                chunk_idx += 1

        return chunks

    def _map_block_sections(
        self, sections: List[LegalSection], mapping: Dict[str, LegalSection]
    ) -> None:
        """Recursively populate block_id to LegalSection mapping."""
        for sec in sections:
            for b_id in sec.block_ids:
                mapping[b_id] = sec
            if sec.subsections:
                self._map_block_sections(sec.subsections, mapping)
