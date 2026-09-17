import json
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.agent_runner import ReplayAgentRunner
from orchestrator.mandate import Mandate
from orchestrator.pipeline import run_pipeline

REPO_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "orchestrator" / "fixtures" / "2026-09-17-eth-cycle"
MANDATE_PATH = REPO_ROOT / "config" / "mandate.example.yaml"


class TestReplayPipeline(unittest.TestCase):
    def setUp(self):
        self.mandate = Mandate.load(MANDATE_PATH)
        self.tmp_runs_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_runs_dir, ignore_errors=True)

    def test_real_2026_09_17_cycle_stops_before_agent7(self):
        """End-to-end replay of the actual recorded cycle: Agent 1-6 run and
        validate cleanly, then the pipeline halts because Agent 6's order is
        still awaiting human confirmation — exactly what really happened."""
        runner = ReplayAgentRunner(FIXTURES_DIR)
        result = run_pipeline(runner, self.mandate, fixtures_dir=FIXTURES_DIR, runs_dir=self.tmp_runs_dir)

        self.assertEqual(
            result.completed_stages,
            [
                "agent1_market_analyst",
                "agent2_strategist",
                "agent3_validator",
                "agent4_risk_manager",
                "agent5_portfolio_manager",
                "agent6_execution_trader",
            ],
        )
        self.assertEqual(result.halted_at, "agent6_execution_trader")
        self.assertIn("menschliche Bestätigung", result.halt_reason)

        # Audit trail must exist and contain the real input/output for every stage.
        for stage in result.completed_stages:
            self.assertTrue((result.run_dir / stage / "input.json").exists())
            self.assertTrue((result.run_dir / stage / "output.json").exists())
        summary = json.loads((result.run_dir / "run-summary.json").read_text())
        self.assertEqual(summary["run_id"], result.run_id)

    def test_daily_loss_breach_stops_before_agent4(self):
        """If the pre-existing portfolio already breached the daily loss
        limit, the orchestrator must stop BEFORE calling Agent 4 at all —
        it should not need an agent to notice this for it."""
        tmp_fixtures = Path(tempfile.mkdtemp())
        for f in FIXTURES_DIR.glob("*.json"):
            shutil.copy(f, tmp_fixtures / f.name)
        breached = json.loads((tmp_fixtures / "portfolio_context.json").read_text())
        breached["daily_pnl_pct"] = -0.08
        (tmp_fixtures / "portfolio_context.json").write_text(json.dumps(breached))

        runner = ReplayAgentRunner(tmp_fixtures)
        result = run_pipeline(runner, self.mandate, fixtures_dir=tmp_fixtures, runs_dir=self.tmp_runs_dir)

        self.assertEqual(
            result.completed_stages,
            ["agent1_market_analyst", "agent2_strategist", "agent3_validator"],
        )
        self.assertEqual(result.halted_at, "killswitch:daily_loss_limit")
        self.assertIn("Tagesverlust", result.halt_reason)
        shutil.rmtree(tmp_fixtures, ignore_errors=True)

    def test_global_veto_stops_before_agent5(self):
        tmp_fixtures = Path(tempfile.mkdtemp())
        for f in FIXTURES_DIR.glob("*.json"):
            shutil.copy(f, tmp_fixtures / f.name)
        vetoed = json.loads((tmp_fixtures / "agent4_risk_manager.json").read_text())
        vetoed["global_veto"] = True
        vetoed["global_veto_reason"] = "Test: erzwungenes Veto"
        (tmp_fixtures / "agent4_risk_manager.json").write_text(json.dumps(vetoed))

        runner = ReplayAgentRunner(tmp_fixtures)
        result = run_pipeline(runner, self.mandate, fixtures_dir=tmp_fixtures, runs_dir=self.tmp_runs_dir)

        self.assertEqual(
            result.completed_stages,
            ["agent1_market_analyst", "agent2_strategist", "agent3_validator", "agent4_risk_manager"],
        )
        self.assertEqual(result.halted_at, "killswitch:global_veto")
        self.assertIn("globales Veto", result.halt_reason)
        shutil.rmtree(tmp_fixtures, ignore_errors=True)

    def test_agent5_exceeding_agent4_ceiling_is_caught(self):
        """Defense in depth: even a broken Agent 5 fixture that ignores its
        own ceiling must be stopped by the orchestrator, not waved through."""
        tmp_fixtures = Path(tempfile.mkdtemp())
        for f in FIXTURES_DIR.glob("*.json"):
            shutil.copy(f, tmp_fixtures / f.name)
        broken = json.loads((tmp_fixtures / "agent5_portfolio_manager.json").read_text())
        broken["approved_orders"][0]["position_pct"] = 0.99  # far above the 0.10 ceiling
        (tmp_fixtures / "agent5_portfolio_manager.json").write_text(json.dumps(broken))

        runner = ReplayAgentRunner(tmp_fixtures)
        result = run_pipeline(runner, self.mandate, fixtures_dir=tmp_fixtures, runs_dir=self.tmp_runs_dir)

        self.assertEqual(result.halted_at, "killswitch:position_size_ceiling")
        self.assertIn("Obergrenze", result.halt_reason)
        shutil.rmtree(tmp_fixtures, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
