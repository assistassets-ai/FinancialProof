"""
FinancialProof - Analysis View UI Komponente
Statistische-Analyse-Tab mit Auftragserteilung und Ergebnisanzeige.
(Historische Analysen, keine Anlageberatung; siehe Disclaimer.)
"""
import streamlit as st
import pandas as pd
from typing import Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import texts
from analysis.registry import get_analyzer_for_ui, list_analyzers, ensure_initialized
from jobs.manager import JobManager
from jobs.executor import executor, auto_selector
from core.database import JobStatus


def render_analysis_view(symbol: str, data: pd.DataFrame):
    """
    Rendert den Tiefen-Analyse-Bereich.

    Args:
        symbol: Das aktuelle Symbol
        data: DataFrame mit Marktdaten
    """
    ensure_initialized()

    st.header(f"Statistische Analyse: {symbol}")
    st.caption(
        "Historische Musteranalyse auf Marktdaten — keine Anlageberatung, "
        "keine Prognose, keine Kauf-/Verkaufsempfehlung."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        _render_analysis_controls(symbol, data)

    with col2:
        _render_results_view(symbol)


def _render_analysis_controls(symbol: str, data: pd.DataFrame):
    """Rendert die Steuerung für Analysen"""
    st.subheader("🕵️ Analyse beauftragen")

    # Kategorien und Analysen laden
    categories = get_analyzer_for_ui()

    if not categories:
        st.warning("Keine Analyse-Module verfügbar")
        return

    # Tabs für Kategorien
    category_names = list(categories.keys())
    category_tabs = st.tabs([
        f"{categories[c]['icon']} {categories[c]['name']}"
        for c in category_names
    ])

    for i, cat_key in enumerate(category_names):
        with category_tabs[i]:
            cat_data = categories[cat_key]

            for analyzer_info in cat_data['analyzers']:
                _render_analyzer_card(symbol, analyzer_info)

    st.markdown("---")

    # Automatische Auswahl
    st.subheader("🤖 Automatische Methoden-Auswahl")

    if st.button("Geeignete Methoden automatisch auswählen", use_container_width=True):
        with st.spinner("Analysiere Marktdaten..."):
            selection = auto_selector.select_and_execute(symbol, data)

            if 'error' not in selection:
                st.success(f"Ausgewählte Analyse-Methoden: {', '.join(selection['selected_methods'])}")

                for method in selection['selected_methods']:
                    job_id = JobManager.create_job(symbol, method)
                    st.info(f"Auftrag #{job_id} erstellt: {method}")
            else:
                st.error(selection['error'])

    # Alle Analysen starten
    if st.button("Alle Analysen starten", type="secondary", use_container_width=True):
        all_analyzers = list_analyzers()
        for info in all_analyzers:
            job_id = JobManager.create_job(symbol, info['name'])
        st.success(f"{len(all_analyzers)} Aufträge erstellt")
        st.rerun()


def _render_analyzer_card(symbol: str, info: Dict):
    """Rendert eine Karte für einen einzelnen Analyzer"""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{info['display_name']}**")
            st.caption(info['description'])

        with col2:
            if st.button("▶️", key=f"start_{info['name']}_{symbol}"):
                job_id = JobManager.create_job(symbol, info['name'])
                st.success(f"Auftrag #{job_id} erstellt")
                st.rerun()


def _render_results_view(symbol: str):
    """Rendert die Ergebnis-Ansicht"""
    st.subheader("📋 Ergebnisse & Berichte")

    # Filter
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        show_only_completed = st.checkbox("Nur abgeschlossene", value=False)

    with filter_col2:
        show_only_symbol = st.checkbox(f"Nur {symbol}", value=True)

    # Jobs laden
    if show_only_symbol:
        jobs = JobManager.get_jobs_for_symbol(symbol, limit=30)
    else:
        jobs = JobManager.get_all_jobs(limit=30)

    if show_only_completed:
        jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]

    if not jobs:
        st.info("Keine Analysen vorhanden. Starte eine Analyse links.")
        return

    # Jobs anzeigen
    for job in jobs:
        _render_job_card(job)


