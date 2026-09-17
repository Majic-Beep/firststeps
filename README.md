# AI-Hedgefonds — Multi-Agenten-Konzept

Dieses Repository enthält ein vollständiges Konzept für einen KI-gestützten Hedgefonds aus
kooperierenden, spezialisierten Agenten: Marktanalyse → Strategie-Entwicklung → Validierung/Backtesting
→ Risikoprüfung → Exekution → Lernen aus Fehlern. Es basiert auf einer Recherche bestehender
Open-Source- und Forschungsprojekte (siehe [`docs/01-marktrecherche.md`](docs/01-marktrecherche.md))
und übersetzt deren Best Practices in ein konkretes, umsetzbares Design mit fertigen Agenten-Prompts.

## Inhalt

| Datei | Inhalt |
|---|---|
| [`docs/01-marktrecherche.md`](docs/01-marktrecherche.md) | Was es am Markt schon gibt (TradingAgents, ai-hedge-fund, AutoHedge, AIBrokers, …) |
| [`docs/02-architektur.md`](docs/02-architektur.md) | Das gewählte Konzept: 7-Agenten-Pipeline, Datenfluss, Diagramm |
| [`agents/`](agents/) | Fertige System-Prompts für jeden einzelnen Agenten |
| [`docs/03-risiken-empfehlungen.md`](docs/03-risiken-empfehlungen.md) | Regulatorik (BaFin/KWG/MiFID II), technische Risiken, Betriebsempfehlungen |
| [`docs/04-roadmap.md`](docs/04-roadmap.md) | Phasenplan von Paper-Trading bis (vorsichtigem) Live-Betrieb |

## Kurzfassung des Konzepts

Sieben Agenten, jeder mit eigenem, engem Auftrag und eigenem System-Prompt, verbunden über
strukturierte Zwischenergebnisse (JSON) statt freiem Fließtext:

1. **Marktanalyst** — sammelt und verdichtet Markt-, News-, Sentiment- und Makrodaten zu einem „Market Brief".
2. **Stratege (Researcher)** — leitet daraus Handelshypothesen ab, inkl. Bull-/Bear-Gegenrede.
3. **Validator/Backtester** — prüft jede Hypothese historisch (Backtest, Walk-Forward, Overfitting-Check).
4. **Risikomanager** — prüft Positionsgröße, Exposure, Korrelation, Drawdown-Limits — Vetorecht.
5. **Portfolio-Manager (Orchestrator)** — trifft die finale Kapitalallokations-Entscheidung.
6. **Execution-Trader** — setzt genehmigte Orders um (zunächst ausschließlich Paper-Trading).
7. **Lern-Agent (Post-Mortem)** — vergleicht Erwartung vs. Ergebnis, speist Learnings in alle anderen Agenten zurück.

Diese Umgebung stellt bereits passende Werkzeuge bereit, mit denen sich das Konzept 1:1 umsetzen lässt:
**TradingView-MCP** (Marktdaten/Technicals/News → Agent 1), **tradingkit-MCP** (Backtesting/Optimierung
→ Agent 3) und **Co-Invest-MCP** (Orderausführung/Portfolio, inkl. Paper-Trading-Modus → Agent 6).
Details dazu in [`docs/02-architektur.md`](docs/02-architektur.md).

⚠️ **Wichtiger Hinweis:** Dies ist ein Konzept- und Prompt-Entwurf, keine Anlageberatung und kein
fertiges, geprüftes Handelssystem. Bitte unbedingt [`docs/03-risiken-empfehlungen.md`](docs/03-risiken-empfehlungen.md)
lesen, bevor auch nur ein Euro echtes Kapital involviert wird.
