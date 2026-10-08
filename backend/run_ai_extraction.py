"""
Sample execution script for Step 4 AI Entity & Relationship Extraction pipeline.
Loads a document via Step 2 ingestion, runs Step 3 deterministic extraction,
runs Step 4 GLiNER-Relex extraction, and outputs combined results.
"""

import sys
import logging
from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.ai_pipeline import AIExtractionPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_ai_extraction.py <path_to_legal_document>")
        file_path = "tests/samples/sample_contract.pdf"
    else:
        file_path = sys.argv[1]

    print(f"\n--- Loading Document: {file_path} ---")
    ingestion = DocumentIngestionPipeline(base_storage_dir="storage")
    document = ingestion.process_document(file_path, case_id="case_sample_step4")

    print(f"\n--- Running Step 4 AI Extraction Pipeline ---")
    ai_pipeline = AIExtractionPipeline()
    combined_result = ai_pipeline.run_pipeline(document)

    print("\n=======================================================")
    print("STEP 4 AI EXTRACTION SUMMARY REPORT")
    print("=======================================================")
    print(f"Document ID:               {combined_result.document_id}")
    print(f"Case ID:                   {combined_result.case_id}")
    print(f"Deterministic Candidates:  {combined_result.total_deterministic_entities}")
    print(f"AI Extracted Entities:     {combined_result.total_ai_entities}")
    print(f"AI Extracted Relations:    {combined_result.total_ai_relations}")
    print("-------------------------------------------------------")

    print("\n[AI Extracted Candidate Entities (Sample)]")
    for ent in combined_result.ai_result.entities[:15]:
        print(
            f"  - Page {ent.page_number} | [{ent.entity_type.value}] '{ent.text}' | conf={ent.confidence} | span=[{ent.start_offset}:{ent.end_offset}]"
        )

    print("\n[AI Extracted Candidate Relations (Sample)]")
    for rel in combined_result.ai_result.relations[:15]:
        print(
            f"  - Page {rel.page_number} | [{rel.source_entity.text}] -[{rel.relation_type.value}]-> [{rel.target_entity.text}] | conf={rel.confidence}"
        )

    if combined_result.ai_result.rejected_relations:
        print("\n[Flagged / Rejected Relations (Triplet Constraint Violations)]")
        for rej in combined_result.ai_result.rejected_relations[:10]:
            print(
                f"  - [REJECTED] [{rej.source_entity.entity_type.value}: '{rej.source_entity.text}'] -[{rej.relation_type.value}]-> [{rej.target_entity.entity_type.value}: '{rej.target_entity.text}'] | Error: {rej.validation_error}"
            )

    print("\nPipeline execution complete.\n")


if __name__ == "__main__":
    main()
