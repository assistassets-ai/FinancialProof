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

### BUG-2026-05-13-01: Forecast-Charts brachen bei RangeIndex-Daten
**Entdeckt:** 2026-05-13
**Behoben:** 2026-05-13
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `analysis/base.py`, `analysis/statistical/arima.py`, `analysis/statistical/monte_carlo.py`

**Beschreibung:**
ARIMA- und Monte-Carlo-Ausgaben leiteten den Chart-Start direkt aus `historical.index[-1]` ab. Bei synthetischen Daten oder anderen nicht-datetimebasierten Indizes konnte das zu falschen Forecast-Daten oder Abstürzen bei der Visualisierung führen.

**Ursache:**
Die Visualisierung setzte stillschweigend einen `DatetimeIndex` voraus, obwohl die Analysen auch mit Testdaten und anderen Index-Typen arbeiten.

**Lösung:**
Eine zentrale Hilfsfunktion bestimmt jetzt einen robusten Forecast-Startzeitpunkt. Datetime-Indexe verwenden den letzten Zeitstempel, andere Index-Typen fallen auf den nächsten Business Day ab heute zurück.

**Test:**
`python -m pytest tests/test_analysis_error_handling.py tests/test_rate_limiter.py -q` -> 37/37 bestanden.
`python -m pytest tests -q` -> 154/154 bestanden.

### BUG-2026-05-13-02: ARIMA verwendete noch Kauf-/Verkaufsterminologie
**Entdeckt:** 2026-05-13
**Behoben:** 2026-05-13
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `analysis/statistical/arima.py`

**Beschreibung:**
ARIMA lieferte im Resultatfluss weiterhin `buy`/`sell`/`hold`, obwohl die App auf deskriptive Musteranalyse umgestellt ist.

**Ursache:**
Die alte Empfehlungslogik war im Analyseergebnis noch nicht vollständig auf die neue Terminologie umgestellt.

**Lösung:**
Die Labels wurden auf `bullish`/`bearish`/`neutral` umgestellt und per Regressionstest abgesichert.

**Test:**
`python -m pytest tests -q` -> 154/154 bestanden.

### BUG-2026-05-13-03: Korruptes Secrets-JSON blockierte API-Keys
**Entdeckt:** 2026-05-13
**Behoben:** 2026-05-13
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `config.py`

**Beschreibung:**
Eine beschädigte oder falsch formatierte `data/.secrets`-Datei konnte das Laden und spätere Speichern von API-Schlüsseln blockieren.

**Ursache:**
`json.load` lief ohne robuste Fehlerbehandlung, und das Ergebnis wurde nicht auf ein JSON-Objekt geprüft.

**Lösung:**
`APIKeyManager` lädt die Secrets-Datei jetzt mit UTF-8, validiert den JSON-Typ, protokolliert beschädigte Dateien und fällt sauber auf ein leeres Mapping zurück.

**Test:**
`python -m pytest tests/test_config.py tests -q` -> 154/154 bestanden.

### BUG-2026-05-14-01: RSI behandelte Aufwärtstrends als neutral
**Entdeckt:** 2026-05-14
**Behoben:** 2026-05-14
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `indicators/technical.py`

**Beschreibung:**
Die RSI-Berechnung setzte Division-durch-Null-Fälle pauschal auf `50`. Dadurch lieferten strikt steigende Preisreihen einen neutralen RSI statt des erwarteten Extremwerts `100`.

**Ursache:**
`avg_loss == 0` wurde nicht separat behandelt. Ein reiner Aufwärtstrend fiel daher auf das pauschale `fillna(50)` zurück, obwohl nur die Verlustseite null war.

**Lösung:**
Zero-Loss wird jetzt als RSI `100`, Zero-Gain als RSI `0` und echte Neutralität als RSI `50` behandelt.

**Test:**
`python -m pytest tests/test_indicators.py -q` -> 17/17 bestanden.
`python -m pytest tests -q` -> 157/157 bestanden.

### BUG-2026-05-16-01: Mehrere Regressionen in Analyse, Indikatoren und Konfiguration
**Entdeckt:** 2026-05-16
**Behoben:** 2026-05-16
**Schweregrad:** Mittel
**Status:** Behoben
**Betrifft:** `config.py`, `analysis/base.py`, `analysis/statistical/arima.py`, `analysis/statistical/monte_carlo.py`, `indicators/technical.py`

**Beschreibung:**
Der Testlauf zeigte mehrere robuste, aber fachlich relevante Schwachstellen: eine beschädigte `data/.secrets`-Datei konnte das Laden von API-Keys blockieren, Forecast-Charts brachen bei nicht-datetimebasierten Indizes, der RSI gab bei reinen Trend- oder Flat-Serien nicht immer die erwarteten Extremwerte aus, und ARIMA verwendete weiterhin Empfehlungsterminologie statt deskriptiver Musterlabels.

**Lösung:**
`APIKeyManager` ignoriert defektes JSON jetzt sauber und protokolliert die Ursache. Forecast-Startdaten werden zentral und indexrobust bestimmt. RSI unterscheidet zwischen reinen Gewinn-, Verlust- und Flat-Serien. ARIMA gibt nur noch `bullish`/`bearish`/`neutral` aus und behandelt unsichere Konfidenzwerte defensiv.

**Test:**
`python -m pytest tests -q` -> 157/157 bestanden.

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
| Behoben (gesamt) | 5 |

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

*Letzte Aktualisierung: 2026-05-16*
