"""Evaluation and attribution for EvoQuant pilot."""

from __future__ import annotations

import math
from statistics import mean, pstdev

from nanobot.evoquant.models import EvalMetrics, EvalReport
from nanobot.tools.quant_backtest import BacktestResult


def _max_drawdown(returns: list[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd


def _regime_robustness(returns: list[float]) -> float:
    if len(returns) < 6:
        return 0.0
    chunk = len(returns) // 3
    a = mean(returns[:chunk])
    b = mean(returns[chunk : 2 * chunk])
    c = mean(returns[2 * chunk :])
    vals = [a, b, c]
    m = mean(vals)
    s = pstdev(vals) if len(vals) > 1 else 0.0
    return max(0.0, 1.0 - (s / (abs(m) + 1e-9)))


def evaluate(strategy_id: str, result: BacktestResult) -> EvalReport:
    """Convert backtest result into unified metrics + diagnosis tags."""
    dr = result.daily_returns
    avg = mean(dr) if dr else 0.0
    vol = pstdev(dr) if len(dr) > 1 else 0.0
    arr = avg * 252
    sharpe = (avg / (vol + 1e-9)) * math.sqrt(252)
    mdd = _max_drawdown(dr)
    rank_ic = avg / (vol + 1e-6)
    regime = _regime_robustness(dr)

    # Simplified deflated Sharpe approximation.
    dsr = sharpe - 0.35

    fitness = 0.35 * dsr + 0.25 * rank_ic + 0.25 * regime - 0.1 * result.turnover - 0.05 * mdd

    tags: list[str] = []
    if dsr < 0.2:
        tags.append("low_dsr")
    if mdd > 0.2:
        tags.append("high_mdd")
    if result.turnover > 2.5:
        tags.append("high_turnover")
    if regime < 0.35:
        tags.append("style_drift")

    report = EvalReport(
        strategy_id=strategy_id,
        metrics=EvalMetrics(
            arr=arr,
            vol=vol,
            sharpe=sharpe,
            dsr=dsr,
            mdd=mdd,
            rank_ic=rank_ic,
            turnover=result.turnover,
            regime_robustness=regime,
            fitness=fitness,
        ),
        diagnosis_tags=tags,
        attribution_summary={
            "alpha_contrib": 0.6,
            "timing_contrib": 0.25,
            "risk_contrib": 0.15,
        },
    )
    return report
