# Phase-1-Test: Agent 3 (Validator/Backtester) isoliert

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/03-validator-backtester.md`](../../agents/03-validator-backtester.md)
**Output dieses Laufs:** [`validated-hypotheses-2026-09-17.json`](validated-hypotheses-2026-09-17.json)

## Setup

Drei von Hand geschriebene Test-Hypothesen, in mcprule-konformes Pine Script v6 übersetzt und
über die **echte** tradingkit-Backtest-Engine (`tv_jul26`, TradingView-Paritätsprofil: 0.05%
Commission, 100% Equity-Sizing, Pyramiding 1) auf `BYBIT:BTCUSDT.P` (1h) gelaufen:

- **Hypothese A** — EMA20/50-Trendfolge (long-only), getestet In-Sample (2023–2024) und
  Out-of-Sample (2025–2026, echter Walk-Forward-Test).
- **Hypothese B** — RSI14-Mean-Reversion 30/55 (long-only), gleiches In-/Out-of-Sample-Schema.
- **Hypothese C** — absichtlicher Overfitting-Testfall: seltene Bedingung (RSI < 15 UND Kurs
  über SMA200) in einem bewusst zu kurzen ~6,5-Wochen-Fenster (Aug–Sep 2026), wie in
  [`docs/04-roadmap.md`](../../docs/04-roadmap.md) Phase 1 vorgesehen.

Kein Kapital, keine Order-Ausführung — reine Backtests auf historischen Daten.

## Prüfkriterium aus der Roadmap: „Erkennt er absichtlich eingebaute Overfitting-Fälle korrekt als nicht belastbar?"

### ✅ Ja — und mit einem deutlicheren Ergebnis als geplant

Hypothese C sollte laut Roadmap-Beispiel "eine Strategie mit nur 5 Trades" simulieren. Der
tatsächliche Lauf produzierte etwas noch Extremeres: **0 von 0 möglichen Trades** — die gewählte
Bedingung war im gesamten Fenster kein einziges Mal erfüllt. Der Validator hat das korrekt als
`not_testable` eingestuft, nicht als `rejected` (was fälschlich implizieren würde, die Strategie
sei getestet und schlecht) und erst recht nicht als `validated`. Das folgt exakt Regel 1
("wenn zu vage/nicht operationalisierbar → not_testable") sinngemäß auf den Fall "zu wenig Daten"
übertragen.

## Zusätzliche, nicht ursprünglich erwartete Befunde

Die beiden realistischeren Hypothesen (A und B) haben den Test deutlich wertvoller gemacht als
ein reiner Overfitting-Demo-Fall, weil sie **zwei unterschiedliche Arten von "kein Validate"**
zeigen:

| | Hypothese A (EMA-Trend) | Hypothese B (RSI-Mean-Reversion) |
|---|---|---|
| In-Sample Return | **+167.7%** | -0.12% |
| Out-of-Sample Return | **-28.8%** | -1.66% |
| In-Sample Sharpe | 1.56 | 0.12 |
| Out-of-Sample Sharpe | -0.54 | 0.08 |
| Trades (IS / OOS) | 168 / 142 | 102 / 103 |
| Muster | **Große IS/OOS-Kluft** → Overfitting-/Regime-Warnsignal | **Konsistent** über beide Fenster, aber konsistent unprofitabel |
| Verdikt | `rejected` | `rejected` |

Das ist genau die Unterscheidung, die Agent 3s Prompt in Regel 4 verlangt (In-Sample- vs.
Out-of-Sample-Lücke explizit benennen) — der Validator hat beide Fälle korrekt, aber mit
unterschiedlicher Begründung abgelehnt, statt beide über einen Kamm zu scheren. Hypothese A ist
das Lehrbuchbeispiel für eine Strategie, die nur deshalb gut aussah, weil der Backtest-Zeitraum
zufällig einen starken Bullenmarkt enthielt. Hypothese B zeigt das Gegenteil-Problem: eine hohe,
psychologisch verführerische Trefferquote (~64%) bei strukturell ungünstigem Gewinn/Verlust-
Verhältnis, die erst nach Kosten sichtbar ins Minus kippt — genau der Fall, vor dem Regel 5
("Kosten müssen eingepreist sein") warnt.

## Weitere Prüfpunkte aus dem Prompt

- **Kosten eingepreist? ✅** Alle drei Läufe liefen unter dem TradingView-Paritätsprofil mit
  0.05% Commission pro Order; `commissionPaid` ist in den Rohdaten für A und B explizit
  ausgewiesen (siehe `backtest_links`).
- **Mehrere Marktregime abgedeckt (A/B)? ✅** In-Sample- und Out-of-Sample-Fenster zusammen
  decken Bear-Erholung 2023, Bullenmarkt 2024 und Korrektur/Konsolidierung 2025-2026 ab.
- **Baseline-Vergleich (Regel: "compare_backtests gegen Buy&Hold")? ⚠️ Nicht wie geplant möglich**
  — siehe Tooling-Limitation unten. Dies ist eine ehrliche Lücke im Testlauf, keine
  Fehlleistung des Validator-Prompts.

## Entdeckte Tooling-Limitation (echter, ungeplanter Fund)

Ein einfaches "Kaufen auf der ersten Bar, nie verkaufen"-Pine-Skript als Buy&Hold-Baseline wurde
zweimal unabhängig implementiert (`bar_index == 0` und eine `var bool`-Flag-Variante) — beide
Male zeigte die tradingkit-Engine `totalTrades: 0`, `netProfit: 0` und eine über das gesamte
Fenster exakt konstante Equity-Kurve (10000 → 10000), obwohl eine Long-Position rein logisch
hätte offen sein müssen. Die Engine scheint ausschließlich **realisierte (geschlossene)** Trades
in ihren Kennzahlen abzubilden, keine Mark-to-Market-Bewertung offener Positionen.

**Konsequenz:** Der in Agent 3s Prompt vorgesehene Baseline-Vergleich (`compare_backtests` gegen
Buy&Hold) ließ sich mit den verfügbaren Tools in diesem Testlauf nicht wie spezifiziert
umsetzen. Das ist keine Schwäche des Agenten-Prompts, sondern eine Tooling-Lücke, die vor
Phase 2 geklärt werden sollte (siehe Empfehlung in
[`validated-hypotheses-2026-09-17.json`](validated-hypotheses-2026-09-17.json),
Feld `tooling_limitations_discovered`).

## Fazit

**Agent 3 besteht den isolierten Phase-1-Test.** Er unterscheidet korrekt zwischen "zu wenig
Daten für eine Aussage" (Hypothese C: `not_testable`), "Overfitting/Regimewechsel-Artefakt"
(Hypothese A: `rejected` wegen IS/OOS-Kluft) und "konsistent kein Edge" (Hypothese B: `rejected`
trotz fehlender Kluft) — drei unterschiedliche, korrekt benannte Ablehnungsgründe statt einer
pauschalen Bewertung. Die entdeckte Baseline-Tooling-Lücke ist vor Phase 2 zu schließen.

**Nächster Schritt laut Roadmap:** Weiter mit Agent 4 (Risikomanager) isoliert, oder — da sowohl
Agent 1 als auch Agent 3 jetzt einzeln bestanden haben — Entscheidung treffen, ob zunächst alle
sieben Agenten einzeln getestet werden oder bereits mit einer ersten Teil-Verkettung (Agent 1 →
2 → 3) begonnen wird.
