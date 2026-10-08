import sys
import logging
from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.resolution.pipeline import EntityResolutionPipeline
from app.validation.pipeline import ValidationPipeline
from app.temporal.pipeline import TemporalPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def run_sample_pipeline(file_path: str = "tests/samples/scansmpl.pdf"):
    print(f"\n=======================================================")
    print(f"RUNNING STEP 2 - 7 PIPELINE ON REAL SAMPLE: {file_path}")
    print(f"=======================================================")

    # Step 2: Document Ingestion
    print(f"\n--- Step 2: Ingesting Document ---")
    ingestion = DocumentIngestionPipeline(base_storage_dir="storage")
    document = ingestion.process_document(file_path, case_id="case_sample_step7")
    print(
        f"Ingested {len(document.pages)} pages for document ID: {document.document_id}"
    )

    # Step 3 & 4: AI + Deterministic Extraction
    print(f"\n--- Step 3 & 4: Extraction (Deterministic + AI) ---")
    ai_pipeline = AIExtractionPipeline()
    combined_result = ai_pipeline.run_pipeline(document)

    # Step 5: Entity Resolution
    print(f"\n--- Step 5: Entity Resolution ---")
    resolution_pipeline = EntityResolutionPipeline()
    all_entities = (
        combined_result.deterministic_result.candidates
        + combined_result.ai_result.entities
    )
    all_relations = combined_result.ai_result.relations

    resolution_result = resolution_pipeline.resolve(
        document_id=document.document_id,
        case_id=document.case_id,
        entities=all_entities,
        relations=all_relations,
    )

    # Step 6: Validation
    print(f"\n--- Step 6: Validation & Consistency Checking ---")
    validation_pipeline = ValidationPipeline()
    validation_result = validation_pipeline.validate(resolution_result)

    # Step 7: Temporal Event & Timeline Extraction
    print(f"\n--- Step 7: Temporal Event & Timeline Extraction ---")
    temporal_pipeline = TemporalPipeline()
    case_timeline = temporal_pipeline.process_timeline(
        document=document,
        resolution_result=resolution_result,
        validation_result=validation_result,
    )

    print("\n=======================================================")
    print("STEP 7 REAL DOCUMENT TIMELINE SUMMARY REPORT")
    print("=======================================================")
    print(f"Document Name:                         {file_path}")
    print(f"Number of Pages:                       {len(document.pages)}")
    print(
        f"Total Temporal Expressions Detected:   {case_timeline.summary_counts.get('total_temporal_expressions_detected', 0)}"
    )
    print(
        f"Total Events Identified:               {case_timeline.summary_counts.get('total_events_identified', 0)}"
    )
    print(
        f"Events with Exact Dates:               {case_timeline.summary_counts.get('events_with_exact_dates', 0)}"
    )
    print(
        f"Events with Partial/Uncertain Dates:   {case_timeline.summary_counts.get('events_with_partial_dates', 0)}"
    )
    print(
        f"Deadlines Identified:                  {case_timeline.summary_counts.get('deadlines_count', 0)}"
    )
    print(
        f"Temporal Relationships:                {case_timeline.summary_counts.get('temporal_relationships_count', 0)}"
    )
    print(
        f"Unresolved Temporal Expressions:       {case_timeline.summary_counts.get('unresolved_temporal_expressions_count', 0)}"
    )
    print(
        f"Temporal Validation Warnings:          {case_timeline.summary_counts.get('temporal_validation_warnings_count', 0)}"
    )
    print("-------------------------------------------------------")

    print("\n--- EXTRACTED CASE TIMELINE EVENTS (CHRONOLOGICAL) ---")
    for idx, ev in enumerate(case_timeline.events, start=1):
        date_display = ev.event_date or ev.start_date or "[UNDATED]"
        print(
            f"{idx:02d}. [{date_display}] ({ev.date_precision.value}) - {ev.description}"
        )
        if ev.source_text:
            print(
                f'    Source Quote: "{ev.source_text[:100]}..." (Page {ev.source_page or 1})'
            )
        if ev.derived_from:
            print(f"    Derivation: {ev.derived_from}")

    return case_timeline


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "tests/samples/scansmpl.pdf"
    run_sample_pipeline(file_arg)
