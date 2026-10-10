"""
Core Evaluation Engine for LegalLens Step 11.
Provides KnowledgeGraphEvaluator to evaluate extraction quality, entity resolution,
temporal events, schema validation, provenance completeness, escalation rates,
and in-memory graph consistency.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging

from app.evaluation.models import (
    GoldDataset,
    GoldDocumentData,
    GoldEntity,
    GoldRelationship,
    GoldEvent,
    GoldEquivalencePair,
    ExtractionMetrics,
    ResolutionMetrics,
    TemporalMetrics,
    ValidationMetrics,
    ProvenanceMetrics,
    EscalationMetrics,
    GraphConsistencyMetrics,
    Step11EvaluationReport,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphEvaluator:
    """
    Evaluates system predictions against gold-standard datasets across all knowledge graph stages.
    """

    @staticmethod
    def _normalize_str(val: Any) -> str:
        """Normalizes string or enum for robust, case-insensitive comparison."""
        if val is None:
            return ""
        if hasattr(val, "value"):
            val = val.value
        val_str = str(val)
        if "." in val_str and (
            val_str.startswith("EntityType.") or val_str.startswith("RelationshipType.")
        ):
            val_str = val_str.split(".", 1)[1]
        return val_str.strip().lower().replace("_", " ").replace("-", " ")

    def evaluate_entities(
        self,
        predicted_entities: List[Dict[str, Any]],
        gold_entities: List[GoldEntity],
    ) -> Tuple[ExtractionMetrics, Dict[str, ExtractionMetrics]]:
        """
        Evaluates entity extractions against gold entities.
        Supports dicts, CandidateEntity, or ExtractedCandidateEntity models.
        """
        # Collect all categories
        gold_categories = set(self._normalize_str(g.entity_type) for g in gold_entities)
        pred_categories = set(
            self._normalize_str(p.get("entity_type") or p.get("category"))
            for p in predicted_entities
        )
        all_categories = sorted(gold_categories | pred_categories)

        per_cat_metrics: Dict[str, ExtractionMetrics] = {}
        overall_tp, overall_fp, overall_fn = 0, 0, 0

        for cat in all_categories:
            cat_golds = [
                g for g in gold_entities if self._normalize_str(g.entity_type) == cat
            ]
            cat_preds = [
                p
                for p in predicted_entities
                if self._normalize_str(p.get("entity_type") or p.get("category")) == cat
            ]

            matched_gold_indices: Set[int] = set()
            tp, fp = 0, 0

            for pred in cat_preds:
                pred_text = self._normalize_str(
                    pred.get("text") or pred.get("original_value")
                )
                pred_doc = str(pred.get("document_id") or "")
                pred_page = pred.get("page_number")

                matched = False
                for idx, gold in enumerate(cat_golds):
                    if idx in matched_gold_indices:
                        continue

                    # Document ID check if available
                    if gold.document_id and pred_doc and gold.document_id != pred_doc:
                        continue

                    gold_text = self._normalize_str(gold.text)
                    gold_norm = self._normalize_str(gold.normalized_value)

                    # Text match check (substring or equality)
                    text_matched = (
                        gold_text == pred_text
                        or gold_text in pred_text
                        or pred_text in gold_text
                    )
                    if not text_matched and gold_norm:
                        text_matched = (
                            gold_norm == pred_text
                            or gold_norm in pred_text
                            or pred_text in gold_norm
                        )

                    if text_matched:
                        tp += 1
                        matched_gold_indices.add(idx)
                        matched = True
                        break

                if not matched:
                    fp += 1

            fn = len(cat_golds) - len(matched_gold_indices)

            m = ExtractionMetrics(
                category=cat.upper(),
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
            )
            m.compute_scores()
            per_cat_metrics[cat.upper()] = m

            overall_tp += tp
            overall_fp += fp
            overall_fn += fn

        overall_m = ExtractionMetrics(
            category="OVERALL_ENTITIES",
            true_positives=overall_tp,
            false_positives=overall_fp,
            false_negatives=overall_fn,
        )
        overall_m.compute_scores()

        return overall_m, per_cat_metrics

    def evaluate_relationships(
        self,
        predicted_relations: List[Dict[str, Any]],
        gold_relations: List[GoldRelationship],
    ) -> Tuple[ExtractionMetrics, Dict[str, ExtractionMetrics]]:
        """
        Evaluates relationship extractions against gold relationships.
        """
        gold_categories = set(
            self._normalize_str(g.relation_type) for g in gold_relations
        )
        pred_categories = set(
            self._normalize_str(p.get("relation_type")) for p in predicted_relations
        )
        all_categories = sorted(gold_categories | pred_categories)

        per_cat_metrics: Dict[str, ExtractionMetrics] = {}
        overall_tp, overall_fp, overall_fn = 0, 0, 0

        for cat in all_categories:
            cat_golds = [
                g for g in gold_relations if self._normalize_str(g.relation_type) == cat
            ]
            cat_preds = [
                p
                for p in predicted_relations
                if self._normalize_str(p.get("relation_type")) == cat
            ]

            matched_gold_indices: Set[int] = set()
            tp, fp = 0, 0

            for pred in cat_preds:
                # Extract source/target text from dict or candidate models
                src_text = self._normalize_str(
                    pred.get("source_entity_text")
                    or (
                        pred.get("source_entity", {}).get("text")
                        if isinstance(pred.get("source_entity"), dict)
                        else getattr(pred.get("source_entity"), "text", "")
                    )
                )
                tgt_text = self._normalize_str(
                    pred.get("target_entity_text")
                    or (
                        pred.get("target_entity", {}).get("text")
                        if isinstance(pred.get("target_entity"), dict)
                        else getattr(pred.get("target_entity"), "text", "")
                    )
                )
                pred_doc = str(pred.get("document_id") or "")

                matched = False
                for idx, gold in enumerate(cat_golds):
                    if idx in matched_gold_indices:
                        continue

                    if gold.document_id and pred_doc and gold.document_id != pred_doc:
                        continue

                    gold_src = self._normalize_str(gold.source_entity_text)
                    gold_tgt = self._normalize_str(gold.target_entity_text)

                    src_match = (
                        gold_src == src_text
                        or gold_src in src_text
                        or src_text in gold_src
                    )
                    tgt_match = (
                        gold_tgt == tgt_text
                        or gold_tgt in tgt_text
                        or tgt_text in gold_tgt
                    )

                    if src_match and tgt_match:
                        tp += 1
                        matched_gold_indices.add(idx)
                        matched = True
                        break

                if not matched:
                    fp += 1

            fn = len(cat_golds) - len(matched_gold_indices)

            m = ExtractionMetrics(
                category=cat.upper(),
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
            )
            m.compute_scores()
            per_cat_metrics[cat.upper()] = m

            overall_tp += tp
            overall_fp += fp
            overall_fn += fn

        overall_m = ExtractionMetrics(
            category="OVERALL_RELATIONS",
            true_positives=overall_tp,
            false_positives=overall_fp,
            false_negatives=overall_fn,
        )
        overall_m.compute_scores()

        return overall_m, per_cat_metrics

    def evaluate_entity_resolution(
        self,
        canonical_entities: List[Dict[str, Any]],
        gold_pairs: List[GoldEquivalencePair],
    ) -> ResolutionMetrics:
        """
        Evaluates pairwise precision/recall/accuracy on entity resolution equivalence pairs.
        """
        if not gold_pairs:
            m = ResolutionMetrics()
            m.compute_scores()
            return m

        # Build mapping from entity mention text to canonical entity ID
        text_to_canonical: Dict[str, str] = {}
        for c in canonical_entities:
            cid = str(c.get("canonical_id") or c.get("id") or "")
            cname = self._normalize_str(c.get("canonical_name"))
            if cname and cid:
                text_to_canonical[cname] = cid

            aliases = c.get("aliases") or []
            for alias in aliases:
                norm_alias = self._normalize_str(alias)
                if norm_alias and cid:
                    text_to_canonical[norm_alias] = cid

            mentions = c.get("mentions") or []
            for mention in mentions:
                mtext = self._normalize_str(
                    mention.get("text") if isinstance(mention, dict) else str(mention)
                )
                if mtext and cid:
                    text_to_canonical[mtext] = cid

        tp, fp, fn, tn = 0, 0, 0, 0

        for pair in gold_pairs:
            t1 = self._normalize_str(pair.entity_text_1)
            t2 = self._normalize_str(pair.entity_text_2)

            cid1 = text_to_canonical.get(t1)
            cid2 = text_to_canonical.get(t2)

            # System resolved them into same cluster if both exist and IDs match
            system_equivalent = (
                (cid1 is not None) and (cid2 is not None) and (cid1 == cid2)
            )

            if pair.are_equivalent:
                if system_equivalent:
                    tp += 1
                else:
                    fn += 1
            else:
                if system_equivalent:
                    fp += 1
                else:
                    tn += 1

        m = ResolutionMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
        )
        m.compute_scores()
        return m

    def evaluate_temporal_events(
        self,
        predicted_events: List[Dict[str, Any]],
        gold_events: List[GoldEvent],
    ) -> TemporalMetrics:
        """
        Evaluates temporal date & event matching against gold events.
        """
        if not gold_events and not predicted_events:
            m = TemporalMetrics()
            m.compute_scores()
            return m

        matched_count = 0
        exact_date_count = 0
        partial_date_count = 0

        matched_gold_indices: Set[int] = set()

        for pred in predicted_events:
            pred_desc = self._normalize_str(
                pred.get("description") or pred.get("raw_text")
            )
            pred_date = str(
                pred.get("event_date")
                or pred.get("start_date")
                or pred.get("iso_value")
                or ""
            ).strip()
            pred_doc = str(
                pred.get("source_document_id") or pred.get("document_id") or ""
            )

            for idx, gold in enumerate(gold_events):
                if idx in matched_gold_indices:
                    continue

                if gold.document_id and pred_doc and gold.document_id != pred_doc:
                    continue

                gold_desc = self._normalize_str(gold.description)
                gold_date = str(gold.event_date or "").strip()

                desc_match = (
                    gold_desc == pred_desc
                    or gold_desc in pred_desc
                    or pred_desc in gold_desc
                )

                if desc_match:
                    matched_count += 1
                    matched_gold_indices.add(idx)

                    if gold_date and pred_date:
                        if gold_date == pred_date:
                            exact_date_count += 1
                        elif (
                            gold_date in pred_date
                            or pred_date in gold_date
                            or gold_date[:4] == pred_date[:4]
                        ):
                            partial_date_count += 1
                    break

        m = TemporalMetrics(
            total_gold_events=len(gold_events),
            total_predicted_events=len(predicted_events),
            matched_events_count=matched_count,
            exact_date_matches=exact_date_count,
            partial_date_matches=partial_date_count,
        )
        m.compute_scores()
        return m

    def evaluate_validation(
        self,
        validated_entities: List[Dict[str, Any]],
        validated_relationships: List[Dict[str, Any]],
        validation_warnings: List[Any],
        review_required_items: List[Any],
        invalid_entities: List[Dict[str, Any]],
        invalid_relationships: List[Dict[str, Any]],
    ) -> ValidationMetrics:
        """
        Evaluates schema & ontology validation metrics.
        """
        tot_val = len(validated_entities) + len(validated_relationships)
        inv_cnt = len(invalid_entities) + len(invalid_relationships)
        total_items = tot_val + inv_cnt

        m = ValidationMetrics(
            total_items_validated=total_items,
            valid_items_count=tot_val,
            invalid_items_count=inv_cnt,
            warning_count=len(validation_warnings),
            review_required_count=len(review_required_items),
        )
        m.compute_scores()
        return m

    def evaluate_provenance(
        self, candidate_items: List[Dict[str, Any]]
    ) -> ProvenanceMetrics:
        """
        Evaluates extraction provenance completeness across candidate items.
        """
        tot = len(candidate_items)
        if tot == 0:
            m = ProvenanceMetrics()
            m.compute_scores()
            return m

        with_page = 0
        with_offsets = 0
        with_text = 0
        full_prov = 0

        for item in candidate_items:
            page = item.get("page_number") or item.get("source_page")
            s_off = item.get("start_offset")
            e_off = item.get("end_offset")
            span = item.get("char_span")
            stext = item.get("source_text") or item.get("raw_text")

            has_p = bool(page and page >= 1)
            has_o = bool(
                (s_off is not None and e_off is not None and e_off >= s_off)
                or (span and len(span) == 2 and span[1] >= span[0])
            )
            has_t = bool(stext and len(str(stext).strip()) > 0)

            if has_p:
                with_page += 1
            if has_o:
                with_offsets += 1
            if has_t:
                with_text += 1

            if has_p and has_o and has_t:
                full_prov += 1

        m = ProvenanceMetrics(
            total_evaluated_items=tot,
            items_with_page_number=with_page,
            items_with_offsets=with_offsets,
            items_with_source_text=with_text,
            fully_provenanced_items=full_prov,
        )
        m.compute_scores()
        return m

    def evaluate_escalation(
        self,
        total_candidates: int,
        review_items: List[Dict[str, Any]],
    ) -> EscalationMetrics:
        """
        Evaluates human-review escalation rates.
        """
        esc_cnt = len(review_items)
        approved_cnt = max(0, total_candidates - esc_cnt)

        m = EscalationMetrics(
            total_candidates_processed=total_candidates,
            escalated_for_review_count=esc_cnt,
            approved_without_review_count=approved_cnt,
        )
        m.compute_scores()
        return m

    def evaluate_graph_consistency(
        self,
        canonical_entities: List[Dict[str, Any]],
        resolved_relations: List[Dict[str, Any]],
    ) -> GraphConsistencyMetrics:
        """
        Evaluates in-memory Knowledge Graph consistency without live Neo4j database.
        """
        node_ids = set()
        for c in canonical_entities:
            cid = str(c.get("canonical_id") or c.get("id") or "")
            if cid:
                node_ids.add(cid)

        dangling_count = 0
        connected_node_ids = set()
        invalid_triplets = 0

        for r in resolved_relations:
            src_id = str(r.get("source_entity_id") or r.get("source_id") or "")
            tgt_id = str(r.get("target_entity_id") or r.get("target_id") or "")
            is_val = r.get("is_valid", True)

            if not is_val:
                invalid_triplets += 1

            src_exists = src_id in node_ids
            tgt_exists = tgt_id in node_ids

            if not src_exists or not tgt_exists:
                dangling_count += 1

            if src_exists:
                connected_node_ids.add(src_id)
            if tgt_exists:
                connected_node_ids.add(tgt_id)

        orphan_count = len(node_ids - connected_node_ids)

        m = GraphConsistencyMetrics(
            total_nodes=len(node_ids),
            total_edges=len(resolved_relations),
            dangling_edges_count=dangling_count,
            orphan_nodes_count=orphan_count,
            invalid_triplet_types_count=invalid_triplets,
        )
        m.compute_scores()
        return m

    def run_full_evaluation(
        self,
        gold_dataset: GoldDataset,
        predictions: Dict[str, Any],
        model_config: Optional[Dict[str, Any]] = None,
    ) -> Step11EvaluationReport:
        """
        Executes complete evaluation across all components and returns Step11EvaluationReport.
        """
        all_gold_entities: List[GoldEntity] = []
        all_gold_relations: List[GoldRelationship] = []
        all_gold_events: List[GoldEvent] = []
        all_gold_pairs: List[GoldEquivalencePair] = []

        for doc in gold_dataset.documents:
            all_gold_entities.extend(doc.entities)
            all_gold_relations.extend(doc.relationships)
            all_gold_events.extend(doc.events)
            all_gold_pairs.extend(doc.equivalence_pairs)

        pred_entities = predictions.get("entities", [])
        pred_relations = predictions.get("relations", [])
        pred_canonical = predictions.get("canonical_entities", [])
        pred_resolved_rel = predictions.get("resolved_relations", [])
        pred_events = predictions.get("timeline_events", [])
        pred_validation = predictions.get("validation", {})
        pred_candidates = predictions.get("all_candidates", pred_entities)
        pred_reviews = predictions.get("review_items", [])

        # Compute component metrics
        entity_m, per_cat_ent = self.evaluate_entities(pred_entities, all_gold_entities)
        rel_m, per_cat_rel = self.evaluate_relationships(
            pred_relations, all_gold_relations
        )
        res_m = self.evaluate_entity_resolution(pred_canonical, all_gold_pairs)
        temp_m = self.evaluate_temporal_events(pred_events, all_gold_events)

        val_m = self.evaluate_validation(
            validated_entities=pred_validation.get(
                "validated_entities", pred_canonical
            ),
            validated_relationships=pred_validation.get(
                "validated_relationships", pred_resolved_rel
            ),
            validation_warnings=pred_validation.get("warnings", []),
            review_required_items=pred_validation.get("review_required", []),
            invalid_entities=pred_validation.get("invalid_entities", []),
            invalid_relationships=pred_validation.get("invalid_relationships", []),
        )

        prov_m = self.evaluate_provenance(pred_candidates)
        esc_m = self.evaluate_escalation(
            total_candidates=len(pred_candidates), review_items=pred_reviews
        )
        graph_m = self.evaluate_graph_consistency(pred_canonical, pred_resolved_rel)

        report = Step11EvaluationReport(
            dataset_id=gold_dataset.dataset_id,
            is_illustrative_fixture=gold_dataset.is_illustrative,
            num_documents_evaluated=len(gold_dataset.documents),
            model_configuration=model_config or {},
            entity_metrics=entity_m,
            relationship_metrics=rel_m,
            resolution_metrics=res_m,
            temporal_metrics=temp_m,
            validation_metrics=val_m,
            provenance_metrics=prov_m,
            escalation_metrics=esc_m,
            graph_consistency_metrics=graph_m,
            per_category_entity=per_cat_ent,
            per_category_relationship=per_cat_rel,
        )
        return report
