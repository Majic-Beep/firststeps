# Phase-1-Test: Agent 6 (Execution-Trader) — echter Versuch im Paper-Modus

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/06-execution-trader.md`](../../agents/06-execution-trader.md)
(inzwischen korrigiert, siehe unten)
**Ausführungsumgebung:** Co-Invest-MCP (Liquid-Plattform), verifiziert im Paper-Modus
**Protokoll:** [`execution-attempt-2026-09-17.json`](execution-attempt-2026-09-17.json)

## Was getestet wurde

Anders als bei den Agenten 1–5 wurde hier nicht nur ein Prompt gegen synthetische oder reale
Daten laufen lassen, sondern **tatsächlich versucht, die von Agent 5 genehmigte ETH-Order über
das echte Ausführungs-Tool (Co-Invest) zu platzieren** — im verifizierten Paper-Modus, mit voller
Befolgung der in `agents/06-execution-trader.md` beschriebenen Sicherheitsreihenfolge
(`paper_trading_status` prüfen → `enable_paper_trading` explizit bestätigen → Portfolio-
Ausgangszustand erfassen → erst dann die Order vorbereiten).

## Zentraler Befund: Direkte Ausführung ist auf dieser Plattform gar nicht möglich — für niemanden

Der bislang wichtigste Einzelbefund der gesamten Testreihe: **`execute_order` und
`execute_tpsl` sind laut ihrer eigenen Tool-Beschreibung ausschließlich für den internen Aufruf
durch die Bestätigungs-Oberfläche der Plattform bestimmt** ("Do not call directly" /
"The model must NEVER call this tool directly"). `suggest_order` — das einzige Tool, das ein
Agent tatsächlich aufrufen darf — bereitet lediglich einen Review-Link vor
(`reviewUrl`, hier korrekt mit `mode=paper` markiert). Erst wenn ein **Mensch** diesen Link öffnet
und in der Liquid-Oberfläche bestätigt, wird intern `execute_order` ausgelöst. Ein zweiter
Aufruf von `get_portfolio` nach `suggest_order` bestätigt: Es wurde nichts ausgeführt, das
Portfolio ist unverändert.

Das gilt **ausnahmslos** — unabhängig davon, ob Paper- oder Live-Modus aktiv ist, und
unabhängig davon, wie viele vorgelagerte Agenten die Order bereits geprüft und freigegeben haben.

## Warum das wichtig ist

`agents/06-execution-trader.md` ging in seiner ursprünglichen Fassung davon aus, dass der
Execution-Trader-Agent `execute_order` und `execute_tpsl` selbst aufruft, sobald Paper-Trading
aktiviert ist (siehe die ursprüngliche Werkzeug-Empfehlung und Regel 3 zu Take-Profit/Stop-Loss).
Das ist auf der in dieser Umgebung verfügbaren Plattform **technisch unmöglich** — nicht wegen
fehlender Berechtigungen, sondern weil das Tool selbst so gebaut ist, dass es nur von einer
Bestätigungs-Oberfläche ausgelöst werden kann, die einen Menschen voraussetzt.

**Das ist eine eingebaute, plattformseitige Sicherheitseigenschaft**, keine Einschränkung, die
umgangen werden sollte. Sie erzwingt strukturell genau das "Mensch im Loop"-Prinzip, das
`docs/03-risiken-empfehlungen.md` bisher nur als Empfehlung für den späteren Live-Betrieb
(Roadmap-Phase 4) formuliert hatte — hier gilt es bereits **ab dem ersten Paper-Trade**.

## Korrektur an `agents/06-execution-trader.md`

Der Prompt wurde entsprechend angepasst (siehe Commit-Diff):
- Die Rolle des Agenten endet bei der **Order-Vorbereitung** (Äquivalent zu `suggest_order`)
  plus einer klaren Übergabe des Review-Links an einen Menschen — nicht bei der Ausführung
  selbst.
- Regel 3 (Take-Profit/Stop-Loss "sofort mit execute_tpsl setzen") wurde korrigiert: TP/SL
  werden ebenfalls nur vorgeschlagen, die tatsächliche Einrichtung erfordert dieselbe menschliche
  Bestätigung.
- Ein neuer Hinweis wurde ergänzt, dass die genaue technische Grenze (welche Tools ein Agent
  direkt aufrufen darf vs. welche nur von einer Bestätigungs-UI ausgelöst werden) **vor jeder
  Integration mit einer realen Handelsplattform geprüft werden muss** — sie ist nicht aus der
  Tool-Liste allein ersichtlich, sondern nur aus den einzelnen Tool-Beschreibungen selbst.

## Nebenbefund: dritte, eigene Symbol-Notation

Co-Invest/Liquid verwendet ein drittes Symbol-Schema (`ETH`), das weder mit TradingViews
Analyse-Symbolen (`BINANCE:ETHUSDT`) noch mit tradingkits Backtest-Symbolen
(`BYBIT:ETHUSDT.P`) übereinstimmt. Das bestätigt und verschärft die bereits im Kettentest
1→2→3 dokumentierte Symbol-Identitäts-Lücke (siehe `tests/chain-agent1-2-3/evaluation-2026-09-17.md`,
Befund 1): Es gibt jetzt **drei** verschiedene Venue-Namensräume in dieser einen Pipeline
(TradingView, Bybit/tradingkit, Liquid/Co-Invest), nicht nur zwei.

## Nebenbefund: bestehende, pipeline-fremde Position korrekt unangetastet gelassen

Das Paper-Portfolio enthielt bereits vor diesem Test eine TSLA-Position, die nicht aus dieser
Pipeline stammt. Sie wurde nicht verändert — teils durch bewusste Beachtung von Regel 1
("ausschließlich genehmigte Orders"), teils weil die Plattform ohnehin kein Tool für einen
direkten, unilateralen Positions-Schluss durch einen Agenten anbietet (laut `get_portfolio`-
Beschreibung: Schließen geschieht ausschließlich über einen vom Menschen gedrückten
Oberflächen-Button). Auch das ist eine weitere strukturelle Sicherheitsschicht, keine reine
Prompt-Disziplin.

## Fazit

Der Test ist **nicht** im klassischen Sinne "bestanden" oder "durchgefallen" — er hat etwas
Wichtigeres getan: er hat eine falsche Grundannahme im ursprünglichen Agent-6-Prompt aufgedeckt,
bevor sie in einem produktiveren Kontext zu Verwirrung geführt hätte. Die Pipeline endet auf
dieser Plattform korrekt und sicher bei einer vorbereiteten, aber unausgeführten Order mit
Review-Link — und das ist, richtig verstanden, ein Feature, kein Bug.

**Nächster Schritt:** Diesen Review-Link dem Menschen (dir) zur eigenen Entscheidung vorlegen
— siehe [`tests/chain-agent1-2-3-4-5-6/`](../chain-agent1-2-3-4-5-6/). Agent 7 (Lern-Agent)
kann sinnvollerweise erst getestet werden, nachdem eine Order tatsächlich (mit menschlicher
Bestätigung) ausgeführt wurde und ein echtes Ergebnis vorliegt.
