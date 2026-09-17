# Architektur: 7-Agenten-Pipeline

## Überblick

```
                     ┌─────────────────────┐
                     │   0. Orchestrator     │   steuert Takt (z. B. täglich/stündlich),
                     │      / Scheduler      │   hält Zustand (Portfolio, Mandat, Logs)
                     └──────────┬────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  1. Marktanalyst              │  → market_brief.json
                 │  (TradingView-MCP)            │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  2. Stratege (Bull/Bear)      │  → trade_hypotheses.json
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  3. Validator / Backtester    │  → validated_hypotheses.json
                 │  (tradingkit-MCP)             │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  4. Risikomanager             │  → risk_verdict.json (VETO möglich)
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  5. Portfolio-Manager         │  → approved_orders.json
                 │  (finale Kapitalallokation)   │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  6. Execution-Trader          │  → execution_report.json
                 │  (Co-Invest-MCP, Paper Mode)  │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │  7. Lern-Agent (Post-Mortem)  │  → lessons_learned.json
                 └──────────────┬──────────────┘
                                │
                     zurück in Prompt-Zusätze /
                     Parameter für Agenten 1–6
```

Jeder Pfeil transportiert **strukturiertes JSON**, kein Fließtext. Das erzwingt, dass jeder Agent
seine Ausgabe in einem festen Schema liefert (Feld `reasoning` für die nachvollziehbare Begründung,
plus maschinenlesbare Felder für die nächste Stufe). Das macht die Kette testbar, loggbar und
ersetzbar (jeder Agent kann einzeln durch ein anderes Modell/eine andere Implementierung getauscht
werden).

## Warum diese Reihenfolge?

- **Trennung von „was könnte funktionieren" (2) und „hat es historisch funktioniert" (3):**
  Ideen-Generierung und Validierung sind bewusst unterschiedliche Agenten mit unterschiedlichen
  Anreizen — der Stratege darf kreativ/optimistisch sein, der Validator ist bewusst skeptisch
  instruiert.
- **Risiko (4) ist von Portfolio-Entscheidung (5) getrennt**, wie bei TradingAgents: Der
  Risikomanager hat ein reines Veto-/Warnrecht, aber keine Allokationsmacht — die finale
  Kapitalentscheidung (Diversifikation, Priorisierung bei begrenztem Kapital) liegt beim
  Portfolio-Manager. Das verhindert, dass ein einzelner Agent gleichzeitig „Gas gibt" und „bremst".
- **Exekution (6) ist strikt vom Portfolio-Manager entkoppelt:** Der Execution-Agent bekommt nur
  bereits genehmigte Orders, trifft selbst keine Entscheidung mehr — er kann Slippage/Orderbuch
  prüfen und ggf. ablehnen, aber nicht eigenmächtig neue Positionen eröffnen.
- **Lern-Agent (7) schließt den Kreis:** Ohne diese Rolle bleibt jedes der recherchierten
  Frameworks bei „einmal ausführen, Ergebnis ansehen" stehen. Hier fließen Ist-Ergebnisse
  systematisch zurück in die Prompts/Parameter der vorgelagerten Agenten (siehe unten).

## Mapping auf in dieser Umgebung verfügbare Werkzeuge

Diese Session hat bereits drei MCP-Server verbunden, die sich nahtlos auf die Pipeline abbilden
lassen — das Konzept ist also nicht nur Theorie, sondern in dieser Umgebung direkt testbar:

| Agent | MCP-Server | Relevante Tools (Auszug) |
|---|---|---|
| 1. Marktanalyst | **TradingView** | `get_quote`, `get_technicals`, `get_full_technicals`, `run_screener`, `get_news`, `get_economic_calendar`, `get_earnings_calendar`, `analyze_smc_tool`, `analyze_swing_tool`, `analyze_sector_tool`, `analyze_multi_timeframe` |
| 2. Stratege | (kein Tool nötig — reines LLM-Reasoning auf Basis von Agent 1) | ggf. `search_symbols`, `compare_symbols_tool` |
| 3. Validator/Backtester | **tradingkit** | `run_backtest`, `quick_backtest`, `optimize_strategy`, `compare_backtests`, `get_equity_curve`, `get_trades`, `plan_backtest_window` |
| 4. Risikomanager | **TradingView** | `calculate_correlation_tool` (Klumpenrisiko), `get_technicals_rating` (Volatilität) |
| 5. Portfolio-Manager | **Co-Invest** | `get_portfolio`, `plan_portfolio`, `suggest_trades_batch` (nur als Zweitmeinung, nicht als Ersatz für eigenes Urteil) |
| 6. Execution-Trader | **Co-Invest** | `enable_paper_trading` (⚠️ zuerst!), `suggest_order`, `execute_order`, `execute_orders_batch`, `execute_tpsl`, `update_leverage`, `cancel_order` |
| 7. Lern-Agent | **Co-Invest** / **tradingkit** | `get_transaction_history`, `get_trades`, `get_signal_stats`, `report_outcome` |

**Wichtig:** `enable_paper_trading` in Co-Invest sollte der erste Aufruf überhaupt sein, bevor
irgendein Execution-Agent produktiv geschaltet wird (siehe Roadmap).

## Datenschema (Beispiel: Übergabe Agent 1 → Agent 2)

```json
{
  "timestamp": "2026-09-17T08:00:00Z",
  "universe": ["NASDAQ:AAPL", "NASDAQ:MSFT"],
  "macro": { "events_today": [...], "regime": "risk-on" },
  "per_symbol": {
    "NASDAQ:AAPL": {
      "technical_summary": "...",
      "sentiment_score": 0.32,
      "news_flags": ["earnings in 3 days"],
      "volatility_regime": "elevated"
    }
  },
  "confidence": 0.6,
  "sources": ["tradingview:get_technicals", "tradingview:get_news"]
}
```

Jeder nachfolgende Agent bekommt ein vergleichbares, versioniertes Schema. Das lohnt sich, formal
z. B. als JSON-Schema-Dateien in `schemas/` zu pflegen, sobald das Konzept implementiert wird.

## Orchestrierung

Empfehlung: kein „ein großer Agent ruft alle Sub-Agenten als Tools auf"-Muster, sondern ein
**externer, deterministischer Orchestrator** (normaler Code, kein LLM), der:

1. die Agenten in fester Reihenfolge aufruft,
2. jede Ausgabe gegen das erwartete JSON-Schema validiert (harter Fehler bei Abweichung),
3. Retries/Timeouts pro Agent handhabt,
4. alle Ein-/Ausgaben persistiert (Audit-Trail, Grundlage für Agent 7),
5. **Kill-Switches** zwischen jeder Stufe prüft (z. B. Tagesverlustlimit erreicht → Pipeline stoppt
   vor Agent 6, unabhängig davon was die Agenten „wollen").

Das hält LLM-Nichtdeterminismus aus der Kontrollebene heraus — die Agenten liefern Inhalte, der
Orchestrator entscheidet, ob überhaupt weitergemacht wird.
