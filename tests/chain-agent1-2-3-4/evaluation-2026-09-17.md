# Verkettungstest: Agent 1 → Agent 2 → Agent 3 → Agent 4

**Datum:** 2026-09-17
**Aufbauend auf:** [`tests/chain-agent1-2-3/`](../chain-agent1-2-3/) (Marktanalyse, Bull/Bear-
Hypothesen, Backtest-Validierung für BTC/ETH/SOL) und
[`tests/phase1-agent4/`](../phase1-agent4/) (isolierte Stresstests des Risikomanagers).

## Was diese Stufe prüft

Anders als der vorherige Kettentest (1→2→3) ist die Übergabe von Agent 3 zu Agent 4 strukturell
einfacher, weil die Pipeline (siehe `agents/04-risk-manager.md`) explizit vorsieht, dass nur
Hypothesen mit Verdikt `validated` oder `validated_with_caveats` überhaupt bei Agent 4 ankommen.
Von den drei getesteten Symbolen war das nach Agent 3 nur noch **ETH** — BTC und SOL wurden
bereits vorher aussortiert. Das ist ein guter Realitäts-Check: Eine vollständige 3-Symbol-Analyse
kann am Ende der Kette auf einen einzigen (oder gar keinen) umsetzbaren Kandidaten schrumpfen,
und das ist kein Fehler der Pipeline, sondern ihr eigentlicher Zweck (schlechte Ideen aussieben,
bevor Kapital involviert wird).

## Ergebnis

Agent 4 hat den verbleibenden ETH-Kandidaten mit einem leeren Ausgangsportfolio bewertet (siehe
[`04-risk-verdict-2026-09-17.json`](04-risk-verdict-2026-09-17.json)):

- **Kein Veto** — keine harten Limits aus `config/mandate.example.yaml` verletzt.
- **Risiko "mittel" statt "niedrig"**, obwohl kein Limit verletzt wurde — Agent 4 hat dafür
  explizit Agent 3s eigene Kennzahlen herangezogen (Out-of-Sample-Sharpe nur 0.24, Max Drawdown
  32.6%) und den Validator-Status `validated_with_caveats` direkt in eine vorsichtigere
  Einstufung übersetzt, statt das "kein Veto" mit "alles gut" gleichzusetzen.

Das ist die entscheidende Beobachtung dieses Kettenschritts: **Agent 4 liest nicht nur die
Portfolio-Struktur (Korrelation, Konzentration), sondern auch die Qualitäts-Metadaten aus Agent
3s Backtest** (Sharpe, Drawdown, Verdikt-Nuance `validated` vs. `validated_with_caveats`). Das
war im Prompt so vorgesehen (Regel 2, "Drawdown-Verträglichkeit ... basierend auf den
Backtest-Kennzahlen aus Agent 3"), aber erst dieser Kettentest zeigt, dass die Übergabe der dafür
nötigen Felder (`validator_verdict`, `out_of_sample_stats`) tatsächlich funktioniert, wenn man
sie explizit mitgibt.

## Schnittstellen-Beobachtung: Agent 3s Schema gibt Backtest-Kennzahlen nicht in einer Form aus, die Agent 4 direkt nach unten reichen kann

Im Schema aus `agents/03-validator-backtester.md` stehen `in_sample`/`out_of_sample`-Kennzahlen
pro Hypothese, aber es gibt kein einzelnes, "mitnehmbares" Feld, das Agent 4 unverändert in seine
eigene Ausgabe (bzw. in seine Rationale) übernehmen soll. In diesem Testlauf wurden die
relevanten Werte (Sharpe, Max Drawdown, Profit Factor) manuell aus Agent 3s `out_of_sample`-
Objekt in ein separates `validator_out_of_sample_stats`-Feld im Agent-4-Input kopiert. Für einen
automatisierten Orchestrator ist das unproblematisch (einfache Feld-Extraktion), aber es lohnt
sich, das explizit in `docs/02-architektur.md` als Teil des Datenflusses zwischen Agent 3 und
Agent 4 zu dokumentieren, damit es nicht bei der Implementierung übersehen wird.

## Fazit

Die Kette 1 → 2 → 3 → 4 funktioniert durchgängig. Von ursprünglich drei fast identisch bullisch
bewerteten Krypto-Symbolen bleibt am Ende genau eine konkrete, risikogeprüfte Position mit
mittlerem statt fälschlich niedrigem Risiko übrig — nachvollziehbar begründet über alle vier
Stufen hinweg. Die einzige gefundene Lücke ist rein dokumentarisch (fehlende explizite
Feld-Zuordnung zwischen Agent 3 und Agent 4 in der Architektur-Doku), keine funktionale.

**Nächster Schritt:** Agent 5 (Portfolio-Manager) testen und anhängen (1→2→3→4→5) — an diesem
Punkt liegt dann eine vollständige, wenn auch noch manuell verkettete, Kapitalallokations-
Entscheidung vor. Alternativ: jetzt den deterministischen Orchestrator bauen, der diese vier
bereits bestätigten Übergaben automatisiert, statt die Kette manuell Agent für Agent zu erweitern.
