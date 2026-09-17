# Risiken und Empfehlungen

Dies ist der wichtigste Teil dieses Repositories. Bitte vollständig lesen, bevor irgendein
Agent Zugriff auf echtes Kapital oder reale Order-Ausführung erhält.

## 1. Regulatorik (Deutschland/EU) — unbedingt vorab klären

Dieser Punkt wird in praktisch keinem der recherchierten Open-Source-Projekte behandelt, ist
aber für einen tatsächlichen Betrieb entscheidend:

- **Eigenes Geld, eigene Entscheidung, du drückst selbst den Knopf:** In der Regel erlaubnisfrei
  möglich — du handelst für dich selbst, das System ist ein Werkzeug wie eine
  Trading-Software. Empfehlenswert trotzdem: rechtliche Kurzprüfung, sobald Hebelprodukte,
  Derivate oder automatisierte Order-Ausführung ohne manuellen Klick pro Trade im Spiel sind.
- **Vollautomatisierte Ausführung ohne Klick pro Order (dein eigenes Geld):** Bewegt sich meist
  noch im Rahmen der Eigenverwaltung, aber: Broker-AGB prüfen (manche untersagen oder
  beschränken automatisierten API-Handel für Privatkunden), und bei Derivaten/Hebelprodukten
  MiFID-II-Geeignetheitsprüfungen des Brokers nicht durch Automatisierung umgehen.
