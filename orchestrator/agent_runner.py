"""Pluggable interface between the deterministic pipeline and an actual agent.

The orchestrator itself contains no LLM calls and no market-data/broker
integrations — that would duplicate what the MCP tools (TradingView,
tradingkit, Co-Invest) already do inside a Claude Code session, and this
package needs to run as a plain, testable Python script outside that
session too.

Two implementations are provided:

- ReplayAgentRunner: reads back the real, already-validated pipeline
  output from 2026-09-17 (see orchestrator/fixtures/). This is what the
  test suite and the `replay` CLI mode use — it proves the deterministic
  scaffolding (schema validation, kill-switches, audit trail) actually
  works, using real numbers, without needing any API key.
- ClaudeAgentRunner: a documented extension point for wiring this up to
  a real, live Claude API call per stage. It is intentionally NOT a full
  implementation — see its docstring for exactly what is missing and why.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class AgentRunner(Protocol):
    def run(self, stage: str, input_data: dict) -> dict:
        """Return the agent's JSON output for this stage, given its input."""
        ...


class ReplayAgentRunner:
    """Replays a fixed set of real fixture files, one per stage.

    fixtures_dir must contain "<stage>.json" for each stage name in
    orchestrator.schemas.SCHEMAS_BY_STAGE. See
    orchestrator/fixtures/2026-09-17-eth-cycle/ for the concrete example
    this repo ships, reshaped from tests/chain-agent1-2-3-4-5-6/ into the
    canonical schemas in orchestrator/schemas.py.
    """

    def __init__(self, fixtures_dir: str | Path):
        self.fixtures_dir = Path(fixtures_dir)

    def run(self, stage: str, input_data: dict) -> dict:
        fixture_path = self.fixtures_dir / f"{stage}.json"
        if not fixture_path.exists():
            raise FileNotFoundError(
                f"Kein Fixture für Stufe '{stage}' unter {fixture_path} — "
                f"ReplayAgentRunner kann diese Stufe nicht simulieren."
            )
        return json.loads(fixture_path.read_text(encoding="utf-8"))


class ClaudeAgentRunner:
    """Extension point for a real, live agent call — NOT implemented here.

    To make this real, three things are needed that are deliberately out
    of scope for this repo's orchestrator code:

    1. An Anthropic API key and the `anthropic` Python package, to send
       the relevant agents/0N-*.md system prompt plus `input_data` as a
       message and parse the JSON response.
    2. Real tool access for whichever data source that stage's prompt
       calls for (TradingView for Agent 1, tradingkit for Agent 3,
       Co-Invest for Agent 6, ...). Inside a Claude Code session these
       are MCP servers already connected to that session; a standalone
       script has no equivalent unless someone wires up direct REST
       clients for each one.
    3. For Agent 6 specifically: docs/06 and the real test in
       tests/phase1-agent6/ found that Co-Invest requires a human to
       confirm every order via a review link — this runner must stop at
       "prepared_awaiting_human_confirmation" and hand that link back to
       a person, exactly like the pipeline already does in replay mode.
       It must never be modified to auto-confirm.
    """

    def run(self, stage: str, input_data: dict) -> dict:
        raise NotImplementedError(
            "ClaudeAgentRunner is a documented extension point, not a working "
            "implementation — see this class's docstring for what is missing "
            "before it can be used for a real run."
        )
