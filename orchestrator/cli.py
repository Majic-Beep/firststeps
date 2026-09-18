"""Command-line entry point: `python -m orchestrator.cli --mode replay`."""
from __future__ import annotations

import argparse
import sys

from orchestrator.agent_runner import ClaudeAgentRunner, ReplayAgentRunner
from orchestrator.mandate import Mandate
from orchestrator.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI-Hedgefonds Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["replay", "live"],
        default="replay",
        help="'replay' re-runs the pipeline against the real 2026-09-17 fixtures "
        "(no API key needed). 'live' calls a real Claude agent per stage, but only "
        "Agents 2/4/5/7 are implemented (and unverified without ANTHROPIC_API_KEY) — "
        "a full --mode live run will fail at Agent 1. See "
        "orchestrator/agent_runner.py:ClaudeAgentRunner and docs/05-orchestrator.md.",
    )
    parser.add_argument(
        "--mandate",
        default="config/mandate.example.yaml",
        help="Path to the mandate/config YAML file.",
    )
    parser.add_argument(
        "--fixtures",
        default="orchestrator/fixtures/2026-09-17-eth-cycle",
        help="Fixture directory for --mode replay.",
    )
    parser.add_argument("--runs-dir", default="runs", help="Where to write the audit trail.")
    args = parser.parse_args(argv)

    mandate = Mandate.load(args.mandate)
    runner = ReplayAgentRunner(args.fixtures) if args.mode == "replay" else ClaudeAgentRunner()

    try:
        result = run_pipeline(runner, mandate, fixtures_dir=args.fixtures, runs_dir=args.runs_dir)
    except NotImplementedError as exc:
        print(f"Gestoppt: {exc}")
        print(
            "\n--mode live deckt bisher nur einzelne Reasoning-Stufen ab (Agent 2/4/5/7), "
            "keinen vollständigen Zyklus. Rufe ClaudeAgentRunner().run(stage, input_data) "
            "direkt für eine unterstützte Stufe auf, statt run_pipeline()."
        )
        return 1

    print(f"Run-ID: {result.run_id}")
    print(f"Audit-Trail: {result.run_dir}")
    print(f"Abgeschlossene Stufen: {', '.join(result.completed_stages)}")
    if result.halted_at:
        print(f"\nZyklus gestoppt bei: {result.halted_at}")
        print(f"Grund: {result.halt_reason}")
    else:
        print("\nZyklus vollständig durchgelaufen (Agent 1-6).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
