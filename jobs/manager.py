"""
FinancialProof - Job Manager
Verwaltet Analyse-Aufträge und deren Status
"""
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db, Job, JobStatus, AnalysisResult as DBResult


class JobManager:
    """
    Verwaltet den Lebenszyklus von Analyse-Aufträgen.

    Erstellt, aktualisiert und löscht Jobs in der Datenbank.
    """

    @staticmethod
    def create_job(
        symbol: str,
        analysis_type: str,
        parameters: Optional[Dict] = None
    ) -> int:
        """
        Erstellt einen neuen Analyse-Auftrag.

        Args:
            symbol: Das zu analysierende Symbol
            analysis_type: Name des Analyse-Typs
            parameters: Optionale Parameter für die Analyse

        Returns:
            Die Job-ID
        """
        job = Job(
            symbol=symbol.upper(),
            analysis_type=analysis_type,
            parameters=parameters,
            status=JobStatus.PENDING,
            progress=0
        )

        job_id = db.create_job(job)
        return job_id

    @staticmethod
    def create_multiple_jobs(
        symbol: str,
        analysis_types: List[str],
        parameters: Optional[Dict] = None
    ) -> List[int]:
        """
        Erstellt mehrere Jobs für ein Symbol.

        Args:
            symbol: Das zu analysierende Symbol
            analysis_types: Liste der Analyse-Typen
            parameters: Gemeinsame Parameter

        Returns:
            Liste der Job-IDs
        """
        job_ids = []
        for analysis_type in analysis_types:
            job_id = JobManager.create_job(symbol, analysis_type, parameters)
            job_ids.append(job_id)
        return job_ids

    @staticmethod
    def get_job(job_id: int) -> Optional[Job]:
        """Holt einen Job anhand der ID"""
        return db.get_job(job_id)

    @staticmethod
    def get_jobs_for_symbol(symbol: str, limit: int = 20) -> List[Job]:
        """Holt alle Jobs für ein bestimmtes Symbol"""
        return db.get_jobs(symbol=symbol, limit=limit)

    @staticmethod
    def get_pending_jobs(limit: int = 10) -> List[Job]:
        """Holt alle wartenden Jobs"""
        return db.get_jobs(status=JobStatus.PENDING, limit=limit)

    @staticmethod
    def get_running_jobs() -> List[Job]:
        """Holt alle laufenden Jobs"""
        return db.get_jobs(status=JobStatus.RUNNING, limit=100)

    @staticmethod
    def get_completed_jobs(limit: int = 20) -> List[Job]:
        """Holt alle abgeschlossenen Jobs"""
        return db.get_jobs(status=JobStatus.COMPLETED, limit=limit)

    @staticmethod
    def get_all_jobs(limit: int = 50) -> List[Job]:
        """Holt alle Jobs"""
        return db.get_jobs(limit=limit)

    @staticmethod
    def update_status(
        job_id: int,
        status: JobStatus,
        progress: int = None,
        error: str = None
    ):
        """
        Aktualisiert den Job-Status.

        Args:
            job_id: Die Job-ID
            status: Der neue Status
            progress: Optionaler Fortschritt (0-100)
            error: Optionale Fehlermeldung
        """
        db.update_job_status(job_id, status, progress, error)

    @staticmethod
    def start_job(job_id: int):
        """Markiert einen Job als gestartet"""
        db.update_job_status(job_id, JobStatus.RUNNING, progress=0)

    @staticmethod
    def complete_job(job_id: int):
        """Markiert einen Job als abgeschlossen"""
        db.update_job_status(job_id, JobStatus.COMPLETED, progress=100)

    @staticmethod
    def fail_job(job_id: int, error: str):
        """Markiert einen Job als fehlgeschlagen"""
        db.update_job_status(job_id, JobStatus.FAILED, error=error)

    @staticmethod
    def cancel_job(job_id: int):
        """Bricht einen Job ab (wenn noch möglich)"""
        job = db.get_job(job_id)
        if job and job.status == JobStatus.PENDING:
            db.update_job_status(job_id, JobStatus.CANCELLED)
            return True
        return False

    @staticmethod
    def delete_job(job_id: int):
        """Löscht einen Job und seine Ergebnisse"""
        db.delete_job(job_id)

    @staticmethod
    def save_result(
        job_id: int,
        result: Any  # AnalysisResult from analysis.base
    ):
        """
        Speichert das Analyse-Ergebnis.

        Args:
            job_id: Die Job-ID
            result: Das AnalysisResult-Objekt
        """
        db_result = DBResult(
            job_id=job_id,
            summary=result.summary,
            details=str(result.predictions) if result.predictions else None,
            data=result.data,
            signals=[s if isinstance(s, dict) else vars(s) for s in result.signals] if result.signals else None,
            confidence=result.confidence
        )

        db.save_result(db_result)

    @staticmethod
    def get_results_for_job(job_id: int) -> List[DBResult]:
        """Holt alle Ergebnisse für einen Job"""
        return db.get_results_for_job(job_id)

    @staticmethod
    def get_results_for_symbol(
        symbol: str,
        analysis_type: Optional[str] = None
    ) -> List[DBResult]:
        """Holt alle Ergebnisse für ein Symbol"""
        return db.get_results_for_symbol(symbol, analysis_type)

    @staticmethod
    def get_job_statistics() -> Dict[str, int]:
        """Gibt Statistiken über alle Jobs zurück"""
        return db.get_job_counts()

    @staticmethod
    def get_recent_activity(limit: int = 10) -> List[Dict]:
        """Holt die neuesten Aktivitäten"""
        return db.get_recent_activity(limit)


