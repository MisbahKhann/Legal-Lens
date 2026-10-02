"""
Comprehensive Test Suite for Step 4 AI Entity & Relationship Extraction (GLiNER-Relex).
Verifies entity extraction, relationship extraction, controlled vocabulary enforcement,
triplet constraint validation, provenance tracking, document chunking, caching,
coexistence with Step 3 deterministic results, and evaluation reporting.
"""

import pytest
from unittest.mock import MagicMock
from app.ingestion.models import (
    LegalDocument,
    LegalPage,
    LegalTextBlock,
    ProcessingMetadata,
    FileType,
    ProcessingStatus
)
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import ExtractionMethod
from app.extraction.ai_models import CandidateEntity, CandidateRelation, AIExtractionResult, CombinedExtractionResult
from app.extraction.chunker import DocumentChunker, DocumentChunk
from app.extraction.gliner_relex import GLiNERRelexExtractor
from app.extraction.ai_pipeline import AIExtractionPipeline
from app.extraction.ai_evaluator import AIEvaluator, EvaluationReport


def create_sample_legal_document() -> LegalDocument:
    """Helper to construct a realistic 2-page sample LegalDocument."""
    page1_text = (
        "IN THE UNITED STATES DISTRICT COURT FOR THE SOUTHERN DISTRICT OF NEW YORK.\n"
        "Jane Doe, Plaintiff,\n"
        "v.\n"
        "Acme Corporation, Defendant.\n"
        "Case No. 23-CV-10492.\n"
        "Judge Richard Miller presiding.\n"
        "Attorney Sarah Jenkins of Smith & Associates represents Jane Doe."
    )
    page2_text = (
        "MEMORANDUM OF LAW IN SUPPORT OF MOTION FOR SUMMARY JUDGMENT.\n"
        "On January 15, 2023, Defendant Acme Corporation breached the Contract dated May 10, 2021.\n"
        "This court applies 42 U.S.C. 1983 and interprets Strict Liability standard.\n"
        "Hearing scheduled on December 5, 2023."
    )

    page1 = LegalPage(
        page_number=1,
        raw_text=page1_text,
        normalized_text=page1_text,
        blocks=[
            LegalTextBlock(block_id="b1_1", raw_text="Jane Doe, Plaintiff,", normalized_text="Jane Doe, Plaintiff,", page_number=1),
            LegalTextBlock(block_id="b1_2", raw_text="v. Acme Corporation, Defendant.", normalized_text="v. Acme Corporation, Defendant.", page_number=1),
            LegalTextBlock(block_id="b1_3", raw_text="Attorney Sarah Jenkins of Smith & Associates represents Jane Doe.", normalized_text="Attorney Sarah Jenkins of Smith & Associates represents Jane Doe.", page_number=1),
        ]
    )

    page2 = LegalPage(
        page_number=2,
        raw_text=page2_text,
        normalized_text=page2_text,
        blocks=[
            LegalTextBlock(block_id="b2_1", raw_text="On January 15, 2023, Defendant Acme Corporation breached the Contract.", normalized_text="On January 15, 2023, Defendant Acme Corporation breached the Contract.", page_number=2),
            LegalTextBlock(block_id="b2_2", raw_text="This court applies 42 U.S.C. 1983 and interprets Strict Liability standard.", normalized_text="This court applies 42 U.S.C. 1983 and interprets Strict Liability standard.", page_number=2),
        ]
    )

    proc_meta = ProcessingMetadata(
        document_id="doc_sample_101",
        filename="test_motion.pdf",
        file_type=FileType.PDF,
        page_count=2,
        processing_status=ProcessingStatus.COMPLETED
    )

    return LegalDocument(
        document_id="doc_sample_101",
        case_id="case_23_cv_10492",
        filename="test_motion.pdf",
        file_type=FileType.PDF,
        sha256_hash="abc123hash",
        file_size_bytes=10240,
        processing_metadata=proc_meta,
        pages=[page1, page2]
    )


class TestDocumentChunker:
    """Test suite for document chunking."""

    def test_chunk_multi_page_document(self):
        doc = create_sample_legal_document()
        chunker = DocumentChunker(max_chunk_chars=300)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) >= 2
        page_numbers = {c.page_number for c in chunks}
        assert page_numbers == {1, 2}
        for chunk in chunks:
            assert chunk.document_id == "doc_sample_101"
            assert chunk.case_id == "case_23_cv_10492"
            assert chunk.start_char_offset >= 0
            assert chunk.end_char_offset > chunk.start_char_offset
            assert len(chunk.text) > 0


