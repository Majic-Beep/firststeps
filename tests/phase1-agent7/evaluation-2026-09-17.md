# Phase-1-Test: Agent 7 (Lern-Agent) — erster echter Post-Mortem

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/07-learning-postmortem.md`](../../agents/07-learning-postmortem.md)
**Output dieses Laufs:** [`agent7-outputs-2026-09-17.json`](agent7-outputs-2026-09-17.json)

## Setup

Anders als bei den Agenten 1–6 gab es für Agent 7 bisher **keine** Testmöglichkeit — er braucht
ein tatsächliches Ausführungsergebnis, und das lag erst vor, nachdem der Nutzer den von Agent 6
vorbereiteten ETH-Trade über den Co-Invest-Review-Link real bestätigt hat (siehe
`tests/chain-agent1-2-3-4-5-6/`). Drei Szenarien:

- **A (real):** der tatsächliche 2026-09-17-Zyklus.
- **B, C (synthetisch, klar gekennzeichnet):** prüfen gezielt Regel 2/3 des Prompts — die
  Unterscheidung zwischen einem Einzelfall (nur beobachten) und einem wiederkehrenden Muster
  (Regeländerung vorschlagen) —, weil dafür mehrere Zyklen nötig sind, die real noch nicht
  existieren.

## Ergebnis Szenario A: ein echter, unmittelbar verwertbarer Fund

Agent 7 hat die tatsächliche Ausführung analysiert und einen klaren **Prozessfehler** bei Agent 6
identifiziert: Trotz Regel 3 in `agents/06-execution-trader.md` ("Schlage Take-Profit UND
Stop-Loss für JEDE vorzubereitende Position mit vor") wurde die ETH-Order ohne TP/SL-Vorschlag
vorbereitet und so auch vom Nutzer bestätigt — die Position ist aktuell ungeschützt offen.

Wichtig ist, **wie** Agent 7 das eingeordnet hat: als eindeutige Regelverletzung (Rule 1:
"Prozessfehler"), nicht als mehrdeutige Ergebnis-Varianz. Das rechtfertigt laut Prompt-Logik eine
sofortige Änderungsempfehlung, auch bei nur einem Vorkommen — im Unterschied zu Regel 3, die vor
vorschnellen Regeländerungen bei normaler Marktunsicherheit warnt (siehe Szenario B/C). Agent 7
hat diese Unterscheidung selbst explizit benannt, nicht nur zufällig richtig geraten.

Zusätzlich korrekt eingeordnet: Die **Kernthese** (regelbasierter Ausstieg über EMA20/RSI) ist
mangels Positionsabschluss noch **nicht beurteilbar** — Agent 7 hat sich nicht dazu verleiten
lassen, aus einem noch offenen Trade voreilig "richtig" oder "falsch" abzuleiten.

## Umgesetzte Korrektur

Der von Agent 7 vorgeschlagene Fix wurde umgesetzt (nach Regel 6: „Vorschläge, keine
selbstständige Übernahme" — hier durch menschliches Review freigegeben):

- `orchestrator/schemas.py`: `EXECUTION_ITEM_SCHEMA` verlangt jetzt ein Pflichtfeld
  `tp_sl_proposed`.
- `orchestrator/killswitch.py`: neue Funktion `check_tp_sl_proposed()` — stoppt die Pipeline
  hart, wenn eine Position ohne vorgeschlagenes TP/SL eröffnet/vorbereitet würde.
- Ein neuer Orchestrator-Test (`test_real_2026_09_17_cycle_now_caught_by_tp_sl_killswitch`)
  bestätigt: Würde der reale 2026-09-17-Zyklus heute erneut laufen, würde die Pipeline diesen
  Fehler **vor** der menschlichen Bestätigung abfangen, statt ihn wie tatsächlich geschehen
  durchzulassen.

## Ergebnis Szenario B: kein Overreacting bei einem Einzelfall

Ein synthetischer, korrekt durchgeführter Verlust-Trade (-2,1%, alle Regeln befolgt, TP/SL
korrekt gesetzt) wurde von Agent 7 zutreffend als `kein_fehler_normale_varianz` /
`ergebnisfehler_bei_korrektem_prozess` eingestuft — **keine** Regeländerung vorgeschlagen, nur
ein `watch_item`. Das ist die in Regel 2/6 geforderte Zurückhaltung: nicht jeder Verlust ist ein
Bug.

## Ergebnis Szenario C: korrekte Eskalation beim dritten Vorkommen

Derselbe Verlust-Typ, aber als **dritter** aufeinanderfolgender Fall mit identischer Regel auf
korrelierten Symbolen: Jetzt hat Agent 7 `recurring_pattern.is_recurring: true` gesetzt und einen
konkreten `proposed_change` formuliert (Parameter-Sensitivitätsanalyse vor erneuter Verwendung
der Regel). Zusammen mit Szenario B zeigt das: Die Schwelle „Einzelfall vs. Muster" aus Regel 3
wird nicht nur behauptet, sondern in zwei kontrastierenden Fällen tatsächlich unterschiedlich
behandelt.

## Fazit

**Agent 7 besteht den ersten echten Test** — und liefert dabei sofort einen konkreten, jetzt im
Code verankerten Sicherheitsgewinn (TP/SL-Pflichtprüfung), statt nur eine plausible Analyse ohne
Konsequenz. Die beiden synthetischen Szenarien bestätigen zusätzlich, dass die im Prompt zentrale
Unterscheidung zwischen Einzelfall und Muster tatsächlich zu unterschiedlichem Verhalten führt,
nicht nur auf dem Papier steht.

**Damit ist der konzeptionelle 7-Agenten-Kreis zum ersten Mal vollständig durchlaufen** — siehe
[`tests/chain-agent1-2-3-4-5-6-7/`](../chain-agent1-2-3-4-5-6-7/) für die Einordnung, warum der
*automatisierte* Orchestrator-Lauf dieses Zyklus trotzdem vor Agent 7 stehen bleibt (die neue
Sicherung greift genau da, wo sie soll).

⚠️ **Offener Punkt:** Die reale ETH-Position auf Co-Invest hat aktuell weiterhin kein Stop-Loss.
Das zu beheben (per neuem `suggest_order`/TP-SL-Review-Link) ist eine bewusste, separate
Entscheidung des Nutzers, keine automatische Folge dieses Tests.
