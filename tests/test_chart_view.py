"""
Regression-Tests fuer chart_view.render_main_chart.

Regression: st.plotly_chart wurde mit width="stretch" aufgerufen, was in
Streamlit >= 1.40 ein TypeError auslöst. Korrekt ist use_container_width=True.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    np.random.seed(0)
    n = 60
    close = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
        },
        index=pd.date_range("2025-01-01", periods=n, freq="B"),
    )


class TestRenderMainChart:
    """plotly_chart wird korrekt mit use_container_width=True aufgerufen (Regression)."""

    def test_plotly_chart_called_with_use_container_width(self, sample_df):
        """Kein width='stretch'; use_container_width=True muss uebergeben werden."""
        st_mock = MagicMock()
        # make_subplots muss echte Fig zurueckgeben damit add_trace usw. nicht failen
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        indicators = {
            "sma_20": True,
            "sma_50": False,
            "sma_200": False,
            "bollinger": False,
            "rsi": False,
            "macd": False,
        }

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            # ui.chart_view wurde moeglicherweise bereits importiert — neu laden
            import importlib
            import ui.chart_view as chart_view
            importlib.reload(chart_view)

            chart_view._render_main_chart(sample_df, "TEST", indicators, [])

        # Sicherstellen dass plotly_chart ueberhaupt aufgerufen wurde
        assert st_mock.plotly_chart.called, "st.plotly_chart wurde nicht aufgerufen"

        # use_container_width=True muss im ersten (und einzigen) Aufruf stehen
        _, kwargs = st_mock.plotly_chart.call_args
        assert kwargs.get("use_container_width") is True, (
            "st.plotly_chart muss mit use_container_width=True aufgerufen werden, "
            f"tatsaechliche kwargs: {kwargs}"
        )
        assert "width" not in kwargs, (
            "st.plotly_chart darf kein width-Argument erhalten (TypeError in Streamlit>=1.40)"
        )
