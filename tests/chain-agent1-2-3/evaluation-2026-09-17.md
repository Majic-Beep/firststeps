# Verkettungstest: Agent 1 → Agent 2 → Agent 3

**Datum:** 2026-09-17
**Getestete Dokumente:** [`agents/01-market-analyst.md`](../../agents/01-market-analyst.md),
[`agents/02-strategy-researcher.md`](../../agents/02-strategy-researcher.md),
[`agents/03-validator-backtester.md`](../../agents/03-validator-backtester.md)

Anders als die bisherigen Einzeltests prüft dieser Lauf nicht mehr "kann Agent X seine eigene
Aufgabe erfüllen", sondern **"passen die Schnittstellen zwischen den Agenten tatsächlich
zusammen, wenn man sie hintereinanderschaltet"**. Dafür wurde ein Krypto-Universum (BTC, ETH,
SOL) gewählt, weil es das einzige ist, das sowohl von TradingView (Agent 1) als auch von
tradingkit (Agent 3) unterstützt wird — siehe Befund 1 unten, der genau diese Notwendigkeit
aufdeckt.

## Ergebnis der Kette selbst

| Symbol | Agent 1 (Technik) | Agent 2 (These) | Agent 3 In-Sample | Agent 3 Out-of-Sample | Verdikt |
|---|---|---|---|---|---|
| BTC | mostly_bullish | long, Konfidenz 0.5 | +54.6% | **-3.5%** | `rejected` |
| ETH | mostly_bullish | long, Konfidenz 0.45 | +57.8% | **+6.8%** | `validated_with_caveats` |
| SOL | mostly_bullish (stärkste Einzelthese) | long, Konfidenz 0.5 | +133.2% | **-19.7%** | `rejected` |

Der zentrale inhaltliche Befund: **Drei von Agent 1 fast identisch bewertete Symbole mit von
Agent 2 fast identischer Handelsregel liefern bei Agent 3 drei unterschiedliche Ergebnisse.**
Das ist genau der Wert, den die Pipeline liefern soll — keine der vorgelagerten Stufen hätte
diesen Unterschied allein sichtbar gemacht.

## Befund 1: Symbol-Identität ist zwischen Agent 1 und Agent 3 nicht eindeutig definiert

Agent 1 analysierte `BINANCE:BTCUSDT` (und intern löste das Multi-Timeframe-Tool das sogar
zu einem aggregierten `CRYPTO:BTCUSD`-Index-Feed auf — leicht abweichender Preis, siehe
`data_quality_flags` im Market Brief). Agent 3 konnte aber nur über tradingkit backtesten,
das ausschließlich Bybit-USDT-Perpetuals kennt (`BTCUSDT` → `BYBIT:BTCUSDT.P`). Das musste in
diesem Testlauf **manuell** aufgelöst werden — die Architektur (`docs/02-architektur.md`) sagt
zwar, welches Tool welcher Agent nutzt, aber nicht, wie ein Symbol-Identifier über die
Tool-Grenze hinweg konsistent gehalten wird.

**Praktische Konsequenz:** Für Aktien (wie im Agent-1-Solotest mit AAPL etc.) wäre das ein noch
größeres Problem, da tradingkit dort überhaupt keine Instrumente anbietet — die Verkettung
funktioniert aktuell **nur für Krypto/Forex**, nicht für das ursprünglich getestete
Aktien-Universum. Das ist eine reale Einschränkung des in dieser Umgebung verfügbaren
Werkzeugsatzes, keine Prompt-Schwäche.

**Empfehlung:** `docs/02-architektur.md` um einen Abschnitt "Symbol-Auflösung" ergänzen, der
festlegt, dass Agent 1 künftig sowohl den Analyse-Symbol-String als auch (wo verfügbar) einen
kanonischen, exekutierbaren Instrument-Identifier mitgibt, den Agent 2 und Agent 3 unverändert
weiterreichen. Für ein produktives System zusätzlich klären, ob Aktien-Strategien über ein
anderes Backtest-Tool laufen müssten als tradingkit.

## Befund 2: Agent 2s Hypothesen-Schema hatte kein Timeframe-Feld — echte Lücke, jetzt behoben

