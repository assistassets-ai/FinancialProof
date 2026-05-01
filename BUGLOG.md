# BUGLOG - FinancialProof

Dokumentation bekannter Bugs, deren Status und Behebung.

---

## Offene Bugs

_Aktuell keine bekannten Bugs_

<!--
### BUG-001: Beispiel Bug
**Entdeckt:** 2026-01-20
**Schweregrad:** Hoch | Mittel | Niedrig
**Status:** Offen
**Betrifft:** v1.0.0

**Beschreibung:**
Kurze Beschreibung des Problems.

**Schritte zur Reproduktion:**
1. Schritt 1
2. Schritt 2
3. Fehler tritt auf

**Erwartetes Verhalten:**
Was sollte passieren.

**Tatsächliches Verhalten:**
Was passiert stattdessen.

**Workaround:**
Temporäre Lösung, falls vorhanden.

**Zugewiesen:** @username
**Issue:** #123
-->

---

## In Bearbeitung

_Aktuell keine Bugs in Bearbeitung_

---

## Behoben

### BUG-2026-05-01-01: Research Agent gab BUY/SELL als App-Einschätzung aus
**Entdeckt:** 2026-05-01
**Behoben:** 2026-05-01
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `analysis/nlp/research_agent.py`

**Beschreibung:**
Der Web-Recherche-Agent erzeugte im Ergebnis-Summary eine `Gesamteinschaetzung: BUY/SELL` und reichte `buy`/`sell` als App-eigene Signaltypen durch. Das widersprach der dokumentierten Nicht-Anlageberatung und der Umstellung auf rein deskriptive Muster.

**Ursache:**
Die Altlogik des Research Agents nutzte weiterhin Empfehlungslabels für die kombinierte Auswertung aus Fundamentaldaten, Kursziel-Abweichung und Analystenkonsens.

**Lösung:**
Die Ergebnislogik wurde auf deskriptive Polaritäten (`bullish`, `bearish`, `neutral`) umgestellt. Summary und UI-Beschreibung sprechen nun von historischer Musterlage statt Empfehlung.

**Test:**
`python -m pytest tests -q` -> 107/107 bestanden.

<!--
### BUG-001: Beispiel behobener Bug
**Entdeckt:** 2026-01-15
**Behoben:** 2026-01-18
**Schweregrad:** Mittel
**Status:** Behoben in v1.0.1

**Beschreibung:**
RSI-Berechnung lieferte NaN bei weniger als 14 Datenpunkten.

**Ursache:**
Fehlende Prüfung auf minimale Datenmenge vor der Berechnung.

**Lösung:**
Validierung hinzugefügt, die mindestens `period + 1` Datenpunkte erfordert.

**Commit:** abc1234
**PR:** #45
-->

---

## Statistik

| Kategorie | Anzahl |
|-----------|--------|
| Offen | 0 |
| In Bearbeitung | 0 |
| Behoben (gesamt) | 1 |

---

## Schweregrad-Definitionen

| Schweregrad | Beschreibung |
|-------------|--------------|
| **Kritisch** | App startet nicht, Datenverlust, Sicherheitslücke |
| **Hoch** | Kernfunktion nicht nutzbar, keine Workarounds |
| **Mittel** | Funktion eingeschränkt, Workaround verfügbar |
| **Niedrig** | Kosmetisch, Minor UX-Problem |

---

## Bug melden

Neuen Bug gefunden?

1. Prüfe, ob der Bug hier bereits dokumentiert ist
2. Erstelle ein [GitHub Issue](../../issues/new?template=buglog.md)
3. Verwende das Bug-Report Template

---

*Letzte Aktualisierung: 2026-05-01*