class JobQueue:
    """
    Verwaltet die Job-Warteschlange.

    Ermöglicht das Einfügen und Abholen von Jobs
    in der richtigen Reihenfolge.
    """

    def __init__(self):
        self._running_jobs: Dict[int, Any] = {}
        self._recover_stale_jobs()

    def _recover_stale_jobs(self):
        """
        Markiert Jobs, die beim letzten Programmstart noch RUNNING waren,
        als FAILED (Crash-Recovery).
        """
        stale_jobs = JobManager.get_running_jobs()
        for job in stale_jobs:
            JobManager.fail_job(
                job.id,
                error="Job unterbrochen: Prozess wurde unerwartet beendet (Crash-Recovery)"
            )

    def enqueue(
        self,
        symbol: str,
        analysis_type: str,
        parameters: Optional[Dict] = None
    ) -> int:
        """Fügt einen Job zur Warteschlange hinzu"""
        return JobManager.create_job(symbol, analysis_type, parameters)

    def dequeue(self) -> Optional[Job]:
        """Holt den nächsten Job aus der Warteschlange"""
        pending = JobManager.get_pending_jobs(limit=1)
        if pending:
            job = pending[0]
            JobManager.start_job(job.id)
            self._running_jobs[job.id] = job
            return job
        return None

    def get_queue_length(self) -> int:
        """Gibt die Anzahl der wartenden Jobs zurück"""
        stats = JobManager.get_job_statistics()
        return stats.get('pending', 0)

    def is_job_running(self, job_id: int) -> bool:
        """Prüft ob ein Job läuft (in-memory Cache + DB-Fallback)"""
        if job_id in self._running_jobs:
            return True
        job = JobManager.get_job(job_id)
        return job is not None and job.status == JobStatus.RUNNING

    def mark_complete(self, job_id: int, result: Any):
        """Markiert einen Job als abgeschlossen"""
        JobManager.save_result(job_id, result)
        JobManager.complete_job(job_id)
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]

    def mark_failed(self, job_id: int, error: str):
        """Markiert einen Job als fehlgeschlagen"""
        JobManager.fail_job(job_id, error)
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]


# Globale Instanz
job_queue = JobQueue()
