"""End-to-end EvoQuant nightly evolution engine."""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from nanobot.evoquant.memory import EvoMemoryStore
from nanobot.evoquant.models import EvalReport, EvolutionResult, TaskConfig
from nanobot.evoquant.mutator import evolve_population
from nanobot.evoquant.planner import build_initial_population
from nanobot.tools import quant_backtest, quant_data, quant_eval, quant_riskcheck


def _write_report(run_dir: Path, reports: list[EvalReport], top_k: int) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "top_k": top_k,
        "reports": [asdict(r) for r in reports],
    }
    (run_dir / "report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def run_evolution(config: TaskConfig) -> EvolutionResult:
    """Run full nightly evolution and persist outputs."""
    rng = random.Random(config.seed)
    data = quant_data.load(config)
    population = build_initial_population(config)
    memory = EvoMemoryStore(Path(config.output_dir) / "memory")

    all_reports: list[EvalReport] = []

    for _ in range(config.generations):
        ranked: list[tuple] = []
        for genome in population:
            bt = quant_backtest.run(genome, data, config)
            rep = quant_eval.evaluate(genome.id, bt)
            rep = quant_riskcheck.scan(genome, rep, config)
            ranked.append((genome, rep))
            all_reports.append(rep)

            if rep.passed_risk_gate:
                memory.record_success(genome, rep)
            else:
                memory.record_failure(genome, rep)

        ranked.sort(key=lambda x: x[1].metrics.fitness, reverse=True)
        population = evolve_population(ranked, config, rng)

    final_ranked = sorted(all_reports, key=lambda r: r.metrics.fitness, reverse=True)
    top_candidates = [r for r in final_ranked if r.passed_risk_gate][: config.top_k]

    if top_candidates:
        memory.record_meta_rule("prefer lower turnover under weak DSR", support=0.67)

    timestamp = datetime.utcnow()
    run_dir = Path(config.output_dir) / config.run_id
    _write_report(run_dir, final_ranked, config.top_k)

    return EvolutionResult(
        config=config,
        timestamp=timestamp,
        top_candidates=top_candidates,
        reports=final_ranked,
        memory_updates=memory.summarize_counts(),
    )
