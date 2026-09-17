# Roadmap: Von der Idee zum (vorsichtigen) Betrieb

## Phase 0 — Konzept (dieses Repository)

- [x] Recherche bestehender Konzepte
- [x] Architektur mit 7 Agenten definiert
- [x] System-Prompts für alle Agenten geschrieben
- [x] Risiken und regulatorische Fragen dokumentiert

## Phase 1 — Einzelagenten isoliert testen

Ziel: Jeden Agenten-Prompt einzeln gegen echte, aber read-only Daten testen — noch ohne
Verkettung, noch ohne jede Ausführung.

- Agent 1 (Marktanalyst) mit TradingView-MCP für ein kleines, festes Symbol-Universum (z. B.
  3–5 Aktien) laufen lassen. Prüfen: Hält er sich an das JSON-Schema? Erfindet er Zahlen?
  Erkennt er die eingebauten Data-Quality-Flags korrekt?
- Agent 3 (Validator) mit tradingkit gegen 2–3 einfache, von Hand geschriebene
  Test-Hypothesen laufen lassen. Prüfen: Erkennt er absichtlich eingebaute Overfitting-Fälle
  (z. B. eine Strategie mit nur 5 Trades) korrekt als nicht belastbar?
- **Kein Kapital, keine Order-Tools in dieser Phase.**

## Phase 2 — Verkettete Pipeline im Trockentest

Ziel: Alle 7 Agenten als vollständige Pipeline laufen lassen, aber Agent 6 nur im
**Paper-Trading-Modus** (`enable_paper_trading` in Co-Invest **muss vor jedem ersten Lauf**
aktiv sein — das ist keine Option, sondern Voraussetzung).

- Orchestrator implementieren (deterministischer Code, siehe `docs/02-architektur.md`), inkl.
  Schema-Validierung zwischen den Stufen und Persistierung aller Ein-/Ausgaben.
- Mandat/Konfiguration (`mandate.yaml`) definieren: Symbol-Universum, Kapitalbasis (fiktiv),
  Risikolimits (max. Symbolanteil, max. Sektoranteil, Tagesverlustlimit, max. Hebel),
  Rebalance-Takt.
- Mehrere vollständige Zyklen (mindestens mehrere Wochen, über unterschiedliche
  Marktbedingungen) im Paper-Modus laufen lassen.
- Agent 7 (Lern-Agent) erstmals mit echten (Paper-)Ausführungsdaten laufen lassen und die
  vorgeschlagenen Prompt-/Konfigurationsänderungen manuell reviewen, bevor sie übernommen werden.
- **Explizites Kriterium für „bestanden":** Kein einziger technischer Kill-Switch-Fehlgriff
  (Limit wurde überschritten UND nicht gestoppt), Schema-Validierung nie fehlgeschlagen,
  Audit-Trail vollständig und nachvollziehbar. Performance selbst ist in dieser Phase
  zweitrangig — es geht zuerst um Prozesssicherheit.

## Phase 3 — Rechtliche Klärung (parallel zu Phase 2, vor Phase 4 abschließen)

- Klären: Reine Eigenverwaltung mit automatisierter Ausführung — Broker-AGB-konform?
- Falls jemals Kapital Dritter oder ein Produkt/SaaS in Betracht gezogen wird: BaFin-Erlaubnis-
  pflicht (§ 32 KWG) rechtlich prüfen lassen, **bevor** auch nur ein Prototyp mit fremdem
  Kapital läuft (siehe `docs/03-risiken-empfehlungen.md`, Abschnitt 1).
- Steuerliche Dokumentationspflichten klären und Protokollierung entsprechend aufsetzen.

## Phase 4 — Sehr kleiner, überwachter Live-Betrieb (eigenes Kapital)

Nur starten, wenn Phase 2 und 3 vollständig abgeschlossen sind.

- Start mit einem Kapitalbetrag, dessen kompletter Verlust unproblematisch wäre.
- Menschliche Freigabe zwischen Agent 5 und Agent 6 für JEDE Order (kein Vollautomatik-Start).
- Enge Tagesverlustlimits, deutlich unterhalb dessen, was man „aushalten" könnte.
- Wöchentliche manuelle Review-Runde: Agent-7-Report lesen, vorgeschlagene Änderungen bewusst
  freigeben oder ablehnen, niemals automatisch übernehmen lassen.

## Phase 5 — Schrittweise Automatisierung (optional, nur nach nachgewiesener Stabilität)

- Manuelle Freigabe schrittweise durch Stichproben-Freigabe ersetzen (z. B. jede 5. Order
  manuell prüfen), nie vollständig entfernen, solange reales Kapital involviert ist.
- Kapital nur langsam erhöhen, gekoppelt an nachgewiesene Prozessstabilität (nicht an kurzfristig
  gute Performance — siehe Ehrliche Erwartungshaltung in `docs/03-risiken-empfehlungen.md`).

---

**Grundprinzip über alle Phasen hinweg:** Jede Stufe wird erst verlassen, wenn die vorherige
nachweislich (nicht gefühlt) stabil lief. Der teuerste Fehler bei einem System wie diesem ist
nicht eine einzelne falsche Handelsentscheidung, sondern ein übersprungener Sicherheits- oder
Rechtsschritt.