Beim Übersetzen von Agent 2s Ausgabe in Pine-Code für Agent 3 fiel auf: Das in
`agents/02-strategy-researcher.md` definierte JSON-Schema für Hypothesen hat `entry_condition`
als freien Text, aber **kein Feld, das explizit festlegt, auf welchem Chart-Zeitrahmen** die
Bedingung geprüft werden soll. Im Market Brief hat jedes Symbol 1D-, 4h- und 1W-Werte — ohne
explizites Timeframe-Feld muss der Validator raten, welcher Wert gemeint ist. In diesem Testlauf
wurde "1D" implizit aus dem Kontext ("Tagesschluss") abgeleitet, aber das ist Interpretation,
keine feste Vorgabe.

**Behoben:** `agents/02-strategy-researcher.md` wurde um ein Pflichtfeld `"timeframe"` im
Hypothesen-Schema ergänzt (siehe Diff in diesem Commit) — eine kleine, konkrete Korrektur, die
direkt aus diesem Testlauf folgt, analog zu dem, was Agent 7 (Lern-Agent) im späteren Betrieb
systematisch vorschlagen soll.

## Befund 3: Freitext-Entry-Bedingung → Pine-Code ist ein nicht spezifizierter Übersetzungsschritt

Agent 2 liefert `entry_condition` als natürlichsprachlichen Satz
("Tagesschluss > EMA(20) UND RSI(14) zwischen 45 und 65"). Agent 3 muss daraus eindeutigen,
deterministischen Code erzeugen. In diesem Testlauf war die Übersetzung eindeutig genug, um sie
ohne Rückfrage in Pine zu übertragen — aber nichts in den beiden Prompts erzwingt das. Bei
komplexeren Bedingungen (z. B. "wenn der Kurs ein neues 20-Tage-Hoch macht, aber das Volumen
unterdurchschnittlich ist") könnten zwei unabhängige Ausführungen von Agent 3 zu unterschiedlichem
Code kommen.

**Empfehlung (noch nicht umgesetzt, für spätere Iteration vormerken):** Entweder Agent 2 auf
eine kleine, kontrollierte Ausdruckssprache beschränken, die sich 1:1 auf Agent 3s
Indikator-Allowlist abbildet, oder Agent 3 verpflichten, seine wörtliche Code-Interpretation der
Bedingung zur Kontrolle mit auszugeben, bevor der Backtest läuft.

## Befund 4: Agent 2s Diversifikations-Regel griff sichtbar und sinnvoll

Regel 4 in `agents/02-strategy-researcher.md` verlangt, bei der Priorisierung auch
Diversifikation zu berücksichtigen, nicht nur Konfidenz. Die Korrelationsmatrix aus Agent 1s
Market Brief (BTC/ETH 0.88, ETH/SOL 0.83, BTC/SOL 0.829 — alle "sehr stark positiv") wurde
genutzt, um trotz technisch stärkster Einzelthese bei SOL dessen vorgeschlagene Positionsgröße
am kleinsten anzusetzen (0.05 vs. 0.15 bei BTC). Das hat sich im Nachhinein durch Agent 3 sogar
bestätigt: SOL lieferte das schlechteste Out-of-Sample-Ergebnis der drei — die Diversifikations-
Vorsicht war nicht nur regelkonform, sondern hätte hier auch inhaltlich vor der größten
Enttäuschung geschützt (auch wenn das im Einzelfall Zufall sein kann, nicht als Beweis für
generelle Treffsicherheit misszuverstehen).

## Fazit

Die Verkettung 1 → 2 → 3 funktioniert **inhaltlich** gut: Die Ausgabe jeder Stufe war für die
nächste Stufe verwendbar, und das Endergebnis (1 von 3 Hypothesen validiert-mit-Vorbehalt, 2
abgelehnt) ist genau die Art von differenzierter, nicht-trivialer Aussage, die die ganze Pipeline
rechtfertigt. Zwei konkrete Schema-/Architektur-Lücken wurden gefunden: Symbol-Identität über
Tool-Grenzen hinweg (Befund 1, für später) und fehlendes Timeframe-Feld bei Hypothesen
(Befund 2, **bereits behoben**). Befund 3 (Freitext-zu-Code-Übersetzung) bleibt ein offener,
bewusst nicht überstürzt gelöster Punkt für eine spätere Iteration.

**Empfehlung für den nächsten Schritt:** Da jetzt 1→2→3 nachweislich funktioniert, als Nächstes
entweder Agent 4 (Risikomanager) isoliert testen und dann in dieselbe Kette einhängen (1→2→3→4),
oder direkt mit dem Aufbau des in `docs/02-architektur.md` beschriebenen deterministischen
Orchestrators beginnen, der diese Übergaben künftig automatisch statt manuell durchführt.
