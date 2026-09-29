import sys, json
from pathlib import Path
from app.ingestion.pipeline import DocumentIngestionPipeline

pipe = DocumentIngestionPipeline(base_storage_dir="storage")
for f in sys.argv[1:]:
    try:
        d = pipe.process_document(f, case_id="test_case")
        m = d.processing_metadata
        print(f"\n== {Path(f).name} ==")
        print("status:", m.processing_status.value, "| pages:", m.page_count,
              "| OCR:", m.ocr_used, m.ocr_engine)
        tables = sum(len(p.tables) for p in d.pages)
        print("tables:", tables, "| sections:", len(d.sections))
        for p in d.pages[:2]:
            print(f"  p{p.page_number}: raw={len(p.raw_text)} norm={len(p.normalized_text)} "
                  f"blocks={len(p.blocks)} ocr={p.ocr_applied}")
            print("   ", p.normalized_text[:150].replace("\n", " "))
    except Exception as e:
        print(f"\n== {Path(f).name} == FAILED: {e}")