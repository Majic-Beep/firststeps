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
- ClaudeAgentRunner: a REAL implementation for the four pure-reasoning
  stages (Agent 2, 4, 5, 7) — see its own docstring for exactly what is
  implemented, what remains unsupported (Agent 1/3/6, which need real
  market-data/backtest/execution tool access this standalone script does
  not have), and — important — that the implemented part has NOT been
  exercised against the real Anthropic API in this environment (no API
  key was available here). It is untested code, clearly labeled as such,
  not a claim that it works.
"""
from __future__ import annotations

import json
import os
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


def _extract_prompt_block(markdown_text: str, heading_contains: str) -> str:
    """Pull one fenced ```...``` block out of an agents/0N-*.md file.

    Finds a line starting with "## System-Prompt" that also contains
    heading_contains (pass "" to match the first/only one in a file), then
    returns the content of the next fenced code block after that heading.
    This is a small, file-format-specific parser, not a general Markdown
    parser — it only needs to handle the exact structure of this repo's
    agents/*.md files.
    """
    search_from = 0
    while True:
        idx = markdown_text.find("## System-Prompt", search_from)
        if idx == -1:
            raise ValueError(
                f"Keine '## System-Prompt'-Überschrift mit {heading_contains!r} gefunden."
            )
        line_end = markdown_text.find("\n", idx)
        heading_line = markdown_text[idx:line_end]
        if heading_contains in heading_line:
            break
        search_from = line_end + 1

    fence_start = markdown_text.find("```", line_end)
    content_start = markdown_text.find("\n", fence_start) + 1
    fence_end = markdown_text.find("```", content_start)
    if fence_start == -1 or fence_end == -1:
        raise ValueError(f"Kein Code-Block nach Überschrift {heading_line!r} gefunden.")
    return markdown_text[content_start:fence_end].strip()


def _parse_json_response(raw_text: str) -> dict:
    """Best-effort extraction of a JSON object from a model's text reply."""
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        raw_text = parts[1] if len(parts) > 1 else raw_text
        if raw_text.lstrip().lower().startswith("json"):
            raw_text = raw_text.lstrip()[4:]
    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Antwort ist kein gültiges JSON: {exc}\n--- Rohtext ---\n{raw_text}"
        ) from exc


class ClaudeAgentRunner:
    """Real (but UNTESTED — see below) implementation for Agents 2, 4, 5, 7.

    ## Why only these four

    Agents 2 (Stratege), 4 (Risikomanager), 5 (Portfolio-Manager) and 7
    (Lern-Agent) are, by their own prompt design in agents/0N-*.md, pure
    LLM reasoning over data the orchestrator already assembles as
    input_data — they list their tool use as optional cross-checks at
    most, not a requirement. That makes a live call here a *complete*
    implementation for these four stages, not a stub.

    Agents 1 (Marktanalyst), 3 (Validator/Backtester) and 6
    (Execution-Trader) fundamentally require real tool access this
    standalone script does not have (TradingView market data, the
    tradingkit backtest engine, the Co-Invest trading platform — all MCP
    servers only connected inside a Claude Code session). Calling
    run() with one of those stage names raises NotImplementedError rather
    than pretending to work with a degraded, tool-less prompt.

    ## Status: implemented, NOT verified against the real API

    This environment had no ANTHROPIC_API_KEY and no `anthropic` package
    installed when this class was written, so the actual API call path
    below has never been executed successfully end to end. What HAS been
    tested (see orchestrator/tests/test_claude_agent_runner.py, runs
    without any key): prompt extraction from the real agents/*.md files,
    and that the unsupported stages and the missing-key case raise the
    right errors. The `anthropic.messages.create(...)` call itself, and
    whether the four agents' real prompts reliably produce schema-valid
    JSON from a live model, are unverified. Test this yourself with a
    real key before relying on it:

        pip install -r requirements-live.txt
        export ANTHROPIC_API_KEY=sk-ant-...
        python -m unittest orchestrator.tests.test_claude_agent_runner -v

    ## Agent 2 is three calls, not one

    agents/02-strategy-researcher.md defines three separate prompts
    (Bull-Researcher, Bear-Researcher, Moderator) and explicitly
    recommends keeping them as separate calls so the model can't "agree
    with itself". This runner does the same: Bull runs on the market
    brief alone, Bear runs on the market brief plus the Bull output, and
    the Moderator runs on all three and produces the final hypotheses
    JSON that the pipeline actually uses.
    """

    SUPPORTED_STAGES = {
        "agent2_strategist",
        "agent4_risk_manager",
        "agent5_portfolio_manager",
        "agent7_learning",
    }

    _PROMPT_FILES = {
        "agent4_risk_manager": "04-risk-manager.md",
        "agent5_portfolio_manager": "05-portfolio-manager.md",
        "agent7_learning": "07-learning-postmortem.md",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        agents_dir: str | Path = "agents",
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        self.agents_dir = Path(agents_dir)

    def run(self, stage: str, input_data: dict) -> dict:
        if stage not in self.SUPPORTED_STAGES:
            raise NotImplementedError(
                f"ClaudeAgentRunner unterstützt Stufe '{stage}' nicht — sie braucht echten "
                f"Markt-/Backtest-/Ausführungs-Tool-Zugriff, den dieses eigenständige Skript "
                f"nicht hat (siehe Klassen-Docstring). Nur {sorted(self.SUPPORTED_STAGES)} "
                f"sind live implementiert."
            )
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY nicht gesetzt — ein Live-Aufruf ist ohne Key nicht möglich."
            )
        if stage == "agent2_strategist":
            return self._run_agent2(input_data)

        markdown = (self.agents_dir / self._PROMPT_FILES[stage]).read_text(encoding="utf-8")
        system_prompt = _extract_prompt_block(markdown, "")
        return self._call_claude(system_prompt, input_data)

    def _run_agent2(self, input_data: dict) -> dict:
        markdown = (self.agents_dir / "02-strategy-researcher.md").read_text(encoding="utf-8")
        bull_prompt = _extract_prompt_block(markdown, "Bull-Researcher")
        bear_prompt = _extract_prompt_block(markdown, "Bear-Researcher")
        moderator_prompt = _extract_prompt_block(markdown, "Moderator")

        market_brief = input_data["market_brief"]
        bull_output = self._call_claude(bull_prompt, {"market_brief": market_brief})
        bear_output = self._call_claude(
            bear_prompt, {"market_brief": market_brief, "bull_thesis": bull_output}
        )
        return self._call_claude(
            moderator_prompt,
            {
                "market_brief": market_brief,
                "bull_thesis": bull_output,
                "bear_thesis": bear_output,
            },
        )

    def _call_claude(self, system_prompt: str, input_data: dict) -> dict:
        import anthropic  # lazy import — only required when live mode is actually used

        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Eingabedaten (JSON):\n"
                        + json.dumps(input_data, ensure_ascii=False, indent=2)
                        + "\n\nAntworte AUSSCHLIESSLICH mit dem im System-Prompt geforderten "
                        "JSON-Objekt — kein Fließtext davor oder danach."
                    ),
                }
            ],
        )
        raw_text = "".join(block.text for block in message.content if block.type == "text")
        return _parse_json_response(raw_text)
