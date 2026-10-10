"""
Terminal CLI Evaluation Runner for Step 11 — Extraction Evaluation & Benchmarking.
Allows running knowledge graph evaluation from the VS Code terminal against gold-standard datasets.

Usage:
  python run_step11_evaluation.py --dataset storage/eval_gold_sample.json
  python run_step11_evaluation.py --dataset path/to/gold.json --predictions path/to/preds.json
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add backend directory to sys.path for direct script invocation
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.evaluation.runner import EvaluationRunner
from app.evaluation.models import GoldDataset


def get_default_sample_predictions(dataset: GoldDataset) -> dict:
    """
    Generates representative sample prediction payload matching gold-standard dataset,
    allowing evaluation of saved predictions without calling Ollama or live model inference.
    """
    entities = []
    relations = []
    canonical_entities = []
    resolved_relations = []
    events = []
    all_candidates = []

    for doc in dataset.documents:
        for idx, g_ent in enumerate(doc.entities):
            ent_dict = {
                "entity_id": f"pred_ent_{idx + 1}",
                "entity_type": g_ent.entity_type,
                "text": g_ent.text,
                "normalized_value": g_ent.normalized_value or g_ent.text,
                "document_id": doc.document_id,
                "page_number": g_ent.page_number or 1,
                "source_text": f"Sample verbatim quote for {g_ent.text}",
                "start_offset": 10,
                "end_offset": 10 + len(g_ent.text),
                "confidence": 0.95,
            }
            entities.append(ent_dict)
            all_candidates.append(ent_dict)

        for idx, g_rel in enumerate(doc.relationships):
            rel_dict = {
                "relation_id": f"pred_rel_{idx + 1}",
                "relation_type": g_rel.relation_type,
                "source_entity_text": g_rel.source_entity_text,
                "target_entity_text": g_rel.target_entity_text,
                "document_id": doc.document_id,
                "page_number": g_rel.page_number or 1,
                "confidence": 0.90,
                "is_valid": True,
            }
            relations.append(rel_dict)

        # Build canonical entities from equivalence pairs
        for idx, pair in enumerate(doc.equivalence_pairs):
            if pair.are_equivalent:
                cname = pair.canonical_name or pair.entity_text_1
                canonical_entities.append(
                    {
                        "canonical_id": f"c_ent_{idx + 1}",
                        "canonical_name": cname,
                        "aliases": [pair.entity_text_1, pair.entity_text_2],
                        "mentions": [
                            {"text": pair.entity_text_1},
                            {"text": pair.entity_text_2},
                        ],
                        "document_id": doc.document_id,
                    }
                )

        for idx, g_evt in enumerate(doc.events):
            evt_dict = {
                "event_id": f"pred_evt_{idx + 1}",
                "event_type": g_evt.event_type,
                "description": g_evt.description,
                "event_date": g_evt.event_date,
                "source_document_id": doc.document_id,
                "source_page": g_evt.page_number or 1,
                "source_text": g_evt.description,
                "char_span": [5, 45],
            }
            events.append(evt_dict)

        # Build resolved relation linked to canonical entities
        if canonical_entities:
            resolved_relations.append(
                {
                    "relation_id": "r_rel_1",
                    "relation_type": "FILED_ACTION",
                    "source_entity_id": canonical_entities[0]["canonical_id"],
                    "target_entity_id": canonical_entities[-1]["canonical_id"],
                    "is_valid": True,
                }
            )

    return {
        "entities": entities,
        "relations": relations,
        "canonical_entities": canonical_entities,
        "resolved_relations": resolved_relations,
        "timeline_events": events,
        "all_candidates": all_candidates,
        "validation": {
            "validated_entities": canonical_entities,
            "validated_relationships": resolved_relations,
            "warnings": [],
            "review_required": [],
            "invalid_entities": [],
            "invalid_relationships": [],
        },
        "review_items": [],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Step 11 — LegalLens Extraction Evaluation & Benchmarking Runner"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="storage/eval_gold_sample.json",
        help="Path to gold-standard JSON dataset file.",
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default=None,
        help="Path to saved predictions JSON file. If omitted, uses dataset sample predictions.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="storage/eval_reports",
        help="Directory to save JSON evaluation report artifact.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress info log messages."
    )

    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    print("\nStarting Step 11 Legal Knowledge Graph Extraction Evaluation...")

    runner = EvaluationRunner()

    gold_ds = runner.load_gold_dataset(args.dataset)

    if args.predictions:
        preds = runner.load_predictions(args.predictions)
    else:
        print(
            "No predictions file specified — evaluating against sample fixture predictions."
        )
        preds = get_default_sample_predictions(gold_ds)

    report = runner.run_evaluation(
        gold_dataset_source=gold_ds,
        predictions_source=preds,
        output_dir=args.output_dir,
        model_config={
            "eval_mode": (
                "offline_fixture" if not args.predictions else "saved_predictions"
            )
        },
    )

    print("\n" + report.print_summary())
    print(
        f"\nEvaluation Complete! JSON report written to: {args.output_dir}/eval_report_{report.run_id}.json\n"
    )


if __name__ == "__main__":
    main()
