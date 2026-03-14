"""
FinancialProof - Job Executor
Führt Analyse-Jobs aus
"""
import asyncio
from typing import Optional, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Job, JobStatus
from core.data_provider import DataProvider
from analysis.base import AnalysisParameters, AnalysisTimeframe
from analysis.registry import get_analyzer, ensure_initialized
from jobs.manager import JobManager


class JobExecutor:
    """
    Führt Analyse-Jobs aus.

    Lädt Daten, wählt den richtigen Analyzer und
    speichert die Ergebnisse.
    """

    def __init__(self):
        ensure_initialized()

    async def execute_job(self, job_id: int) -> bool:
        """
        Führt einen einzelnen Job aus.

        Args:
            job_id: Die Job-ID

        Returns:
            True wenn erfolgreich, False sonst
        """
        job = JobManager.get_job(job_id)
        if not job:
            return False

        if job.status != JobStatus.PENDING:
            return False

        try:
            # Job starten
            JobManager.start_job(job_id)
            JobManager.update_status(job_id, JobStatus.RUNNING, progress=5)

            # Daten laden
            data = DataProvider.get_market_data(job.symbol, period="1y")
            if data is None or data.empty:
                JobManager.fail_job(job_id, "Keine Marktdaten verfügbar")
                return False

            JobManager.update_status(job_id, JobStatus.RUNNING, progress=20)

            # Analyzer holen
            analyzer = get_analyzer(job.analysis_type)
            if analyzer is None:
                JobManager.fail_job(job_id, f"Analyzer '{job.analysis_type}' nicht gefunden")
                return False

            JobManager.update_status(job_id, JobStatus.RUNNING, progress=30)

            # Parameter vorbereiten
            timeframe = AnalysisTimeframe.MEDIUM
            if job.parameters and 'timeframe' in job.parameters:
                tf = job.parameters['timeframe']
                if tf in [t.value for t in AnalysisTimeframe]:
                    timeframe = AnalysisTimeframe(tf)

            params = AnalysisParameters(
                symbol=job.symbol,
                data=data,
                timeframe=timeframe,
                custom_params=job.parameters or {}
            )

            # Analyse durchführen
            JobManager.update_status(job_id, JobStatus.RUNNING, progress=40)
            result = await analyzer.analyze(params)

            JobManager.update_status(job_id, JobStatus.RUNNING, progress=90)

            # Ergebnis speichern
            JobManager.save_result(job_id, result)
            JobManager.complete_job(job_id)

            return True

        except Exception as e:
            JobManager.fail_job(job_id, str(e))
            return False

    def execute_job_sync(self, job_id: int) -> bool:
        """
        Synchrone Version von execute_job fuer Streamlit (Python 3.10+ sicher).

        Erstellt stets einen neuen Event-Loop in einem eigenen Thread.
        Vermeidet undefiniertes Verhalten bei vorhandenem laufenden Loop.

        Args:
            job_id: Die Job-ID

        Returns:
            True wenn erfolgreich, False sonst
        """
        import concurrent.futures

        def _run_in_new_loop() -> bool:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute_job(job_id))
            finally:
                loop.close()
                asyncio.set_event_loop(None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_new_loop)
            return future.result()

    async def execute_all_pending(self, max_jobs: int = 10) -> Dict[str, int]:
        """
        Führt alle wartenden Jobs aus.

        Args:
            max_jobs: Maximale Anzahl zu bearbeitender Jobs

        Returns:
            Dict mit 'completed', 'failed', 'total'
        """
        pending = JobManager.get_pending_jobs(limit=max_jobs)

        completed = 0
        failed = 0

        for job in pending:
            success = await self.execute_job(job.id)
            if success:
                completed += 1
            else:
                failed += 1

        return {
            'completed': completed,
            'failed': failed,
            'total': len(pending)
        }

    async def execute_for_symbol(
        self,
        symbol: str,
        analysis_types: list
    ) -> Dict[str, Any]:
        """
        Führt mehrere Analysen für ein Symbol aus.

        Args:
            symbol: Das Symbol
            analysis_types: Liste der Analyse-Typen

        Returns:
            Dict mit Ergebnissen pro Analyse-Typ
        """
        results = {}

        for analysis_type in analysis_types:
            # Job erstellen
            job_id = JobManager.create_job(symbol, analysis_type)

            # Ausführen
            success = await self.execute_job(job_id)

            if success:
                # Ergebnisse holen
                job_results = JobManager.get_results_for_job(job_id)
                if job_results:
                    results[analysis_type] = {
                        'success': True,
                        'job_id': job_id,
                        'summary': job_results[0].summary,
                        'confidence': job_results[0].confidence,
                        'data': job_results[0].data
                    }
                else:
                    results[analysis_type] = {
                        'success': True,
                        'job_id': job_id,
                        'summary': 'Keine Details verfügbar'
                    }
            else:
                job = JobManager.get_job(job_id)
                results[analysis_type] = {
                    'success': False,
                    'job_id': job_id,
                    'error': job.error_message if job else 'Unbekannter Fehler'
                }

        return results


class AutoMethodSelector:
    """
    Wählt automatisch die besten Analyse-Methoden.
    """

    def __init__(self):
        from analysis.base import method_selector
        self.selector = method_selector

    def select_and_execute(
        self,
        symbol: str,
        data=None
    ) -> Dict[str, Any]:
        """
        Wählt automatisch Methoden und führt sie aus.

        Args:
            symbol: Das Symbol
            data: Optionale Marktdaten (werden sonst geladen)

        Returns:
            Dict mit ausgewählten Methoden und Ergebnissen
        """
        if data is None:
            data = DataProvider.get_market_data(symbol, period="1y")

        if data is None or data.empty:
            return {'error': 'Keine Daten verfügbar'}

        # Verfügbare Methoden aus Registry
        from analysis.registry import AnalysisRegistry
        available = AnalysisRegistry.list_names()

        # Beste Methoden auswählen
        selected = self.selector.select_methods(data, available)

        return {
            'symbol': symbol,
            'selected_methods': selected,
            'available_methods': available,
            'selection_reason': self._get_selection_reasons(data)
        }

    def _get_selection_reasons(self, data) -> Dict[str, str]:
        """Gibt Begründungen für die Methodenauswahl zurück"""
        import numpy as np

        close = data['Close']
        returns = close.pct_change().dropna()

        volatility = returns.std() * np.sqrt(252)
        trend = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]

        reasons = {}

        if volatility > 0.3:
            reasons['monte_carlo'] = f'Hohe Volatilität ({volatility:.1%})'
        if abs(trend) > 0.1:
            reasons['arima'] = f'Starker Trend ({trend:+.1%} in 20 Tagen)'
        if abs(trend) < 0.05:
            reasons['mean_reversion'] = 'Seitwärtsbewegung erkannt'

        reasons['sentiment'] = 'Immer relevant für aktuelle Stimmung'

        return reasons


# Globale Instanzen
executor = JobExecutor()
auto_selector = AutoMethodSelector()
