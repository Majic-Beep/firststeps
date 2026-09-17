# Verkettungstest: Agent 1 → … → Agent 6

Erster Test mit einem **echten** Ausführungs-Tool-Aufruf (Co-Invest, verifizierter Paper-Modus)
statt synthetischer Daten. Setzt [`tests/chain-agent1-2-3-4-5/`](../chain-agent1-2-3-4-5/) fort.

## Läufe

| Datum | Ergebnis | Dateien |
|---|---|---|
| 2026-09-17 | ⚠️ Order korrekt vorbereitet, Ausführung erfordert menschliche Bestätigung (Plattform-Eigenschaft, kein Fehler) | [`06-execution-status-2026-09-17.json`](06-execution-status-2026-09-17.json), [`evaluation-2026-09-17.md`](evaluation-2026-09-17.md) |

## Wichtigster Befund

`execute_order`/`execute_tpsl` sind auf der Co-Invest-Plattform ausschließlich für den internen
Aufruf durch eine menschliche Bestätigungs-Oberfläche bestimmt — ein Agent kann sie nicht direkt
aufrufen, auch nicht im Paper-Modus. `agents/06-execution-trader.md` wurde entsprechend
korrigiert. Details in [`tests/phase1-agent6/evaluation-2026-09-17.md`](../phase1-agent6/evaluation-2026-09-17.md).

Der vorbereitete Review-Link liegt bereit, falls der Trade tatsächlich bestätigt werden soll —
das ist eine bewusste, offene Entscheidung für den Menschen, nicht Teil der Pipeline selbst.
