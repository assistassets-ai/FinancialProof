# TESTLOG - FinancialProof

Dokumentation angeforderter Tests, Testergebnisse und Testabdeckung.

---

## Angeforderte Tests

### TEST-001: Basis-Funktionalität
**Angefordert:** 2026-01-20
**Priorität:** Hoch
**Status:** Ausstehend

**Testbereich:** Core-Funktionen
**Beschreibung:** Grundlegende App-Funktionalität testen

**Testfälle:**
- [ ] App startet ohne Fehler (`streamlit run app.py`)
- [ ] Sidebar rendert korrekt
- [ ] Symbol-Eingabe funktioniert (AAPL, MSFT, BTC-USD)
- [ ] Daten werden geladen und angezeigt
- [ ] Chart wird gerendert
- [ ] Tabs wechseln funktioniert

**Zugewiesen:** -
**Issue:** -

---

### TEST-002: Technische Indikatoren
**Angefordert:** 2026-01-20
**Priorität:** Hoch
**Status:** Ausstehend

**Testbereich:** Indicators
**Beschreibung:** Alle technischen Indikatoren validieren

**Testfälle:**
- [ ] SMA(20) Berechnung korrekt
- [ ] SMA(50) Berechnung korrekt
- [ ] SMA(200) Berechnung korrekt
- [ ] EMA(12) Berechnung korrekt
- [ ] EMA(26) Berechnung korrekt
- [ ] RSI(14) im Bereich 0-100
- [ ] Bollinger Bands (Upper > Mid > Lower)
- [ ] MACD Histogram korrekt
- [ ] Stochastic %K und %D im Bereich 0-100

**Zugewiesen:** -
**Issue:** -

---

### TEST-003: Technische Muster und Indikatoren
**Angefordert:** 2026-01-20
**Priorität:** Mittel
**Status:** Ausstehend

**Testbereich:** Indicators / Pattern Detection
**Beschreibung:** Historische technische Muster und Indikatorzustände testen. Diese Tests prüfen keine Kauf-/Verkaufsempfehlungen.

**Testfälle:**
- [ ] Golden-Cross-Muster wird erkannt (SMA50 kreuzt SMA200 nach oben)
- [ ] Death-Cross-Muster wird erkannt (SMA50 kreuzt SMA200 nach unten)
- [ ] RSI-Überkauft-Zustand bei RSI > 70 erkannt
- [ ] RSI-Überverkauft-Zustand bei RSI < 30 erkannt
- [ ] Bollinger-Ausbruch oben erkannt
- [ ] Bollinger-Ausbruch unten erkannt
- [ ] MACD Crossover erkannt

**Zugewiesen:** -
**Issue:** -

---

### TEST-004: Analyse-Module
**Angefordert:** 2026-01-20
**Priorität:** Hoch
**Status:** Ausstehend

**Testbereich:** Analysis
**Beschreibung:** Alle KI-Analyse-Module testen

**Testfälle:**
- [ ] ARIMA läuft ohne Fehler
- [ ] ARIMA liefert historische Modellkennzahlen
- [ ] Monte Carlo Simulation läuft
- [ ] Monte Carlo liefert VaR-Werte
- [ ] Mean Reversion Analyse funktioniert
- [ ] Random Forest Training erfolgreich
- [ ] Random Forest Trendklassifikation funktioniert
- [ ] Neural Network (falls TensorFlow installiert)
- [ ] Sentiment-Analyse mit News
- [ ] Research Agent (falls optionale API-Keys vorhanden)

**Zugewiesen:** -
**Issue:** -

---

### TEST-005: Job-Queue System
**Angefordert:** 2026-01-20
**Priorität:** Hoch
**Status:** Ausstehend

**Testbereich:** Jobs
**Beschreibung:** Job-Verwaltung und Persistenz testen

**Testfälle:**
- [ ] Job erstellen funktioniert
- [ ] Job erscheint in Queue mit Status "pending"
- [ ] Job-Ausführung setzt Status auf "running"
- [ ] Erfolgreicher Job hat Status "completed"
- [ ] Fehlerhafter Job hat Status "failed"
- [ ] Ergebnisse werden in DB gespeichert
- [ ] Jobs überleben App-Neustart
- [ ] Job-Queue Ansicht zeigt alle Jobs

**Zugewiesen:** -
**Issue:** -

---

### TEST-006: Datenbank
**Angefordert:** 2026-01-20
**Priorität:** Mittel
**Status:** Ausstehend

**Testbereich:** Database
**Beschreibung:** SQLite-Datenbank Operationen testen

