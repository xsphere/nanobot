"""Data loader for EvoQuant pilot.

This implementation provides deterministic synthetic data so the pipeline can
run end-to-end without external data dependencies.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from nanobot.evoquant.models import TaskConfig


@dataclass
class DataBundle:
    markets: dict[str, dict[str, list[float]]]


def _series(rng: random.Random, n: int, drift: float, noise: float) -> list[float]:
    out: list[float] = []
    value = 0.0
    for _ in range(n):
        value = drift + 0.4 * value + rng.uniform(-noise, noise)
        out.append(value)
    return out


def load(config: TaskConfig) -> DataBundle:
    """Load market-factor dataset for one run."""
    rng = random.Random(config.seed)
    markets: dict[str, dict[str, list[float]]] = {}
    for market in config.markets:
        returns = _series(rng, config.periods, drift=0.0006, noise=0.018)
        momentum = _series(rng, config.periods, drift=0.02, noise=0.2)
        value = _series(rng, config.periods, drift=0.0, noise=0.15)
        volatility = [abs(x) for x in _series(rng, config.periods, drift=0.1, noise=0.3)]
        flow = _series(rng, config.periods, drift=0.01, noise=0.22)
        markets[market] = {
            "returns": returns,
            "momentum": momentum,
            "value": value,
            "volatility": volatility,
            "flow": flow,
        }
    return DataBundle(markets=markets)
