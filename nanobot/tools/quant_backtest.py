"""Backtest engine for EvoQuant pilot."""

from __future__ import annotations

from dataclasses import dataclass

from nanobot.evoquant.models import StrategyGenome, TaskConfig
from nanobot.tools.quant_data import DataBundle


@dataclass
class BacktestResult:
    daily_returns: list[float]
    turnover: float


def _clip(v: float, low: float, high: float) -> float:
    return max(low, min(high, v))


def run(strategy: StrategyGenome, data: DataBundle, cfg: TaskConfig) -> BacktestResult:
    """Run simplified cross-market sector rotation + timing backtest."""
    alpha = strategy.slots["alpha_slot"]
    risk = strategy.slots["risk_slot"]
    exec_slot = strategy.slots["execution_slot"]
    max_weight = float(strategy.slots["portfolio_slot"]["max_weight"])
    cost_bps = float(exec_slot["cost_bps"])
    rebalance_days = int(exec_slot["rebalance_days"])

    n = cfg.periods
    markets = list(data.markets.keys())
    prev_weights = {m: 1.0 / len(markets) for m in markets}
    daily_returns: list[float] = []
    turnover = 0.0

    for t in range(n):
        scores: dict[str, float] = {}
        for m in markets:
            f = data.markets[m]
            score = (
                alpha["momentum_w"] * f["momentum"][t]
                + alpha["value_w"] * f["value"][t]
                + alpha["volatility_w"] * f["volatility"][t]
                + alpha["flow_w"] * f["flow"][t]
            )
            scores[m] = score

        # industry rotation weights
        denom = sum(abs(v) for v in scores.values()) + 1e-9
        raw_weights = {m: _clip(abs(scores[m]) / denom, 0.0, max_weight) for m in markets}
        sum_raw = sum(raw_weights.values()) + 1e-9
        weights = {m: raw_weights[m] / sum_raw for m in markets}

        # timing gate
        avg_vol = sum(data.markets[m]["volatility"][t] for m in markets) / len(markets)
        timing = 1.0 - risk["de_risk"] * _clip(avg_vol, 0.0, 1.0)
        timing = _clip(timing, 0.1, 1.2)

        ret = 0.0
        for m in markets:
            ret += weights[m] * data.markets[m]["returns"][t]

        if t % rebalance_days == 0:
            step_turnover = sum(abs(weights[m] - prev_weights[m]) for m in markets)
            turnover += step_turnover
            ret -= step_turnover * cost_bps / 10000.0
            prev_weights = dict(weights)

        # stop-loss style clamp
        ret = _clip(ret * timing, -risk["stop_loss"], 0.2)
        daily_returns.append(ret)

    return BacktestResult(daily_returns=daily_returns, turnover=turnover)
