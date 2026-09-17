# Phase-1-Test: Agent 4 (Risikomanager) isoliert

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/04-risk-manager.md`](../../agents/04-risk-manager.md)
**Getestete Konfiguration:** [`config/mandate.example.yaml`](../../config/mandate.example.yaml)
**Output dieses Laufs:** [`risk-scenarios-2026-09-17.json`](risk-scenarios-2026-09-17.json)

## Setup

Drei Szenarien, aufbauend auf den echten Ergebnissen aus
[`tests/chain-agent1-2-3/`](../chain-agent1-2-3/) (BTC/ETH/SOL-Korrelationsmatrix, ETH als
einziger `validated_with_caveats`-Kandidat). Da `mandate.yaml` in diesem Repository bisher nur
als Konzept referenziert, aber nie tatsächlich angelegt war, wurde
`config/mandate.example.yaml` mit plausiblen Beispiel-Limits neu erstellt — eine direkte
Voraussetzung, um Agent 4 überhaupt testen zu können.

- **Szenario A (Normalfall):** Bestehende 8%-BTC-Position, neuer ETH-Kandidat (10%
  vorgeschlagen), Tagesverlust -1.2% (unauffällig).
- **Szenario B (harter Veto-Stresstest):** Wie A, aber Tagesverlust bereits bei -6.1% —
  über dem Mandats-Limit von 5%.
- **Szenario C (Cluster-Limit-Stresstest):** Bestehende BTC-Position bereits bei 25%, sodass
  der volle ETH-Vorschlag (10%) das Cluster-Limit (30%) brechen würde.

## Ergebnis

### ✅ Szenario A: Korrekte moderate Risikoeinstufung ohne Über-/Untertreibung

Kein hartes Limit verletzt, aber die 0.88-Korrelation zur bestehenden BTC-Position wurde korrekt
als Grund für "mittel" statt "niedrig" benannt — Agent 4 hat nicht einfach genickt, nur weil
keine harte Grenze überschritten war (Regel 4 des Prompts: abgestufte Einschätzung auch ohne
Veto).

### ✅ Szenario B: Globales Veto korrekt und unabhängig von der Kandidaten-Qualität

Das ist der wichtigste Testfall für diesen Agenten, analog zum Overfitting-Test bei Agent 3.
Der Risikomanager hat das Tagesverlustlimit als **hartes, nicht verhandelbares** Kriterium
behandelt (Regel 3: "Eine Überschreitung eines harten Limits ist ein VETO, kein Interpretations-
spielraum") und `global_veto: true` gesetzt — unabhängig davon, dass der ETH-Kandidat inhaltlich
identisch mit dem in Szenario A ist, wo er akzeptiert wurde. Das bestätigt: Die Qualität einer
Hypothese darf ein bereits gebrochenes Portfolio-Limit nicht "aufwiegen".

### ✅ Szenario C: Kappen statt pauschalem Veto — richtige Unterscheidung getroffen

Dieses Szenario prüft eine Nuance, die im Prompt nicht explizit vorformuliert war: Was passiert,
wenn ein hartes Limit durch die **volle** vorgeschlagene Positionsgröße verletzt würde, aber
nicht durch eine **kleinere** Größe? Der Risikomanager hat das Cluster-Limit korrekt als
Obergrenze für `max_position_pct` interpretiert (10% vorgeschlagen → auf 5% verbleibendes
Cluster-Budget gekappt) statt die gesamte Hypothese pauschal zu verwerfen. Das folgt konsistent
aus Regel 4 ("kann kleiner sein als von Agent 2 vorgeschlagen — niemals größer") und zeigt, dass
`max_position_pct` als Werkzeug für genau diesen Fall gedacht ist, nicht nur für weiche
Risikoeinschätzungen.

## Entdeckte Lücke: `mandate.yaml` existierte nicht

Sowohl `agents/04-risk-manager.md` als auch `docs/02-architektur.md` verweisen mehrfach auf eine
zentrale Mandats-/Konfigurationsdatei, aber keine der bisherigen Test-Läufe hatte sie tatsächlich
angelegt — jeder Agent-Test bis hierhin hat Limits improvisiert statt sie aus einer echten,
versionierten Quelle zu lesen. Das ist jetzt mit
[`config/mandate.example.yaml`](../../config/mandate.example.yaml) behoben; künftige Tests
(auch die des Portfolio-Managers, Agent 5) sollten dieselbe Datei referenzieren, damit Limits
über alle Agenten hinweg konsistent bleiben.

## Fazit

**Agent 4 besteht den isolierten Test in allen drei Szenarien**, einschließlich einer vom
Prompt nicht wörtlich vorweggenommenen Kappungs-Logik (Szenario C), die sich aber konsistent aus
den bestehenden Regeln ableiten ließ. Das ist ein gutes Zeichen für die Prompt-Qualität: Die
Regeln sind allgemein genug formuliert, um auch nicht explizit durchgespielte Situationen korrekt
zu behandeln.

**Nächster Schritt:** Szenario A (der realistische Fall) in die bestehende Kette einhängen →
siehe [`tests/chain-agent1-2-3-4/`](../chain-agent1-2-3-4/).
