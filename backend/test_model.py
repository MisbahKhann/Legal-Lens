from app.extraction.gliner_relex import GLiNERRelexExtractor
from app.extraction.chunker import DocumentChunk

ex = GLiNERRelexExtractor()
c = DocumentChunk(
    chunk_id="t1",
    document_id="d",
    page_number=1,
    text="John Doe filed a complaint against ABC Corp. in the Southern District of New York on January 15, 2024, represented by Smith & Jones LLP.",
    start_char_offset=0,
    end_char_offset=140,
)
ents, rels = ex.extract_from_chunk(c)
print("ENTITIES:", len(ents), "| RELATIONS:", len(rels))
for e in ents:
    print(" ", e.entity_type.value, "|", e.text, "|", e.confidence)
for r in rels:
    print(
        " ",
        r.source_entity.text,
        r.relation_type.value,
        r.target_entity.text,
        "| valid:",
        r.is_valid,
    )
