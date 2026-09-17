# Verkettungstest: Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5

**Datum:** 2026-09-17
**Aufbauend auf:** [`tests/chain-agent1-2-3-4/`](../chain-agent1-2-3-4/)

## Meilenstein

Mit diesem Schritt ist zum ersten Mal die **gesamte Entscheidungs-Hälfte** der Pipeline
end-to-end durchlaufen worden: von rohen Marktdaten (Agent 1) über eine strukturierte
Bull/Bear-Debatte (Agent 2), eine echte Backtest-Validierung (Agent 3) und eine Risikoprüfung
(Agent 4) bis zu einer konkreten, kapitalgewichteten Order-Freigabe (Agent 5). Es fehlen jetzt nur
noch Exekution (Agent 6) und die Lernschleife (Agent 7), um den vollen 7-Agenten-Kreis aus
`docs/02-architektur.md` zu schließen.

## Ergebnis

Da nach Agent 4 nur noch ein einziger Kandidat übrig war (ETH, siehe vorherige Kettentests) und
das Portfolio leer war, war dies der einfachste der bisher getesteten Agent-5-Fälle — keine
Kapitalknappheit, kein Konflikt mit Bestandspositionen, keine Priorisierung zwischen mehreren
Kandidaten nötig (diese komplexeren Fälle wurden bereits in
[`tests/phase1-agent5/`](../phase1-agent5/) isoliert und synthetisch geprüft). Agent 5 hat die
volle risikofreigegebene Positionsgröße (10%) genehmigt und explizit begründet, warum keine
zusätzliche eigene Kürzung nötig war: Agent 4 hatte die Vorsicht (Risiko "mittel" statt "niedrig")
bereits in die Größenbegrenzung eingepreist — eine zweite, unabhängige Kürzung durch Agent 5 wäre
doppelt gemoppelt gewesen und hätte die Vorsicht der vorherigen Stufe faktisch verdoppelt, ohne
neue Information.

**Das ist eine wichtige Beobachtung für das Gesamtsystem:** Die Pipeline funktioniert nur dann
kalibriert, wenn jede Stufe weiß, dass die vorherige Stufe ihre eigene Vorsicht bereits
eingearbeitet hat, und nicht "zur Sicherheit" nochmal pauschal nachlegt. Würde jede Stufe (Agent
3 durch konservative Konfidenz, Agent 4 durch Risikoabschlag, Agent 5 durch eigene Vorsicht)
unabhängig voneinander die Positionsgröße kürzen, würde eine an sich schon vorsichtig bewertete
Hypothese am Ende der Kette auf eine wirtschaftlich bedeutungslose Mini-Position schrumpfen. Der
Prompt für Agent 5 sagt das nicht explizit, aber die Rationale in diesem Testlauf macht es
implizit richtig: Regel 2 ("max_position_pct ist eine Obergrenze") wird als Obergrenze behandelt,
nicht als Ausgangspunkt für eine weitere eigene Reduktion.

## Vollständiges Ergebnis-Protokoll dieses Zyklus (alle 5 Stufen)

| Stufe | Kernaussage |
|---|---|
| Agent 1 | BTC/ETH/SOL alle "mostly_bullish", aber Korrelation 0.82-0.88 - ein Cluster, keine drei unabhängigen Signale |
| Agent 2 | Gleiche Handelsregel für alle drei, Positionsgrößen-Vorschlag bereits nach Diversifikation gestaffelt (SOL am kleinsten) |
| Agent 3 | Nur ETH übersteht die Out-of-Sample-Prüfung (`validated_with_caveats`); BTC und SOL `rejected` trotz teils stärkerer In-Sample-Zahlen |
| Agent 4 | ETH ohne Veto freigegeben, aber Risiko "mittel" statt "niedrig" wegen schwacher Out-of-Sample-Kennzahlen |
| Agent 5 | ETH-Long, 10% Kapitaleinsatz, 90% bleiben bewusst Cash |

**Endergebnis dieses Zyklus:** Aus drei Ausgangs-Ideen wird eine einzige, mit 10% Kapitaleinsatz
vorsichtig dimensionierte Position — nachvollziehbar über fünf Stufen hinweg begründet, keine
Stufe hat eine andere überstimmt oder ihre Vorsicht ignoriert.

## Fazit

Kette 1→2→3→4→5 funktioniert durchgängig, ohne neue strukturelle Schnittstellenprobleme (die
beiden bisher gefundenen Lücken — Symbol-Identität, Timeframe-Feld — betrafen frühere Stufen und
sind dokumentiert bzw. behoben). Die einzige neue Erkenntnis ist konzeptionell, nicht technisch:
Vorsicht darf sich über die Kette nicht kumulieren, ohne dass jede Stufe weiß, was die vorherige
bereits eingepreist hat.

**Nächster Schritt:** Agent 6 (Execution-Trader) testen und anhängen — hier wird zum ersten Mal
scharf zwischen Paper- und Live-Modus unterschieden werden müssen (siehe
`docs/04-roadmap.md`, Phase 2). Dieser Schritt sollte **ausschließlich im Paper-Trading-Modus**
von Co-Invest erfolgen.
