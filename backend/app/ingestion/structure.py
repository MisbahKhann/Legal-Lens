"""
Extracts structural hierarchy, page boundaries, bounding boxes, tables,
and legal provenance from Docling conversion outputs.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import uuid

from docling.datamodel.base_models import DocItemLabel
from docling.datamodel.document import DoclingDocument, TextItem, TableItem, SectionHeaderItem

from app.ingestion.models import (
    LegalDocument,
    LegalPage,
    LegalTextBlock,
    LegalTable,
    LegalTableCell,
    LegalSection,
    BoundingBox,
    TextBlockType,
    FileType,
    ProcessingMetadata,
    ProcessingStatus,
    DocumentMetadata,
)
from app.ingestion.parser import DoclingParseResult
from app.schema.provenance import Provenance, ExtractionMethod


LABEL_MAPPING = {
    DocItemLabel.TITLE: TextBlockType.HEADING,
    DocItemLabel.SECTION_HEADER: TextBlockType.HEADING,
    DocItemLabel.PARAGRAPH: TextBlockType.PARAGRAPH,
    DocItemLabel.TEXT: TextBlockType.PARAGRAPH,
    DocItemLabel.LIST_ITEM: TextBlockType.LIST_ITEM,
    DocItemLabel.PAGE_HEADER: TextBlockType.HEADER,
    DocItemLabel.PAGE_FOOTER: TextBlockType.FOOTER,
    DocItemLabel.CAPTION: TextBlockType.CAPTION,
    DocItemLabel.CODE: TextBlockType.CODE,
}


class StructureExtractor:
    """Extracts pages, blocks, tables, sections, and provenance from parsed documents."""

    def map_label(self, label: DocItemLabel) -> TextBlockType:
        return LABEL_MAPPING.get(label, TextBlockType.OTHER)

    def extract_bbox(self, item: Any, default_page: int) -> Optional[BoundingBox]:
        """Extracts BoundingBox from Docling item provenance if present."""
        if hasattr(item, "prov") and item.prov and len(item.prov) > 0:
            prov = item.prov[0]
            page_no = getattr(prov, "page_no", default_page)
            if hasattr(prov, "bbox") and prov.bbox:
                b = prov.bbox
                # Docling bbox object typically has l, t, r, b or x0, y0, x1, y1
                l = getattr(b, "l", getattr(b, "x0", 0.0))
                t = getattr(b, "t", getattr(b, "y0", 0.0))
                r = getattr(b, "r", getattr(b, "x1", 0.0))
                bottom = getattr(b, "b", getattr(b, "y1", 0.0))
                coord_origin = str(getattr(b, "coord_origin", "TOPLEFT"))
                return BoundingBox(
                    l=float(l),
                    t=float(t),
                    r=float(r),
                    b=float(bottom),
                    page_number=page_no,
                    coord_origin=coord_origin
                )
        return None

    def extract_structure(
        self,
        parse_result: DoclingParseResult,
        document_id: str,
        case_id: str,
        filename: str,
        sha256_hash: str,
        file_size_bytes: int,
        raw_file_path: Optional[str] = None,
        has_native_text: bool = True
    ) -> LegalDocument:
        """
        Translates a Docling parse result into a standardized LegalDocument instance.
        """
        docling_doc: DoclingDocument = parse_result.conversion_result.document
        
        # Determine total page count
        page_count = len(docling_doc.pages) if hasattr(docling_doc, "pages") and docling_doc.pages else 1
        if page_count < 1:
            page_count = 1

        pages_map: Dict[int, LegalPage] = {}
        for p_num in range(1, page_count + 1):
            w, h = None, None
            if hasattr(docling_doc, "pages") and p_num in docling_doc.pages:
                page_obj = docling_doc.pages[p_num]
                if hasattr(page_obj, "size") and page_obj.size:
                    w = float(getattr(page_obj.size, "width", 0.0))
                    h = float(getattr(page_obj.size, "height", 0.0))
            
            pages_map[p_num] = LegalPage(
                page_number=p_num,
                width=w,
                height=h,
                has_native_text=has_native_text,
                ocr_applied=parse_result.ocr_used,
                blocks=[],
                tables=[]
            )

        extracted_blocks: List[LegalTextBlock] = []
        block_counter = 0

        # Iterate over texts / items in docling_doc
        items = list(docling_doc.texts) if hasattr(docling_doc, "texts") else []
        for item in items:
            raw_text = getattr(item, "text", "").strip()
            if not raw_text:
                continue

            block_counter += 1
            block_id = f"blk_{block_counter:04d}"

            label = getattr(item, "label", DocItemLabel.PARAGRAPH)
            block_type = self.map_label(label)

            page_no = 1
            if hasattr(item, "prov") and item.prov and len(item.prov) > 0:
                page_no = getattr(item.prov[0], "page_no", 1)

            if page_no not in pages_map:
                pages_map[page_no] = LegalPage(
                    page_number=page_no,
                    has_native_text=has_native_text,
                    ocr_applied=parse_result.ocr_used
                )

            bbox = self.extract_bbox(item, page_no)
            heading_level = getattr(item, "level", None) if block_type == TextBlockType.HEADING else None

            # Build provenance
            prov_obj = Provenance(
                case_id=case_id,
                source_document_id=document_id,
                source_page=page_no,
                source_text=raw_text[:500],  # sample quote
                extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                created_by="ingestion_pipeline"
            )

            block = LegalTextBlock(
                block_id=block_id,
                block_type=block_type,
                raw_text=raw_text,
                normalized_text="",  # Will be populated by normalizer step
                page_number=page_no,
                level=heading_level,
                bbox=bbox,
                provenance=prov_obj
            )

            extracted_blocks.append(block)
            pages_map[page_no].blocks.append(block)

        # Iterate over tables in docling_doc
        table_counter = 0
        tables = list(docling_doc.tables) if hasattr(docling_doc, "tables") else []
        for tbl in tables:
            table_counter += 1
            table_id = f"tbl_{table_counter:03d}"

            page_no = 1
            if hasattr(tbl, "prov") and tbl.prov and len(tbl.prov) > 0:
                page_no = getattr(tbl.prov[0], "page_no", 1)

            if page_no not in pages_map:
                pages_map[page_no] = LegalPage(page_number=page_no)

            bbox = self.extract_bbox(tbl, page_no)

            cells: List[LegalTableCell] = []
            num_rows = getattr(tbl.data, "num_rows", 0) if hasattr(tbl, "data") else 0
            num_cols = getattr(tbl.data, "num_cols", 0) if hasattr(tbl, "data") else 0

            if hasattr(tbl, "data") and hasattr(tbl.data, "table_cells"):
                for c in tbl.data.table_cells:
                    cells.append(
                        LegalTableCell(
                            row_index=getattr(c, "start_row_offset_idx", 0),
                            col_index=getattr(c, "start_col_offset_idx", 0),
                            row_span=getattr(c, "row_span", 1),
                            col_span=getattr(c, "col_span", 1),
                            text=getattr(c, "text", "").strip(),
                            is_header=bool(getattr(c, "column_header", False) or getattr(c, "row_header", False))
                        )
                    )

            md_content = ""
            csv_content = ""
            try:
                if hasattr(tbl, "export_to_markdown"):
                    md_content = tbl.export_to_markdown()
                if hasattr(tbl, "export_to_csv"):
                    csv_content = tbl.export_to_csv()
            except Exception:
                pass

            legal_table = LegalTable(
                table_id=table_id,
                page_number=page_no,
                num_rows=num_rows,
                num_cols=num_cols,
                cells=cells,
                csv_content=csv_content,
                markdown_content=md_content,
                bbox=bbox,
                caption=getattr(tbl, "caption", None)
            )
            pages_map[page_no].tables.append(legal_table)

        # Synthesize raw text per page
        for p_num in sorted(pages_map.keys()):
            p = pages_map[p_num]
            block_texts = [b.raw_text for b in p.blocks]
            table_texts = [t.markdown_content for t in p.tables if t.markdown_content]
            p.raw_text = "\n\n".join(block_texts + table_texts)

        # Build Section Hierarchy
        sections = self.build_sections(extracted_blocks)

        # Assemble processing metadata
        proc_metadata = ProcessingMetadata(
            document_id=document_id,
            filename=filename,
            file_type=parse_result.file_type,
            page_count=len(pages_map),
            ocr_used=parse_result.ocr_used,
            ocr_engine=parse_result.ocr_engine,
            processing_status=ProcessingStatus.PARSING,
            started_at=datetime.now(timezone.utc)
        )

        doc_metadata = DocumentMetadata(
            title=getattr(docling_doc, "name", filename),
            language="en"
        )

        sorted_pages = [pages_map[k] for k in sorted(pages_map.keys())]

        return LegalDocument(
            document_id=document_id,
            case_id=case_id,
            filename=filename,
            file_type=parse_result.file_type,
            raw_file_path=raw_file_path,
            sha256_hash=sha256_hash,
            file_size_bytes=file_size_bytes,
            document_metadata=doc_metadata,
            processing_metadata=proc_metadata,
            pages=sorted_pages,
            sections=sections
        )

    def build_sections(self, blocks: List[LegalTextBlock]) -> List[LegalSection]:
        """Groups text blocks into structural sections based on HEADING tags."""
        sections: List[LegalSection] = []
        current_section: Optional[LegalSection] = None
        sec_counter = 0

        for block in blocks:
            if block.block_type == TextBlockType.HEADING:
                if current_section:
                    sections.append(current_section)
                
                sec_counter += 1
                current_section = LegalSection(
                    section_id=f"sec_{sec_counter:03d}",
                    title=block.raw_text,
                    level=block.level or 1,
                    page_start=block.page_number,
                    page_end=block.page_number,
                    block_ids=[block.block_id]
                )
            else:
                if not current_section:
                    sec_counter += 1
                    current_section = LegalSection(
                        section_id=f"sec_{sec_counter:03d}",
                        title="Document Body",
                        level=1,
                        page_start=block.page_number,
                        page_end=block.page_number,
                        block_ids=[]
                    )
                current_section.block_ids.append(block.block_id)
                current_section.page_end = max(current_section.page_end, block.page_number)

        if current_section:
            sections.append(current_section)

        return sections
