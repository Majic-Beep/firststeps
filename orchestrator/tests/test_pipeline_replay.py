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

    def test_real_2026_09_17_cycle_now_caught_by_tp_sl_killswitch(self):
        """End-to-end replay of the actual, now-completed cycle: the ETH order
        was for real confirmed by the user on Co-Invest (status "executed" in
        the fixture), but WITHOUT a proposed take-profit/stop-loss — a real
        violation of agents/06-execution-trader.md, Regel 3, found by Agent 7
        (see tests/phase1-agent7/). The check_tp_sl_proposed kill-switch added
        because of that finding now stops the pipeline right after Agent 6,
        before Agent 7 even runs. This is the intended, corrected behavior:
        if this check had existed on 2026-09-17, the missing TP/SL would have
        been caught before a human was ever asked to confirm the order."""
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
        self.assertEqual(result.halted_at, "killswitch:tp_sl_proposed")
        self.assertIn("Take-Profit/Stop-Loss", result.halt_reason)

        # Audit trail must exist and contain the real input/output for every stage.
        for stage in result.completed_stages:
            self.assertTrue((result.run_dir / stage / "input.json").exists())
            self.assertTrue((result.run_dir / stage / "output.json").exists())
        summary = json.loads((result.run_dir / "run-summary.json").read_text())
        self.assertEqual(summary["run_id"], result.run_id)

    def test_full_cycle_reaches_agent7_when_tp_sl_proposed(self):
        """Synthetic mechanics test (NOT a claim about a real trade): if Agent
        6 had proposed TP/SL as its own Regel 3 requires, the pipeline would
        sail through the new kill-switch and actually reach Agent 7. This
        proves the conditional Agent 7 stage itself works, using a corrected
        copy of the real fixtures rather than pretending this is what really
        happened on 2026-09-17."""
        tmp_fixtures = Path(tempfile.mkdtemp())
        for f in FIXTURES_DIR.glob("*.json"):
            shutil.copy(f, tmp_fixtures / f.name)
        corrected = json.loads((tmp_fixtures / "agent6_execution_trader.json").read_text())
        corrected["executions"][0]["tp_sl_proposed"] = True
        corrected["executions"][0]["tp_sl_set"] = True
        (tmp_fixtures / "agent6_execution_trader.json").write_text(json.dumps(corrected))
        (tmp_fixtures / "agent7_learning.json").write_text(
            json.dumps(
                {
                    "cycle_id": "synthetic-test-only",
                    "root_cause": {
                        "stage": "kein_fehler_normale_varianz",
                        "type": "ergebnisfehler_bei_korrektem_prozess",
                        "explanation": "Synthetischer Testfall fuer die Pipeline-Mechanik.",
                    },
                    "recurring_pattern": {"is_recurring": False, "prior_occurrences": []},
                    "proposed_changes": [],
                    "watch_items": ["Nur ein Mechanik-Test, keine echte Auswertung."],
                }
            )
        )

        runner = ReplayAgentRunner(tmp_fixtures)
        result = run_pipeline(runner, self.mandate, fixtures_dir=tmp_fixtures, runs_dir=self.tmp_runs_dir)

        self.assertIsNone(result.halted_at)
        self.assertIn("agent7_learning", result.completed_stages)
        shutil.rmtree(tmp_fixtures, ignore_errors=True)

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
