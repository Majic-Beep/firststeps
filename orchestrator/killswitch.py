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


def check_tp_sl_proposed(execution_report: dict) -> None:
    """Every position-opening execution must have a proposed protective order.

    Added directly as a result of Agent 7's first real post-mortem
    (tests/phase1-agent7/): the 2026-09-17 ETH cycle was prepared and
    confirmed WITHOUT take-profit/stop-loss, in violation of
    agents/06-execution-trader.md, Regel 3. That was a clear-cut rule
    violation, not ambiguous outcome variance, so it is enforced here in
    code rather than left to an agent remembering the rule next time.

    What "tp_sl_proposed: true" requires is platform-dependent, and
    agents/06-execution-trader.md is the source of truth per platform:
    - Co-Invest (human-confirmed): both take-profit AND stop-loss must be
      proposed, as originally required.
    - Alpaca (autonomous execution, added 2026-09-21): stop-loss ALONE
      satisfies this flag. A real test on 2026-09-20/21 showed Alpaca
      rejects both `bracket` and `oco` order classes for crypto, and two
      independent resting sell orders (a TP limit and an SL stop_limit)
      cannot coexist — each tries to reserve the full position, so the
      second is rejected with "insufficient balance". Risk protection
      (stop-loss) was deliberately prioritized over profit-taking
      (take-profit) for this platform — see agents/06 for the full
      rationale. This function does not need to know which platform
      produced the report; it only checks the flag Agent 6 already
      set correctly per its own platform-specific rules.
    """
    opens = {"prepared_awaiting_human_confirmation", "executed"}
    for execution in execution_report.get("executions", []):
        if execution["status"] in opens and not execution.get("tp_sl_proposed"):
            raise KillSwitchTriggered(
                f"{execution['symbol']}: Position wird eröffnet/vorbereitet ohne "
                f"vorgeschlagenes Take-Profit/Stop-Loss (bzw. mindestens Stop-Loss "
                f"auf Plattformen, die kein gleichzeitiges TP+SL erlauben, siehe "
                f"agents/06-execution-trader.md). Das verletzt Regel 3 — Pipeline "
                f"gestoppt, bevor die Order als abgeschlossen gilt."
            )


def check_leverage(order_leverage: float, mandate: Mandate) -> None:
    if order_leverage > mandate.max_leverage:
        raise KillSwitchTriggered(
            f"Angeforderter Hebel {order_leverage}x überschreitet das "
            f"Mandats-Limit von {mandate.max_leverage}x."
        )
