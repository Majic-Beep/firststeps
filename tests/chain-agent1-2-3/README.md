# Verkettungstest: Agent 1 → Agent 2 → Agent 3

Erster Test der Schnittstellen zwischen mehreren Agenten (nicht nur eines Agenten isoliert),
wie in [`docs/04-roadmap.md`](../../docs/04-roadmap.md) als Zwischenschritt vor der vollen
7-Agenten-Pipeline (Phase 2) vorgesehen.

## Läufe

| Datum | Universum | Ergebnis | Dateien |
|---|---|---|---|
| 2026-09-17 | BTC/ETH/SOL (Krypto, wegen Tool-Kompatibilität siehe Auswertung) | ✅ Kette funktioniert inhaltlich, 2 Schnittstellen-Lücken gefunden (1 behoben) | [`01-market-brief-crypto-2026-09-17.json`](01-market-brief-crypto-2026-09-17.json), [`02-hypotheses-crypto-2026-09-17.json`](02-hypotheses-crypto-2026-09-17.json), [`03-validated-hypotheses-crypto-2026-09-17.json`](03-validated-hypotheses-crypto-2026-09-17.json), [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md) |

## Wichtigste Erkenntnis

Drei von Agent 1 fast identisch bullisch bewertete, hoch korrelierte Krypto-Symbole (BTC/ETH/SOL,
Korrelation 0.82–0.88) erhielten von Agent 2 dieselbe Handelsregel — Agent 3 zeigte anhand echter
Backtests, dass die Regel nur bei einem der drei Symbole (ETH) out-of-sample tatsächlich
funktioniert. Das bestätigt empirisch, warum die Pipeline einen eigenständigen Validierungs-Schritt
braucht statt sich auf Marktanalyse und Strategie-Debatte allein zu verlassen.

Details, gefundene Schnittstellen-Lücken (Symbol-Identität zwischen TradingView/tradingkit,
fehlendes Timeframe-Feld — inzwischen in `agents/02-strategy-researcher.md` behoben) und
offene Punkte in [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md).
