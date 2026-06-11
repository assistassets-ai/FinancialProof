"""
Interaction-oriented tests for the Streamlit UI modules.
"""
import importlib
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


def _install_streamlit_stub():
    try:
        __import__("streamlit")
        return
    except ModuleNotFoundError:
        pass

    streamlit = types.ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit.sidebar = types.SimpleNamespace()
    streamlit.column_config = types.SimpleNamespace(
        NumberColumn=lambda **kwargs: None,
        TextColumn=lambda **kwargs: None,
    )

    def _no_op(*args, **kwargs):
        return None

    for name in [
        "button",
        "caption",
        "checkbox",
        "columns",
        "container",
        "error",
        "expander",
        "header",
        "info",
        "markdown",
        "metric",
        "plotly_chart",
        "progress",
        "rerun",
        "spinner",
        "subheader",
        "success",
        "tabs",
        "text_input",
        "title",
        "warning",
    ]:
        setattr(streamlit, name, _no_op)

    sys.modules["streamlit"] = streamlit


def _install_plotly_stub():
    try:
        __import__("plotly")
        return
    except ModuleNotFoundError:
        pass

    plotly = types.ModuleType("plotly")
    graph_objects = types.ModuleType("plotly.graph_objects")
    subplots = types.ModuleType("plotly.subplots")

    class _Trace:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeFigure:
        def __init__(self):
            self.data = []
            self.layout = SimpleNamespace(title=SimpleNamespace(text=None))
            self.xaxis_updates = []
            self.yaxis_updates = []
            self.hlines = []

        def add_trace(self, trace, row=None, col=None):
            self.data.append({"trace": trace, "row": row, "col": col})

        def add_hline(self, **kwargs):
            self.hlines.append(kwargs)

        def update_yaxes(self, **kwargs):
            self.yaxis_updates.append(kwargs)

        def update_layout(self, **kwargs):
            if "title" in kwargs:
                self.layout.title.text = kwargs["title"]
            for key, value in kwargs.items():
                if key == "title":
                    continue
                setattr(self.layout, key, value)

        def update_xaxes(self, **kwargs):
            self.xaxis_updates.append(kwargs)

    graph_objects.Candlestick = _Trace
    graph_objects.Scatter = _Trace
    graph_objects.Bar = _Trace
    subplots.make_subplots = lambda **kwargs: FakeFigure()

    plotly.graph_objects = graph_objects
    plotly.subplots = subplots
    sys.modules["plotly"] = plotly
    sys.modules["plotly.graph_objects"] = graph_objects
    sys.modules["plotly.subplots"] = subplots


_install_streamlit_stub()
_install_plotly_stub()

sys.path.insert(0, str(Path(__file__).parent.parent))

analysis_view = importlib.import_module("ui.analysis_view")
chart_view = importlib.import_module("ui.chart_view")
sidebar = importlib.import_module("ui.sidebar")


class FakeContext:
    """Small context-manager object for Streamlit layout primitives."""

    def __init__(self, root):
        self.root = root

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def success(self, message):
        self.root.success(message)

    def error(self, message):
        self.root.error(message)

    def info(self, message):
        self.root.info(message)

    def metric(self, label, value, delta=None, delta_color=None):
        self.root.metric(label, value, delta=delta, delta_color=delta_color)

    def caption(self, message):
        self.root.caption(message)


class FakeSidebar:
    """Sidebar facade that reuses the root fake state."""

    def __init__(self, root):
        self.root = root

    def title(self, message):
        self.root.sidebar_titles.append(message)

    def header(self, message):
        self.root.sidebar_headers.append(message)

    def subheader(self, message):
        self.root.sidebar_subheaders.append(message)

    def markdown(self, message):
        self.root.markdowns.append(message)

    def caption(self, message):
        self.root.captions.append(message)

    def text_input(self, label, value="", **kwargs):
        return self.root.text_inputs.get(label, value)

    def selectbox(self, label, options, index=0, **kwargs):
        return self.root.selectboxes.get(label, index)

    def checkbox(self, label, value=False, **kwargs):
        return self.root.checkboxes.get(label, value)

    def button(self, label, key=None, **kwargs):
        return self.root.button(label, key=key, **kwargs)

    def columns(self, spec):
        return self.root.columns(spec)

    def expander(self, label, **kwargs):
        return FakeContext(self.root)


