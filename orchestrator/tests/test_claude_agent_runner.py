"""Tests for ClaudeAgentRunner.

Most of these run without any API key and exercise real, testable code
(prompt extraction from the actual agents/*.md files, error handling for
unsupported stages / missing key). The one test that calls the real
Anthropic API is explicitly skipped unless ANTHROPIC_API_KEY is set, so a
green test run never implies that path has actually been verified — see
ClaudeAgentRunner's docstring in orchestrator/agent_runner.py.
"""
import os
import unittest
from pathlib import Path

from orchestrator.agent_runner import ClaudeAgentRunner, _extract_prompt_block

AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"
HAS_API_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))


class TestUnsupportedStagesAndErrors(unittest.TestCase):
    """Runs without a key: these are pure control-flow checks."""

    def test_agent1_raises_not_implemented(self):
        runner = ClaudeAgentRunner(api_key="dummy-key-not-used")
        with self.assertRaises(NotImplementedError):
            runner.run("agent1_market_analyst", {})

    def test_agent3_raises_not_implemented(self):
        runner = ClaudeAgentRunner(api_key="dummy-key-not-used")
        with self.assertRaises(NotImplementedError):
            runner.run("agent3_validator", {})

    def test_agent6_raises_not_implemented(self):
        runner = ClaudeAgentRunner(api_key="dummy-key-not-used")
        with self.assertRaises(NotImplementedError):
            runner.run("agent6_execution_trader", {})

    def test_missing_api_key_raises_clear_runtime_error(self):
        runner = ClaudeAgentRunner(api_key=None)
        with self.assertRaises(RuntimeError):
            runner.run("agent7_learning", {})


class TestPromptExtraction(unittest.TestCase):
    """Runs without a key: verifies the prompts can be pulled out of the
    real agents/*.md files correctly. This is fully testable code, not
    part of the "untested" live-API path."""

    def test_extracts_agent4_prompt(self):
        markdown = (AGENTS_DIR / "04-risk-manager.md").read_text(encoding="utf-8")
        prompt = _extract_prompt_block(markdown, "")
        self.assertIn("Risikomanager", prompt)
        self.assertIn("Ausgabeschema", prompt)

    def test_extracts_agent5_prompt(self):
        markdown = (AGENTS_DIR / "05-portfolio-manager.md").read_text(encoding="utf-8")
        prompt = _extract_prompt_block(markdown, "")
        self.assertIn("Portfolio-Manager", prompt)

    def test_extracts_agent7_prompt(self):
        markdown = (AGENTS_DIR / "07-learning-postmortem.md").read_text(encoding="utf-8")
        prompt = _extract_prompt_block(markdown, "")
        self.assertIn("Lern-Agent", prompt)

    def test_extracts_agent2_three_distinct_prompts(self):
        markdown = (AGENTS_DIR / "02-strategy-researcher.md").read_text(encoding="utf-8")
        bull = _extract_prompt_block(markdown, "Bull-Researcher")
        bear = _extract_prompt_block(markdown, "Bear-Researcher")
        moderator = _extract_prompt_block(markdown, "Moderator")
        self.assertIn("BULL-RESEARCHER", bull)
        self.assertIn("BEAR-RESEARCHER", bear)
        self.assertIn("Debatten-Moderator", moderator)
        self.assertNotEqual(bull, bear)
        self.assertNotEqual(bear, moderator)

    def test_unknown_heading_raises(self):
        with self.assertRaises(ValueError):
            _extract_prompt_block("# nothing here", "Does Not Exist")


@unittest.skipUnless(
    HAS_API_KEY,
    "ANTHROPIC_API_KEY not set — the real API call path is unverified without it, "
    "see ClaudeAgentRunner's docstring",
)
class TestRealLiveCall(unittest.TestCase):
    """Only runs if a real key is provided. Not exercised in this repo's CI
    or by the author — genuinely untested until someone runs this with a
    key of their own."""

    def test_agent7_live_call_returns_schema_valid_output(self):
        from orchestrator import schemas

        runner = ClaudeAgentRunner()
        synthetic_input = {
            "hypothesis": {"symbol": "TEST", "confidence": 0.5},
            "validation": {"verdict": "validated_with_caveats"},
            "risk_verdict": {"veto": False},
            "approved_orders": {"approved_orders": []},
            "execution_report": {"executions": []},
            "prior_cycles": [],
        }
        output = runner.run("agent7_learning", synthetic_input)
        schemas.validate(output, schemas.LEARNING_REPORT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
