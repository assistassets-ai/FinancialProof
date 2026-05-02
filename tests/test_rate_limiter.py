"""
Tests fuer das Rate-Limiter-Modul (core.rate_limiter)
"""
import sys
import threading
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rate_limiter import (  # noqa: E402
    BucketConfig,
    RateLimiter,
    RateLimitStats,
    TokenBucket,
    rate_limited,
    rate_limited_call,
)


class FakeClock:
    """Steuerbarer Zeitgeber fuer deterministische Tests."""

    def __init__(self, start: float = 0.0):
        self.now = float(start)

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)

    def sleep(self, seconds: float) -> None:
        # Sleep wird im Test als zeitliche Vorruecken simuliert.
        self.advance(seconds)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Vor und nach jedem Test einen sauberen Limiter-Status sicherstellen."""
    RateLimiter.reset()
    RateLimiter.set_default_config(capacity=60.0, refill_rate=1.0)
    yield
    RateLimiter.reset()
    RateLimiter.set_default_config(capacity=60.0, refill_rate=1.0)


class TestBucketConfig:
    def test_valid_config(self):
        cfg = BucketConfig(capacity=10.0, refill_rate=2.0)
        assert cfg.capacity == 10.0
        assert cfg.refill_rate == 2.0

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            BucketConfig(capacity=0, refill_rate=1.0)

    def test_invalid_refill(self):
        with pytest.raises(ValueError):
            BucketConfig(capacity=10.0, refill_rate=0)


class TestRateLimitStats:
    def test_stats_default_values(self):
        stats = RateLimitStats()
        assert stats.requests == 0
        assert stats.acquired == 0
        assert stats.timeouts == 0
        assert stats.last_low_tokens_at is None


class TestTokenBucket:
    def test_try_consume_succeeds_within_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate=1.0)
        assert bucket.try_consume(1) is True
        assert bucket.try_consume(1) is True
        assert bucket.try_consume(1) is True

    def test_try_consume_fails_when_empty(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=2,
            refill_rate=1.0,
            time_func=clock.time,
            sleep_func=clock.sleep,
        )
        assert bucket.try_consume(2) is True
        assert bucket.try_consume(1) is False

    def test_refill_over_time(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=2,
            refill_rate=1.0,
            time_func=clock.time,
            sleep_func=clock.sleep,
        )
        bucket.try_consume(2)
        clock.advance(2.0)  # 2 Sekunden -> 2 Tokens nachgeladen
        assert bucket.try_consume(1) is True
        assert bucket.try_consume(1) is True

    def test_refill_does_not_exceed_capacity(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=5,
            refill_rate=10.0,
            time_func=clock.time,
            sleep_func=clock.sleep,
        )
        clock.advance(60)  # weit ueber Kapazitaet hinaus
        assert bucket.available_tokens() == pytest.approx(5.0)

    def test_acquire_with_wait(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=1,
            refill_rate=2.0,
            time_func=clock.time,
            sleep_func=clock.sleep,
        )
        assert bucket.acquire(1) is True  # Token sofort verfuegbar
        # Bucket ist leer, naechster Aufruf wartet ~0.5s
        assert bucket.acquire(1, timeout=2.0) is True

    def test_acquire_timeout(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=1,
            refill_rate=0.5,
            time_func=clock.time,
            sleep_func=clock.sleep,
        )
        bucket.acquire(1)  # Token konsumiert
        # Bei refill_rate=0.5 dauert ein neuer Token 2s; Timeout=0.5s
        assert bucket.acquire(1, timeout=0.5) is False

    def test_acquire_invalid_args(self):
        bucket = TokenBucket(capacity=2, refill_rate=1.0)
        with pytest.raises(ValueError):
            bucket.acquire(0)
        with pytest.raises(ValueError):
            bucket.acquire(99)  # > capacity

    def test_thread_safety(self):
        bucket = TokenBucket(capacity=100, refill_rate=1000.0)
        results: List[bool] = []
        results_lock = threading.Lock()

        def worker():
            for _ in range(10):
                ok = bucket.try_consume(1)
                with results_lock:
                    results.append(ok)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 50 Versuche, max. 100 Tokens vorhanden -> alle muessen erfolgreich sein
        assert all(results)
        assert len(results) == 50

    def test_stats_record_immediate_consumption(self):
        bucket = TokenBucket(capacity=3, refill_rate=1.0)
        assert bucket.try_consume(1) is True

        stats = bucket.stats_snapshot()

        assert stats["requests"] == 1
        assert stats["acquired"] == 1
        assert stats["immediate_acquired"] == 1
        assert stats["delayed_acquired"] == 0
        assert stats["timeouts"] == 0
        assert stats["tokens_consumed"] == pytest.approx(1.0)
        assert stats["available_tokens"] == pytest.approx(2.0)

    def test_stats_record_wait_when_tokens_are_low(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=1,
            refill_rate=2.0,
            time_func=clock.time,
            sleep_func=clock.sleep,
            event_time_func=clock.time,
        )

        assert bucket.acquire(1) is True
        assert bucket.acquire(1, timeout=2.0) is True

        stats = bucket.stats_snapshot()

        assert stats["requests"] == 2
        assert stats["acquired"] == 2
        assert stats["immediate_acquired"] == 1
        assert stats["delayed_acquired"] == 1
        assert stats["low_token_events"] == 1
        assert stats["timeouts"] == 0
        assert stats["total_wait_seconds"] == pytest.approx(0.5)
        assert stats["max_wait_seconds"] == pytest.approx(0.5)
        assert stats["last_wait_seconds"] == pytest.approx(0.5)
        assert stats["last_low_tokens_at"] == pytest.approx(0.0)
        assert stats["last_acquired_at"] == pytest.approx(0.5)

    def test_stats_record_timeout_when_tokens_stay_unavailable(self):
        clock = FakeClock()
        bucket = TokenBucket(
            capacity=1,
            refill_rate=0.5,
            time_func=clock.time,
            sleep_func=clock.sleep,
            event_time_func=clock.time,
        )

        assert bucket.acquire(1) is True
        assert bucket.acquire(1, timeout=0.5) is False

        stats = bucket.stats_snapshot()

        assert stats["requests"] == 2
        assert stats["acquired"] == 1
        assert stats["timeouts"] == 1
        assert stats["low_token_events"] == 1
        assert stats["total_wait_seconds"] == pytest.approx(0.5)
        assert stats["max_wait_seconds"] == pytest.approx(0.5)
        assert stats["last_timeout_at"] == pytest.approx(0.5)

    def test_reset_stats_keeps_bucket_tokens(self):
        bucket = TokenBucket(capacity=2, refill_rate=1.0)
        assert bucket.try_consume(1) is True
        assert bucket.available_tokens() == pytest.approx(1.0)

        bucket.reset_stats()
        stats = bucket.stats_snapshot()

        assert stats["requests"] == 0
        assert stats["acquired"] == 0
        assert stats["available_tokens"] == pytest.approx(1.0)


class TestRateLimiterRegistry:
    def test_get_bucket_creates_default(self):
        bucket = RateLimiter.get_bucket("any-name")
        assert isinstance(bucket, TokenBucket)
        assert bucket.capacity == 60.0  # Default

    def test_configure_bucket_overrides(self):
        RateLimiter.configure_bucket("yfinance", capacity=5, refill_rate=10.0)
        bucket = RateLimiter.get_bucket("yfinance")
        assert bucket.capacity == 5
        assert bucket.refill_rate == 10.0

    def test_acquire_uses_named_bucket(self):
        RateLimiter.configure_bucket("strict", capacity=2, refill_rate=0.001)
        assert RateLimiter.acquire("strict") is True
        assert RateLimiter.acquire("strict") is True
        # Nun ist der Bucket leer; mit kurzem Timeout muss False zurueckkommen.
        assert RateLimiter.acquire("strict", timeout=0.05) is False

    def test_reset_clears_all_buckets(self):
        RateLimiter.configure_bucket("x", capacity=2, refill_rate=1.0)
        RateLimiter.acquire("x")
        RateLimiter.acquire("x")
        RateLimiter.reset()
        # Nach reset wird automatisch ein neuer Default-Bucket angelegt.
        bucket = RateLimiter.get_bucket("x")
        assert bucket.capacity == 60.0

    def test_get_stats_returns_named_bucket_snapshot(self):
        RateLimiter.configure_bucket("metrics", capacity=2, refill_rate=1.0)
        assert RateLimiter.acquire("metrics") is True

        stats = RateLimiter.get_stats("metrics")

        assert stats["name"] == "metrics"
        assert stats["capacity"] == 2
        assert stats["requests"] == 1
        assert stats["acquired"] == 1

    def test_get_all_stats_lists_existing_buckets(self):
        RateLimiter.configure_bucket("a", capacity=2, refill_rate=1.0)
        RateLimiter.configure_bucket("b", capacity=3, refill_rate=1.0)
        RateLimiter.acquire("a")

        stats = RateLimiter.get_all_stats()

        assert {item["name"] for item in stats} == {"a", "b"}
        assert next(item for item in stats if item["name"] == "a")["requests"] == 1

    def test_reset_stats_clears_bucket_telemetry(self):
        RateLimiter.configure_bucket("x", capacity=2, refill_rate=1.0)
        RateLimiter.acquire("x")

        RateLimiter.reset_stats("x")
        stats = RateLimiter.get_stats("x")

        assert stats["requests"] == 0
        assert stats["acquired"] == 0


class TestRateLimitedDecorator:
    def test_decorator_calls_function_when_tokens_available(self):
        RateLimiter.configure_bucket("test", capacity=5, refill_rate=1.0)
        calls = []

        @rate_limited("test")
        def add(a, b):
            calls.append((a, b))
            return a + b

        assert add(1, 2) == 3
        assert calls == [(1, 2)]

    def test_decorator_returns_none_on_timeout(self):
        RateLimiter.configure_bucket("slow", capacity=1, refill_rate=0.001)
        calls = []

        @rate_limited("slow", timeout=0.05)
        def work():
            calls.append("done")
            return 42

        assert work() == 42  # 1. Aufruf konsumiert das einzige Token
        assert work() is None  # 2. Aufruf laeuft in Timeout
        assert calls == ["done"]


class TestRateLimitedCall:
    def test_executes_callable(self):
        RateLimiter.configure_bucket("y", capacity=3, refill_rate=1.0)
        result = rate_limited_call("y", lambda x: x * 2, 5)
        assert result == 10

    def test_returns_none_on_timeout(self):
        RateLimiter.configure_bucket("y", capacity=1, refill_rate=0.001)
        rate_limited_call("y", lambda: "first")  # Token verbraucht
        result = rate_limited_call("y", lambda: "second", timeout=0.05)
        assert result is None

    def test_passes_kwargs(self):
        RateLimiter.configure_bucket("y", capacity=3, refill_rate=1.0)

        def fn(a, b, c=10):
            return a + b + c

        assert rate_limited_call("y", fn, 1, 2, c=3) == 6


class TestInitFromConfig:
    def test_init_from_config_uses_fields(self):
        from core.rate_limiter import init_from_config

        class FakeConfig:
            API_RATE_LIMIT_YFINANCE_CAPACITY = 7.0
            API_RATE_LIMIT_YFINANCE_REFILL = 0.5

        init_from_config(FakeConfig())
        bucket = RateLimiter.get_bucket("yfinance")
        assert bucket.capacity == 7.0
        assert bucket.refill_rate == 0.5

    def test_init_from_config_skips_invalid(self):
        from core.rate_limiter import init_from_config

        class FakeConfig:
            API_RATE_LIMIT_YFINANCE_CAPACITY = "nope"
            API_RATE_LIMIT_YFINANCE_REFILL = 1.0

        # Default soll 60.0 bleiben
        init_from_config(FakeConfig())
        bucket = RateLimiter.get_bucket("yfinance")
        assert bucket.capacity == 60.0