class FakeStreamlit:
    """Configurable Streamlit test double for interaction-heavy flows."""

    def __init__(self):
        self.session_state = {}
        self.sidebar = FakeSidebar(self)
        self.sidebar_titles = []
        self.sidebar_headers = []
        self.sidebar_subheaders = []
        self.text_inputs = {}
        self.selectboxes = {}
        self.checkboxes = {}
        self.button_presses = {}
        self.success_messages = []
        self.error_messages = []
        self.info_messages = []
        self.warning_messages = []
        self.markdowns = []
        self.captions = []
        self.headers = []
        self.subheaders = []
        self.metrics = []
        self.progress_values = []
        self.plotly_figures = []
        self.rerun_called = False

    def _lookup_button(self, label=None, key=None):
        if key is not None and key in self.button_presses:
            return self.button_presses[key]
        return self.button_presses.get(label, False)

    def button(self, label, key=None, **kwargs):
        return self._lookup_button(label=label, key=key)

    def checkbox(self, label, value=False, **kwargs):
        return self.checkboxes.get(label, value)

    def text_input(self, label, value="", **kwargs):
        return self.text_inputs.get(label, value)

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [FakeContext(self) for _ in range(count)]

    def tabs(self, labels):
        return [FakeContext(self) for _ in labels]

    def container(self):
        return FakeContext(self)

    def expander(self, label, **kwargs):
        return FakeContext(self)

    @contextmanager
    def spinner(self, message):
        yield

    def title(self, message):
        self.headers.append(("title", message))

    def header(self, message):
        self.headers.append(("header", message))

    def subheader(self, message):
        self.subheaders.append(message)

    def caption(self, message):
        self.captions.append(message)

    def markdown(self, message, **kwargs):
        self.markdowns.append(message)

    def metric(self, label, value, delta=None, delta_color=None):
        self.metrics.append(
            {
                "label": label,
                "value": value,
                "delta": delta,
                "delta_color": delta_color,
            }
        )

    def success(self, message):
        self.success_messages.append(message)

    def error(self, message):
        self.error_messages.append(message)

    def info(self, message):
        self.info_messages.append(message)

    def warning(self, message):
        self.warning_messages.append(message)

    def progress(self, value):
        self.progress_values.append(value)

    def plotly_chart(self, figure, **kwargs):
        self.plotly_figures.append(figure)

    def rerun(self):
        self.rerun_called = True


def _sample_price_frame():
    index = pd.date_range("2026-04-01", periods=3, freq="D")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000, 1100, 1200],
        },
        index=index,
    )


def test_render_sidebar_normalizes_symbol_and_returns_indicator_settings(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.text_inputs[sidebar.texts.SIDEBAR_SYMBOL] = " msft "
    fake_st.selectboxes[sidebar.texts.SIDEBAR_PERIOD] = 0
    fake_st.checkboxes["MACD"] = True

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.db, "get_watchlist", lambda: [])
    monkeypatch.setattr(sidebar.db, "is_in_watchlist", lambda symbol: True)

    symbol, period, indicators = sidebar.render_sidebar()

    assert symbol == "MSFT"
    assert fake_st.session_state["selected_symbol"] == "MSFT"
    assert period == list(sidebar.texts.PERIODS.keys())[0]
    assert indicators["sma_20"] is True
    assert indicators["macd"] is True


