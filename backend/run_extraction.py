import sys
from collections import Counter
from app.ingestion.pipeline import DocumentIngestionPipeline
from app.extraction.pipeline import DeterministicExtractionPipeline

ing = DocumentIngestionPipeline(base_storage_dir="storage")
ext = DeterministicExtractionPipeline()

doc = ing.process_document(sys.argv[1], case_id="test_case")
res = ext.extract_candidates(doc)
print("counts:", res.summary_counts)
for c in res.candidates[:40]:
    print(
        f"p{c.page_number} [{c.category}] {c.original_value!r} -> {c.normalized_value!r} "
        f"conf={c.confidence} span={c.char_span}"
    )
