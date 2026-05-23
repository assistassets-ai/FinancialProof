"""
FinancialProof - Rate Limiter

Token-Bucket-basiertes Rate Limiting fuer Aufrufe gegen externe APIs
(z.B. yfinance, News-Quellen). Schuetzt vor Sperren durch zu hohe Frequenz
und sorgt fuer kontrolliertes Throttling auch bei parallelen Jobs.

Bestandteile:
- ``TokenBucket``: Thread-sicherer Token-Bucket-Algorithmus.
- ``RateLimiter``: Komfort-Schicht mit dynamisch erzeugten benannten Buckets.
- ``rate_limited``: Dekorator zum Drosseln einzelner Funktionen.
- ``rate_limited_call``: Manuelles Throttling fuer Methoden-Aufrufe.
- Telemetrie-Snapshots fuer erfolgreiche, wartende und abgebrochene Aufrufe.

Standardgrenzen koennen via ``config.py`` (``API_RATE_LIMIT_*``) ueberschrieben
werden. Tests koennen ueber ``RateLimiter.reset()`` einen sauberen Zustand
herstellen oder per ``configure_bucket`` eigene Limits setzen.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import asdict, dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class BucketConfig:
    """Konfiguration eines Token-Buckets."""

    capacity: float
    refill_rate: float

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.refill_rate <= 0:
            raise ValueError("refill_rate must be positive")


@dataclass
class RateLimitStats:
    """Laufzeit-Telemetrie fuer einen Token-Bucket."""

    requests: int = 0
    acquired: int = 0
    immediate_acquired: int = 0
    delayed_acquired: int = 0
    timeouts: int = 0
    nonblocking_denials: int = 0
    low_token_events: int = 0
    tokens_consumed: float = 0.0
    total_wait_seconds: float = 0.0
    max_wait_seconds: float = 0.0
    last_wait_seconds: float = 0.0
    last_acquired_at: Optional[float] = None
    last_low_tokens_at: Optional[float] = None
    last_timeout_at: Optional[float] = None
    last_denied_at: Optional[float] = None


class TokenBucket:
    """Thread-sicherer Token-Bucket.

    Args:
        capacity: Maximale Anzahl an Tokens (Burst-Kapazitaet).
        refill_rate: Wieder aufgefuellte Tokens pro Sekunde.
        time_func: Quelle fuer Zeitwerte. Wird in Tests ueberschrieben,
            um deterministisch zu testen.
        sleep_func: Wartefunktion. Wird in Tests ebenfalls ersetzt.
        event_time_func: Zeitquelle fuer Diagnose-Zeitstempel. Standard ist
            ``time.time`` fuer menschenlesbare Runtime-Auswertung.
    """

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        time_func: Callable[[], float] = time.monotonic,
        sleep_func: Callable[[float], None] = time.sleep,
        event_time_func: Callable[[], float] = time.time,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._tokens = float(capacity)
        self._last_refill = time_func()
        self._lock = threading.Lock()
        self._time = time_func
        self._sleep = sleep_func
        self._event_time = event_time_func
        self._stats = RateLimitStats()

    def _refill(self) -> None:
        now = self._time()
        elapsed = max(0.0, now - self._last_refill)
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

    def try_consume(self, tokens: float = 1.0) -> bool:
        """Versucht ohne Warten Tokens zu entnehmen.

        Returns:
            True wenn Tokens entnommen wurden, False sonst.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self._lock:
            self._stats.requests += 1
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                self._record_acquired_locked(tokens=tokens, wait_seconds=0.0)
                return True
            self._record_low_tokens_locked()
            self._stats.nonblocking_denials += 1
            self._stats.last_denied_at = self._event_time()
            return False

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Wartet ggf. bis Tokens verfuegbar sind und entnimmt sie.

        Args:
            tokens: Zu entnehmende Tokenmenge.
            timeout: Maximale Wartezeit in Sekunden (``None`` = unbegrenzt).

        Returns:
            ``True`` wenn Tokens entnommen wurden, ``False`` bei Timeout.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            raise ValueError("tokens cannot exceed bucket capacity")

        start = self._time()
        request_counted = False
        waited_for_tokens = False
        while True:
            with self._lock:
                if not request_counted:
                    self._stats.requests += 1
                    request_counted = True
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    wait_seconds = self._time() - start if waited_for_tokens else 0.0
                    self._record_acquired_locked(
                        tokens=tokens,
                        wait_seconds=wait_seconds,
                    )
                    return True
                missing = tokens - self._tokens
                wait_time = missing / self.refill_rate
                if not waited_for_tokens:
                    self._record_low_tokens_locked()
                    waited_for_tokens = True

            if timeout is not None:
                elapsed = self._time() - start
                remaining = timeout - elapsed
                if remaining <= 0:
                    with self._lock:
                        self._record_timeout_locked(elapsed)
                    return False
                wait_time = min(wait_time, remaining)

            # Kleinste Wartezeit, um nicht in eine Busy-Loop zu geraten
            self._sleep(max(wait_time, 0.001))

    def available_tokens(self) -> float:
        """Aktueller Token-Stand (nach Refill, fuer Diagnose/Tests)."""
        with self._lock:
            self._refill()
            return self._tokens

    def stats_snapshot(self) -> Dict[str, Any]:
        """Gibt einen thread-sicheren Telemetrie-Snapshot zurueck."""
        with self._lock:
            self._refill()
            snapshot = asdict(self._stats)
            snapshot.update(
                {
                    "capacity": self.capacity,
                    "refill_rate": self.refill_rate,
                    "available_tokens": self._tokens,
                }
            )
            return snapshot

    def reset_stats(self) -> None:
        """Setzt Telemetrie zurueck, ohne Token-Stand oder Limits zu aendern."""
        with self._lock:
            self._stats = RateLimitStats()

    def _record_acquired_locked(self, tokens: float, wait_seconds: float) -> None:
        self._stats.acquired += 1
        self._stats.tokens_consumed += tokens
        self._stats.last_acquired_at = self._event_time()
        if wait_seconds > 0:
            self._stats.delayed_acquired += 1
            self._record_wait_locked(wait_seconds)
        else:
            self._stats.immediate_acquired += 1

    def _record_low_tokens_locked(self) -> None:
        self._stats.low_token_events += 1
        self._stats.last_low_tokens_at = self._event_time()

    def _record_timeout_locked(self, wait_seconds: float) -> None:
        self._stats.timeouts += 1
        self._stats.last_timeout_at = self._event_time()
        self._record_wait_locked(max(0.0, wait_seconds))

    def _record_wait_locked(self, wait_seconds: float) -> None:
        self._stats.last_wait_seconds = wait_seconds
        self._stats.total_wait_seconds += wait_seconds
        self._stats.max_wait_seconds = max(
            self._stats.max_wait_seconds,
            wait_seconds,
        )


