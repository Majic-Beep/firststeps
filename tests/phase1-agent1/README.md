# Phase-1-Tests: Isolierte Agenten-Läufe

Dieses Verzeichnis sammelt Testläufe einzelner Agenten aus `agents/`, isoliert und ohne
Verkettung mit anderen Agenten oder Order-Tools — wie in
[`docs/04-roadmap.md`](../../docs/04-roadmap.md), Phase 1, vorgesehen. Jeder Lauf besteht aus:

- dem tatsächlichen Output des Agenten (JSON, exakt nach dem Schema aus dem jeweiligen
  Prompt in `agents/`),
- einer Auswertung gegen die Phase-1-Kriterien (Schema-Treue, keine erfundenen Daten,
  korrekte Data-Quality-Erkennung).

## Läufe

| Datum | Agent | Ergebnis | Dateien |
|---|---|---|---|
| 2026-09-17 | Agent 1 — Marktanalyst | ✅ Bestanden | [`market-brief-2026-09-17.json`](market-brief-2026-09-17.json), [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md) |
