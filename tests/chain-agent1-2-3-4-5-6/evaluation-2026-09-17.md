# Verkettungstest: Agent 1 → … → Agent 6

**Datum:** 2026-09-17
**Aufbauend auf:** [`tests/chain-agent1-2-3-4-5/`](../chain-agent1-2-3-4-5/),
[`tests/phase1-agent6/`](../phase1-agent6/)

## Ergebnis

Die Kette wurde bis Agent 6 durchgezogen — mit einem echten, nicht simulierten Tool-Aufruf gegen
die Co-Invest-Plattform im verifizierten Paper-Modus. Das Ergebnis ist **kein** abgeschlossener
Trade, sondern eine korrekt vorbereitete, unausgeführte Order mit Review-Link (siehe
[`06-execution-status-2026-09-17.json`](06-execution-status-2026-09-17.json)) — aus gutem Grund,
siehe [`tests/phase1-agent6/evaluation-2026-09-17.md`](../phase1-agent6/evaluation-2026-09-17.md).

## Was das für die Roadmap bedeutet

`docs/04-roadmap.md` sah für Phase 2 vor, dass Agent 6 im Paper-Modus **autonom** mehrere
Zyklen durchläuft, um die Pipeline zu validieren, bevor in Phase 4 eine menschliche Freigabe pro
Order eingeführt wird. Der heutige Test zeigt: **Auf der hier verfügbaren Plattform gibt es diese
Stufung gar nicht** — die menschliche Bestätigung ist ab dem ersten Paper-Trade technisch
erzwungen, nicht erst ab dem Live-Betrieb. Das ist keine schlechte Nachricht: Es bedeutet, dass
die in `docs/03-risiken-empfehlungen.md` empfohlene Vorsicht bereits strukturell eingebaut ist,
und dass Phase 2 der Roadmap (mehrere autonome Paper-Zyklen) auf dieser konkreten Plattform in
der ursprünglich gedachten Form nicht durchführbar ist, ohne dass jede einzelne Order von einem
Menschen bestätigt wird.

**Für ein zukünftiges, tatsächlich mehrere Zyklen autonom laufendes Paper-Trading-Setup** müsste
entweder eine andere Ausführungsplattform mit einer echten, direkt aufrufbaren
Paper-Order-API gefunden werden, oder Phase 2 der Roadmap müsste angepasst werden zu: "mehrere
Zyklen durchlaufen, aber jede Order-Vorbereitung wird gesammelt und dem Menschen als Batch zur
Bestätigung vorgelegt" statt vollautomatisch zu laufen.

## Was ist jetzt dein Zug

Der [reviewUrl](https://app.liquid.trade/trade/ETH?side=long&orderType=market&size=1000&sizeUnit=USDC&leverage=1&mode=paper)
aus `06-execution-status-2026-09-17.json` liegt bereit, falls du diesen (Paper-)Trade tatsächlich
bestätigen möchtest — das ist deine Entscheidung, nicht die eines Agenten. Falls du das nicht
willst, ist auch das ein vollkommen gültiges Ergebnis dieses Tests: Die Pipeline hat funktioniert,
der letzte Schritt liegt bewusst bei dir.

## Fazit

Dies ist der bisher wichtigste einzelne Befund der gesamten Testreihe: Eine reale
Sicherheitsgrenze der Zielplattform, die im ursprünglichen Konzept nicht vorgesehen war, wurde
durch tatsächliches Ausprobieren entdeckt statt in der Theorie übersehen zu werden. Der
Agent-6-Prompt wurde entsprechend korrigiert.

**Nächster Schritt:** Agent 7 (Lern-Agent) kann sinnvoll erst getestet werden, sobald eine Order
tatsächlich (mit deiner Bestätigung) ausgeführt wurde und ein echtes Ausführungsergebnis
vorliegt, das mit der ursprünglichen Erwartung verglichen werden kann. Bis dahin bleibt der
7-Agenten-Zyklus an dieser Stelle offen.