class RateLimiter:
    """Registry fuer benannte Token-Buckets.

    Buckets koennen pro API-Domain benannt werden (z.B. ``"yfinance"``).
    Die Klasse ist thread-sicher; alle Methoden sind statisch oder
    klassenbezogen, damit der Limiter ohne Singleton-Konstrukt nutzbar ist.
    """

    _buckets: Dict[str, TokenBucket] = {}
    _configs: Dict[str, BucketConfig] = {}
    _registry_lock = threading.Lock()
    _default_config: BucketConfig = BucketConfig(capacity=60.0, refill_rate=1.0)

    @classmethod
    def configure_bucket(
        cls,
        name: str,
        capacity: float,
        refill_rate: float,
    ) -> None:
        """Setzt oder aktualisiert die Konfiguration eines Buckets.

        Bestehende Buckets werden ersetzt, damit Tests deterministisch
        eigene Limits setzen koennen.
        """
        cfg = BucketConfig(capacity=capacity, refill_rate=refill_rate)
        with cls._registry_lock:
            cls._configs[name] = cfg
            cls._buckets[name] = TokenBucket(cfg.capacity, cfg.refill_rate)

    @classmethod
    def set_default_config(cls, capacity: float, refill_rate: float) -> None:
        """Setzt das Standardlimit fuer noch unbekannte Buckets."""
        cls._default_config = BucketConfig(capacity=capacity, refill_rate=refill_rate)

    @classmethod
    def get_bucket(cls, name: str) -> TokenBucket:
        """Liefert den Bucket fuer ``name`` und legt ihn ggf. an."""
        with cls._registry_lock:
            bucket = cls._buckets.get(name)
            if bucket is None:
                cfg = cls._configs.get(name, cls._default_config)
                bucket = TokenBucket(cfg.capacity, cfg.refill_rate)
                cls._buckets[name] = bucket
            return bucket

    @classmethod
    def acquire(
        cls,
        name: str,
        tokens: float = 1.0,
        timeout: Optional[float] = None,
    ) -> bool:
        """Erwirbt Tokens am benannten Bucket (ggf. mit Warten)."""
        return cls.get_bucket(name).acquire(tokens=tokens, timeout=timeout)

    @classmethod
    def get_stats(cls, name: str) -> Dict[str, Any]:
        """Liefert Telemetrie fuer einen benannten Bucket.

        Der Aufruf legt unbekannte Buckets wie ``get_bucket`` mit der
        Default-Konfiguration an. Dadurch koennen Monitoring-Oberflaechen
        denselben API-Pfad nutzen, ohne Sonderfaelle fuer leere Registry zu
        behandeln.
        """
        stats = cls.get_bucket(name).stats_snapshot()
        stats["name"] = name
        return stats

    @classmethod
    def get_all_stats(cls) -> List[Dict[str, Any]]:
        """Liefert Telemetrie-Snapshots aller aktuell angelegten Buckets."""
        with cls._registry_lock:
            names = sorted(cls._buckets)
        return [cls.get_stats(name) for name in names]

    @classmethod
    def reset_stats(cls, name: Optional[str] = None) -> None:
        """Setzt Telemetrie zurueck.

        Args:
            name: Optionaler Bucket-Name. Ohne Name werden alle vorhandenen
                Bucket-Statistiken zurueckgesetzt.
        """
        if name is not None:
            cls.get_bucket(name).reset_stats()
            return
        with cls._registry_lock:
            buckets = list(cls._buckets.values())
        for bucket in buckets:
            bucket.reset_stats()

    @classmethod
    def reset(cls) -> None:
        """Verwirft alle Buckets und Konfigurationen.

        Wird vor allem in Tests verwendet, um Seiteneffekte zwischen
        Testfaellen zu isolieren. Das Default-Limit bleibt erhalten.
        """
        with cls._registry_lock:
            cls._buckets.clear()
            cls._configs.clear()


