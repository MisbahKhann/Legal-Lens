import pytest
from app.validation.models import ValidationStatus, ValidationSeverity
from app.validation.pipeline import ValidationPipeline
from app.resolution.models import ResolutionResult, CanonicalEntity, ResolvedRelation
from app.extraction.ai_models import CandidateEntity, CandidateRelation
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import ExtractionMethod


@pytest.fixture
def empty_resolution_result():
    return ResolutionResult(
        document_id="doc_1",
        case_id="case_1",
        canonical_entities=[],
        resolved_relations=[],
    )


def test_valid_entity(empty_resolution_result):
    pipeline = ValidationPipeline()
    ent = CanonicalEntity(
        entity_type=EntityType.PERSON,
        canonical_name="John Doe",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.PERSON,
                text="John Doe",
                document_id="doc_1",
                page_number=1,
                source_text="John Doe",
                start_offset=0,
                end_offset=8,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.canonical_entities.append(ent)

    val_result = pipeline.validate(empty_resolution_result)
    assert len(val_result.validated_entities) == 1
    assert len(val_result.invalid_entities) == 0


def test_invalid_entity_type(empty_resolution_result):
    pipeline = ValidationPipeline()
    # Create with an invalid type string forcefully bypassing Pydantic enum check for the test
    ent = CanonicalEntity.model_construct(
        canonical_id="ent_1",
        entity_type="INVALID_TYPE",
        canonical_name="John Doe",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.PERSON,
                text="John Doe",
                document_id="doc_1",
                page_number=1,
                source_text="John Doe",
                start_offset=0,
                end_offset=8,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.canonical_entities.append(ent)

    val_result = pipeline.validate(empty_resolution_result)
    assert len(val_result.invalid_entities) == 1
    assert len(val_result.validated_entities) == 0


def test_missing_entity_name(empty_resolution_result):
    pipeline = ValidationPipeline()
    ent = CanonicalEntity.model_construct(
        canonical_id="ent_1",
        entity_type=EntityType.PERSON,
        canonical_name="",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.PERSON,
                text="John Doe",
                document_id="doc_1",
                page_number=1,
                source_text="John Doe",
                start_offset=0,
                end_offset=8,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.canonical_entities.append(ent)
    val_result = pipeline.validate(empty_resolution_result)
    assert len(val_result.invalid_entities) == 1


def test_missing_provenance(empty_resolution_result):
    pipeline = ValidationPipeline()
    ent = CanonicalEntity(
        entity_type=EntityType.PERSON,
        canonical_name="John Doe",
        document_id="doc_1",
        mentions=[],
    )
    empty_resolution_result.canonical_entities.append(ent)
    val_result = pipeline.validate(empty_resolution_result)
    assert len(val_result.invalid_entities) == 1


def test_valid_relationship_and_duplicate(empty_resolution_result):
    pipeline = ValidationPipeline()
    ent1 = CanonicalEntity(
        canonical_id="e1",
        entity_type=EntityType.PERSON,
        canonical_name="John",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.PERSON,
                text="John",
                document_id="doc_1",
                page_number=1,
                source_text="John",
                start_offset=0,
                end_offset=4,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    ent2 = CanonicalEntity(
        canonical_id="e2",
        entity_type=EntityType.LAWYER,
        canonical_name="Sarah",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.LAWYER,
                text="Sarah",
                document_id="doc_1",
                page_number=1,
                source_text="Sarah",
                start_offset=0,
                end_offset=5,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.canonical_entities.extend([ent1, ent2])

    rel1 = ResolvedRelation(
        relation_type=RelationshipType.REPRESENTS,
        source_entity_id="e2",
        target_entity_id="e1",
        document_id="doc_1",
        mentions=[
            CandidateRelation(
                relation_type=RelationshipType.REPRESENTS,
                source_entity=ent2.mentions[0],
                target_entity=ent1.mentions[0],
                document_id="doc_1",
                page_number=1,
                source_text="Sarah represents John",
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )

    rel2 = ResolvedRelation(
        relation_type=RelationshipType.REPRESENTS,
        source_entity_id="e2",
        target_entity_id="e1",
        document_id="doc_1",
        mentions=[
            CandidateRelation(
                relation_type=RelationshipType.REPRESENTS,
                source_entity=ent2.mentions[0],
                target_entity=ent1.mentions[0],
                document_id="doc_1",
                page_number=2,
                source_text="Sarah acts for John",
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )

    empty_resolution_result.resolved_relations.extend([rel1, rel2])
    val_result = pipeline.validate(empty_resolution_result)

    # 2 valid relationships, but one warning about duplicates
    assert len(val_result.validated_relationships) == 2
    assert any(
        w.validation_rule == "DUPLICATE_RELATIONSHIP" for w in val_result.warnings
    )


def test_contradiction(empty_resolution_result):
    pipeline = ValidationPipeline()
    ent1 = CanonicalEntity(
        canonical_id="e1",
        entity_type=EntityType.PERSON,
        canonical_name="John",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.PERSON,
                text="John",
                document_id="doc_1",
                page_number=1,
                source_text="John",
                start_offset=0,
                end_offset=4,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    ent2 = CanonicalEntity(
        canonical_id="case1",
        entity_type=EntityType.CASE,
        canonical_name="Case A",
        document_id="doc_1",
        mentions=[
            CandidateEntity(
                entity_type=EntityType.CASE,
                text="Case A",
                document_id="doc_1",
                page_number=1,
                source_text="Case A",
                start_offset=0,
                end_offset=4,
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.canonical_entities.extend([ent1, ent2])

    rel1 = ResolvedRelation(
        relation_type=RelationshipType.PLAINTIFF_IN,
        source_entity_id="e1",
        target_entity_id="case1",
        document_id="doc_1",
        mentions=[
            CandidateRelation(
                relation_type=RelationshipType.PLAINTIFF_IN,
                source_entity=ent1.mentions[0],
                target_entity=ent2.mentions[0],
                document_id="doc_1",
                page_number=1,
                source_text="x",
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    rel2 = ResolvedRelation(
        relation_type=RelationshipType.DEFENDANT_IN,
        source_entity_id="e1",
        target_entity_id="case1",
        document_id="doc_1",
        mentions=[
            CandidateRelation(
                relation_type=RelationshipType.DEFENDANT_IN,
                source_entity=ent1.mentions[0],
                target_entity=ent2.mentions[0],
                document_id="doc_1",
                page_number=1,
                source_text="x",
                confidence=0.9,
                extraction_method=ExtractionMethod.GLINER_RELEX,
            )
        ],
    )
    empty_resolution_result.resolved_relations.extend([rel1, rel2])
    val_result = pipeline.validate(empty_resolution_result)

    assert any(r.validation_rule == "CONTRADICTION" for r in val_result.review_required)
