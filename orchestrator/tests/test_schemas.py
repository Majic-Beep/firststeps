import unittest

from orchestrator import schemas


class TestValidate(unittest.TestCase):
    def test_valid_hypotheses_passes(self):
        data = {
            "hypotheses": [
                {
                    "symbol": "BYBIT:ETHUSDT.P",
                    "timeframe": "1D",
                    "direction": "long",
                    "entry_condition": "close > EMA20",
                    "suggested_position_pct": 0.1,
                    "confidence": 0.5,
                }
            ],
            "no_thesis_symbols": [],
        }
        schemas.validate(data, schemas.HYPOTHESES_SCHEMA)  # should not raise

    def test_missing_required_field_raises(self):
        data = {"hypotheses": []}  # missing no_thesis_symbols
        with self.assertRaises(schemas.SchemaError):
            schemas.validate(data, schemas.HYPOTHESES_SCHEMA)

    def test_missing_timeframe_on_hypothesis_raises(self):
        """Regression test for the real gap found in tests/chain-agent1-2-3/."""
        data = {
            "hypotheses": [
                {
                    "symbol": "BYBIT:ETHUSDT.P",
                    # "timeframe" deliberately omitted
                    "direction": "long",
                    "entry_condition": "close > EMA20",
                    "suggested_position_pct": 0.1,
                    "confidence": 0.5,
                }
            ],
            "no_thesis_symbols": [],
        }
        with self.assertRaises(schemas.SchemaError):
            schemas.validate(data, schemas.HYPOTHESES_SCHEMA)

    def test_invalid_enum_value_raises(self):
        data = {
            "verdicts": [
                {
                    "symbol": "X",
                    "veto": False,
                    "risk_level": "SEHR_HOCH",  # not in the allowed enum
                    "max_position_pct": 0.1,
                    "rationale": "...",
                }
            ],
            "global_veto": False,
        }
        with self.assertRaises(schemas.SchemaError):
            schemas.validate(data, schemas.RISK_VERDICT_SCHEMA)

    def test_wrong_type_raises(self):
        with self.assertRaises(schemas.SchemaError):
            schemas.validate({"executions": "not-a-list"}, schemas.EXECUTION_REPORT_SCHEMA)

    def test_all_fixtures_validate(self):
        """The shipped 2026-09-17 fixtures must themselves be schema-valid."""
        import json
        from pathlib import Path

        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "2026-09-17-eth-cycle"
        for stage, schema in schemas.SCHEMAS_BY_STAGE.items():
            data = json.loads((fixtures_dir / f"{stage}.json").read_text(encoding="utf-8"))
            schemas.validate(data, schema)


if __name__ == "__main__":
    unittest.main()
