# Verkettungstest: Agent 1 → … → Agent 7 — der Kreis schließt sich

**Datum:** 2026-09-17
**Aufbauend auf:** [`tests/chain-agent1-2-3-4-5-6/`](../chain-agent1-2-3-4-5-6/),
[`tests/phase1-agent7/`](../phase1-agent7/)

## Der Zyklus, konzeptionell vollständig

Zum ersten Mal ist der gesamte, in [`docs/02-architektur.md`](../../docs/02-architektur.md)
beschriebene Kreis einmal komplett durchlaufen worden — mit echten Daten an jeder Stufe:

| Stufe | Ergebnis |
|---|---|
| 1. Marktanalyst | BTC/ETH/SOL alle "mostly_bullish", aber Korrelation 0,82–0,88 |
| 2. Stratege | Gleiche Handelsregel für alle drei, Positionsgrößen nach Diversifikation gestaffelt |
| 3. Validator | Nur ETH übersteht Out-of-Sample-Test (`validated_with_caveats`) |
| 4. Risikomanager | ETH ohne Veto, Risiko "mittel" wegen schwacher Kennzahlen |
| 5. Portfolio-Manager | ETH-Long, 10% Kapitaleinsatz genehmigt |
| 6. Execution-Trader | Order vorbereitet, vom Nutzer real über Co-Invest bestätigt: **ETH-PERP long, 0,408 ETH @ 2451**, aber ohne TP/SL |
| 7. Lern-Agent | Findet den fehlenden TP/SL als Prozessfehler, schlägt konkreten Code-Fix vor |

## Warum der automatisierte Orchestrator trotzdem vor Agent 7 stehen bleibt — und das richtig so ist

Direkt nachdem Agent 7 den TP/SL-Fund gemacht hat, wurde die Korrektur in den Orchestrator
eingebaut (`orchestrator/killswitch.py:check_tp_sl_proposed`). Würde man diesen exakten
2026-09-17-Zyklus heute erneut durch `python -m orchestrator.cli --mode replay` laufen lassen,
stoppt die Pipeline jetzt **nach Agent 6, vor Agent 7** — mit der Begründung, dass keine Position
ohne vorgeschlagenes TP/SL eröffnet werden darf. Das ist kein Rückschritt, sondern der Beweis,
dass die neue Sicherung funktioniert: Der reale Fehler, der diesmal erst im Nachhinein von Agent 7
gefunden wurde, würde beim nächsten Mal **vor** der menschlichen Bestätigung abgefangen.

Mit anderen Worten: Dieser eine Zyklus musste "von Hand" bis Agent 7 durchgespielt werden, genau
weil die Sicherung, die ihn beim automatisierten Orchestrator-Lauf gestoppt hätte, zum Zeitpunkt
des Zyklus noch nicht existierte. Ein synthetischer Mechanik-Test
(`test_full_cycle_reaches_agent7_when_tp_sl_proposed`) bestätigt zusätzlich, dass die
Agent-7-Stufe im Orchestrator selbst korrekt funktioniert, sobald diese eine Bedingung erfüllt
ist.

## Offene Punkte

1. **Die reale ETH-Position hat weiterhin kein Stop-Loss.** Das ist keine automatische Folge
   dieses Tests — ob und wie das nachträglich behoben wird (neuer Review-Link über Co-Invest),
   ist eine bewusste Entscheidung des Nutzers.
2. **Die Kernthese ist noch offen.** Erst wenn die Position schließt (regelbasiert oder manuell),
   lässt sich beurteilen, ob die ursprüngliche EMA20/RSI-These selbst richtig war — das ist ein
   zukünftiger, eigenständiger Agent-7-Lauf, kein Teil dieses Zyklus.
3. **Konfidenz-Kalibrierung** (Regel 5 des Lern-Agenten) bleibt mit einem einzigen Zyklus nicht
   beurteilbar — das erfordert mehrere abgeschlossene Zyklen.

## Fazit

Der 7-Agenten-Kreis ist nicht nur als Konzept fertig, sondern einmal vollständig mit echten
Daten, echten Tool-Aufrufen und einer echten menschlichen Bestätigung durchlaufen worden — und
hat dabei einen echten, jetzt behobenen Fehler im eigenen Prozess gefunden. Das ist genau die
Feedback-Schleife, die die ursprüngliche Aufgabenstellung ("Lernen aus den Fehlern bei der
Exekution") verlangt hat.

**Nächster sinnvoller Schritt laut Roadmap:** Warten, bis die ETH-Position schließt, um einen
vollständigen Post-Mortem (Kernthese richtig oder falsch?) durchzuführen — oder einen zweiten,
unabhängigen Zyklus starten, um erstmals die Muster-Erkennung von Agent 7 mit echten (statt
synthetischen) Wiederholungsfällen zu testen.
