# Verkettungstest: Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5

Schließt die Entscheidungs-Hälfte der Pipeline ab (Marktanalyse bis Kapitalallokation). Setzt
[`tests/chain-agent1-2-3-4/`](../chain-agent1-2-3-4/) fort.

## Läufe

| Datum | Ergebnis | Dateien |
|---|---|---|
| 2026-09-17 | ✅ Erster vollständiger Durchlauf Markt→Entscheidung: ETH-Long, 10% Kapitaleinsatz | [`05-approved-orders-2026-09-17.json`](05-approved-orders-2026-09-17.json), [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md) |

Siehe auch [`tests/phase1-agent5/`](../phase1-agent5/) für die isolierten Stresstests von Agent 5
(bindendes Veto, widersprüchliche Bestandsposition, Kapitalknappheit mit Priorisierung).

## Nächster Schritt

Agent 6 (Execution-Trader) — **ausschließlich im Paper-Trading-Modus** von Co-Invest, wie in
[`docs/04-roadmap.md`](../../docs/04-roadmap.md) und
[`agents/06-execution-trader.md`](../../agents/06-execution-trader.md) gefordert.
