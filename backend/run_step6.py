import sys
import logging
from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.resolution.pipeline import EntityResolutionPipeline
from app.validation.pipeline import ValidationPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def main():
    file_path = "tests/samples/scansmpl.pdf"

    print(f"\n--- Loading Document: {file_path} ---")
    ingestion = DocumentIngestionPipeline(base_storage_dir="storage")
    document = ingestion.process_document(file_path, case_id="case_sample_step6")

    print(f"\n--- Running Step 3 & 4 AI Extraction ---")
    ai_pipeline = AIExtractionPipeline()
    combined_result = ai_pipeline.run_pipeline(document)

    print(f"\n--- Running Step 5 Resolution ---")
    resolution_pipeline = EntityResolutionPipeline()
    # Provide all candidate entities and relations (from both Step 3 deterministic and Step 4 AI)
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

    print(f"\n--- Running Step 6 Validation ---")
    validation_pipeline = ValidationPipeline()
    validation_result = validation_pipeline.validate(resolution_result)

    print("\n=======================================================")
    print("STEP 6 VALIDATION SUMMARY REPORT")
    print("=======================================================")
    print(f"Valid Entities:        {len(validation_result.validated_entities)}")
    print(f"Invalid Entities:      {len(validation_result.invalid_entities)}")
    print(f"Valid Relations:       {len(validation_result.validated_relationships)}")
    print(f"Invalid Relations:     {len(validation_result.invalid_relationships)}")
    print(f"Warnings:              {len(validation_result.warnings)}")
    print(f"Reviews Required:      {len(validation_result.review_required)}")
    print("-------------------------------------------------------")


if __name__ == "__main__":
    main()
