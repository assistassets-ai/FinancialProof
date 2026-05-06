"""
FinancialProof - Job Queue UI Komponente
Übersicht über alle Analyse-Aufträge
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import texts
from jobs.manager import JobManager
from jobs.executor import executor
from core.database import JobStatus


def render_job_queue():
    """Rendert die Job-Queue Übersicht"""
    st.header("📋 Auftrags-Übersicht")

    # Statistiken
    _render_job_statistics()

    st.markdown("---")

    # Tabs für verschiedene Status
    tab_all, tab_pending, tab_completed, tab_failed = st.tabs([
        "Alle",
        f"⏳ Wartend",
        f"✅ Abgeschlossen",
        f"❌ Fehlgeschlagen"
    ])

    with tab_all:
        _render_job_list(None)

    with tab_pending:
        _render_job_list(JobStatus.PENDING)

    with tab_completed:
        _render_job_list(JobStatus.COMPLETED)

    with tab_failed:
        _render_job_list(JobStatus.FAILED)


def _render_job_statistics():
    """Rendert die Job-Statistiken"""
    stats = JobManager.get_job_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Wartend", stats.get('pending', 0))

    with col2:
        st.metric("Läuft", stats.get('running', 0))

    with col3:
        st.metric("Abgeschlossen", stats.get('completed', 0))

    with col4:
        st.metric("Fehlgeschlagen", stats.get('failed', 0))

    # Aktionen
    col1, col2, col3 = st.columns(3)

    with col1:
        pending_count = stats.get('pending', 0)
        if pending_count > 0:
            if st.button(f"▶️ Alle {pending_count} ausführen", width="stretch"):
                with st.spinner(f"Führe {pending_count} Analysen aus..."):
                    import asyncio
                    import concurrent.futures
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    if loop and loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = pool.submit(asyncio.run, executor.execute_all_pending(max_jobs=pending_count))
                            result = future.result()
                    else:
                        result = asyncio.run(executor.execute_all_pending(max_jobs=pending_count))
                    st.success(
                        f"Fertig: {result['completed']} erfolgreich, "
                        f"{result['failed']} fehlgeschlagen"
                    )
                st.rerun()

    with col2:
        if stats.get('completed', 0) > 0 or stats.get('failed', 0) > 0:
            if st.button("🧹 Alte Jobs bereinigen", width="stretch"):
                _cleanup_old_jobs()

    with col3:
        if st.button("🔄 Aktualisieren", width="stretch"):
            st.rerun()


def _render_job_list(status_filter: JobStatus = None):
    """Rendert eine Liste von Jobs"""
    if status_filter:
        if status_filter == JobStatus.PENDING:
            jobs = JobManager.get_pending_jobs(limit=50)
        elif status_filter == JobStatus.COMPLETED:
            jobs = JobManager.get_completed_jobs(limit=50)
        else:
            jobs = [j for j in JobManager.get_all_jobs(limit=50) if j.status == status_filter]
    else:
        jobs = JobManager.get_all_jobs(limit=50)

    if not jobs:
        st.info("Keine Jobs vorhanden")
        return

    # Als Tabelle anzeigen
    job_data = []
    for job in jobs:
        job_data.append({
            'ID': job.id,
            'Symbol': job.symbol,
            'Analyse': job.analysis_type,
            'Status': _get_status_display(job.status),
            'Erstellt': _format_datetime(job.created_at),
            'Abgeschlossen': _format_datetime(job.completed_at) if job.completed_at else '-'
        })

    df = pd.DataFrame(job_data)
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            'ID': st.column_config.NumberColumn(width="small"),
            'Status': st.column_config.TextColumn(width="medium")
        }
    )

    # Bulk-Aktionen
    if status_filter == JobStatus.PENDING and jobs:
        st.markdown("### Bulk-Aktionen")
        selected = st.multiselect(
            "Jobs auswählen",
            options=[j.id for j in jobs],
            format_func=lambda x: f"#{x} - {next(j for j in jobs if j.id == x).analysis_type}"
        )

        if selected:
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"▶️ {len(selected)} ausführen"):
                    with st.spinner("Führe Analysen aus..."):
                        for job_id in selected:
                            executor.execute_job_sync(job_id)
                    st.rerun()

            with col2:
                if st.button(f"🗑️ {len(selected)} abbrechen"):
                    for job_id in selected:
                        JobManager.cancel_job(job_id)
                    st.rerun()


def _get_status_display(status: JobStatus) -> str:
    """Gibt den Status als lesbare Zeichenkette zurück"""
    status_map = {
        JobStatus.PENDING: "⏳ Wartend",
        JobStatus.RUNNING: "🔄 Läuft",
        JobStatus.COMPLETED: "✅ Abgeschlossen",
        JobStatus.FAILED: "❌ Fehlgeschlagen",
        JobStatus.CANCELLED: "🚫 Abgebrochen"
    }
    return status_map.get(status, str(status))


def _format_datetime(dt) -> str:
    """Formatiert ein Datetime-Objekt"""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return dt

    if isinstance(dt, datetime):
        return dt.strftime("%d.%m.%Y %H:%M")
    return str(dt)


def _cleanup_old_jobs():
    """Bereinigt alte Jobs"""
    completed = JobManager.get_completed_jobs(limit=100)
    failed = [j for j in JobManager.get_all_jobs(limit=100) if j.status == JobStatus.FAILED]

    count = 0
    for job in completed[20:]:  # Behalte die letzten 20
        JobManager.delete_job(job.id)
        count += 1

    for job in failed[10:]:  # Behalte die letzten 10
        JobManager.delete_job(job.id)
        count += 1

    if count > 0:
        st.success(f"{count} alte Jobs gelöscht")
    else:
        st.info("Keine alten Jobs zu bereinigen")

    st.rerun()