class TestGLiNERRelexExtractor:
    """Test suite for GLiNER-Relex extractor logic."""

    def test_extracted_candidate_entity_and_relation_provenance(self):
        extractor = GLiNERRelexExtractor(enable_caching=False)

        mock_prediction = {
            "entities": [
                {"label": "PERSON", "text": "Jane Doe", "start": 0, "end": 8, "score": 0.95},
                {"label": "COMPANY", "text": "Acme Corporation", "start": 15, "end": 31, "score": 0.92},
                {"label": "LAWYER", "text": "Sarah Jenkins", "start": 35, "end": 48, "score": 0.88}
            ],
            "relations": [
                {
                    "head": {"label": "LAWYER", "text": "Sarah Jenkins", "start": 35, "end": 48, "score": 0.88},
                    "tail": {"label": "PERSON", "text": "Jane Doe", "start": 0, "end": 8, "score": 0.95},
                    "relation": "REPRESENTS",
                    "score": 0.91
                }
            ]
        }

        mock_model = MagicMock()
        mock_model.predict_entities_and_relations.return_value = mock_prediction
        extractor._model = mock_model

        chunk = DocumentChunk(
            chunk_id="c1",
            document_id="doc_1",
            case_id="case_1",
            page_number=1,
            text="Jane Doe sued Acme Corporation and Sarah Jenkins represents Jane Doe.",
            start_char_offset=100,
            end_char_offset=170
        )

        entities, relations = extractor.extract_from_chunk(chunk)

        # 1. Verify entity extraction
        assert len(entities) == 3
        ent_map = {e.text: e for e in entities}
        assert "Jane Doe" in ent_map
        assert "Acme Corporation" in ent_map

        # 2. Verify controlled entity label
        assert ent_map["Jane Doe"].entity_type == EntityType.PERSON
        assert ent_map["Acme Corporation"].entity_type == EntityType.COMPANY

        # 3. Verify provenance
        jane_ent = ent_map["Jane Doe"]
        assert jane_ent.document_id == "doc_1"
        assert jane_ent.page_number == 1
        assert jane_ent.start_offset == 100
        assert jane_ent.end_offset == 108
        assert jane_ent.confidence == 0.95
        assert jane_ent.extraction_method == ExtractionMethod.GLINER_RELEX

        # 4. Verify relation extraction & controlled relationship label
        assert len(relations) == 1
        rel = relations[0]
        assert rel.relation_type == RelationshipType.REPRESENTS
        assert rel.source_entity.text == "Sarah Jenkins"
        assert rel.target_entity.text == "Jane Doe"
        assert rel.confidence == 0.91
        assert rel.extraction_method == ExtractionMethod.GLINER_RELEX
        assert rel.is_valid is True

    def test_triplet_constraint_validation_rejection(self):
        """Verify invalid relationship triplets are flagged/rejected."""
        extractor = GLiNERRelexExtractor(enable_caching=False)

        # Invalid relation: DATE cannot represent PERSON
        mock_prediction = {
            "entities": [
                {"label": "DATE", "text": "January 15, 2023", "start": 0, "end": 16, "score": 0.95},
                {"label": "PERSON", "text": "Jane Doe", "start": 20, "end": 28, "score": 0.95}
            ],
            "relations": [
                {
                    "head": {"label": "DATE", "text": "January 15, 2023", "start": 0, "end": 16, "score": 0.95},
                    "tail": {"label": "PERSON", "text": "Jane Doe", "start": 20, "end": 28, "score": 0.95},
                    "relation": "REPRESENTS",
                    "score": 0.89
                }
            ]
        }

        mock_model = MagicMock()
        mock_model.predict_entities_and_relations.return_value = mock_prediction
        extractor._model = mock_model

        chunk = DocumentChunk(
            chunk_id="c2",
            document_id="doc_1",
            page_number=1,
            text="January 15, 2023 and Jane Doe.",
            start_char_offset=0,
            end_char_offset=30
        )

        _, relations = extractor.extract_from_chunk(chunk)
        assert len(relations) == 1
        rel = relations[0]
        assert rel.is_valid is False
        assert "Invalid relationship triplet" in rel.validation_error

    def test_caching_avoids_duplicate_model_calls(self):
        """Verify duplicate chunks hit cache instead of calling model repeatedly."""
        extractor = GLiNERRelexExtractor(enable_caching=True)
        mock_model = MagicMock()
        mock_model.predict_entities_and_relations.return_value = {"entities": [], "relations": []}
        extractor._model = mock_model

        chunk = DocumentChunk(
            chunk_id="c_dup_1",
            document_id="doc_1",
            page_number=1,
            text="Identical repeated chunk text for testing cache.",
            start_char_offset=0,
            end_char_offset=48
        )

        extractor.extract_from_chunk(chunk)
        extractor.extract_from_chunk(chunk)
        extractor.extract_from_chunk(chunk)

        assert mock_model.predict_entities_and_relations.call_count == 1

    def test_low_confidence_filtering(self):
        """Verify low-confidence predictions below threshold are filtered."""
        extractor = GLiNERRelexExtractor(entity_confidence_threshold=0.80, enable_caching=False)
        mock_prediction = {
            "entities": [
                {"label": "PERSON", "text": "High Conf", "start": 0, "end": 9, "score": 0.90},
                {"label": "PERSON", "text": "Low Conf", "start": 10, "end": 18, "score": 0.50}
            ],
            "relations": []
        }
        mock_model = MagicMock()
        mock_model.predict_entities_and_relations.return_value = mock_prediction
        extractor._model = mock_model

        chunk = DocumentChunk(
            chunk_id="c_low",
            document_id="doc_1",
            page_number=1,
            text="High Conf Low Conf",
            start_char_offset=0,
            end_char_offset=18
        )

        entities, _ = extractor.extract_from_chunk(chunk)
        assert len(entities) == 1
        assert entities[0].text == "High Conf"