- **Sobald Kapital Dritter verwaltet wird** (Familie, Freunde, „gebt mir Geld, ich handle für
  euch mit dem System"), **auch informell und auch ohne Gewinnbeteiligung**: Das ist in
  Deutschland grundsätzlich **erlaubnispflichtige Finanzportfolioverwaltung nach § 1 Abs. 1a
  Satz 2 Nr. 3 i. V. m. § 32 KWG** (BaFin-Erlaubnis). Ohne Erlaubnis ist das eine Straftat
  (§ 54 KWG), unabhängig davon, ob es gut gemeint ist oder Verluste entstehen. Auch reine
  „Signalgeber"-Modelle (das System gibt Empfehlungen, andere führen selbst aus) können je nach
  Ausgestaltung als Anlageberatung/Anlagevermittlung erlaubnispflichtig sein.
- **Ein SaaS/Produkt daraus machen** (andere nutzen „deinen" Hedgefonds-Agenten mit eigenem
  Kapital): Zusätzlich Fragen zu Anlageberatung, Robo-Advisor-Regulierung, Prospektpflichten
  und ggf. Investmentfonds-Regulierung (KAGB), falls gepooltes Kapital entsteht.
- **Handlungsempfehlung:** Solange das System nur mit eigenem Kapital und eigener finaler
  Kontrolle läuft, ist das Risiko überschaubar — trotzdem einmalig mit einem auf Bankaufsichtsrecht
  spezialisierten Anwalt oder direkt mit der BaFin-Erstauskunft klären, sobald automatisierte
  Ausführung ohne Klick pro Trade oder gar Kapital Dritter geplant ist. Diese Klärung **vor**
  Phase 3 der Roadmap einholen, nicht danach.

## 2. Technische/methodische Risiken

- **Halluzination bei Finanzdaten:** LLMs erfinden plausibel klingende Zahlen, Kursstände oder
  Ereignisse, wenn sie nicht strikt an Tool-Ergebnisse gebunden werden. Gegenmaßnahme: Jeder
  Agenten-Prompt in diesem Repo verlangt explizit Quellenangaben und verbietet das Erfinden von
  Daten (siehe Agent 1, Regel 2) — das MUSS technisch durchgesetzt werden (z. B. durch
  Validierung, dass jede genannte Zahl auf einen tatsächlichen Tool-Call zurückführbar ist).
- **Overfitting im Backtest:** Eine Strategie, die auf historische Daten „optimiert" wurde,
  performt auf denselben Daten fast immer gut — das sagt wenig über die Zukunft. Agent 3 ist
  bewusst mit Out-of-Sample-Pflicht und Overfitting-Checks instruiert; diese Disziplin darf
  unter Erfolgsdruck nicht aufgeweicht werden.
- **Nicht-Stationarität der Märkte:** Ein Regime, in dem eine Strategie funktioniert hat, kann
  sich ändern (Zinswende, Liquiditätsschock, neue Marktteilnehmer). Kein Backtest kann das
  vollständig vorwegnehmen. Deshalb: harte Risikolimits (Agent 4) als Fallback, unabhängig
  davon, wie gut eine Strategie historisch aussah.
- **Nichtdeterminismus/Reproduzierbarkeit von LLMs:** Gleiche Eingabe kann zu unterschiedlichen
  Ausgaben führen (Modell-Sampling). Für die Kontroll-/Risikoebene deshalb deterministischen
  Code verwenden (siehe Architektur, Abschnitt „Orchestrierung"), LLMs nur für Inhalte, nicht
  für die Durchsetzung von Sicherheitsregeln.
- **Prompt-Injection über externe Daten:** News-Texte, Social-Media-Sentiment oder sogar
  Orderbuch-Kommentare könnten (absichtlich oder zufällig) wie Anweisungen an das System
  aussehen. Agent 1 ist explizit instruiert, solche Inhalte als Daten, nicht als Befehle zu
  behandeln (siehe Agent 1, Regel 6) — diese Trennung muss auch technisch (z. B. klare
  Markierung von Fremddaten im Prompt) unterstützt werden.
- **Kostenkontrolle:** Ein 24/7 laufendes Multi-Agenten-System mit häufigen LLM-Aufrufen kann
  überraschend hohe API-Kosten verursachen, besonders bei Krypto-Märkten ohne Handelsschluss.
  Von Anfang an Kosten pro Zyklus messen und Obergrenzen definieren.

## 3. Betriebs-/Sicherheitsempfehlungen

- **Nie ohne Paper-Trading starten.** `enable_paper_trading` (Co-Invest) ist der erste Aufruf,
  bevor irgendein Agent produktiven Order-Zugriff bekommt. Siehe `docs/04-roadmap.md`.
- **Kill-Switches auf Code-Ebene, nicht nur im Prompt.** Tagesverlustlimit, maximaler Hebel,
  maximale Positionsgröße: als harte Checks im Orchestrator implementieren, die unabhängig vom
  Agenten-Output greifen (defense in depth — siehe Agent 4, Hinweise).
- **Least Privilege pro Agent.** Nur Agent 6 (Execution) bekommt Schreibzugriff auf
  Order-Ausführung. Alle anderen Agenten bekommen ausschließlich lesenden Tool-Zugriff. Das ist
  keine Prompt-Regel, sondern sollte durch tatsächliche Tool-/API-Berechtigungen erzwungen werden.
- **Vollständiger Audit-Trail.** Jede Agenten-Ein-/Ausgabe persistieren (siehe Architektur). Ohne
  das kann der Lern-Agent (Agent 7) nicht sinnvoll arbeiten, und im Streitfall (auch gegenüber
  Aufsichtsbehörden) ist Nachvollziehbarkeit entscheidend.
- **Mensch im Loop, solange real Geld bewegt wird.** Empfehlung: Auch nach erfolgreicher
  Paper-Trading-Phase zunächst eine manuelle Freigabe zwischen Agent 5 (Portfolio-Entscheidung)
  und Agent 6 (Exekution) einbauen, bevor vollautomatischer Live-Betrieb erwogen wird.
- **Keine Selbstüberschreibung von Sicherheitsregeln.** Der Lern-Agent (Agent 7) darf Änderungen
  an Prompts/Limits nur vorschlagen, nie automatisch aktivieren (siehe Agent 7, Regel 6) —
  sonst kann sich das System über die Zeit selbst „freischalten".
- **Modell- und Prompt-Versionierung.** Jede Änderung an einem Agenten-Prompt versionieren und
  mit dem Zeitraum verknüpfen, für den sie galt — sonst ist spätere Performance-Analyse (Agent 7)
  nicht möglich.
- **Steuerliche Dokumentation von Anfang an.** Automatisierter Handel erzeugt schnell sehr viele
  Einzeltransaktionen; die vollständige, exportierbare Transaktionshistorie (`get_transaction_history`)
  ist auch für die eigene Steuererklärung (Abgeltungssteuer, bei Derivaten/Krypto teils
  komplexere Regeln) wichtig — frühzeitig sauber protokollieren statt später rekonstruieren.

## 4. Ehrliche Erwartungshaltung

Keines der recherchierten Referenzprojekte (siehe `docs/01-marktrecherche.md`) hat einen
öffentlich verifizierten, langfristigen Live-Track-Record, der zeigt, dass dieser Ansatz
verlässlich Überrendite erzielt. Ein gut gebautes Multi-Agenten-System liefert vor allem:
**Struktur, Nachvollziehbarkeit und Disziplin** (kein emotionales Trading, systematische
Risikokontrolle, dokumentierte Lernschleife) — das ist wertvoll, ersetzt aber keinen echten,
belastbaren Edge am Markt. Plane das Projekt entsprechend eher als „diszipliniertes,
gut instrumentiertes System zum systematischen Lernen und Risikomanagement" statt als
„Garantie auf Überrendite".