def test_render_watchlist_click_selects_symbol_and_triggers_rerun(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["wl_TSLA"] = True

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(
        sidebar.db,
        "get_watchlist",
        lambda: [sidebar.WatchlistItem(symbol="TSLA", name="Tesla", asset_type="stock")],
    )
    monkeypatch.setattr(sidebar.DataProvider, "get_current_price", lambda symbol: (100.0, 2.0, 2.0))

    sidebar._render_watchlist("AAPL")

    assert fake_st.session_state["selected_symbol"] == "TSLA"
    assert fake_st.rerun_called is True


def test_render_watchlist_adds_current_symbol(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["➕ AAPL hinzufügen"] = True
    added = []

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.db, "get_watchlist", lambda: [])
    monkeypatch.setattr(sidebar.db, "is_in_watchlist", lambda symbol: False)
    monkeypatch.setattr(sidebar.DataProvider, "get_ticker_info", lambda symbol: {"longName": "Apple Inc."})
    monkeypatch.setattr(sidebar.DataProvider, "get_asset_type", lambda symbol: "stock")
    monkeypatch.setattr(sidebar.db, "add_to_watchlist", lambda item: added.append(item))

    sidebar._render_watchlist("AAPL")

    assert len(added) == 1
    assert added[0].symbol == "AAPL"
    assert added[0].name == "Apple Inc."
    assert added[0].asset_type == "stock"
    assert fake_st.rerun_called is True


def test_render_settings_db_reset_button_sets_session_state(monkeypatch):
    """Regression: st.button+st.checkbox anti-pattern — button click sets session_state."""
    fake_st = FakeStreamlit()
    fake_st.button_presses["🗑️ Datenbank zurücksetzen"] = True

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.api_keys, "has_api_key", lambda name: False)

    sidebar._render_settings()

    assert fake_st.session_state.get("_confirm_db_reset") is True


def test_render_settings_db_reset_cancel_clears_session_state(monkeypatch):
    """Cancel button clears session_state without deleting the database."""
    fake_st = FakeStreamlit()
    fake_st.session_state["_confirm_db_reset"] = True
    fake_st.button_presses["_db_reset_no"] = True

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.api_keys, "has_api_key", lambda name: False)

    sidebar._render_settings()

    assert "_confirm_db_reset" not in fake_st.session_state
    assert fake_st.rerun_called is True


def test_render_settings_reports_permission_error_on_database_reset(monkeypatch):
    """PermissionError on deletion shows error and clears session_state."""
    fake_st = FakeStreamlit()
    # Session_state persists across reruns — confirmation dialog was triggered earlier
    fake_st.session_state["_confirm_db_reset"] = True
    fake_st.button_presses["_db_reset_yes"] = True

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.api_keys, "has_api_key", lambda name: False)

    import os

    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        os,
        "remove",
        lambda path: (_ for _ in ()).throw(PermissionError("locked")),
    )

    sidebar._render_settings()

    assert fake_st.error_messages == [
        "Datenbank ist gesperrt (OneDrive-Sync oder anderer Prozess). Bitte später erneut versuchen."
    ]
    assert "_confirm_db_reset" not in fake_st.session_state


def test_render_settings_db_reset_deletes_db_on_confirmation(monkeypatch, tmp_path):
    """Confirmed deletion removes the DB file and clears session_state."""
    fake_st = FakeStreamlit()
    fake_st.session_state["_confirm_db_reset"] = True
    fake_st.button_presses["_db_reset_yes"] = True

    db_file = tmp_path / "financial.db"
    db_file.write_text("fake-db-content")

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.api_keys, "has_api_key", lambda name: False)
    monkeypatch.setattr(sidebar.config, "DB_PATH", str(db_file))

    sidebar._render_settings()

    assert not db_file.exists()
    assert "_confirm_db_reset" not in fake_st.session_state
    assert fake_st.success_messages == ["Datenbank wurde zurückgesetzt"]