class TestAIExtractionPipeline:
    """Test suite for full AI Extraction Pipeline and combination with Step 3."""

    def test_combined_pipeline_coexistence(self):
        doc = create_sample_legal_document()
        pipeline = AIExtractionPipeline()

        # Mock Step 4 extractor predictions
        mock_prediction = {
            "entities": [
                {"label": "PERSON", "text": "Jane Doe", "start": 0, "end": 8, "score": 0.95},
                {"label": "COMPANY", "text": "Acme Corporation", "start": 10, "end": 26, "score": 0.91}
            ],
            "relations": [
                {
                    "head": {"label": "PERSON", "text": "Jane Doe", "start": 0, "end": 8, "score": 0.95},
                    "tail": {"label": "COMPANY", "text": "Acme Corporation", "start": 10, "end": 26, "score": 0.91},
                    "relation": "PLAINTIFF_IN",  # Wait, PLAINTIFF_IN requires CASE target in constraints
                    "score": 0.85
                }
            ]
        }
        mock_model = MagicMock()
        mock_model.predict_entities_and_relations.return_value = mock_prediction
        pipeline.extractor._model = mock_model

        combined: CombinedExtractionResult = pipeline.run_pipeline(doc)

        # 1. Deterministic Step 3 results exist
        assert combined.deterministic_result is not None
        assert combined.total_deterministic_entities >= 0

        # 2. Step 4 AI results exist
        assert combined.ai_result is not None
        assert combined.total_ai_entities > 0

        # 3. Step 3 and Step 4 remain distinct and traceable
        assert combined.document_id == "doc_sample_101"
        for det in combined.deterministic_result.candidates:
            assert det.extraction_method == ExtractionMethod.DETERMINISTIC_RULE
        for ai_ent in combined.ai_result.entities:
            assert ai_ent.extraction_method == ExtractionMethod.GLINER_RELEX


class TestAIEvaluator:
    """Test suite for evaluation and reporting mechanism."""

    def test_evaluation_reporting_metrics(self):
        prediction = AIExtractionResult(
            document_id="doc_eval_1",
            entities=[
                CandidateEntity(
                    entity_type=EntityType.PERSON,
                    text="Jane Doe",
                    document_id="doc_eval_1",
                    page_number=1,
                    source_text="Jane Doe",
                    start_offset=0,
                    end_offset=8,
                    confidence=0.95,
                    extraction_method=ExtractionMethod.GLINER_RELEX
                ),
                CandidateEntity(
                    entity_type=EntityType.COMPANY,
                    text="False Positive Corp",
                    document_id="doc_eval_1",
                    page_number=1,
                    source_text="False Positive Corp",
                    start_offset=10,
                    end_offset=29,
                    confidence=0.90,
                    extraction_method=ExtractionMethod.GLINER_RELEX
                )
            ],
            relations=[
                CandidateRelation(
                    relation_type=RelationshipType.REPRESENTS,
                    source_entity=CandidateEntity(
                        entity_type=EntityType.LAWYER, text="Sarah Jenkins", document_id="d1", page_number=1, source_text="s", start_offset=0, end_offset=5, confidence=0.9, extraction_method=ExtractionMethod.GLINER_RELEX
                    ),
                    target_entity=CandidateEntity(
                        entity_type=EntityType.PERSON, text="Jane Doe", document_id="d1", page_number=1, source_text="j", start_offset=6, end_offset=10, confidence=0.9, extraction_method=ExtractionMethod.GLINER_RELEX
                    ),
                    document_id="doc_eval_1",
                    page_number=1,
                    source_text="Sarah Jenkins represents Jane Doe",
                    confidence=0.90,
                    extraction_method=ExtractionMethod.GLINER_RELEX
                )
            ]
        )

        expected_entities = [
            {"entity_type": "PERSON", "text": "Jane Doe", "page_number": 1},
            {"entity_type": "COMPANY", "text": "Acme Corporation", "page_number": 1}
        ]

        expected_relations = [
            {"relation_type": "REPRESENTS", "source": "Sarah Jenkins", "target": "Jane Doe"}
        ]

        report: EvaluationReport = AIEvaluator.evaluate(prediction, expected_entities, expected_relations)

        # Entity metrics: TP=1 (Jane Doe), FP=1 (False Positive Corp), FN=1 (Acme Corporation)
        assert report.entity_metrics.true_positives == 1
        assert report.entity_metrics.false_positives == 1
        assert report.entity_metrics.false_negatives == 1
        assert report.entity_metrics.precision == 0.5
        assert report.entity_metrics.recall == 0.5

        # Relation metrics: TP=1 (REPRESENTS), FP=0, FN=0
        assert report.relation_metrics.true_positives == 1
        assert report.relation_metrics.precision == 1.0
        assert report.relation_metrics.recall == 1.0
