"""
Regression-Tests fuer ui/job_queue._render_job_list.

Regression: st.dataframe wurde mit width="stretch" aufgerufen, was in
Streamlit >= 1.40 einen TypeError fuer nicht-integer width-Werte ausloest.
Korrekt ist use_container_width=True.
"""
import datetime
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestRenderJobList:
    """st.dataframe wird korrekt mit use_container_width=True aufgerufen (Regression)."""

    def test_dataframe_called_with_use_container_width(self):
        """Kein width='stretch'; use_container_width=True muss uebergeben werden."""
        st_mock = MagicMock()

        fake_job = MagicMock()
        fake_job.id = 1
        fake_job.symbol = "AAPL"
        fake_job.analysis_type = "arima"
        fake_job.status = MagicMock(spec=str)
        fake_job.created_at = datetime.datetime(2025, 1, 1, 12, 0, 0)
        fake_job.completed_at = None

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            import ui.job_queue as job_queue
            importlib.reload(job_queue)

            with patch.object(job_queue.JobManager, "get_all_jobs", return_value=[fake_job]):
                job_queue._render_job_list(None)

        assert st_mock.dataframe.called, "st.dataframe wurde nicht aufgerufen"

        _, kwargs = st_mock.dataframe.call_args
        assert kwargs.get("use_container_width") is True, (
            "st.dataframe muss mit use_container_width=True aufgerufen werden, "
            f"tatsaechliche kwargs: {kwargs}"
        )
        assert "width" not in kwargs, (
            "st.dataframe darf kein width-Argument erhalten "
            "(TypeError in Streamlit >= 1.40 fuer nicht-integer width-Werte)"
        )
