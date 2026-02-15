"""Risk/compliance checks for EvoQuant pilot."""

from __future__ import annotations

from nanobot.evoquant.models import EvalReport, StrategyGenome, TaskConfig


def scan(strategy: StrategyGenome, report: EvalReport, cfg: TaskConfig) -> EvalReport:
    """Apply risk gates to evaluation report."""
    reasons: list[str] = []
    if report.metrics.mdd > cfg.mdd_limit:
        reasons.append("mdd_limit_exceeded")
    if report.metrics.turnover > cfg.turnover_limit:
        reasons.append("turnover_limit_exceeded")

    alpha = strategy.slots.get("alpha_slot", {})
    if alpha.get("momentum_w", 0) > 1.2:
        reasons.append("suspicious_alpha_weight")

    report.passed_risk_gate = len(reasons) == 0
    report.risk_reasons = reasons
    return report
