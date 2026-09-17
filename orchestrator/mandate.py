"""Loads the risk mandate (config/mandate.example.yaml or a real mandate.yaml).

The orchestrator reads these limits as plain data. No agent, and no code in
this package, ever writes back to this file — see agents/04-risk-manager.md,
"Hinweise zur Implementierung".
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Mandate:
    initial_capital: float
    universe: list[str]
    max_position_pct_per_symbol: float
    max_position_pct_per_cluster: float
    correlation_cluster_threshold: float
    max_daily_loss_pct: float
    max_leverage: float
    min_trades_for_statistical_significance: int
    require_out_of_sample_test: bool

    @staticmethod
    def load(path: str | Path) -> "Mandate":
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        limits = raw["risk_limits"]
        validation = raw.get("validation_limits", {})
        return Mandate(
            initial_capital=float(raw["capital"]["initial_capital"]),
            universe=list(raw.get("universe", [])),
            max_position_pct_per_symbol=float(limits["max_position_pct_per_symbol"]),
            max_position_pct_per_cluster=float(limits["max_position_pct_per_cluster"]),
            correlation_cluster_threshold=float(limits["correlation_cluster_threshold"]),
            max_daily_loss_pct=float(limits["max_daily_loss_pct"]),
            max_leverage=float(limits["max_leverage"]),
            min_trades_for_statistical_significance=int(
                validation.get("min_trades_for_statistical_significance", 30)
            ),
            require_out_of_sample_test=bool(
                validation.get("require_out_of_sample_test", True)
            ),
        )
