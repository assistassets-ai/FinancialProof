"""Regression tests for the local Windows launcher."""
from __future__ import annotations

import subprocess
from unittest import mock

import financialproof_launcher as launcher


def test_streamlit_available_returns_false_on_import_timeout():
    """A hanging Streamlit import check must not crash the launcher."""
    with mock.patch(
        "financialproof_launcher.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["python", "-c", "import streamlit"], 10),
    ):
        assert launcher._streamlit_available(["python"]) is False