def test_rate_limit_status_shows_stats_and_can_reset(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["Rate-Limit-Statistik zurücksetzen"] = True
    reset_calls = []

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(
        sidebar.RateLimiter,
        "get_all_stats",
        lambda: [
            {
                "name": "yfinance",
                "requests": 7,
                "delayed_acquired": 2,
                "timeouts": 1,
                "low_token_events": 3,
                "available_tokens": 4.5,
                "capacity": 10.0,
                "last_low_tokens_at": 1_700_000_000.0,
                "last_timeout_at": None,
            }
        ],
    )
    monkeypatch.setattr(sidebar.RateLimiter, "reset_stats", lambda: reset_calls.append("all"))

    sidebar._render_rate_limit_status()

    assert any("Anfragen: 7" in caption for caption in fake_st.captions)
    assert any("Token knapp: 3" in caption for caption in fake_st.captions)
    assert any("Letzte Knappheit:" in caption for caption in fake_st.captions)
    assert any(caption == "_yfinance_" for caption in fake_st.captions)
    assert reset_calls == ["all"]
    assert fake_st.success_messages == ["Rate-Limit-Statistik zurückgesetzt"]


def test_rate_limit_status_lists_multiple_buckets(monkeypatch):
    fake_st = FakeStreamlit()

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(
        sidebar.RateLimiter,
        "get_all_stats",
        lambda: [
            {
                "name": "yfinance",
                "requests": 3,
                "delayed_acquired": 0,
                "timeouts": 0,
                "low_token_events": 0,
                "available_tokens": 9.0,
                "capacity": 10.0,
                "last_low_tokens_at": None,
                "last_timeout_at": None,
            },
            {
                "name": "twitter",
                "requests": 5,
                "delayed_acquired": 1,
                "timeouts": 2,
                "low_token_events": 4,
                "available_tokens": 0.5,
                "capacity": 5.0,
                "last_low_tokens_at": 1_700_000_500.0,
                "last_timeout_at": 1_700_000_900.0,
            },
        ],
    )

    sidebar._render_rate_limit_status()

    assert any(caption == "_yfinance_" for caption in fake_st.captions)
    assert any(caption == "_twitter_" for caption in fake_st.captions)
    assert any("Anfragen: 3" in caption for caption in fake_st.captions)
    assert any("Anfragen: 5" in caption for caption in fake_st.captions)
    assert any("Letzter Timeout:" in caption for caption in fake_st.captions)


def test_rate_limit_status_handles_empty_registry(monkeypatch):
    fake_st = FakeStreamlit()

    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(sidebar.RateLimiter, "get_all_stats", lambda: [])

    sidebar._render_rate_limit_status()

    assert any("Noch keine API-Aufrufe" in caption for caption in fake_st.captions)
    assert fake_st.success_messages == []


def test_rate_limit_status_reflects_data_provider_yfinance_calls(monkeypatch):
    fake_st = FakeStreamlit()
    data_provider = importlib.import_module("core.data_provider")
    DataProvider = data_provider.DataProvider

    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol
            self.info = {"symbol": symbol, "longName": "Apple Inc."}

    monkeypatch.setattr(data_provider.yf, "download", lambda *args, **kwargs: _sample_price_frame())
    monkeypatch.setattr(data_provider.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(sidebar, "st", fake_st)

    DataProvider.get_market_data.cache_clear()
    DataProvider.get_ticker_info.cache_clear()
    try:
        market_data = DataProvider.get_market_data("AAPL", period="5d")
        info = DataProvider.get_ticker_info("AAPL")

        assert market_data is not None
        assert len(market_data) == 3
        assert info["longName"] == "Apple Inc."

        sidebar._render_rate_limit_status()

        assert any(caption == "_yfinance_" for caption in fake_st.captions)
        assert any("Anfragen: 2" in caption for caption in fake_st.captions)
        assert any("Timeouts: 0" in caption for caption in fake_st.captions)
    finally:
        DataProvider.get_market_data.cache_clear()
        DataProvider.get_ticker_info.cache_clear()


def test_render_chart_view_handles_empty_dataframe(monkeypatch):
    fake_st = FakeStreamlit()
    monkeypatch.setattr(chart_view, "st", fake_st)

    chart_view.render_chart_view(pd.DataFrame(), "AAPL", {})

    assert fake_st.error_messages == [chart_view.texts.MSG_NO_DATA]


def test_render_chart_view_builds_plot_with_active_indicator_paths(monkeypatch):
    fake_st = FakeStreamlit()
    source_df = _sample_price_frame()
    captured = {}

    def fake_calculate_all(df, active_indicators):
        captured["active_indicators"] = list(active_indicators)
        enriched = df.copy()
        enriched["sma_20"] = [100.0, 101.0, 102.0]
        enriched["rsi"] = [40.0, 55.0, 65.0]
        enriched["macd"] = [0.1, 0.2, 0.3]
        enriched["macd_signal"] = [0.05, 0.1, 0.15]
        enriched["macd_histogram"] = [0.05, 0.1, 0.15]
        return enriched

    class DummySignalGenerator:
        def generate_all_signals(self, df):
            return []

        def get_signal_summary(self, df):
            return {
                "overall_signal": SimpleNamespace(value="buy"),
                "buy_count": 1,
                "sell_count": 0,
                "recent_signals": [],
            }

    monkeypatch.setattr(chart_view, "st", fake_st)
    monkeypatch.setattr(chart_view.TechnicalIndicators, "calculate_all", fake_calculate_all)
    monkeypatch.setattr(chart_view, "SignalGenerator", DummySignalGenerator)

    chart_view.render_chart_view(
        source_df,
        "AAPL",
        {
            "sma_20": True,
            "sma_50": False,
            "sma_200": False,
            "bollinger": False,
            "rsi": True,
            "macd": True,
        },
    )

    assert captured["active_indicators"] == ["sma_20", "rsi", "macd"]
    assert len(fake_st.plotly_figures) == 1
    assert fake_st.plotly_figures[0].layout.title.text == "AAPL - Kursverlauf"
    assert any(metric["label"] == "Kurs" for metric in fake_st.metrics)
    assert fake_st.success_messages == ["🟢 Tendenz: überwiegend bullische Muster"]


def test_analysis_controls_auto_selection_creates_jobs(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["Geeignete Methoden automatisch auswählen"] = True
    created = []

    monkeypatch.setattr(analysis_view, "st", fake_st)
    monkeypatch.setattr(
        analysis_view,
        "get_analyzer_for_ui",
        lambda: {
            "statistical": {
                "icon": "📊",
                "name": "Statistik",
                "analyzers": [
                    {
                        "display_name": "ARIMA",
                        "description": "Forecasting",
                        "name": "arima",
                    }
                ],
            }
        },
    )
    monkeypatch.setattr(
        analysis_view.auto_selector,
        "select_and_execute",
        lambda symbol, data: {"selected_methods": ["arima", "monte_carlo"]},
    )
    monkeypatch.setattr(
        analysis_view.JobManager,
        "create_job",
        lambda symbol, method, parameters=None: created.append((symbol, method)) or len(created),
    )

    analysis_view._render_analysis_controls("AAPL", _sample_price_frame())

    assert created == [("AAPL", "arima"), ("AAPL", "monte_carlo")]
    assert fake_st.success_messages == ["Ausgewählte Analyse-Methoden: arima, monte_carlo"]
    assert fake_st.info_messages == ["Auftrag #1 erstellt: arima", "Auftrag #2 erstellt: monte_carlo"]


def test_analysis_controls_all_analyzers_button_creates_jobs_and_reruns(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["Alle Analysen starten"] = True
    created = []

    monkeypatch.setattr(analysis_view, "st", fake_st)
    monkeypatch.setattr(
        analysis_view,
        "get_analyzer_for_ui",
        lambda: {
            "statistical": {
                "icon": "📊",
                "name": "Statistik",
                "analyzers": [],
            }
        },
    )
    monkeypatch.setattr(
        analysis_view,
        "list_analyzers",
        lambda: [{"name": "arima"}, {"name": "mean_reversion"}],
    )
    monkeypatch.setattr(
        analysis_view.JobManager,
        "create_job",
        lambda symbol, method, parameters=None: created.append((symbol, method)) or len(created),
    )

    analysis_view._render_analysis_controls("AAPL", _sample_price_frame())

    assert created == [("AAPL", "arima"), ("AAPL", "mean_reversion")]
    assert fake_st.success_messages == ["2 Aufträge erstellt"]
    assert fake_st.rerun_called is True


def test_render_pending_job_executes_job_and_reruns(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["run_17"] = True

    monkeypatch.setattr(analysis_view, "st", fake_st)
    monkeypatch.setattr(analysis_view.executor, "execute_job_sync", lambda job_id: True)

    analysis_view._render_pending_job(SimpleNamespace(id=17))

    assert fake_st.success_messages == ["Analyse abgeschlossen!"]
    assert fake_st.rerun_called is True


def test_render_failed_job_retries_with_new_job(monkeypatch):
    fake_st = FakeStreamlit()
    fake_st.button_presses["retry_23"] = True
    deleted = []

    monkeypatch.setattr(analysis_view, "st", fake_st)
    monkeypatch.setattr(
        analysis_view.JobManager,
        "create_job",
        lambda symbol, analysis_type, parameters=None: 99,
    )
    monkeypatch.setattr(analysis_view.JobManager, "delete_job", lambda job_id: deleted.append(job_id))

    analysis_view._render_failed_job(
        SimpleNamespace(id=23, symbol="AAPL", analysis_type="arima", parameters={"window": 20}, error_message="Boom")
    )

    assert deleted == [23]
    assert fake_st.success_messages == ["Neuer Auftrag #99 erstellt"]
    assert fake_st.rerun_called is True


def test_app_render_header_no_inverse_delta_color_in_source():
    """Regression: _render_header darf kein delta_color='inverse' mehr an st.metric übergeben.

    delta_color='inverse' macht Kursrückgänge grün (Streamlit: 'inverse' = gut wenn niedrig).
    Korrekt ist der Streamlit-Standard 'normal' (kein explizites delta_color).
    """
    app_path = Path(__file__).parent.parent / "app.py"
    source = app_path.read_text(encoding="utf-8")
    assert 'delta_color="inverse"' not in source, (
        "delta_color='inverse' in app.py gefunden — Fix wurde rückgängig gemacht! "
        "Kursrückgänge würden grün angezeigt."
    )
    assert "delta_color='inverse'" not in source, (
        "delta_color='inverse' in app.py gefunden — Fix wurde rückgängig gemacht!"
    )


def test_render_header_metric_has_no_inverse_delta_color():
    """Behavioral regression: _render_header ruft st.metric ohne delta_color='inverse' auf.

    delta_color='inverse' lässt Kursrückgänge grün erscheinen — der Fix entfernte
    den Parameter vollständig; der Streamlit-Default 'normal' ist korrekt.
    Dieser Test führt _render_header tatsächlich aus (kein Quelltext-Grep).
    """
    from unittest.mock import MagicMock, patch

    # MagicMock als streamlit — module-level Aufrufe (set_page_config, markdown)
    # werden transparent zu No-Ops, ohne dass weitere Stub-Einträge nötig sind.
    magic_st = MagicMock()
    magic_st.session_state = {}

    with patch.dict(sys.modules, {"streamlit": magic_st}):
        with patch("ui.disclaimer_widget.ensure_acknowledged", return_value=None):
            import app as _app_module
            importlib.reload(_app_module)

    # FakeStreamlit übernimmt das Modul-st für den tatsächlichen Aufruf
    fake_st = FakeStreamlit()
    _app_module.st = fake_st

    data = pd.DataFrame({"Close": [100.0, 105.0], "Volume": [1_000, 1_100]})
    _app_module._render_header("AAPL", {}, data)

    kurs_metrics = [m for m in fake_st.metrics if m["label"] == "Aktueller Kurs"]
    assert kurs_metrics, (
        "_render_header muss st.metric('Aktueller Kurs', ...) aufrufen — keiner gefunden"
    )
    for m in kurs_metrics:
        assert m.get("delta_color") != "inverse", (
            f"delta_color='inverse' in st.metric-Aufruf gefunden — Regression: {m}"
        )
