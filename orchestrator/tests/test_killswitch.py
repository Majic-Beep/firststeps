import unittest

from orchestrator import killswitch
from orchestrator.mandate import Mandate

MANDATE = Mandate(
    initial_capital=10000,
    universe=["BYBIT:BTCUSDT.P"],
    max_position_pct_per_symbol=0.20,
    max_position_pct_per_cluster=0.30,
    correlation_cluster_threshold=0.70,
    max_daily_loss_pct=0.05,
    max_leverage=2.0,
    min_trades_for_statistical_significance=30,
    require_out_of_sample_test=True,
)


class TestDailyLossLimit(unittest.TestCase):
    def test_within_limit_is_ok(self):
        killswitch.check_daily_loss_limit(-0.012, MANDATE)  # should not raise

    def test_breach_triggers(self):
        with self.assertRaises(killswitch.KillSwitchTriggered):
            killswitch.check_daily_loss_limit(-0.061, MANDATE)

    def test_positive_pnl_never_triggers(self):
        killswitch.check_daily_loss_limit(0.10, MANDATE)  # should not raise


class TestGlobalVeto(unittest.TestCase):
    def test_no_veto_passes(self):
        killswitch.check_global_veto({"global_veto": False})

    def test_veto_triggers_regardless_of_reason_text(self):
        with self.assertRaises(killswitch.KillSwitchTriggered):
            killswitch.check_global_veto({"global_veto": True, "global_veto_reason": "x"})


class TestPositionSizeCeiling(unittest.TestCase):
    def test_within_ceiling_passes(self):
        risk_verdict = {"verdicts": [{"symbol": "ETH", "max_position_pct": 0.10}]}
        approved = {"approved_orders": [{"symbol": "ETH", "position_pct": 0.10}]}
        killswitch.check_position_size_ceiling(approved, risk_verdict)

    def test_exceeding_ceiling_triggers(self):
        """This is the defense-in-depth case: even if Agent 5 mis-sizes an
        order, the orchestrator itself must catch it — not trust the LLM."""
        risk_verdict = {"verdicts": [{"symbol": "ETH", "max_position_pct": 0.10}]}
        approved = {"approved_orders": [{"symbol": "ETH", "position_pct": 0.25}]}
        with self.assertRaises(killswitch.KillSwitchTriggered):
            killswitch.check_position_size_ceiling(approved, risk_verdict)

    def test_symbol_with_no_risk_verdict_is_not_checked(self):
        """Nothing to compare against — this function only re-verifies
        ceilings Agent 4 actually set, it does not invent new ones."""
        risk_verdict = {"verdicts": []}
        approved = {"approved_orders": [{"symbol": "UNKNOWN", "position_pct": 0.99}]}
        killswitch.check_position_size_ceiling(approved, risk_verdict)


if __name__ == "__main__":
    unittest.main()
