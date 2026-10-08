"""
End-to-End Evaluation Script for Step 4 & 5.
Validates GLiNER-Relex inference and Entity Resolution.
"""

import sys
import logging
from typing import List

from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.resolution.pipeline import EntityResolutionPipeline
import gliner
import transformers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def print_header(title: str):
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python eval_pipeline.py <path_to_legal_document>")
        file_path = "tests/samples/scansmpl.pdf"
    else:
        file_path = sys.argv[1]

    print_header("A. MODEL & ENVIRONMENT")
    print(f"GLiNER version: {gliner.__version__}")
    print(f"Transformers version: {transformers.__version__}")

    print_header(f"B. LOADING DOCUMENT: {file_path}")
    ingestion = DocumentIngestionPipeline(base_storage_dir="storage")
    document = ingestion.process_document(file_path, case_id="eval_case_123")
    print(f"Pages: {len(document.pages)}")

    print_header("C. RUNNING STEP 4: AI EXTRACTION")
    ai_pipeline = AIExtractionPipeline()
    combined_result = ai_pipeline.run_pipeline(document)
    ai_res = combined_result.ai_result

    print(f"Exact Model Used: {ai_res.model_name}")
    print(f"Chunks processed: {ai_res.summary_counts.get('total_chunks', 0)}")
    print(f"Entities extracted: {len(ai_res.entities)}")
    print(f"Relations extracted (Valid): {len(ai_res.relations)}")
    print(f"Relations extracted (Rejected): {len(ai_res.rejected_relations)}")

    print_header("D. STEP 4 PROVENANCE & QUALITY SAMPLES")
    print("\n[Sample Entities]")
    for e in ai_res.entities[:10]:
        print(f" - [{e.entity_type.value}] '{e.text}' (Page {e.page_number}, conf: {e.confidence:.2f}, offsets: {e.start_offset}-{e.end_offset})")
        if e.start_offset == 0 and e.end_offset == 0:
            print("   >>> WARNING: Provenance offsets are missing/zero!")

    print("\n[Sample Relations]")
    for r in ai_res.relations[:10]:
        print(f" - [{r.source_entity.text}] -[{r.relation_type.value}]-> [{r.target_entity.text}] (conf: {r.confidence:.2f}, Page: {r.page_number})")

    if ai_res.rejected_relations:
        print("\n[Rejected Relations (Ontology Violation)]")
        for rr in ai_res.rejected_relations[:5]:
            print(f" - [{rr.source_entity.entity_type.value}] -[{rr.relation_type.value}]-> [{rr.target_entity.entity_type.value}] -> {rr.validation_error}")

    print_header("E. RUNNING STEP 5: ENTITY RESOLUTION")
    res_pipeline = EntityResolutionPipeline()
    res_result = res_pipeline.resolve(document.document_id, document.case_id, ai_res.entities, ai_res.relations)

    print(f"Total Canonical Entities: {len(res_result.canonical_entities)}")
    print(f"Total Resolved Relations: {len(res_result.resolved_relations)}")

    print("\n[Sample Resolved Canonical Entities]")
    for ce in res_result.canonical_entities[:10]:
        print(f" - [{ce.entity_type.value}] {ce.canonical_name} (Mentions: {len(ce.mentions)}, Aliases: {ce.aliases})")

    print("\n[Sample Resolved Relations]")
    for rr in res_result.resolved_relations[:5]:
        src = next((c for c in res_result.canonical_entities if c.canonical_id == rr.source_entity_id), None)
        tgt = next((c for c in res_result.canonical_entities if c.canonical_id == rr.target_entity_id), None)
        if src and tgt:
            print(f" - [{src.canonical_name}] -[{rr.relation_type.value}]-> [{tgt.canonical_name}] (Mentions: {len(rr.mentions)})")

    print_header("EVALUATION COMPLETE")


if __name__ == "__main__":
    main()
