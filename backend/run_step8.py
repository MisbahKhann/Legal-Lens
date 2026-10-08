"""
Step 8 Execution Runner.
Runs the complete ingestion pipeline (Steps 2-7) and persists the validated legal knowledge graph into Neo4j (Step 8).
Prints a comprehensive Step 8 execution summary report.
"""

import sys
import logging
from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.resolution.pipeline import EntityResolutionPipeline
from app.validation.pipeline import ValidationPipeline
from app.temporal.pipeline import TemporalPipeline
from app.storage.neo4j_pipeline import Neo4jStoragePipeline
from app.storage.neo4j_store import Neo4jGraphStore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_step8")


def run_step8_pipeline(
    file_path: str = "tests/samples/scansmpl.pdf", case_id: str = "case_sample_step8"
):
    print(f"\n=======================================================")
    print(f"RUNNING STEP 8 PIPELINE ON REAL SAMPLE: {file_path}")
    print(f"=======================================================")

    # Step 2: Document Ingestion
    print(f"\n--- Step 2: Ingesting Document ---")
    ingestion = DocumentIngestionPipeline(base_storage_dir="storage")
    document = ingestion.process_document(file_path, case_id=case_id)
    print(
        f"Ingested {len(document.pages)} pages for document ID: {document.document_id}"
    )

    # Step 3 & 4: AI + Deterministic Extraction
    print(f"\n--- Step 3 & 4: Extraction ---")
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
    print(f"\n--- Step 7: Temporal Extraction ---")
    temporal_pipeline = TemporalPipeline()
    case_timeline = temporal_pipeline.process_timeline(
        document=document,
        resolution_result=resolution_result,
        validation_result=validation_result,
    )

    # Step 8: Neo4j Storage
    print(f"\n--- Step 8: Neo4j Knowledge Graph Storage ---")
    store = Neo4jGraphStore()
    pipeline = Neo4jStoragePipeline(store=store)

    try:
        import_result = pipeline.import_case_graph(
            validation_result=validation_result,
            case_timeline=case_timeline,
            case_id=document.case_id,
        )

        print("\n=======================================================")
        print("STEP 8 NEO4J KNOWLEDGE GRAPH IMPORT SUMMARY")
        print("=======================================================")
        print(f"Case ID:                                {import_result['case_id']}")
        print(
            f"Entities Persisted:                    {import_result['entities_imported']}"
        )
        print(
            f"Relationships Persisted:               {import_result['relationships_imported']}"
        )
        print(
            f"Timeline Events Persisted:             {import_result['timeline_events_imported']}"
        )
        print(
            f"Temporal Relationships Persisted:       {import_result['temporal_relationships_imported']}"
        )
        print(
            f"Invalid Entities Filtered Out:         {import_result['invalid_entities_filtered']}"
        )
        print(
            f"Invalid Relationships Filtered Out:    {import_result['invalid_relationships_filtered']}"
        )
        print("-------------------------------------------------------")

        # Query back imported graph to verify retrieval
        retrieved_graph = store.get_complete_case_graph(document.case_id)
        print(f"\nRetrieved Knowledge Graph for '{document.case_id}':")
        print(f"  - Canonical Nodes:       {len(retrieved_graph['entities'])}")
        print(f"  - Graph Edges:           {len(retrieved_graph['relationships'])}")
        print(f"  - Timeline Event Nodes:  {len(retrieved_graph['timeline_events'])}")

        return import_result
    except Exception as e:
        print(
            f"\n[Neo4j Storage Notice]: Neo4j database is offline or unreachable ({e})."
        )
        print("To run with a live Neo4j database, start Neo4j and re-run this script.")
        return None


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "tests/samples/scansmpl.pdf"
    case_id_arg = sys.argv[2] if len(sys.argv) > 2 else "case_sample_step8"
    run_step8_pipeline(file_arg, case_id=case_id_arg)
