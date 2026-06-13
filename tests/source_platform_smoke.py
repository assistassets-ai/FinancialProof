"""Headless macOS/Linux source smoke for FinancialProof.

Runs without pytest:
    python tests/source_platform_smoke.py
"""

from __future__ import annotations

import importlib
import os
import sqlite3
import sys
import tempfile
import types
from pathlib import Path

import pandas as pd


os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path(tempfile.mkdtemp(prefix="financialproof-smoke-"))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _install_streamlit_stub() -> types.ModuleType:
    streamlit = types.ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit._metrics = []
    streamlit._captions = []
    streamlit._headers = []

    class _Context:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def metric(self, label, value, delta=None, delta_color=None):
            streamlit.metric(label, value, delta=delta, delta_color=delta_color)

        def caption(self, text):
            streamlit.caption(text)

        def markdown(self, text, **kwargs):
            streamlit.markdown(text, **kwargs)

        def info(self, text):
            streamlit.info(text)

        def warning(self, text):
            streamlit.warning(text)

        def error(self, text):
            streamlit.error(text)

        def success(self, text):
            streamlit.success(text)

    class _Sidebar:
        def title(self, *args, **kwargs):
            return None

        def header(self, *args, **kwargs):
            return None

        def subheader(self, *args, **kwargs):
            return None

        def markdown(self, *args, **kwargs):
            return None

        def caption(self, *args, **kwargs):
            return None

        def text_input(self, label, value="", **kwargs):
            return value

        def selectbox(self, label, options, index=0, **kwargs):
            return options[index]

        def checkbox(self, label, value=False, **kwargs):
            return value

        def button(self, *args, **kwargs):
            return False

        def columns(self, spec):
            count = spec if isinstance(spec, int) else len(spec)
            return [_Context() for _ in range(count)]

        def expander(self, *args, **kwargs):
            return _Context()

    def _no_op(*args, **kwargs):
        return None

    def _columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_Context() for _ in range(count)]

    class _Spinner:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    streamlit.sidebar = _Sidebar()
    streamlit.column_config = types.SimpleNamespace(
        NumberColumn=lambda **kwargs: None,
        TextColumn=lambda **kwargs: None,
    )
    streamlit.set_page_config = _no_op
    streamlit.markdown = _no_op
    streamlit.title = lambda text, **kwargs: streamlit._headers.append(text)
    streamlit.header = lambda text, **kwargs: streamlit._headers.append(text)
    streamlit.subheader = _no_op
    streamlit.info = _no_op
    streamlit.warning = _no_op
    streamlit.error = _no_op
    streamlit.success = _no_op
    streamlit.text_area = _no_op
    streamlit.button = lambda *args, **kwargs: False
    streamlit.checkbox = lambda *args, value=False, **kwargs: value
    streamlit.text_input = lambda label, value="", **kwargs: value
    streamlit.selectbox = lambda label, options, index=0, **kwargs: options[index]
    streamlit.columns = _columns
    streamlit.tabs = lambda labels: [_Context() for _ in labels]
    streamlit.container = lambda *args, **kwargs: _Context()
    streamlit.expander = lambda *args, **kwargs: _Context()
    streamlit.spinner = lambda *args, **kwargs: _Spinner()
    streamlit.progress = _no_op
    streamlit.plotly_chart = _no_op
    streamlit.rerun = _no_op
    streamlit.stop = lambda: None
    streamlit.caption = lambda text, **kwargs: streamlit._captions.append(text)

    def _metric(label, value, delta=None, delta_color=None):
        streamlit._metrics.append(
            {
                "label": label,
                "value": value,
                "delta": delta,
                "delta_color": delta_color,
            }
        )

    streamlit.metric = _metric
    sys.modules["streamlit"] = streamlit
    return streamlit


def _install_plotly_stub() -> None:
    plotly = types.ModuleType("plotly")
    graph_objects = types.ModuleType("plotly.graph_objects")
    subplots = types.ModuleType("plotly.subplots")

    class _Trace:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _Figure:
        def __init__(self):
            self.data = []
            self.layout = types.SimpleNamespace(title=types.SimpleNamespace(text=None))

        def add_trace(self, trace, row=None, col=None):
            self.data.append({"trace": trace, "row": row, "col": col})

        def add_hline(self, **kwargs):
            return None

        def update_yaxes(self, **kwargs):
            return None

        def update_xaxes(self, **kwargs):
            return None

        def update_layout(self, **kwargs):
            if "title" in kwargs:
                self.layout.title.text = kwargs["title"]

    graph_objects.Candlestick = _Trace
    graph_objects.Scatter = _Trace
    graph_objects.Bar = _Trace
    subplots.make_subplots = lambda **kwargs: _Figure()

    plotly.graph_objects = graph_objects
    plotly.subplots = subplots
    sys.modules["plotly"] = plotly
    sys.modules["plotly.graph_objects"] = graph_objects
    sys.modules["plotly.subplots"] = subplots


STREAMLIT_STUB = _install_streamlit_stub()
_install_plotly_stub()


def _check(label: str, fn) -> None:
    try:
        fn()
        print(f"  [v] {label}")
    except Exception as exc:  # pragma: no cover - CLI smoke output
        print(f"  [x] {label}: {exc}")
        raise


