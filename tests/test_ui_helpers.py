"""
Tests fuer Disclaimer-Persistenz und UI-Helferfunktionen.
"""
import importlib
import sys
import types
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


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
        "dataframe",
        "error",
        "expander",
        "header",
        "info",
        "markdown",
        "metric",
        "multiselect",
        "plotly_chart",
        "progress",
        "rerun",
        "stop",
        "subheader",
        "success",
        "tabs",
        "text_area",
        "title",
        "warning",
    ]:
        setattr(streamlit, name, _no_op)

    sys.modules["streamlit"] = streamlit


_install_streamlit_stub()

sys.path.insert(0, str(Path(__file__).parent.parent))

analysis_view = importlib.import_module("ui.analysis_view")
disclaimer_widget = importlib.import_module("ui.disclaimer_widget")
job_queue = importlib.import_module("ui.job_queue")


class FakeStreamlit:
    """Kleine Streamlit-Attrappe fuer isolierte Tests."""

    def __init__(self):
        self.session_state = {}
        self.success_messages = []
        self.info_messages = []
        self.rerun_called = False

    def success(self, message):
        self.success_messages.append(message)

    def info(self, message):
        self.info_messages.append(message)

    def rerun(self):
        self.rerun_called = True


def test_save_and_load_acceptance_round_trip(tmp_path, monkeypatch):
    acceptance_file = tmp_path / ".disclaimer_acceptance.json"
    record = {
        "disclaimer_hash": "abc123",
        "accepted_at": "2026-04-29T18:00:00+00:00",
        "acknowledged_labels": ["ä", "Historische Muster"],
    }

    monkeypatch.setattr(disclaimer_widget, "_ACCEPTANCE_FILE", acceptance_file)

    disclaimer_widget._save_acceptance(record)

    assert disclaimer_widget._load_acceptance() == record


def test_persisted_acceptance_requires_matching_hash_and_timestamp(tmp_path, monkeypatch):
    acceptance_file = tmp_path / ".disclaimer_acceptance.json"

    monkeypatch.setattr(disclaimer_widget, "_ACCEPTANCE_FILE", acceptance_file)
    disclaimer_widget._save_acceptance(
        {
            "disclaimer_hash": "expected-hash",
            "accepted_at": "2026-04-29T18:00:00+00:00",
        }
    )

    assert disclaimer_widget._persisted_acceptance_valid("expected-hash") is True
    assert disclaimer_widget._persisted_acceptance_valid("other-hash") is False

    acceptance_file.write_text('{"disclaimer_hash": "expected-hash"}', encoding="utf-8")

    assert disclaimer_widget._persisted_acceptance_valid("expected-hash") is False


def test_load_acceptance_returns_none_for_invalid_json(tmp_path, monkeypatch):
    acceptance_file = tmp_path / ".disclaimer_acceptance.json"
    acceptance_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(disclaimer_widget, "_ACCEPTANCE_FILE", acceptance_file)

    assert disclaimer_widget._load_acceptance() is None


def test_ensure_acknowledged_uses_session_cache(monkeypatch):
    fake_st = FakeStreamlit()
    current_text = disclaimer_widget._build_disclaimer_text()
    current_hash = disclaimer_widget._compute_hash(current_text)
    fake_st.session_state.update(
        {
            "disclaimer_accepted": True,
            "disclaimer_hash": current_hash,
        }
    )

    monkeypatch.setattr(disclaimer_widget, "st", fake_st)
    monkeypatch.setattr(
        disclaimer_widget,
        "_render_acknowledgement_screen",
        lambda text, hash_value: (_ for _ in ()).throw(
            AssertionError("Render sollte nicht aufgerufen werden")
        ),
    )

    disclaimer_widget.ensure_acknowledged()


def test_ensure_acknowledged_restores_valid_persisted_acceptance(tmp_path, monkeypatch):
    acceptance_file = tmp_path / ".disclaimer_acceptance.json"
    fake_st = FakeStreamlit()
    current_text = disclaimer_widget._build_disclaimer_text()
    current_hash = disclaimer_widget._compute_hash(current_text)

    monkeypatch.setattr(disclaimer_widget, "_ACCEPTANCE_FILE", acceptance_file)
    monkeypatch.setattr(disclaimer_widget, "st", fake_st)
    monkeypatch.setattr(
        disclaimer_widget,
        "_render_acknowledgement_screen",
        lambda text, hash_value: (_ for _ in ()).throw(
            AssertionError("Render sollte nicht aufgerufen werden")
        ),
    )

    disclaimer_widget._save_acceptance(
        {
            "disclaimer_hash": current_hash,
            "accepted_at": "2026-04-29T18:00:00+00:00",
        }
    )

    disclaimer_widget.ensure_acknowledged()

    assert fake_st.session_state["disclaimer_accepted"] is True
    assert fake_st.session_state["disclaimer_hash"] == current_hash


