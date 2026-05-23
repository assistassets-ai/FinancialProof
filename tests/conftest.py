"""
Test-Setup fuer optionale Drittanbieter-Abhaengigkeiten.
"""
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_yfinance_stub():
    try:
        __import__("yfinance")
        return
    except ModuleNotFoundError:
        pass

    yfinance = types.ModuleType("yfinance")

    class DummyTicker:
        def __init__(self, *args, **kwargs):
            self.info = {}
            self.news = []
            self.income_stmt = pd.DataFrame()
            self.balance_sheet = pd.DataFrame()
            self.cashflow = pd.DataFrame()
            self.dividends = pd.Series(dtype=float)
            self.recommendations = pd.DataFrame()

        def history(self, *args, **kwargs):
            return pd.DataFrame()

    def download(*args, **kwargs):
        return pd.DataFrame()

    yfinance.Ticker = DummyTicker
    yfinance.download = download
    sys.modules["yfinance"] = yfinance


def _install_cryptography_stub():
    try:
        __import__("cryptography.fernet")
        return
    except ModuleNotFoundError:
        pass

    cryptography = types.ModuleType("cryptography")
    fernet_module = types.ModuleType("cryptography.fernet")

    class DummyFernet:
        def __init__(self, key):
            self.key = key

        @staticmethod
        def generate_key():
            return b"0" * 32

        def encrypt(self, value: bytes) -> bytes:
            return value

        def decrypt(self, value: bytes) -> bytes:
            return value

    fernet_module.Fernet = DummyFernet
    cryptography.fernet = fernet_module
    sys.modules["cryptography"] = cryptography
    sys.modules["cryptography.fernet"] = fernet_module


_install_yfinance_stub()
_install_cryptography_stub()


@pytest.fixture(autouse=True)
def _generous_rate_limiter():
    """Setzt den Rate-Limiter pro Test auf grosszuegige Limits zurueck.

    Verhindert, dass Tests sich durch Token-Verbrauch gegenseitig stoeren.
    Tests, die Token-Knappheit explizit testen (test_rate_limiter.py),
    konfigurieren ihre Buckets selbst und ueberschreiben damit diese Werte.
    """
    try:
        from core.rate_limiter import RateLimiter
    except ImportError:
        yield
        return

    RateLimiter.reset()
    RateLimiter.set_default_config(capacity=10000.0, refill_rate=10000.0)
    RateLimiter.configure_bucket("yfinance", capacity=10000.0, refill_rate=10000.0)
    yield
    RateLimiter.reset()
    RateLimiter.set_default_config(capacity=10000.0, refill_rate=10000.0)
