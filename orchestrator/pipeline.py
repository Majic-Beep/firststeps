"""Runs the seven-agent pipeline in fixed order.

This is the "Orchestrierung" from docs/02-architektur.md, made concrete:
- agents run in a fixed sequence (no LLM decides what runs next),
- every output is validated against its schema before moving on,
- hard risk limits are re-checked in code between stages (see
  orchestrator/killswitch.py) — an agent's own judgment is never the only
  line of defense,
- every stage's input and output is persisted (orchestrator/audit.py),
- Agent 6 never auto-executes: if the runner does not report every order
  as "executed", the pipeline stops there and Agent 7 is skipped for this
  cycle — this mirrors the real finding in tests/phase1-agent6/.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orchestrator import killswitch, schemas
from orchestrator.agent_runner import AgentRunner
from orchestrator.audit import AuditTrail
from orchestrator.mandate import Mandate

STAGES = [
    "agent1_market_analyst",
    "agent2_strategist",
    "agent3_validator",
    "agent4_risk_manager",
    "agent5_portfolio_manager",
    "agent6_execution_trader",
    "agent7_learning",  # conditional — only runs once every order is "executed"
]


class PipelineHalted(Exception):
    """Raised (and caught by run_pipeline) when a stage stops the cycle early.

    This is not a crash — a kill-switch trip, a global veto, or an
    execution stage still awaiting human confirmation are all expected,
    valid outcomes of a cycle, exactly as agents/05-portfolio-manager.md
    and agents/06-execution-trader.md describe.
    """


@dataclass
class PipelineResult:
    run_id: str
    run_dir: Path
    completed_stages: list[str]
    halted_at: str | None
    halt_reason: str | None
    outputs: dict[str, Any]


def _load_portfolio_context(fixtures_dir: Path) -> dict:
    path = fixtures_dir / "portfolio_context.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_pipeline(
    runner: AgentRunner,
    mandate: Mandate,
    fixtures_dir: str | Path,
    runs_dir: str | Path = "runs",
) -> PipelineResult:
    fixtures_dir = Path(fixtures_dir)
    audit = AuditTrail(runs_dir=runs_dir)
    outputs: dict[str, Any] = {}
    portfolio = _load_portfolio_context(fixtures_dir)

    try:
        # --- Agent 1: Marktanalyst ------------------------------------
        stage = "agent1_market_analyst"
        input_data = {"universe": mandate.universe}
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Agent 2: Stratege -----------------------------------------
        stage = "agent2_strategist"
        input_data = {"market_brief": outputs["agent1_market_analyst"]}
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Agent 3: Validator ------------------------------------------
        stage = "agent3_validator"
        input_data = {"hypotheses": outputs["agent2_strategist"]}
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Kill-switch pre-check before risk review ---------------------
        stage = "killswitch:daily_loss_limit"
        killswitch.check_daily_loss_limit(portfolio["daily_pnl_pct"], mandate)

        # --- Agent 4: Risikomanager --------------------------------------
        stage = "agent4_risk_manager"
        input_data = {
            "validated_hypotheses": outputs["agent3_validator"],
            "current_portfolio": portfolio,
            "mandate_limits": {
                "max_position_pct_per_symbol": mandate.max_position_pct_per_symbol,
                "max_position_pct_per_cluster": mandate.max_position_pct_per_cluster,
                "correlation_cluster_threshold": mandate.correlation_cluster_threshold,
                "max_daily_loss_pct": mandate.max_daily_loss_pct,
            },
        }
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Kill-switch: a global veto stops the cycle here, not later --
        stage = "killswitch:global_veto"
        killswitch.check_global_veto(outputs["agent4_risk_manager"])

        # --- Agent 5: Portfolio-Manager ----------------------------------
        stage = "agent5_portfolio_manager"
        input_data = {
            "risk_verdict": outputs["agent4_risk_manager"],
            "current_portfolio": portfolio,
        }
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Kill-switch: re-verify Agent 5 respected Agent 4's ceilings -
        stage = "killswitch:position_size_ceiling"
        killswitch.check_position_size_ceiling(
            outputs["agent5_portfolio_manager"], outputs["agent4_risk_manager"]
        )

        # --- Agent 6: Execution-Trader ------------------------------------
        stage = "agent6_execution_trader"
        input_data = {"approved_orders": outputs["agent5_portfolio_manager"]}
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

        # --- Kill-switch: no position opens without a proposed TP/SL -----
        stage = "killswitch:tp_sl_proposed"
        killswitch.check_tp_sl_proposed(outputs["agent6_execution_trader"])

        # --- Agent 7 gate: only proceed once orders are actually filled --
        pending = [
            e for e in output["executions"] if e["status"] != "executed"
        ]
        if pending:
            reason = (
                f"{len(pending)} von {len(output['executions'])} Order(s) warten auf "
                f"menschliche Bestätigung (Status "
                f"'{pending[0]['status']}') — Agent 7 (Lern-Agent) wird für diesen "
                f"Zyklus übersprungen, siehe tests/phase1-agent6/evaluation-2026-09-17.md."
            )
            audit.record_stopped("agent7_learning", reason)
            raise PipelineHalted(reason)

        # --- Agent 7: Lern-Agent -------------------------------------------
        stage = "agent7_learning"
        input_data = {
            "hypothesis": outputs["agent2_strategist"],
            "validation": outputs["agent3_validator"],
            "risk_verdict": outputs["agent4_risk_manager"],
            "approved_orders": outputs["agent5_portfolio_manager"],
            "execution_report": outputs["agent6_execution_trader"],
            "prior_cycles": [],
        }
        output = _run_stage(runner, audit, stage, input_data)
        outputs[stage] = output

    except (killswitch.KillSwitchTriggered, PipelineHalted) as exc:
        audit.finalize()
        return PipelineResult(
            run_id=audit.run_id,
            run_dir=audit.run_dir,
            completed_stages=list(outputs.keys()),
            halted_at=stage,
            halt_reason=str(exc),
            outputs=outputs,
        )

    audit.finalize()
    return PipelineResult(
        run_id=audit.run_id,
        run_dir=audit.run_dir,
        completed_stages=list(outputs.keys()),
        halted_at=None,
        halt_reason=None,
        outputs=outputs,
    )


def _run_stage(runner: AgentRunner, audit: AuditTrail, stage: str, input_data: dict) -> dict:
    output = runner.run(stage, input_data)
    schemas.validate(output, schemas.SCHEMAS_BY_STAGE[stage])
    audit.record(stage, input_data, output, status="ok")
    return output
