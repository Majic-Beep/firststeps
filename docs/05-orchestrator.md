# Der Orchestrator

Dieses Dokument beschreibt `orchestrator/` — den deterministischen Code, der die sieben
Agenten in fester Reihenfolge aufruft, ihre Ausgaben validiert und harte Risikolimits
unabhängig von jedem Agenten-Urteil selbst prüft. Das ist die konkrete Umsetzung des
Abschnitts „Orchestrierung" in [`docs/02-architektur.md`](02-architektur.md).

## Was er tut

1. Ruft Agent 1–7 in fester Reihenfolge auf (kein Agent entscheidet, was als Nächstes läuft) —
   Agent 7 nur, wenn Agent 6 jede Order tatsächlich als ausgeführt UND mit vorgeschlagenem TP/SL
   meldet (siehe Punkt 5).
2. Validiert jede Ausgabe gegen ein festes Schema (`orchestrator/schemas.py`) — bei Abweichung
   bricht der Lauf hart ab, statt mit unvollständigen Daten weiterzumachen.
3. Prüft harte Risikolimits **im Code, nicht per Agenten-Urteil** (`orchestrator/killswitch.py`):
   Tagesverlustlimit vor Agent 4, globales Veto vor Agent 5, eine Nachprüfung, dass Agent 5
   niemals die von Agent 4 gesetzte Positionsgrößen-Obergrenze überschreitet, und (seit dem
   ersten echten Agent-7-Fund, siehe `tests/phase1-agent7/`) dass keine Position ohne
   vorgeschlagenes Take-Profit/Stop-Loss eröffnet wird — genau das "defense in depth"-Prinzip,
   das `agents/04-risk-manager.md` explizit fordert.
4. Persistiert Ein-/Ausgabe jeder Stufe vollständig (`orchestrator/audit.py`, Ordner `runs/`).
5. Stoppt **immer** vor Agent 7, wenn Agent 6 nicht meldet, dass eine Order tatsächlich
   ausgeführt wurde, oder wenn TP/SL nicht vorgeschlagen wurde — auf Co-Invest ist ohne
   menschliche Bestätigung ohnehin nie eine Ausführung möglich (siehe `tests/phase1-agent6/`),
   und der reale 2026-09-17-Zyklus zeigt, dass selbst nach Bestätigung noch eine echte
   Regelverletzung übersehen werden kann, siehe `tests/phase1-agent7/`.

## Was er bewusst NICHT tut

Der Orchestrator enthält **keine** LLM-Aufrufe und **keine** Markt-/Broker-Integration. Beides
würde entweder die MCP-Tools duplizieren, die innerhalb einer Claude-Code-Session bereits zur
Verfügung stehen (TradingView, tradingkit, Co-Invest), oder eigene, ungetestete REST-Clients für
diese drei Plattformen erfordern. Stattdessen definiert `orchestrator/agent_runner.py` eine
austauschbare Schnittstelle (`AgentRunner`) mit zwei Implementierungen:

- **`ReplayAgentRunner`** — spielt echte, bereits validierte Ergebnisse vom 2026-09-17 ab
  (`orchestrator/fixtures/2026-09-17-eth-cycle/`, aus `tests/chain-agent1-2-3-4-5-6/` in die
  kanonischen Schemas überführt). Das ist der einzige Modus, der tatsächlich getestet und lauffähig
  ist — siehe `orchestrator/tests/`.
- **`ClaudeAgentRunner`** — **echt implementiert, aber unverifiziert** für die vier reinen
  Reasoning-Agenten (2 Stratege, 4 Risikomanager, 5 Portfolio-Manager, 7 Lern-Agent). Diese
  brauchen laut eigenem Prompt keinen zwingenden Tool-Zugriff — der Orchestrator liefert ihnen
  bereits alle nötigen Daten als Input. Für Agent 2 werden dabei bewusst drei getrennte Aufrufe
  gemacht (Bull-, Bear-Researcher, Moderator), wie in `agents/02-strategy-researcher.md`
  empfohlen. Für Agent 1 (Marktanalyst), 3 (Validator) und 6 (Execution-Trader) wirft
  `run()` bewusst `NotImplementedError` — diese brauchen echten Markt-/Backtest-/
  Ausführungs-Tool-Zugriff, den ein eigenständiges Skript ohne eigene REST-Clients für
  TradingView/tradingkit/Co-Invest nicht hat.

  **Wichtig:** In dieser Umgebung stand kein `ANTHROPIC_API_KEY` zur Verfügung, daher wurde der
  eigentliche API-Aufruf-Pfad **nie erfolgreich gegen die echte Anthropic-API getestet**.
  Getestet (ohne Key, siehe `orchestrator/tests/test_claude_agent_runner.py`) sind die Teile,
  die das nicht brauchen: Prompt-Extraktion aus den echten `agents/*.md`-Dateien, und dass die
  nicht unterstützten Stufen sowie ein fehlender Key die richtigen Fehler auslösen. Der Test für
  den echten API-Aufruf ist explizit übersprungen (`@unittest.skipUnless`), solange kein Key
  gesetzt ist — ein grüner Testlauf soll hier nicht vortäuschen, mehr geprüft zu haben, als
  tatsächlich geprüft wurde.

