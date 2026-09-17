# Marktrecherche: Bestehende AI-Hedgefonds-/Multi-Agenten-Konzepte

Stand: September 2026. Diese Übersicht fasst die relevantesten öffentlich bekannten Projekte
zusammen, die als Vorbild für ein eigenes Multi-Agenten-Handelssystem dienen können.

## 1. TradingAgents (Tauric Research)

- **Was:** Wissenschaftlich publiziertes Framework (arXiv 2412.20138), das eine komplette
  Trading-Firma simuliert. Quelle: [github.com/TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents),
  Paper: [arxiv.org/abs/2412.20138](https://arxiv.org/abs/2412.20138).
- **Architektur:**
  - **Analysten-Team** (4 parallele Spezialisten): Fundamentalanalyst, Sentiment-Analyst
    (News/Reddit/StockTwits), News-Analyst (Makro/Events), Technischer Analyst (MACD, RSI, etc.)
  - **Researcher-Team:** Ein Bull- und ein Bear-Researcher führen eine strukturierte Debatte über
    die Analysten-Reports, um Chancen gegen Risiken abzuwägen.
  - **Trader-Agent:** Synthetisiert Analysten- und Researcher-Output zu einer konkreten
    Order-Idee (Timing, Größe).
  - **Risk-Management-Team:** Bewertet Volatilität/Liquidität, gibt Bewertungsbericht an den
  - **Portfolio-Manager:** Der die Order final freigibt oder ablehnt (zweistufiges Gate vor Exekution).
- **Kernidee, die sich lohnt zu übernehmen:** Explizite Bull/Bear-Debatte statt einer einzelnen
  Meinung — macht Fehleinschätzungen sichtbarer und die Entscheidung nachvollziehbar (Audit-Trail
  in natürlicher Sprache statt Black-Box).
- **Einschränkung (vom Projekt selbst benannt):** Ergebnisse variieren stark je nach Modell,
  Temperatur, Zeitraum und Datenqualität. Ausdrücklich **keine** Finanz-/Anlageberatung.

## 2. ai-hedge-fund (virattt) und Fork QuantJosh/ai-hedge-fund

- **Was:** Sehr populäres (~59k Stars) Bildungsprojekt. [github.com/virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)
- **Architektur:** „Investoren-Personas" als pluggable, backtestbare Alpha-Modelle — Agenten, die
  Stile bekannter Investoren nachbilden (wertorientiert, wachstumsorientiert, contrarian, etc.) und
  gegeneinander/gemeinsam über ein „Mandate File" (YAML: Strategie, Kapital, Risiko, Rebalance-Takt)
  konfiguriert werden. Ergebnis sind JSON-Zyklus-Protokolle und lesbare Zusammenfassungen.
- **Kernidee, die sich lohnt zu übernehmen:** Named-Persona-Agenten als Diversifikationsmechanismus
  innerhalb der Strategie-Ebene, plus deklarative Konfiguration (Mandat) statt Hardcoding.
- **Einschränkung (vom Projekt selbst benannt):** Ausdrücklich nur für Bildungs-/Forschungszwecke,
  **führt keine echten Trades aus**, keine Haftung, keine Anlageberatung.

## 3. AutoHedge (The Swarm Corporation)

- **Was:** Swarm-Intelligence-Ansatz, der Marktanalyse, Risikomanagement und Orderausführung
  automatisiert. [github.com/The-Swarm-Corporation/AutoHedge](https://github.com/The-Swarm-Corporation/AutoHedge)
- **Kernidee:** Leichtgewichtiger, produktionsnäherer Aufbau als reine Forschungs-Frameworks —
  guter Referenzpunkt für „schnell startklar", aber mit entsprechend weniger eingebauten
  Sicherheitsmechanismen.

## 4. AIBrokers

- **Was:** Erstes offen gelegtes AI-Hedgefonds-Framework mit Fokus auf Krypto, 24/7-Betrieb.
  [github.com/AI-Brokers/AIBrokers](https://github.com/AI-Brokers/AIBrokers)
- **Relevanz:** Zeigt, wie ein Dauerbetrieb (kein Handelsschluss wie bei Aktien) zusätzliche
  Anforderungen an Monitoring, Kill-Switches und Kostenkontrolle (LLM-Aufrufe 24/7) stellt.

## 5. agent-hedgefund (agentuity) und weitere kleinere Projekte

- Proof-of-Concept-Charakter, nützlich als Inspiration für Orchestrierungs-/Deployment-Muster
  (z. B. Agenten als separate, unabhängig skalierbare Services).
- Eine kuratierte Übersicht weiterer Projekte findet sich unter
  [github.com/LLMQuant/awesome-trading-agents](https://github.com/LLMQuant/awesome-trading-agents).

## Gemeinsame Muster über alle Projekte hinweg

1. **Rollentrennung** entlang der klassischen Trading-Desk-Struktur: Research/Analyse →
   Strategie/Debatte → Risiko → Exekution. Kein Projekt lässt einen einzelnen Agenten alles tun.
2. **Strukturierte Zwischenformate** (JSON/YAML) zwischen den Agenten statt freiem Text — macht
   das System testbar, loggbar und debuggbar.
3. **Explizites Risiko-Gate** vor jeder Exekution, unabhängig vom „Meinungs"-Agenten.
4. **Alle namhaften Projekte grenzen sich explizit von Anlageberatung ab** und weisen auf
   Halluzinations-, Overfitting- und Nicht-Reproduzierbarkeits-Risiken hin — das ist keine
   Standard-Floskel, sondern ein wiederkehrender, ernst gemeinter Befund.
5. **Kein einziges der recherchierten Projekte hat einen belastbaren, langfristig verifizierten
   Live-Track-Record mit echtem Geld.** Alles, was öffentlich zu Performance kursiert, stammt aus
   Backtests oder kurzen Paper-Trading-Phasen.

## Für dieses Konzept übernommene Best Practices

- Bull/Bear-Debatte aus TradingAgents (Agent 2 „Stratege")
- Deklaratives Mandat/Config statt Hardcoding aus ai-hedge-fund
- Zweistufiges Risiko-Gate (Risiko-Check **und** Portfolio-Freigabe getrennt) aus TradingAgents
- Ergänzt um einen expliziten **Lern-Agenten** (Post-Mortem/Feedback-Loop), den keines der
  recherchierten Projekte in dieser Form als eigenständige Rolle führt — das war eine
  ausdrückliche Anforderung aus der Aufgabenstellung und schließt eine Lücke gegenüber den
  bestehenden Konzepten.
