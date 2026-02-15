"""Diversified planner for initializing strategy genomes."""

from __future__ import annotations

import random
from uuid import uuid4

from nanobot.evoquant.models import StrategyGenome, TaskConfig


ROUTES = ["macro", "fundamental", "quant", "event"]


def _random_slot(rng: random.Random, route: str) -> dict[str, dict[str, float | str]]:
    return {
        "data_slot": {"normalize": "zscore", "winsor": 0.03},
        "alpha_slot": {
            "route": route,
            "momentum_w": round(rng.uniform(0.1, 0.8), 3),
            "value_w": round(rng.uniform(0.0, 0.6), 3),
            "volatility_w": round(rng.uniform(-0.7, -0.1), 3),
            "flow_w": round(rng.uniform(0.0, 0.4), 3),
        },
        "portfolio_slot": {"max_weight": round(rng.uniform(0.25, 0.5), 3)},
        "risk_slot": {
            "stop_loss": round(rng.uniform(0.04, 0.12), 3),
            "de_risk": round(rng.uniform(0.2, 0.7), 3),
        },
        "execution_slot": {
            "rebalance_days": int(rng.choice([5, 10, 20])),
            "cost_bps": round(rng.uniform(2, 10), 2),
        },
    }


def build_initial_population(config: TaskConfig) -> list[StrategyGenome]:
    """Build diversified initial strategy population."""
    rng = random.Random(config.seed)
    genomes: list[StrategyGenome] = []
    for i in range(config.population_size):
        route = ROUTES[i % len(ROUTES)]
        genomes.append(
            StrategyGenome(
                id=f"g0-{uuid4().hex[:8]}",
                generation=0,
                route=route,
                slots=_random_slot(rng, route),
                metadata={"hypothesis": f"{route} driven sector rotation"},
            )
        )
    return genomes
