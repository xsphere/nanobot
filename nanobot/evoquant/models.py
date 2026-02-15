"""Core domain models for EvoQuant pilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TaskConfig:
    """Execution config for one nightly evolution run."""

    run_id: str
    markets: list[str] = field(default_factory=lambda: ["cn_sector", "us_sector"])
    periods: int = 252
    population_size: int = 12
    generations: int = 4
    mutation_rate: float = 0.4
    crossover_rate: float = 0.4
    top_k: int = 3
    seed: int = 42
    mdd_limit: float = 0.2
    turnover_limit: float = 2.5
    output_dir: str = "workspace/runs/evoquant"


@dataclass
class StrategyGenome:
    """Slot-based strategy representation."""

    id: str
    generation: int
    parent_ids: list[str] = field(default_factory=list)
    route: str = "quant"
    slots: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalMetrics:
    """Unified evaluation metrics for one strategy."""

    arr: float
    vol: float
    sharpe: float
    dsr: float
    mdd: float
    rank_ic: float
    turnover: float
    regime_robustness: float
    fitness: float


@dataclass
class EvalReport:
    """Detailed report used by mutator and risk gate."""

    strategy_id: str
    metrics: EvalMetrics
    diagnosis_tags: list[str] = field(default_factory=list)
    attribution_summary: dict[str, float] = field(default_factory=dict)
    passed_risk_gate: bool = True
    risk_reasons: list[str] = field(default_factory=list)


@dataclass
class EvolutionResult:
    """Final result for a full run."""

    config: TaskConfig
    timestamp: datetime
    top_candidates: list[EvalReport]
    reports: list[EvalReport]
    memory_updates: dict[str, int]