def _render_job_card(job):
    """Rendert eine Job-Karte"""
    status_icons = {
        JobStatus.PENDING: "⏳",
        JobStatus.RUNNING: "🔄",
        JobStatus.COMPLETED: "✅",
        JobStatus.FAILED: "❌",
        JobStatus.CANCELLED: "🚫"
    }

    icon = status_icons.get(job.status, "❓")
    title = f"{icon} #{job.id} | {job.analysis_type} ({job.symbol})"

    with st.expander(title, expanded=(job.status == JobStatus.PENDING)):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.caption(f"Erstellt: {job.created_at}")
            if job.completed_at:
                st.caption(f"Abgeschlossen: {job.completed_at}")

        with col2:
            st.caption(f"Status: {texts.__dict__.get(f'JOB_{job.status.value.upper()}', job.status.value)}")

        if job.status == JobStatus.PENDING:
            _render_pending_job(job)
        elif job.status == JobStatus.RUNNING:
            _render_running_job(job)
        elif job.status == JobStatus.COMPLETED:
            _render_completed_job(job)
        elif job.status == JobStatus.FAILED:
            _render_failed_job(job)


def _render_pending_job(job):
    """Rendert einen wartenden Job"""
    st.info("Job wartet auf Ausführung")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Jetzt ausführen", key=f"run_{job.id}"):
            with st.spinner("Analyse läuft..."):
                success = executor.execute_job_sync(job.id)
                if success:
                    st.success("Analyse abgeschlossen!")
                else:
                    st.error("Analyse fehlgeschlagen")
            st.rerun()

    with col2:
        if st.button("🗑️ Abbrechen", key=f"cancel_{job.id}"):
            JobManager.cancel_job(job.id)
            st.rerun()


def _render_running_job(job):
    """Rendert einen laufenden Job"""
    st.warning("Analyse läuft...")
    st.progress(job.progress / 100)


def _render_completed_job(job):
    """Rendert einen abgeschlossenen Job"""
    results = JobManager.get_results_for_job(job.id)

    if not results:
        st.warning("Keine Ergebnisse gefunden")
        return

    result = results[0]

    # Zusammenfassung
    st.markdown(f"### {result.summary}")

    # Konfidenz
    if result.confidence:
        conf_percent = result.confidence * 100
        st.progress(min(result.confidence, 1.0))
        st.caption(f"Konfidenz: {conf_percent:.1f}%")

    # Details
    if result.data:
        with st.expander("📊 Details", expanded=False):
            _render_result_details(result.data)

    # Erkannte Muster (deskriptiv, keine Empfehlung)
    if result.signals:
        with st.expander("📈 Erkannte Muster", expanded=False):
            st.caption(
                "Historische Muster — keine Kauf-/Verkaufsempfehlung."
            )
            for signal in result.signals:
                signal_type = signal.get('type', 'hold')
                emoji = (
                    "🟢" if signal_type in ('buy', 'bullish')
                    else "🔴" if signal_type in ('sell', 'bearish')
                    else "🟡"
                )
                label = signal.get('indicator', 'Muster')
                st.markdown(f"{emoji} **{label}**: {signal.get('description', '')}")

    # Lösch-Button
    if st.button("🗑️ Löschen", key=f"delete_{job.id}"):
        JobManager.delete_job(job.id)
        st.rerun()


def _render_failed_job(job):
    """Rendert einen fehlgeschlagenen Job"""
    st.error(f"Fehler: {job.error_message or 'Unbekannter Fehler'}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Wiederholen", key=f"retry_{job.id}"):
            # Neuen Job erstellen
            new_id = JobManager.create_job(job.symbol, job.analysis_type, job.parameters)
            JobManager.delete_job(job.id)
            st.success(f"Neuer Auftrag #{new_id} erstellt")
            st.rerun()

    with col2:
        if st.button("🗑️ Löschen", key=f"del_fail_{job.id}"):
            JobManager.delete_job(job.id)
            st.rerun()


def _render_result_details(data: Dict):
    """Rendert die Detail-Daten eines Ergebnisses"""
    # Formatierte Anzeige der Daten
    for key, value in data.items():
        if isinstance(value, dict):
            st.markdown(f"**{key}:**")
            for sub_key, sub_value in value.items():
                st.markdown(f"  - {sub_key}: {_format_value(sub_value)}")
        elif isinstance(value, list):
            st.markdown(f"**{key}:** ({len(value)} Einträge)")
        else:
            st.markdown(f"**{key}:** {_format_value(value)}")


def _format_value(value) -> str:
    """Formatiert einen Wert für die Anzeige"""
    if isinstance(value, float):
        if abs(value) < 0.01:
            return f"{value:.4f}"
        elif abs(value) > 1000000:
            return f"{value:,.0f}"
        else:
            return f"{value:.2f}"
    return str(value)
