"""Mutation and crossover for slot-based genomes."""

from __future__ import annotations

import copy
import random
from uuid import uuid4

from nanobot.evoquant.models import EvalReport, StrategyGenome, TaskConfig


def mutate(genome: StrategyGenome, report: EvalReport, cfg: TaskConfig, rng: random.Random) -> StrategyGenome:
    """Priority-guided slot mutation."""
    child = copy.deepcopy(genome)
    child.id = f"g{genome.generation + 1}-{uuid4().hex[:8]}"
    child.generation = genome.generation + 1
    child.parent_ids = [genome.id]

    tags = set(report.diagnosis_tags)
    if "low_dsr" in tags:
        child.slots["alpha_slot"]["momentum_w"] = round(
            child.slots["alpha_slot"]["momentum_w"] + rng.uniform(-0.1, 0.15), 3
        )
        child.slots["alpha_slot"]["value_w"] = round(
            max(0.0, child.slots["alpha_slot"]["value_w"] + rng.uniform(-0.05, 0.1)), 3
        )
    if "high_mdd" in tags:
        child.slots["risk_slot"]["stop_loss"] = round(
            max(0.02, child.slots["risk_slot"]["stop_loss"] - rng.uniform(0.005, 0.02)), 3
        )
        child.slots["risk_slot"]["de_risk"] = round(
            min(0.9, child.slots["risk_slot"]["de_risk"] + rng.uniform(0.02, 0.08)), 3
        )
    if "high_turnover" in tags:
        child.slots["execution_slot"]["rebalance_days"] = int(
            min(20, child.slots["execution_slot"]["rebalance_days"] + 5)
        )
    if "style_drift" in tags:
        child.slots["portfolio_slot"]["max_weight"] = round(
            max(0.2, child.slots["portfolio_slot"]["max_weight"] - 0.05), 3
        )

    child.metadata["mutation_reason"] = sorted(tags)
    return child


def crossover(a: StrategyGenome, b: StrategyGenome) -> StrategyGenome:
    """Compositional crossover: alpha from A, risk/execution from B."""
    child = copy.deepcopy(a)
    child.id = f"g{max(a.generation, b.generation) + 1}-{uuid4().hex[:8]}"
    child.generation = max(a.generation, b.generation) + 1
    child.parent_ids = [a.id, b.id]
    child.slots["risk_slot"] = copy.deepcopy(b.slots["risk_slot"])
    child.slots["execution_slot"] = copy.deepcopy(b.slots["execution_slot"])
    child.metadata["crossover"] = "alpha<-A,risk_execution<-B"
    return child


def evolve_population(
    ranked: list[tuple[StrategyGenome, EvalReport]], cfg: TaskConfig, rng: random.Random
) -> list[StrategyGenome]:
    """Build next generation with elitism + mutation + crossover."""
    elites = [g for g, _ in ranked[: max(2, cfg.top_k)]]
    next_population: list[StrategyGenome] = [copy.deepcopy(elites[0])]

    for g, r in ranked[: cfg.population_size // 2]:
        if rng.random() < cfg.mutation_rate:
            next_population.append(mutate(g, r, cfg, rng))

    while len(next_population) < cfg.population_size and len(elites) > 1:
        if rng.random() < cfg.crossover_rate:
            next_population.append(crossover(elites[0], elites[1]))
        else:
            next_population.append(copy.deepcopy(rng.choice(elites)))

    return next_population[: cfg.population_size]
