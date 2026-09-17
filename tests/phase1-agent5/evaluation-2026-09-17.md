# Phase-1-Test: Agent 5 (Portfolio-Manager) isoliert

**Datum:** 2026-09-17
**Getestetes Dokument:** [`agents/05-portfolio-manager.md`](../../agents/05-portfolio-manager.md)
**Output dieses Laufs:** [`scenarios-2026-09-17.json`](scenarios-2026-09-17.json)

## Setup

Drei synthetische Szenarien, die gezielt die Regeln prüfen, die diesen Agenten von den
vorherigen unterscheiden: er ist die einzige Instanz mit tatsächlicher Kapitalallokations-Macht.

## Ergebnis

### ✅ Szenario A: Veto ist bindend — auch bei starkem Verdikt und hoher Konfidenz

Ein Kandidat mit Validator-Verdikt `validated` und Konfidenz 0.75 wurde trotzdem vollständig
abgelehnt, weil Agent 4 ein Veto ausgesprochen hatte. Das ist die wichtigste Regel dieses Agenten
(Regel 1: "nicht verhandelbar, auch nicht wenn du das Backtest-Ergebnis für überzeugend hältst")
und wurde korrekt ohne Abwägung angewendet — es gab keinen Versuch, das Veto durch eine kleinere
Positionsgröße zu "umgehen" (was ohnehin unzulässig wäre, da `max_position_pct` bei einem Veto
0.0 ist).

### ✅ Szenario B: Widersprüchliche Bestandsposition wird explizit adressiert, nicht ignoriert

Eine bestehende Long-Position wurde korrekt geschlossen, bevor die neue, gegenläufige
Short-Hypothese umgesetzt wurde — mit einer nachvollziehbaren Begründung, warum "schließen" statt
"reduzieren" gewählt wurde (die neue These negiert die alte vollständig, statt sie nur zu
relativieren). Ohne Regel 4 hätte ein weniger sorgfältiger Agent beide Positionen unkommentiert
nebeneinander stehen lassen können (Netto-Long trotz aktiver Short-These) oder die neue Order
schlicht ignoriert.

### ✅ Szenario C: Priorisierung nach Verdikt-Qualität UND Diversifikation, volle Kürzung statt Fragmentierung

Dies ist der anspruchsvollste Testfall. Bei Kapitalknappheit (drei Kandidaten summieren sich auf
125% des verfügbaren Kapitals) wurden zwei unterschiedliche Prioritätslogiken korrekt kombiniert:

1. **Verdikt-Qualität zuerst:** Der einzige `validated`-Kandidat (SYMBOL_A) bekam automatisch
   höchste Priorität vor beiden `validated_with_caveats`-Kandidaten.
2. **Diversifikation als Tie-Breaker:** Zwischen den beiden verbleibenden, verdikt-gleichen
   Kandidaten (SYMBOL_B, SYMBOL_C) wurde SYMBOL_C bevorzugt, weil es kaum mit dem bereits
   gewählten SYMBOL_A korreliert (0.10) — SYMBOL_B dagegen stark (0.85) und hätte wirtschaftlich
   kaum zusätzlichen Diversifikationswert gebracht.
3. **Volle Kürzung statt Fragmentierung:** Für das verbleibende, zu kleine Kapitalbudget (15%)
   wurde SYMBOL_B vollständig verworfen statt mit einer Mini-Position von 15% "aufgefüllt" zu
   werden — genau wie Regel 5 es verlangt ("kürze oder verwirf ... vollständig, statt alle
   proportional zu verkleinern").

Diese drei Mechanismen sind im Prompt als separate Regeln formuliert; das Szenario zeigt, dass
sie sich in einer konkreten Situation korrekt und ohne Widerspruch kombinieren lassen.

## Fazit

**Agent 5 besteht den isolierten Test in allen drei Szenarien.** Besonders wertvoll ist Szenario
C, weil es zeigt, dass die Priorisierungsregeln nicht nur einzeln, sondern auch in Kombination
(Qualität → Diversifikation → Kapitaldisziplin) zu einer konsistenten, nachvollziehbaren
Entscheidung führen — kein Agent, der bei der ersten Regel stehen bleibt und die anderen
ignoriert.

**Nächster Schritt:** Den realistischen (deutlich einfacheren) Fall aus der bisherigen Kette
anhängen → siehe [`tests/chain-agent1-2-3-4-5/`](../chain-agent1-2-3-4-5/).
