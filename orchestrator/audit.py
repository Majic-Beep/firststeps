"""Persists every stage's input and output — the pipeline's audit trail.

Required by docs/02-architektur.md ("alle Ein-/Ausgaben persistieren") and
by agents/07-learning-postmortem.md, which needs this history to compare
expectation against outcome across cycles.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditTrail:
    def __init__(self, runs_dir: str | Path = "runs", run_id: str | None = None):
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        self.run_dir = Path(runs_dir) / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._log: list[dict] = []

    def record(self, stage: str, input_data: Any, output_data: Any, status: str) -> None:
        entry = {
            "stage": stage,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._log.append(entry)
        stage_dir = self.run_dir / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / "input.json").write_text(
            json.dumps(input_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (stage_dir / "output.json").write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def record_stopped(self, stage: str, reason: str) -> None:
        self._log.append(
            {
                "stage": stage,
                "status": "stopped",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def finalize(self) -> Path:
        summary_path = self.run_dir / "run-summary.json"
        summary_path.write_text(
            json.dumps({"run_id": self.run_id, "stages": self._log}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return summary_path
