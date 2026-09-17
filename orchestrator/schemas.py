"""Minimal, hand-rolled schema validation for agent output.

We deliberately do not depend on the third-party `jsonschema` package —
the six schemas below are simple enough that a ~40-line recursive checker
covers them, and it keeps this package runnable with only the Python
standard library plus PyYAML (see requirements.txt).

Each SCHEMA is a plain dict using a small subset of JSON Schema:
type, required, properties, items, enum. That is all `validate()` below
understands; it is not a general-purpose implementation.
"""
from __future__ import annotations

from typing import Any


class SchemaError(Exception):
    """Raised when an agent's output does not match its expected schema."""


def validate(data: Any, schema: dict, path: str = "$") -> None:
    """Raise SchemaError with a precise path on the first violation found."""
    expected_type = schema.get("type")
    if expected_type:
        _check_type(data, expected_type, path)

    if expected_type == "object":
        for key in schema.get("required", []):
            if key not in data:
                raise SchemaError(f"{path}: missing required field '{key}'")
        for key, sub_schema in schema.get("properties", {}).items():
            if key in data:
                validate(data[key], sub_schema, f"{path}.{key}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(data):
                validate(item, item_schema, f"{path}[{i}]")

    enum = schema.get("enum")
    if enum is not None and data not in enum:
        raise SchemaError(f"{path}: value {data!r} not in allowed set {enum!r}")


def _check_type(data: Any, expected_type: str, path: str) -> None:
    python_type = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "number": (int, float),
    }.get(expected_type)
    if python_type is None:
        return
    # bool is a subclass of int in Python; keep "number" and "boolean" distinct.
    if expected_type == "number" and isinstance(data, bool):
        raise SchemaError(f"{path}: expected number, got boolean")
    if not isinstance(data, python_type):
        raise SchemaError(
            f"{path}: expected {expected_type}, got {type(data).__name__}"
        )


# ---------------------------------------------------------------------------
# Agent 1 — Marktanalyst (agents/01-market-analyst.md)
# ---------------------------------------------------------------------------
MARKET_BRIEF_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "universe", "macro", "per_symbol", "sources"],
    "properties": {
        "timestamp": {"type": "string"},
        "universe": {"type": "array", "items": {"type": "string"}},
        "macro": {"type": "object", "required": ["regime"], "properties": {}},
        "per_symbol": {"type": "object"},
        "sources": {"type": "array", "items": {"type": "string"}},
    },
}

# ---------------------------------------------------------------------------
# Agent 2 — Stratege (agents/02-strategy-researcher.md)
# ---------------------------------------------------------------------------
HYPOTHESIS_SCHEMA = {
    "type": "object",
    "required": [
        "symbol",
        "timeframe",
        "direction",
        "entry_condition",
        "suggested_position_pct",
        "confidence",
    ],
    "properties": {
        "symbol": {"type": "string"},
        "timeframe": {"type": "string"},
        "direction": {"type": "string", "enum": ["long", "short", "no_edge"]},
        "entry_condition": {"type": "string"},
        "suggested_position_pct": {"type": "number"},
        "confidence": {"type": "number"},
    },
}

HYPOTHESES_SCHEMA = {
    "type": "object",
    "required": ["hypotheses", "no_thesis_symbols"],
    "properties": {
        "hypotheses": {"type": "array", "items": HYPOTHESIS_SCHEMA},
        "no_thesis_symbols": {"type": "array", "items": {"type": "string"}},
    },
}

# ---------------------------------------------------------------------------
# Agent 3 — Validator/Backtester (agents/03-validator-backtester.md)
# ---------------------------------------------------------------------------
VALIDATOR_RESULT_SCHEMA = {
    "type": "object",
    "required": ["symbol", "hypothesis_ref", "costs_included", "verdict", "rationale"],
    "properties": {
        "symbol": {"type": "string"},
        "hypothesis_ref": {"type": "string"},
        "costs_included": {"type": "boolean"},
        "verdict": {
            "type": "string",
            "enum": ["validated", "validated_with_caveats", "rejected", "not_testable"],
        },
        "rationale": {"type": "string"},
    },
}

VALIDATED_HYPOTHESES_SCHEMA = {
    "type": "object",
    "required": ["results"],
    "properties": {"results": {"type": "array", "items": VALIDATOR_RESULT_SCHEMA}},
}

# ---------------------------------------------------------------------------
# Agent 4 — Risikomanager (agents/04-risk-manager.md)
# ---------------------------------------------------------------------------
RISK_VERDICT_ITEM_SCHEMA = {
    "type": "object",
    "required": ["symbol", "veto", "risk_level", "max_position_pct", "rationale"],
    "properties": {
        "symbol": {"type": "string"},
        "veto": {"type": "boolean"},
        "risk_level": {"type": "string", "enum": ["niedrig", "mittel", "hoch"]},
        "max_position_pct": {"type": "number"},
        "rationale": {"type": "string"},
    },
}

RISK_VERDICT_SCHEMA = {
    "type": "object",
    "required": ["verdicts", "global_veto"],
    "properties": {
        "verdicts": {"type": "array", "items": RISK_VERDICT_ITEM_SCHEMA},
        "global_veto": {"type": "boolean"},
    },
}

# ---------------------------------------------------------------------------
# Agent 5 — Portfolio-Manager (agents/05-portfolio-manager.md)
# ---------------------------------------------------------------------------
APPROVED_ORDER_SCHEMA = {
    "type": "object",
    "required": ["symbol", "direction", "position_pct", "rationale"],
    "properties": {
        "symbol": {"type": "string"},
        "direction": {"type": "string", "enum": ["long", "short"]},
        "position_pct": {"type": "number"},
        "rationale": {"type": "string"},
    },
}

APPROVED_ORDERS_SCHEMA = {
    "type": "object",
    "required": [
        "approved_orders",
        "rejected_hypotheses",
        "existing_position_actions",
        "capital_summary",
    ],
    "properties": {
        "approved_orders": {"type": "array", "items": APPROVED_ORDER_SCHEMA},
        "rejected_hypotheses": {"type": "array"},
        "existing_position_actions": {"type": "array"},
        "capital_summary": {"type": "object"},
    },
}

# ---------------------------------------------------------------------------
# Agent 6 — Execution-Trader (agents/06-execution-trader.md)
# ---------------------------------------------------------------------------
EXECUTION_ITEM_SCHEMA = {
    "type": "object",
    "required": ["symbol", "requested", "status"],
    "properties": {
        "symbol": {"type": "string"},
        "requested": {"type": "object"},
        "status": {
            "type": "string",
            "enum": [
                "prepared_awaiting_human_confirmation",
                "execution_deferred",
                "rejected",
                "error",
                "executed",
            ],
        },
    },
}

EXECUTION_REPORT_SCHEMA = {
    "type": "object",
    "required": ["executions"],
    "properties": {"executions": {"type": "array", "items": EXECUTION_ITEM_SCHEMA}},
}

SCHEMAS_BY_STAGE = {
    "agent1_market_analyst": MARKET_BRIEF_SCHEMA,
    "agent2_strategist": HYPOTHESES_SCHEMA,
    "agent3_validator": VALIDATED_HYPOTHESES_SCHEMA,
    "agent4_risk_manager": RISK_VERDICT_SCHEMA,
    "agent5_portfolio_manager": APPROVED_ORDERS_SCHEMA,
    "agent6_execution_trader": EXECUTION_REPORT_SCHEMA,
}