**Testfälle:**
- [ ] DB wird automatisch erstellt
- [ ] Watchlist hinzufügen funktioniert
- [ ] Watchlist abrufen funktioniert
- [ ] Job erstellen funktioniert
- [ ] Job aktualisieren funktioniert
- [ ] Ergebnis speichern funktioniert
- [ ] Ergebnis abrufen funktioniert

**Zugewiesen:** -
**Issue:** -

---

## In Durchführung

_Aktuell keine Tests in Durchführung_

---

## Abgeschlossene Tests

### AUTO-2026-04-30: Automatisierte Regressionstests
**Durchgeführt:** 2026-04-30
**Status:** Bestanden

**Umfang:**
- Analyse-Kernlogik und Registry
- OHLCV-Validierung bei unvollständigen Marktdaten
- Job-Manager, Job-Queue und Executor
- Logging-Initialisierung und Analyzer-Fehlerpfade
- Disclaimer-Persistenz und UI-Helfer
- Streamlit-Interaktionspfade für Sidebar, Chart und Analyse-Trigger

**Ergebnis:** 106/106 Tests bestanden (`python -m pytest tests -q`).

### AUTO-2026-05-01: Research-Agent-Musterlabel
**Durchgeführt:** 2026-05-01
**Status:** Bestanden

**Umfang:**
- Regressionstest für den Web-Recherche-Agenten
- Absicherung gegen App-eigene `BUY`/`SELL`-Zusammenfassungen
- Prüfung der deskriptiven Musterpolaritäten (`bullish`, `bearish`, `neutral`)

**Ergebnis:** 107/107 Tests bestanden (`python -m pytest tests -q`).

### AUTO-2026-05-06: Rate-Limit-Sidebar in Streamlit
**Durchgeführt:** 2026-05-06
**Status:** Bestanden

**Umfang:**
- Streamlit-AppTest mit Disclaimer-Acknowledgement und AAPL-Datenlauf
- Prüfung, dass der Sidebar-Settings-Block den `yfinance`-Bucket direkt mit
  aktuellen Request-Zahlen anzeigt
- Regressionstest für DataProvider-yfinance-Aufrufe bis zur Sidebar-Telemetrie
- Prüfung, dass keine `use_container_width`-Altoptionen im Python-Code bleiben

**Ergebnis:** 149/149 Tests bestanden (`python -m pytest tests -q`).

<!--
### TEST-XXX: Beispiel abgeschlossener Test
**Durchgeführt:** 2026-01-20
**Tester:** @username
**Status:** Bestanden | Fehlgeschlagen | Teilweise bestanden

**Ergebnisse:**
| Testfall | Ergebnis | Notizen |
|----------|----------|---------|
| Testfall 1 | ✅ Bestanden | - |
| Testfall 2 | ❌ Fehlgeschlagen | Bug-001 erstellt |
| Testfall 3 | ⚠️ Übersprungen | Abhängigkeit fehlt |

**Zusammenfassung:**
- Bestanden: 8/10
- Fehlgeschlagen: 1/10
- Übersprungen: 1/10

**Bugs gefunden:** BUG-001, BUG-002
**Commit:** abc1234
-->

---

## Testabdeckung

| Modul | Abdeckung | Status |
|-------|-----------|--------|
| core/ | automatisierte Tests vorhanden | Aktiv |
| indicators/ | automatisierte Tests vorhanden | Aktiv |
| analysis/ | automatisierte Tests vorhanden | Aktiv |
| jobs/ | automatisierte Tests vorhanden | Aktiv |
| ui/ | automatisierte Tests vorhanden | Aktiv |

**Gesamtabdeckung:** 149 automatisierte Tests; keine separate Coverage-Prozentzahl ausgewiesen.
**Ziel:** 80%

---

## Test-Kategorien

| Kategorie | Beschreibung |
|-----------|--------------|
| **Unit** | Einzelne Funktionen/Klassen isoliert |
| **Integration** | Zusammenspiel mehrerer Komponenten |
| **E2E** | Kompletter Workflow von UI bis DB |
| **Regression** | Nach Bug-Fix, um Rückfall zu verhindern |
| **Performance** | Ladezeiten, Speicherverbrauch |

---

## Test ausführen

```bash
# Alle Tests
python -m pytest tests -q

# Mit Coverage
python -m pytest tests --cov=. --cov-report=html

# Einzelnes Modul
python -m pytest tests/test_indicators.py

# Nur markierte Tests
python -m pytest -m "slow"
```

---

## Neuen Test anfordern

1. Erstelle ein [GitHub Issue](../../issues/new?template=testlog.md)
2. Verwende das Test-Request Template
3. Beschreibe den Testbereich und erwartete Testfälle

---

*Letzte Aktualisierung: 2026-05-06*
