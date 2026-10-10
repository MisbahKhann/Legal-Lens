"""
Evaluation Runner for LegalLens Step 11.
Handles loading gold-standard datasets (JSON/JSONL) and saved system predictions,
running the evaluation engine, writing machine-readable JSON reports,
and rendering human-readable summaries.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

from app.evaluation.models import GoldDataset, Step11EvaluationReport
from app.evaluation.evaluator import KnowledgeGraphEvaluator

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Runner for loading evaluation inputs, calculating metrics via KnowledgeGraphEvaluator,
    and persisting evaluation reports.
    """

    def __init__(self, evaluator: Optional[KnowledgeGraphEvaluator] = None):
        self.evaluator = evaluator or KnowledgeGraphEvaluator()

    @staticmethod
    def load_gold_dataset(file_path: str) -> GoldDataset:
        """
        Loads a gold-standard dataset from a JSON file.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"Gold-standard dataset file not found: {file_path}"
            )

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return GoldDataset.model_validate(data)

    @staticmethod
    def load_predictions(
        predictions_source: Union[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Loads system predictions from a JSON file path or returns dictionary directly.
        """
        if isinstance(predictions_source, dict):
            return predictions_source

        path = Path(predictions_source)
        if not path.is_file():
            raise FileNotFoundError(f"Predictions file not found: {predictions_source}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluation(
        self,
        gold_dataset_source: Union[str, GoldDataset],
        predictions_source: Union[str, Dict[str, Any]],
        output_dir: Optional[str] = "storage/eval_reports",
        model_config: Optional[Dict[str, Any]] = None,
    ) -> Step11EvaluationReport:
        """
        Executes evaluation pipeline and saves JSON evaluation report.
        """
        # 1. Load gold dataset
        if isinstance(gold_dataset_source, GoldDataset):
            gold_ds = gold_dataset_source
        else:
            gold_ds = self.load_gold_dataset(str(gold_dataset_source))

        # 2. Load predictions
        preds = self.load_predictions(predictions_source)

        # 3. Compute evaluation report
        report = self.evaluator.run_full_evaluation(
            gold_dataset=gold_ds,
            predictions=preds,
            model_config=model_config,
        )

        # 4. Save JSON report if output_dir provided
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            report_file = out_path / f"eval_report_{report.run_id}.json"

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))

            logger.info(f"Saved evaluation report to {report_file}")

        return report
