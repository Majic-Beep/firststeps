# Verkettungstest: Agent 1 → Agent 2 → Agent 3 → Agent 4

Setzt [`tests/chain-agent1-2-3/`](../chain-agent1-2-3/) fort. Nutzt den einzigen Kandidaten, der
Agent 3s Validierung überstanden hat (ETH, `validated_with_caveats`), und prüft, wie Agent 4
(Risikomanager) ihn gegen ein Mandat (`config/mandate.example.yaml`) bewertet.

## Läufe

| Datum | Ergebnis | Dateien |
|---|---|---|
| 2026-09-17 | ✅ Kette funktioniert; Agent 4 übersetzt Agent 3s Caveat-Status korrekt in eine vorsichtigere Risikoeinstufung, ohne formales Veto | [`04-risk-verdict-2026-09-17.json`](04-risk-verdict-2026-09-17.json), [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md) |

Siehe auch [`tests/phase1-agent4/`](../phase1-agent4/) für die isolierten Stresstests von Agent 4
(hartes Tagesverlust-Veto, Cluster-Limit-Kappung), die diesem Kettentest vorausgingen.
