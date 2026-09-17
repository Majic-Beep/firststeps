# Phase-1-Test: Agent 1 (Marktanalyst) isoliert

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/01-market-analyst.md`](../../agents/01-market-analyst.md)
**Output dieses Laufs:** [`market-brief-2026-09-17.json`](market-brief-2026-09-17.json)

## Setup

- Fixes Symbol-Universum (5 Titel, wie in der Roadmap vorgesehen): `NASDAQ:AAPL`, `NASDAQ:MSFT`,
  `NASDAQ:NVDA`, `NASDAQ:TSLA`, `NASDAQ:AMZN`.
- Ausschließlich lesende TradingView-MCP-Tools verwendet: `get_quotes_batch`,
  `analyze_multi_timeframe_batch`, `get_economic_calendar`, `calculate_correlation_tool`,
  `get_news` (je Symbol).
- **Kein Kapital, keine Order-Tools** — wie von Phase 1 gefordert.
- Der Prompt aus `agents/01-market-analyst.md` wurde wörtlich als Verhaltensgrundlage angewendet
  (keine Vereinfachung der Regeln für den Test).

## Prüfkriterien aus der Roadmap (Phase 1)

### 1. Hält er sich an das JSON-Schema? ✅ Bestanden

Der Output folgt der in `agents/01-market-analyst.md` vorgegebenen Struktur
(`timestamp`, `universe`, `macro`, `per_symbol`, `sources`) und liefert zusätzlich
sinnvolle, im Schema als optional/erweiterbar angelegte Felder (`sentiment_method`,
`data_quality_flags_global`, `cross_symbol`), ohne die Pflichtfelder zu verletzen.

### 2. Erfindet er Zahlen? ✅ Bestanden

Kein Wert im Brief wurde ohne Tool-Beleg erzeugt. Konkret:
- `volume_vs_avg` wurde für **alle** Symbole bewusst auf `null` gesetzt, weil keines der
  verwendeten Tools eine Durchschnittsvolumen-Baseline liefert — statt eine plausible, aber
  erfundene Zahl einzusetzen (das ist genau das Verhalten, das Regel 2 des Prompts verlangt).
- `sentiment_score` wird nicht als präzise, kalibrierte Kennzahl ausgegeben, sondern explizit als
  grobe, manuelle Schlagzeilen-Einordnung mit niedriger Konfidenz (0.25–0.3) gekennzeichnet
  (`sentiment_method`-Feld) — es existiert kein Sentiment-Scoring-Tool im verfügbaren Werkzeugsatz,
  und der Prompt wurde nicht "kreativ" darüber hinweggetäuscht.
- Alle Kurs-, Volumen- und Indikatorwerte sind 1:1 aus den Tool-Antworten übernommen
  (siehe `sources`).

### 3. Erkennt er die eingebauten Data-Quality-Flags korrekt? ✅ Bestanden, mit einem echten Fund

- **Erkannt:** Fehlende Durchschnittsvolumen-Quelle, fehlendes Sentiment-Scoring-Tool,
  eine geringfügige Preisabweichung zwischen zwei fast zeitgleichen Tool-Aufrufen für AAPL
  (332.28 vs. 332.31) korrekt als plausible Marktbewegung statt als Fehler eingeordnet.
- **Echter, nicht vorab eingeplanter Fund:** `get_economic_calendar` wurde mit
  `importance=["high"]` aufgerufen, lieferte aber ein numerisches Feld `"importance": 1` statt
  eines erkennbaren High/Medium/Low-Labels zurück. Der Agent hat dies korrekt als
  Interpretationsunsicherheit geflaggt, statt dem Tool-Filter blind zu vertrauen — genau das in
  Regel 5 geforderte Verhalten bei zweifelhafter Datenqualität.
- **Kontrollierte Fehlalarme (kein Über-Flaggen):** Für keines der 25 gesichteten Schlagzeilen
  wurde fälschlich `prompt_injection_suspected: true` gesetzt — es waren auch tatsächlich keine
  Instruktionsversuche enthalten. Das ist wichtig gegenzuprüfen, weil ein Agent, der bei jeder
  Schlagzeile reflexhaft Alarm schlägt, für die Pipeline nutzlos wäre.
- **Widersprüche korrekt offengelassen statt geglättet:** z. B. AAPL (bullische Technik vs.
  negative Konsum-News), TSLA (bullisches 1D/4h- vs. bearishes 1W-Rating), AMZN (positive
  Tagesbewegung vs. bearishes technisches Composite-Rating) — in allen Fällen wurde der
  Widerspruch benannt, nicht zugunsten einer glatten Erzählung aufgelöst (Regel 4).

## Zusätzliche Beobachtungen (für Agent 7 / künftige Prompt-Iterationen vormerken)

1. **Sentiment-Score-Präzision ist strukturell begrenzt.** Solange kein dediziertes
   Sentiment-Tool angebunden ist, bleiben `sentiment_score`-Werte grobe Schätzungen aus 5
   Schlagzeilen pro Symbol. Für Phase 2 empfiehlt sich entweder (a) ein echtes
   Sentiment-Aggregations-Tool zu ergänzen, oder (b) das Feld im Schema explizit als
   "Richtungstendenz" statt "Score" umzubenennen, um falsche Präzision gegenüber
   nachgelagerten Agenten zu vermeiden.
2. **`importance`-Encoding im TradingView-Wirtschaftskalender vor Produktivnutzung klären.**
   Bevor Agent 4 (Risikomanager) oder der Orchestrator sich jemals auf eine automatische
   High-Impact-Filterung verlassen, sollte verifiziert werden, was der Zahlenwert tatsächlich
   codiert — sonst könnten wichtige Makro-Termine unbemerkt durchrutschen.
3. **Kein Volumen-Baseline-Tool vorhanden.** `volume_vs_avg` ist im Schema vorgesehen, aber mit
   dem aktuellen Werkzeugsatz nicht befüllbar. Entweder Schema-Feld entfernen/als "optional,
   benötigt zusätzliches Tool" kennzeichnen, oder ein Tool ergänzen (z. B. historische
   OHLCV-Daten selbst mitteln).

## Fazit

**Agent 1 besteht den isolierten Phase-1-Test.** Er hält das Schema ein, erfindet keine Daten,
markiert Unsicherheiten korrekt statt sie zu verstecken, und erkennt sowohl eingeplante als auch
einen nicht vorab bekannten Datenqualitäts-Sonderfall (Wirtschaftskalender-Encoding). Die drei
oben genannten Beobachtungen sind keine Fehlschläge, sondern Verbesserungspotenzial für die
Tool-Ausstattung vor Phase 2 (verkettete Pipeline). Empfehlung: **weiter zu Agent 3 (Validator)
isoliert testen**, wie in der Roadmap als nächster Schritt vorgesehen, bevor die Kette verbunden
wird.