def _build_temp_config():
    from config import APIKeyManager, Config

    smoke_root = TEMP_ROOT / "workspace"
    smoke_root.mkdir(parents=True, exist_ok=True)
    temp_config = Config(BASE_DIR=smoke_root)

    manager = APIKeyManager(temp_config)
    manager.save_api_key("demo_service", "smoke-secret")
    assert manager.get_api_key("demo_service") == "smoke-secret"
    assert temp_config.DATA_DIR.is_dir()
    assert temp_config.DB_PATH.parent == temp_config.DATA_DIR
    return temp_config


def _check_database(temp_config) -> None:
    import core.database as database_module

    original_config = database_module.config
    try:
        database_module.config = temp_config
        manager = database_module.DatabaseManager()

        with sqlite3.connect(temp_config.DB_PATH) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert {"watchlist", "jobs", "results", "strategies", "analysis_runs"} <= tables

        item = database_module.WatchlistItem(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            notes="Smoke Watchlist",
        )
        manager.add_to_watchlist(item)
        assert manager.is_in_watchlist("AAPL") is True

        job_id = manager.create_job(
            database_module.Job(symbol="AAPL", analysis_type="arima")
        )
        manager.update_job_status(
            job_id,
            database_module.JobStatus.COMPLETED,
            progress=100,
        )
        manager.save_result(
            database_module.AnalysisResult(
                job_id=job_id,
                summary="Historische Analyse",
                data={"pattern_class": "bullish", "volatility": 2.5},
                confidence=0.73,
            )
        )
        assert manager.get_job_counts()["completed"] >= 1
    finally:
        database_module.config = original_config


def _check_workspace_export(temp_config) -> None:
    import core.database as database_module
    from core.workspace_export import build_workspace_export

    original_config = database_module.config
    try:
        database_module.config = temp_config
        manager = database_module.DatabaseManager()
        payload = build_workspace_export(database=manager, source="source-smoke")
    finally:
        database_module.config = original_config

    assert payload["schema"] == "financialproof-workspace-v1"
    assert payload["legal"]["not_financial_advice"] is True
    assert payload["watchlist"][0]["symbol"] == "AAPL"
    assert payload["analysis_snapshots"][0]["pattern_class"] == "bullish"
    assert "Keine Anlageberatung" in payload["legal"]["warnings"][0]


def _check_data_provider() -> None:
    import yfinance as yf
    from core.data_provider import DataProvider

    class _Ticker:
        def __init__(self, ticker: str):
            self.info = {
                "symbol": ticker,
                "longName": "Apple Inc.",
                "quoteType": "EQUITY",
            }
            self.news = []
            self.income_stmt = pd.DataFrame()
            self.balance_sheet = pd.DataFrame()
            self.cashflow = pd.DataFrame()
            self.dividends = pd.Series(dtype=float)
            self.recommendations = pd.DataFrame()

        def history(self, period="2d"):
            return pd.DataFrame({"Close": [100.0, 102.0]})

    def _download(*args, **kwargs):
        return pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [101.0, 102.0],
                "Low": [99.0, 100.0],
                "Close": [100.5, 101.5],
                "Volume": [1000, 1100],
            }
        )

    original_download = yf.download
    original_ticker = yf.Ticker
    try:
        yf.download = _download
        yf.Ticker = _Ticker
        DataProvider.get_market_data.cache_clear()
        DataProvider.get_ticker_info.cache_clear()

        market_data = DataProvider.get_market_data("AAPL", period="5d")
        info = DataProvider.get_ticker_info("AAPL")
        price = DataProvider.get_current_price("AAPL")

        assert market_data is not None and len(market_data) == 2
        assert info["longName"] == "Apple Inc."
        assert price == (102.0, 2.0, 2.0)
    finally:
        yf.download = original_download
        yf.Ticker = original_ticker
        DataProvider.get_market_data.cache_clear()
        DataProvider.get_ticker_info.cache_clear()


def _check_analysis_registry() -> None:
    from analysis.registry import ensure_initialized, list_analyzers

    ensure_initialized()
    analyzers = list_analyzers()
    assert isinstance(analyzers, list)


def _check_headless_app_import() -> None:
    import ui.disclaimer_widget as disclaimer_widget

    disclaimer_widget.ensure_acknowledged = lambda: None
    app_module = importlib.import_module("app")
    app_module = importlib.reload(app_module)

    STREAMLIT_STUB._metrics.clear()
    STREAMLIT_STUB._captions.clear()

    data = pd.DataFrame(
        {
            "Close": [100.0, 104.0],
            "Volume": [1000, 1100],
        }
    )
    info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Software",
    }
    app_module._render_header("AAPL", info, data)

    labels = {entry["label"] for entry in STREAMLIT_STUB._metrics}
    assert "Aktueller Kurs" in labels
    assert "Marktkapitalisierung" in labels or "Volumen" in labels
    assert any("AAPL" in text for text in STREAMLIT_STUB._captions)


def main() -> None:
    temp_config: dict[str, object] = {}

    def _check_config() -> None:
        temp_config["value"] = _build_temp_config()

    _check("C1 Konfiguration und API-Key-Roundtrip", _check_config)
    _check(
        "C2 SQLite-Schema und Basis-CRUD",
        lambda: _check_database(temp_config["value"]),
    )
    _check(
        "C3 Workspace-Export für den Companion",
        lambda: _check_workspace_export(temp_config["value"]),
    )
    _check("C4 DataProvider mit Stub-Daten", _check_data_provider)
    _check("C5 Analyse-Registry initialisiert headless", _check_analysis_registry)
    _check("C6 App-Import und Header-Renderpfad", _check_headless_app_import)
    print("\n6/6 grün")


if __name__ == "__main__":
    main()