def rate_limited(
    name: str,
    tokens: float = 1.0,
    timeout: Optional[float] = None,
) -> Callable[[Callable], Callable]:
    """Decorator: drosselt Aufrufe einer Funktion ueber den ``RateLimiter``.

    Args:
        name: Name des Token-Buckets (z.B. ``"yfinance"``).
        tokens: Anzahl der zu konsumierenden Tokens pro Aufruf.
        timeout: Maximale Wartezeit. Bei Timeout wird die Funktion nicht
            ausgefuehrt; stattdessen wird ein Warning geloggt und das
            ``rate_limit_default``-Verhalten der Funktion uebernommen.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            acquired = RateLimiter.acquire(name, tokens=tokens, timeout=timeout)
            if not acquired:
                logger.warning(
                    "Rate-Limit-Timeout fuer Bucket %s in Funktion %s",
                    name,
                    func.__qualname__,
                )
                # Wenn die Funktion ein Default-Argument fuer Drosselung
                # liefert, ist der Aufrufer dafuer verantwortlich. Wir
                # geben in diesem Fall nichts zurueck; konsumierende
                # Funktionen sollten None tolerieren (siehe data_provider).
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limited_call(
    name: str,
    func: Callable,
    *args,
    tokens: float = 1.0,
    timeout: Optional[float] = None,
    **kwargs,
):
    """Fuehrt ``func`` nach erfolgreichem Token-Bezug aus.

    Variante fuer Methoden, die nicht zentral dekoriert werden koennen
    (z.B. ``yfinance.Ticker(symbol).news``).

    Returns:
        Rueckgabewert von ``func`` oder ``None`` wenn Tokens nicht verfuegbar
        waren (Timeout).
    """
    acquired = RateLimiter.acquire(name, tokens=tokens, timeout=timeout)
    if not acquired:
        logger.warning(
            "Rate-Limit-Timeout fuer Bucket %s im Aufruf %s",
            name,
            getattr(func, "__qualname__", str(func)),
        )
        return None
    return func(*args, **kwargs)


def init_from_config(cfg) -> None:
    """Initialisiert Standardlimits anhand der ``Config``-Instanz.

    Nutzt die Felder ``API_RATE_LIMIT_YFINANCE_CAPACITY`` und
    ``API_RATE_LIMIT_YFINANCE_REFILL``, falls vorhanden. Idempotent;
    spaetere Aufrufe ueberschreiben bestehende Konfigurationen, was
    Tests die Steuerung der Limits ermoeglicht.
    """
    capacity = getattr(cfg, "API_RATE_LIMIT_YFINANCE_CAPACITY", None)
    refill = getattr(cfg, "API_RATE_LIMIT_YFINANCE_REFILL", None)
    if capacity is None or refill is None:
        return
    try:
        capacity_val = float(capacity)
        refill_val = float(refill)
    except (TypeError, ValueError):
        logger.warning(
            "Ungueltige Rate-Limit-Werte in config: capacity=%s, refill=%s",
            capacity,
            refill,
        )
        return
    RateLimiter.configure_bucket("yfinance", capacity_val, refill_val)


__all__ = [
    "BucketConfig",
    "RateLimitStats",
    "TokenBucket",
    "RateLimiter",
    "rate_limited",
    "rate_limited_call",
    "init_from_config",
]