## Warum der mitgelieferte Zyklus trotzdem nie Agent 7 automatisch erreicht

Der ETH-Trade aus dem mitgelieferten Fixture-Zyklus wurde inzwischen real vom Nutzer über den
Co-Invest-Review-Link bestätigt (siehe `tests/chain-agent1-2-3-4-5-6/`). Trotzdem hält der
Orchestrator-Replay dieses Zyklus **nicht** bei Agent 7 an: Agent 7s eigene Analyse
(`tests/phase1-agent7/`) deckte auf, dass die Order entgegen Regel 3 in
`agents/06-execution-trader.md` ohne Take-Profit/Stop-Loss vorbereitet wurde. Der daraufhin
ergänzte Kill-Switch `check_tp_sl_proposed` stoppt den Lauf jetzt genau dort — nach Agent 6, vor
Agent 7 —, und zeigt damit, dass er den realen Fehler, der sich damals unbemerkt bis zur
menschlichen Bestätigung durchgeschlichen hat, beim nächsten Mal vorher abfangen würde. Ein
zusätzlicher, klar als synthetisch gekennzeichneter Test
(`test_full_cycle_reaches_agent7_when_tp_sl_proposed`) bestätigt, dass die Agent-7-Stufe selbst
funktioniert, sobald diese Bedingung erfüllt ist.

## Ausführen

```bash
pip install -r requirements.txt      # nur PyYAML, fuer --mode replay
python -m unittest discover -s orchestrator/tests -v   # 28 Tests laufen ohne API-Key, 1 wird uebersprungen
python -m orchestrator.cli --mode replay
```

Um den `ClaudeAgentRunner`-Pfad tatsächlich zu verifizieren (bisher ungetestet, siehe oben):

```bash
pip install -r requirements-live.txt   # zusaetzlich: anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python -m unittest orchestrator.tests.test_claude_agent_runner -v   # jetzt 5/5 statt 4/5+1 uebersprungen
```

`--mode live` in der CLI instanziiert `ClaudeAgentRunner`, aber ein **vollständiger** Pipeline-Lauf
damit schlägt aktuell zwangsläufig gleich bei Agent 1 fehl (`NotImplementedError`) — die
Live-Anbindung deckt bisher nur einzelne Reasoning-Stufen ab, keinen kompletten Zyklus. Um eine
der vier unterstützten Stufen isoliert zu testen, `ClaudeAgentRunner().run(stage, input_data)`
direkt aufrufen statt über `run_pipeline()`.

Der Lauf schreibt einen vollständigen Audit-Trail nach `runs/<Zeitstempel>/` (durch `.gitignore`
ausgeschlossen — das sind Laufzeit-Artefakte, kein Quellcode).

## Grenzen dieser ersten Version

- Nur ein einziger, real aufgezeichneter Zyklus ist als Fixture hinterlegt. Für weitere Zyklen
  müssten neue Fixtures nach demselben Muster erstellt werden — oder `ClaudeAgentRunner`
  (siehe oben: implementiert für Agent 2/4/5/7, aber unverifiziert) mit einem echten API-Key
  getestet und für Agent 1/3/6 um echte Tool-Anbindung ergänzt werden.
- `--mode live` kann aktuell keinen vollständigen 7-Agenten-Zyklus durchlaufen — nur einzelne,
  isolierte Aufrufe der vier unterstützten Reasoning-Stufen. Ein Live-Zyklus mit echten
  Marktdaten erfordert weiterhin den manuellen Weg (wie in `tests/chain-agent1-2-3-4-5-6-7/`
  vorgeführt), bis jemand REST-Clients für TradingView/tradingkit/Co-Invest ergänzt.
- Die Kill-Switches decken die vier bisher konkret gefundenen/geforderten Fälle ab
  (Tagesverlust, globales Veto, Positionsgrößen-Obergrenze, fehlendes TP/SL). Weitere Limits aus
  `config/mandate.example.yaml` (Cluster-Limit, Hebel) sind im Mandat definiert, aber noch nicht
  als eigener Kill-Switch verdrahtet — das ist die naheliegende nächste Erweiterung.
- Für den realen 2026-09-17-Zyklus existiert kein `agent7_learning.json`-Fixture, weil dieser
  Zyklus (korrekterweise) nie bis dorthin gekommen ist — Agent 7s Ausgabe für diesen Zyklus liegt
  nur als eigenständige Analyse in `tests/phase1-agent7/` vor, nicht als Orchestrator-Fixture.
- Es gibt noch keinen Scheduler (täglich/stündlich). `run_pipeline()` läuft genau einmal pro
  Aufruf; Wiederholung ist Sache des Aufrufers (Cron, GitHub Actions, o. Ä.), nicht Teil dieses
  Pakets.
