"""
FinancialProof - Konfigurationsmodul
Zentrale Konfiguration für Pfade, API-Keys und App-Einstellungen
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
import json


@dataclass
class Config:
    """Zentrale Konfigurationsklasse"""

    # Pfade
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent)
    DATA_DIR: Path = field(init=False)
    DB_PATH: Path = field(init=False)
    SECRETS_PATH: Path = field(init=False)

    # App Settings
    APP_NAME: str = "FinancialProof"
    APP_VERSION: str = "1.0.0"
    DEFAULT_TICKER: str = "AAPL"
    DEFAULT_PERIOD: str = "1y"

    # Chart Settings
    CHART_THEME: str = "plotly_dark"
    CHART_HEIGHT: int = 600

    # Cache Settings (in Sekunden)
    CACHE_TTL_MARKET_DATA: int = 3600      # 1 Stunde
    CACHE_TTL_TICKER_INFO: int = 86400     # 1 Tag
    CACHE_TTL_NEWS: int = 1800             # 30 Minuten

    # Analyse-Einstellungen
    DEFAULT_SMA_PERIODS: list = field(default_factory=lambda: [20, 50, 200])
    DEFAULT_RSI_PERIOD: int = 14
    DEFAULT_BOLLINGER_PERIOD: int = 20
    DEFAULT_BOLLINGER_STD: float = 2.0

    def __post_init__(self):
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DB_PATH = self.DATA_DIR / "financial.db"
        self.SECRETS_PATH = self.DATA_DIR / ".secrets"
        self._ensure_directories()

    def _ensure_directories(self):
        """Erstellt notwendige Verzeichnisse"""
        self.DATA_DIR.mkdir(exist_ok=True)


class APIKeyManager:
    """Verwaltet API-Keys mit Verschlüsselung"""

    def __init__(self, config: Config):
        self.config = config
        self._key_file = config.DATA_DIR / ".key"
        self._secrets_file = config.SECRETS_PATH
        self._fernet: Optional[Fernet] = None
        self._init_encryption()

    def _init_encryption(self):
        """Initialisiert oder lädt den Verschlüsselungsschlüssel"""
        if self._key_file.exists():
            with open(self._key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self._key_file, "wb") as f:
                f.write(key)
        self._fernet = Fernet(key)

    def save_api_key(self, service: str, api_key: str):
        """Speichert einen API-Key verschlüsselt"""
        secrets = self._load_secrets()
        encrypted = self._fernet.encrypt(api_key.encode()).decode()
        secrets[service] = encrypted
        self._save_secrets(secrets)

    def get_api_key(self, service: str) -> Optional[str]:
        """Lädt einen API-Key"""
        secrets = self._load_secrets()
        if service in secrets:
            try:
                decrypted = self._fernet.decrypt(secrets[service].encode()).decode()
                return decrypted
            except Exception:
                return None
        return None

    def has_api_key(self, service: str) -> bool:
        """Prüft ob ein API-Key existiert"""
        return self.get_api_key(service) is not None

    def delete_api_key(self, service: str):
        """Löscht einen API-Key"""
        secrets = self._load_secrets()
        if service in secrets:
            del secrets[service]
            self._save_secrets(secrets)

    def _load_secrets(self) -> dict:
        """Lädt die Secrets-Datei"""
        if self._secrets_file.exists():
            with open(self._secrets_file, "r") as f:
                return json.load(f)
        return {}

    def _save_secrets(self, secrets: dict):
        """Speichert die Secrets-Datei"""
        with open(self._secrets_file, "w") as f:
            json.dump(secrets, f)


# Globale Instanz
config = Config()
api_keys = APIKeyManager(config)


# ===== UI-Texte (Deutsch) =====
class UIText:
    """Deutsche Beschriftungen für die Benutzeroberfläche"""

    # Allgemein
    APP_TITLE = "FinancialProof - Statistische Marktanalyse"
    APP_SUBTITLE = "Historische Mustererkennung – keine Anlageberatung"

    # Sidebar
    SIDEBAR_TITLE = "Markt-Auswahl"
    SIDEBAR_SYMBOL = "Symbol eingeben"
    SIDEBAR_PERIOD = "Zeitraum"
    SIDEBAR_INDICATORS = "Technische Indikatoren"
    SIDEBAR_WATCHLIST = "Watchlist"
    SIDEBAR_SETTINGS = "Einstellungen"
    SIDEBAR_ADD_ASSET = "Asset hinzufügen"

    # Zeiträume
    PERIODS = {
        "1mo": "1 Monat",
        "3mo": "3 Monate",
        "6mo": "6 Monate",
        "1y": "1 Jahr",
        "2y": "2 Jahre",
        "5y": "5 Jahre",
        "max": "Maximum"
    }

    # Tabs
    TAB_CHART = "Chart & technische Indikatoren"
    TAB_ANALYSIS = "Statistische Analyse"
    TAB_JOBS = "Aufträge"

    # Indikatoren
    IND_SMA = "Gleitender Durchschnitt (SMA)"
    IND_EMA = "Exponentieller MA (EMA)"
    IND_RSI = "Relative Stärke Index (RSI)"
    IND_BOLLINGER = "Bollinger Bänder"
    IND_MACD = "MACD"
    IND_STOCHASTIC = "Stochastic Oscillator"

    # Analysen
    ANALYSIS_ARIMA = "Zeitreihenanalyse (ARIMA)"
    ANALYSIS_MEAN_REV = "Mean Reversion Prüfung"
    ANALYSIS_MONTE_CARLO = "Monte-Carlo-Simulation"
    ANALYSIS_CORRELATION = "Korrelation & Kointegration"
    ANALYSIS_DEEP_LEARNING = "Deep Learning / Pattern"
    ANALYSIS_RL = "Reinforcement Learning"
    ANALYSIS_SENTIMENT = "Sentiment & Recherche"

    # Job-Status
    JOB_PENDING = "Wartend"
    JOB_RUNNING = "Läuft"
    JOB_COMPLETED = "Abgeschlossen"
    JOB_FAILED = "Fehlgeschlagen"

    # Indikator-Labels (intern weiterhin "Signal"-Klassen, aber UI neutral)
    # Rechtlicher Hintergrund: Vermeidung der Suggestion einer Anlageempfehlung
    # (§ 32 KWG, § 2 Abs. 9 WpHG). Die zugrundeliegende Logik bleibt identisch,
    # es wird lediglich die Benennung neutralisiert.
    SIGNAL_BUY = "Bullisches Muster"
    SIGNAL_SELL = "Bärisches Muster"
    SIGNAL_HOLD = "Neutral"

    # Meldungen
    MSG_NO_DATA = "Keine Daten gefunden. Bitte Symbol prüfen."
    MSG_LOADING = "Daten werden geladen..."
    MSG_JOB_STARTED = "Analyse-Auftrag wurde gestartet"
    MSG_JOB_COMPLETED = "Analyse abgeschlossen"

    # API-Keys
    API_KEYS_TITLE = "API-Keys einrichten"
    API_TWITTER = "Twitter/X Bearer Token"
    API_YOUTUBE = "YouTube API Key"
    API_SAVE = "Speichern"
    API_LATER = "Später"

    # Disclaimer (Erststart-Acknowledgement, § 32 KWG / § 2 Abs. 9 WpHG)
    DISCLAIMER_VERSION = "1.0"
    DISCLAIMER_TITLE = "Wichtiger Haftungshinweis — keine Anlageberatung"
    DISCLAIMER_INTRO = (
        "FinancialProof ist ein technisches Werkzeug zur statistischen "
        "Mustererkennung auf historischen Finanzdaten. "
        "Bevor Sie die Anwendung nutzen können, müssen Sie die vier "
        "folgenden Punkte bestätigen."
    )
    DISCLAIMER_BODY = (
        "FinancialProof ist:\n"
        "\n"
        "• KEINE Anlageberatung im Sinne von § 32 KWG oder § 2 Abs. 9 WpHG.\n"
        "• KEINE Kauf- oder Verkaufsempfehlung für Wertpapiere, Kryptowerte "
        "oder andere Finanzinstrumente.\n"
        "• KEINE Prognose künftiger Kurs- oder Marktentwicklungen.\n"
        "• NICHT BaFin-zugelassen und nicht durch eine Aufsichtsbehörde "
        "reguliert.\n"
        "\n"
        "Alle angezeigten Indikatoren, Muster, Statistiken und "
        "Analyseergebnisse beschreiben HISTORISCHE Eigenschaften der "
        "eingespielten Marktdaten. Aus ihnen lassen sich keine gesicherten "
        "Aussagen über zukünftige Entwicklungen ableiten. Vergangene "
        "Wertentwicklungen sind kein verlässlicher Indikator für zukünftige "
        "Ergebnisse.\n"
        "\n"
        "Anlageentscheidungen liegen ausschließlich in Ihrer Verantwortung. "
        "Konsultieren Sie vor jeder Anlageentscheidung qualifizierte "
        "Fachleute (Bank, Steuerberater, zugelassener Anlageberater).\n"
        "\n"
        "Dieses Projekt ist eine unentgeltliche Open-Source-Schenkung "
        "(§§ 516 ff. BGB). Die Haftung des Urhebers ist gemäß § 521 BGB "
        "auf Vorsatz und grobe Fahrlässigkeit beschränkt. Nutzung auf "
        "eigenes Risiko."
    )
    DISCLAIMER_CHECK_NO_ADVICE = (
        "Ich verstehe: Dieses Tool ist **keine Anlageberatung** und "
        "**keine Empfehlung zum Kauf/Verkauf** von Wertpapieren."
    )
    DISCLAIMER_CHECK_HISTORICAL = (
        "Ich verstehe: Die angezeigten Indikatoren sind **historische "
        "statistische Muster**, keine Prognosen."
    )
    DISCLAIMER_CHECK_OWN_RESPONSIBILITY = (
        "Ich treffe Anlageentscheidungen **auf eigene Verantwortung** nach "
        "Rücksprache mit qualifizierten Fachleuten (Bank, Steuerberater, "
        "Anlageberater)."
    )
    DISCLAIMER_CHECK_OWN_RISK = (
        "Ich nutze das Tool **auf eigenes Risiko** (Haftung auf Vorsatz "
        "und grobe Fahrlässigkeit beschränkt, § 521 BGB)."
    )
    DISCLAIMER_BTN_ACCEPT = "Akzeptieren und fortfahren"
    DISCLAIMER_BTN_REJECT = "Ablehnen"
    DISCLAIMER_INFO_BUTTONS = (
        "Alle vier Kästchen müssen bestätigt werden, bevor der "
        "Akzeptieren-Button aktiviert wird. Ein Klick auf Ablehnen "
        "beendet die Anwendung."
    )
    DISCLAIMER_REJECTED = (
        "Sie haben den Haftungshinweis abgelehnt. FinancialProof wird "
        "nicht gestartet. Sie können den Browser-Tab nun schließen."
    )


# Singleton für einfachen Import
texts = UIText()
