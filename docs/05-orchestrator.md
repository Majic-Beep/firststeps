# Der Orchestrator

Dieses Dokument beschreibt `orchestrator/` — den deterministischen Code, der die sieben
Agenten in fester Reihenfolge aufruft, ihre Ausgaben validiert und harte Risikolimits
unabhängig von jedem Agenten-Urteil selbst prüft. Das ist die konkrete Umsetzung des
Abschnitts „Orchestrierung" in [`docs/02-architektur.md`](02-architektur.md).

## Was er tut

1. Ruft Agent 1–6 in fester Reihenfolge auf (kein Agent entscheidet, was als Nächstes läuft).
2. Validiert jede Ausgabe gegen ein festes Schema (`orchestrator/schemas.py`) — bei Abweichung
   bricht der Lauf hart ab, statt mit unvollständigen Daten weiterzumachen.
3. Prüft harte Risikolimits **im Code, nicht per Agenten-Urteil** (`orchestrator/killswitch.py`):
   Tagesverlustlimit vor Agent 4, globales Veto vor Agent 5, und eine Nachprüfung, dass Agent 5
   niemals die von Agent 4 gesetzte Positionsgrößen-Obergrenze überschreitet — genau das
   "defense in depth"-Prinzip, das `agents/04-risk-manager.md` explizit fordert.
4. Persistiert Ein-/Ausgabe jeder Stufe vollständig (`orchestrator/audit.py`, Ordner `runs/`).
5. Stoppt **immer** vor Agent 7, wenn Agent 6 nicht meldet, dass eine Order tatsächlich
   ausgeführt wurde — auf Co-Invest ist das laut `tests/phase1-agent6/` sogar der Normalfall,
   nicht der Ausnahmefall, siehe unten.

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
- **`ClaudeAgentRunner`** — ein dokumentierter, aber **nicht implementierter** Erweiterungspunkt
  für einen echten, live laufenden Agenten-Aufruf. Seine Docstring listet genau, was fehlt (API-Key,
  echte Tool-Anbindung pro Datenquelle, die menschliche Bestätigung bei Co-Invest). Das ist bewusst
  kein halbfertiger Vortäusch-Code, der beim ersten echten Aufruf überraschend fehlschlägt.

## Warum jeder Lauf vor Agent 6 stehen bleibt (Stand heute)

`tests/phase1-agent6/evaluation-2026-09-17.md` hat gezeigt: Co-Invest lässt keine autonome
Ausführung durch einen Agenten zu, auch nicht im Paper-Modus — `execute_order`/`execute_tpsl`
lösen ausschließlich über eine menschliche Bestätigungs-Oberfläche aus. Der mitgelieferte
Fixture-Zyklus bildet genau das ab: Der Lauf endet nach Agent 6 mit Status
`prepared_awaiting_human_confirmation` und einem Review-Link, nicht mit einer erfundenen
Ausführung. Agent 7 wird für diesen Zyklus konsequent übersprungen.

## Ausführen

```bash
pip install -r requirements.txt      # nur PyYAML
python -m unittest discover -s orchestrator/tests -v   # alle Tests laufen ohne API-Key
python -m orchestrator.cli --mode replay
```

Der Lauf schreibt einen vollständigen Audit-Trail nach `runs/<Zeitstempel>/` (durch `.gitignore`
ausgeschlossen — das sind Laufzeit-Artefakte, kein Quellcode).

## Grenzen dieser ersten Version

- Nur ein einziger, real aufgezeichneter Zyklus ist als Fixture hinterlegt. Für weitere Zyklen
  müssten neue Fixtures nach demselben Muster erstellt werden (oder `ClaudeAgentRunner`
  fertig implementiert werden).
- Die Kill-Switches decken die drei in `agents/04` und `agents/05` explizit genannten Fälle ab
  (Tagesverlust, globales Veto, Positionsgrößen-Obergrenze). Weitere Limits aus
  `config/mandate.example.yaml` (Cluster-Limit, Hebel) sind im Mandat definiert, aber noch nicht
  als eigener Kill-Switch verdrahtet — das ist die naheliegende nächste Erweiterung.
- Es gibt noch keinen Scheduler (täglich/stündlich). `run_pipeline()` läuft genau einmal pro
  Aufruf; Wiederholung ist Sache des Aufrufers (Cron, GitHub Actions, o. Ä.), nicht Teil dieses
  Pakets.
