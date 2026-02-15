"""Local/global memory persistence for EvoQuant."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from nanobot.evoquant.models import EvalReport, StrategyGenome


class EvoMemoryStore:
    """Simple JSONL-backed store for alpha zoo and failure museum."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.alpha_zoo_path = self.base_dir / "alpha_zoo.jsonl"
        self.hall_path = self.base_dir / "hall_of_shame.jsonl"
        self.rules_path = self.base_dir / "meta_rules.jsonl"

    def _append(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def record_success(self, genome: StrategyGenome, report: EvalReport) -> None:
        self._append(
            self.alpha_zoo_path,
            {
                "strategy": asdict(genome),
                "report": asdict(report),
            },
        )

    def record_failure(self, genome: StrategyGenome, report: EvalReport) -> None:
        self._append(
            self.hall_path,
            {
                "strategy": asdict(genome),
                "report": asdict(report),
            },
        )

    def record_meta_rule(self, rule: str, support: float) -> None:
        self._append(self.rules_path, {"rule": rule, "support": support})

    def summarize_counts(self) -> dict[str, int]:
        def count(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(1 for _ in path.open("r", encoding="utf-8"))

        return {
            "alpha_zoo": count(self.alpha_zoo_path),
            "hall_of_shame": count(self.hall_path),
            "meta_rules": count(self.rules_path),
        }
