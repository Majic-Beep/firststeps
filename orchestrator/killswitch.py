"""Deterministic, code-level safety checks.

docs/02-architektur.md is explicit that risk limits are "a case where
deterministic code and LLM judgment should back each other up" — an agent
can misread its own instructions, so the orchestrator re-checks the hard
limits itself instead of trusting Agent 4's or Agent 5's output blindly.
These functions never call an LLM and never guess; they only compare
numbers that are already in the pipeline's own JSON against the mandate.
"""
from __future__ import annotations

from orchestrator.mandate import Mandate


class KillSwitchTriggered(Exception):
    """Raised when a hard, non-negotiable limit is breached.

    Stops the pipeline before the next stage runs — see the "Kill-Switches
    zwischen jeder Stufe" requirement in docs/02-architektur.md.
    """


def check_daily_loss_limit(daily_pnl_pct: float, mandate: Mandate) -> None:
    if daily_pnl_pct < 0 and abs(daily_pnl_pct) > mandate.max_daily_loss_pct:
        raise KillSwitchTriggered(
            f"Tagesverlust {daily_pnl_pct:.1%} überschreitet das Mandats-Limit "
            f"von {mandate.max_daily_loss_pct:.1%}. Pipeline gestoppt vor der "
            f"nächsten Stufe, unabhängig davon, was ein Agent vorschlägt."
        )


def check_global_veto(risk_verdict: dict) -> None:
    if risk_verdict.get("global_veto"):
        reason = risk_verdict.get("global_veto_reason", "kein Grund angegeben")
        raise KillSwitchTriggered(
            f"Agent 4 hat ein globales Veto ausgesprochen: {reason}. "
            f"Agent 5/6 werden für diesen Zyklus nicht aufgerufen."
        )


def check_position_size_ceiling(approved_orders: dict, risk_verdict: dict) -> None:
    """Re-verify that Agent 5 never exceeded the ceiling Agent 4 set.

    max_position_pct from Agent 4 is a hard upper bound (agents/05, Regel 2).
    This does not re-judge whether Agent 5's choice was *wise* — only
    whether it stayed within the number Agent 4 already committed to.
    """
    ceilings = {v["symbol"]: v["max_position_pct"] for v in risk_verdict.get("verdicts", [])}
    for order in approved_orders.get("approved_orders", []):
        symbol = order["symbol"]
        ceiling = ceilings.get(symbol)
        if ceiling is not None and order["position_pct"] > ceiling:
            raise KillSwitchTriggered(
                f"Order für {symbol} ({order['position_pct']:.1%}) überschreitet "
                f"die von Agent 4 gesetzte Obergrenze ({ceiling:.1%}). "
                f"Das darf laut agents/05-portfolio-manager.md, Regel 2, nie passieren "
                f"— Pipeline gestoppt statt die Order stillschweigend zu kappen."
            )


def check_leverage(order_leverage: float, mandate: Mandate) -> None:
    if order_leverage > mandate.max_leverage:
        raise KillSwitchTriggered(
            f"Angeforderter Hebel {order_leverage}x überschreitet das "
            f"Mandats-Limit von {mandate.max_leverage}x."
        )
