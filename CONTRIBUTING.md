# Mitwirken bei FinancialProof

Vielen Dank für dein Interesse an FinancialProof! Beiträge sind herzlich willkommen.

## Inhaltsverzeichnis

- [Code of Conduct](#code-of-conduct)
- [Wie kann ich beitragen?](#wie-kann-ich-beitragen)
- [Entwicklungsumgebung](#entwicklungsumgebung)
- [Code-Standards](#code-standards)
- [Pull Request Prozess](#pull-request-prozess)
- [Neue Analyse-Module](#neue-analyse-module)

---

## Code of Conduct

Dieses Projekt folgt einem Code of Conduct. Durch die Teilnahme erklärst du dich bereit, diesen einzuhalten.

- Sei respektvoll und inklusiv
- Konstruktive Kritik ist willkommen
- Keine Belästigung oder diskriminierendes Verhalten

---

## Wie kann ich beitragen?

### Bug Reports

1. Prüfe, ob der Bug bereits gemeldet wurde
2. Erstelle ein [Issue](https://github.com/assistassets-ai/FinancialProof/issues/new) mit:
   - Klare Beschreibung des Problems
   - Schritte zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - Screenshots (falls relevant)
   - System-Informationen (OS, Python-Version)

### Feature Requests

1. Prüfe die [Roadmap](ROADMAP.md) für geplante Features
2. Erstelle ein Issue mit dem Label `enhancement`
3. Beschreibe:
   - Das gewünschte Feature
   - Den Anwendungsfall
   - Mögliche Implementierungsansätze

### Code-Beiträge

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/mein-feature`)
3. Committe deine Änderungen (`git commit -m 'Add: Mein neues Feature'`)
4. Push zum Branch (`git push origin feature/mein-feature`)
5. Erstelle einen Pull Request

---

## Entwicklungsumgebung

### Setup

```bash
# Repository klonen
git clone https://github.com/assistassets-ai/FinancialProof.git
cd FinancialProof

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### Entwickler-Dependencies

```bash
pip install pytest pytest-cov black flake8 mypy
```

### Tests ausführen

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=. --cov-report=html

# Einzelnes Modul
pytest tests/test_indicators.py
```

### Code formatieren

```bash
# Black für Formatierung
black .

# Flake8 für Linting
flake8 .

# Type Checking
mypy .
```

---

## Code-Standards

### Python Style Guide

- Folge [PEP 8](https://pep8.org/)
- Verwende [Black](https://black.readthedocs.io/) für Formatierung
- Maximale Zeilenlänge: 88 Zeichen (Black-Standard)

### Docstrings

Verwende Google-Style Docstrings:

```python
def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Berechnet den Relative Strength Index.

    Args:
        data: Schlusskurse als pandas Series.
        period: Anzahl der Perioden für die Berechnung.

    Returns:
        RSI-Werte als pandas Series.

    Raises:
        ValueError: Wenn period < 2.

    Example:
        >>> rsi = calculate_rsi(df['Close'], period=14)
    """
```

### Commit Messages

Format: `<type>: <description>`

Types:
- `Add`: Neue Funktion
- `Fix`: Bugfix
- `Update`: Änderung bestehender Funktion
- `Remove`: Entfernung von Code
- `Refactor`: Code-Umstrukturierung ohne Funktionsänderung
- `Docs`: Dokumentation
- `Test`: Tests
- `Style`: Formatierung (kein Code-Change)

Beispiele:
```
Add: Monte Carlo Analyse-Modul
Fix: RSI-Berechnung bei fehlenden Daten
Update: Sidebar-Layout für bessere UX
Docs: README mit Installation erweitert
```

### Branch-Naming

- `feature/beschreibung` - Neue Features
- `fix/beschreibung` - Bugfixes
- `docs/beschreibung` - Dokumentation
- `refactor/beschreibung` - Refactoring

---

## Pull Request Prozess

### Checkliste

- [ ] Code folgt den Style-Guidelines
- [ ] Tests sind geschrieben und bestanden
- [ ] Dokumentation ist aktualisiert
- [ ] CHANGELOG.md ist aktualisiert
- [ ] Keine Breaking Changes (oder klar dokumentiert)

### Review-Prozess

1. Automatische Checks (CI) müssen bestanden sein
2. Mindestens ein Maintainer muss approven
3. Alle Kommentare müssen adressiert sein
4. Branch muss aktuell mit `master` sein

### Nach dem Merge

- Dein Branch wird automatisch gelöscht
- Du wirst im CHANGELOG erwähnt

---

## Neue Analyse-Module

### Struktur

```python
# analysis/statistical/mein_modul.py

from analysis.base import BaseAnalyzer, AnalysisResult, AnalysisParameters
from analysis.registry import AnalysisRegistry

@AnalysisRegistry.register
class MeinAnalyzer(BaseAnalyzer):
    """Kurze Beschreibung des Moduls."""

    name = "mein_analyzer"
    display_name = "Mein Analyzer"
    category = "statistical"  # oder "ml", "nlp"
    description = "Detaillierte Beschreibung..."

    def get_default_parameters(self) -> dict:
        return {
            "param1": 10,
            "param2": 0.5
        }

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        # Implementierung hier
        pass
```

### Anforderungen

1. **Basisklasse**: Erbe von `BaseAnalyzer`
2. **Registry**: Dekoriere mit `@AnalysisRegistry.register`
3. **Docstrings**: Dokumentiere alle Parameter
4. **Error Handling**: Fange Exceptions ab
5. **Tests**: Mindestens 80% Coverage

### Beispiel-Test

```python
# tests/test_mein_modul.py

import pytest
from analysis.statistical.mein_modul import MeinAnalyzer

@pytest.fixture
def analyzer():
    return MeinAnalyzer()

def test_analyze_basic(analyzer, sample_data):
    result = analyzer.analyze(sample_data)
    assert result.confidence > 0
    assert result.summary is not None

def test_analyze_empty_data(analyzer):
    with pytest.raises(ValueError):
        analyzer.analyze(pd.DataFrame())
```

---

## Fragen?

- Erstelle ein Issue mit dem Label `question`
- Kontaktiere die Maintainer

Bitte keine echten API-Keys, `.env`-Dateien, Datenbanken oder lokale
Analyseergebnisse in Issues, Pull Requests oder Commits hochladen.

Vielen Dank für deinen Beitrag!