def test_ensure_acknowledged_renders_when_acceptance_missing(tmp_path, monkeypatch):
    acceptance_file = tmp_path / ".disclaimer_acceptance.json"
    fake_st = FakeStreamlit()
    captured = {}

    monkeypatch.setattr(disclaimer_widget, "_ACCEPTANCE_FILE", acceptance_file)
    monkeypatch.setattr(disclaimer_widget, "st", fake_st)
    monkeypatch.setattr(
        disclaimer_widget,
        "_render_acknowledgement_screen",
        lambda text, hash_value: captured.update(
            {
                "text": text,
                "hash": hash_value,
            }
        ),
    )

    disclaimer_widget.ensure_acknowledged()

    assert captured["hash"] == disclaimer_widget._compute_hash(captured["text"])
    assert fake_st.session_state == {}


def test_format_value_handles_small_large_and_plain_values():
    assert analysis_view._format_value(0.0054321) == "0.0054"
    assert analysis_view._format_value(1_234_567.89) == "1,234,568"
    assert analysis_view._format_value(42.4242) == "42.42"
    assert analysis_view._format_value("AAPL") == "AAPL"


def test_format_datetime_handles_none_iso_and_invalid_values():
    assert job_queue._format_datetime(None) == "-"
    assert job_queue._format_datetime("2026-04-29T13:45:00") == "29.04.2026 13:45"
    assert job_queue._format_datetime("not-a-date") == "not-a-date"
    assert job_queue._format_datetime(datetime(2026, 4, 29, 13, 45)) == "29.04.2026 13:45"


def test_get_status_display_maps_known_and_unknown_statuses():
    assert job_queue._get_status_display(job_queue.JobStatus.PENDING) == "⏳ Wartend"
    assert job_queue._get_status_display("custom") == "custom"


def test_cleanup_old_jobs_keeps_recent_entries(monkeypatch):
    completed_jobs = [SimpleNamespace(id=job_id) for job_id in range(1, 26)]
    failed_jobs = [
        SimpleNamespace(id=job_id, status=job_queue.JobStatus.FAILED)
        for job_id in range(101, 114)
    ]
    deleted = []
    fake_st = FakeStreamlit()

    monkeypatch.setattr(job_queue, "st", fake_st)
    monkeypatch.setattr(job_queue.JobManager, "get_completed_jobs", lambda limit=100: completed_jobs)
    monkeypatch.setattr(job_queue.JobManager, "get_all_jobs", lambda limit=100: failed_jobs)
    monkeypatch.setattr(job_queue.JobManager, "delete_job", lambda job_id: deleted.append(job_id))

    job_queue._cleanup_old_jobs()

    assert deleted == [21, 22, 23, 24, 25, 111, 112, 113]
    assert fake_st.success_messages == ["8 alte Jobs gelöscht"]
    assert fake_st.rerun_called is True


def test_cleanup_old_jobs_reports_when_nothing_can_be_deleted(monkeypatch):
    completed_jobs = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    failed_jobs = [SimpleNamespace(id=101, status=job_queue.JobStatus.FAILED)]
    fake_st = FakeStreamlit()

    monkeypatch.setattr(job_queue, "st", fake_st)
    monkeypatch.setattr(job_queue.JobManager, "get_completed_jobs", lambda limit=100: completed_jobs)
    monkeypatch.setattr(job_queue.JobManager, "get_all_jobs", lambda limit=100: failed_jobs)
    monkeypatch.setattr(
        job_queue.JobManager,
        "delete_job",
        lambda job_id: (_ for _ in ()).throw(
            AssertionError("Es duerfen keine Jobs geloescht werden")
        ),
    )

    job_queue._cleanup_old_jobs()

    assert fake_st.info_messages == ["Keine alten Jobs zu bereinigen"]
    assert fake_st.rerun_called is True
