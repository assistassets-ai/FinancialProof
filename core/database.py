"""
FinancialProof - Datenbank-Modul
SQLite-Datenbank für Watchlist, Jobs und Analyse-Ergebnisse
"""
import sqlite3
import json
from datetime import datetime
from typing import Any, Optional, List, Dict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# Füge das Hauptverzeichnis zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


class JobStatus(str, Enum):
    """Status eines Analyse-Auftrags"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WatchlistItem:
    """Ein Asset in der Watchlist"""
    id: Optional[int] = None
    symbol: str = ""
    name: str = ""
    asset_type: str = "stock"  # stock, etf, fund, crypto
    sector: Optional[str] = None
    notes: Optional[str] = None
    added_at: Optional[datetime] = None


@dataclass
class Job:
    """Ein Analyse-Auftrag"""
    id: Optional[int] = None
    symbol: str = ""
    analysis_type: str = ""
    parameters: Optional[Dict] = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class AnalysisResult:
    """Ergebnis einer Analyse"""
    id: Optional[int] = None
    job_id: int = 0
    summary: str = ""
    details: Optional[str] = None
    data: Optional[Dict] = None
    signals: Optional[List[Dict]] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None


@dataclass
class StrategyPreset:
    """Ein Analyse-Preset fuer historische Musterbewertungen."""
    id: Optional[int] = None
    name: str = ""
    asset_type: str = "STOCK"
    rules: Optional[Dict[str, Any]] = None
    is_active: bool = False
    created_at: Optional[datetime] = None


@dataclass
class AnalysisRun:
    """Eine protokollierte Auswertung eines Analyse-Presets."""
    id: Optional[int] = None
    symbol: str = ""
    strategy_id: Optional[int] = None
    job_id: Optional[int] = None
    pattern_class: str = "neutral"
    notes: Optional[str] = None
    evaluated_at: Optional[datetime] = None


class DatabaseManager:
    """Verwaltet die SQLite-Datenbank"""

    def __init__(self):
        self.db_path = config.DB_PATH
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Context Manager für Datenbankverbindungen"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """Initialisiert die Datenbank mit dem Schema"""
        statements = [
            # Beobachtete Assets (Watchlist)
            """CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT,
                asset_type TEXT DEFAULT 'stock',
                sector TEXT,
                notes TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # Portfolio-Positionen
            """CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL,
                avg_buy_price REAL,
                buy_date DATE,
                FOREIGN KEY (symbol) REFERENCES watchlist(symbol) ON DELETE CASCADE
            )""",
            # Analyse-Aufträge
            """CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )""",
            # Analyse-Ergebnisse
            """CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                summary TEXT,
                details TEXT,
                data TEXT,
                signals TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )""",
            # Indices für Performance
            "CREATE INDEX IF NOT EXISTS idx_jobs_symbol ON jobs(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
            """CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                asset_type TEXT NOT NULL,
                rules_json TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                strategy_id INTEGER,
                job_id INTEGER,
                pattern_class TEXT NOT NULL,
                notes TEXT,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE SET NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
            )""",
            "CREATE INDEX IF NOT EXISTS idx_results_job ON results(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_strategies_asset_type ON strategies(asset_type)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_runs_symbol ON analysis_runs(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_runs_strategy_id ON analysis_runs(strategy_id)",
        ]

        with self.get_connection() as conn:
            for stmt in statements:
                conn.execute(stmt)

    # ===== WATCHLIST OPERATIONEN =====

    def add_to_watchlist(self, item: WatchlistItem) -> int:
        """Fügt ein Asset zur Watchlist hinzu"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT OR REPLACE INTO watchlist
                   (symbol, name, asset_type, sector, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (item.symbol.upper(), item.name, item.asset_type,
                 item.sector, item.notes)
            )
            return cursor.lastrowid

    def remove_from_watchlist(self, symbol: str):
        """Entfernt ein Asset aus der Watchlist"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))

    def get_watchlist(self) -> List[WatchlistItem]:
        """Gibt alle Assets in der Watchlist zurück"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watchlist ORDER BY added_at DESC"
            ).fetchall()
            return [WatchlistItem(
                id=row['id'],
                symbol=row['symbol'],
                name=row['name'],
                asset_type=row['asset_type'],
                sector=row['sector'],
                notes=row['notes'],
                added_at=row['added_at']
            ) for row in rows]

    def get_watchlist_item(self, symbol: str) -> Optional[WatchlistItem]:
        """Holt ein einzelnes Watchlist-Item"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM watchlist WHERE symbol = ?", (symbol.upper(),)
            ).fetchone()
            if row:
                return WatchlistItem(
                    id=row['id'],
                    symbol=row['symbol'],
                    name=row['name'],
                    asset_type=row['asset_type'],
                    sector=row['sector'],
                    notes=row['notes'],
                    added_at=row['added_at']
                )
            return None

    def is_in_watchlist(self, symbol: str) -> bool:
        """Prüft ob ein Symbol in der Watchlist ist"""
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT 1 FROM watchlist WHERE symbol = ?", (symbol.upper(),)
            ).fetchone()
            return result is not None

    def update_watchlist_notes(self, symbol: str, notes: str):
        """Aktualisiert Notizen für ein Watchlist-Item"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE watchlist SET notes = ? WHERE symbol = ?",
                (notes, symbol.upper())
            )

    # ===== JOB OPERATIONEN =====

    def create_job(self, job: Job) -> int:
        """Erstellt einen neuen Analyse-Auftrag"""
        params_json = json.dumps(job.parameters) if job.parameters else None
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO jobs (symbol, analysis_type, parameters, status, progress)
                   VALUES (?, ?, ?, ?, ?)""",
                (job.symbol.upper(), job.analysis_type, params_json,
                 job.status.value, job.progress)
            )
            return cursor.lastrowid

    def get_job(self, job_id: int) -> Optional[Job]:
        """Holt einen Job anhand der ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if row:
                return self._row_to_job(row)
            return None

    def get_jobs(self, symbol: Optional[str] = None,
                 status: Optional[JobStatus] = None,
                 limit: int = 50) -> List[Job]:
        """Holt Jobs mit optionalen Filtern"""
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol.upper())
        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_job(row) for row in rows]

    def update_job_status(self, job_id: int, status: JobStatus,
                          progress: int = None, error: str = None):
        """Aktualisiert den Status eines Jobs"""
        updates = ["status = ?"]
        params = [status.value]

        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)

        if status == JobStatus.RUNNING:
            updates.append("started_at = ?")
            params.append(datetime.now().isoformat())
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())

        if error:
            updates.append("error_message = ?")
            params.append(error)

        params.append(job_id)

        with self.get_connection() as conn:
            conn.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?",
                params
            )

    def delete_job(self, job_id: int):
        """Löscht einen Job und seine Ergebnisse"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM results WHERE job_id = ?", (job_id,))
            conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    def _row_to_job(self, row) -> Job:
        """Konvertiert eine DB-Zeile zu einem Job-Objekt"""
        params = json.loads(row['parameters']) if row['parameters'] else None
        return Job(
            id=row['id'],
            symbol=row['symbol'],
            analysis_type=row['analysis_type'],
            parameters=params,
            status=JobStatus(row['status']),
            progress=row['progress'],
            created_at=row['created_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            error_message=row['error_message']
        )

    # ===== RESULT OPERATIONEN =====

    def save_result(self, result: AnalysisResult) -> int:
        """Speichert ein Analyse-Ergebnis"""
        data_json = json.dumps(result.data) if result.data else None
        signals_json = json.dumps(result.signals) if result.signals else None

        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO results (job_id, summary, details, data, signals, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (result.job_id, result.summary, result.details,
                 data_json, signals_json, result.confidence)
            )
            return cursor.lastrowid

    def get_result(self, result_id: int) -> Optional[AnalysisResult]:
        """Holt ein Ergebnis anhand der ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM results WHERE id = ?", (result_id,)
            ).fetchone()
            if row:
                return self._row_to_result(row)
            return None

    def get_results_for_job(self, job_id: int) -> List[AnalysisResult]:
        """Holt alle Ergebnisse für einen Job"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM results WHERE job_id = ? ORDER BY created_at DESC",
                (job_id,)
            ).fetchall()
            return [self._row_to_result(row) for row in rows]

    def get_results_for_symbol(self, symbol: str,
                                analysis_type: Optional[str] = None,
                                limit: int = 20) -> List[AnalysisResult]:
        """Holt alle Ergebnisse für ein Symbol"""
        query = """
            SELECT r.* FROM results r
            JOIN jobs j ON r.job_id = j.id
            WHERE j.symbol = ?
        """
        params = [symbol.upper()]

        if analysis_type:
            query += " AND j.analysis_type = ?"
            params.append(analysis_type)

        query += " ORDER BY r.created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_result(row) for row in rows]

    def _row_to_result(self, row) -> AnalysisResult:
        """Konvertiert eine DB-Zeile zu einem Result-Objekt"""
        data = json.loads(row['data']) if row['data'] else None
        signals = json.loads(row['signals']) if row['signals'] else None
        return AnalysisResult(
            id=row['id'],
            job_id=row['job_id'],
            summary=row['summary'],
            details=row['details'],
            data=data,
            signals=signals,
            confidence=row['confidence'],
            created_at=row['created_at']
        )

    # ===== STRATEGIE OPERATIONEN =====

    def save_strategy(self, strategy: StrategyPreset) -> int:
        """Speichert oder aktualisiert ein Analyse-Preset."""
        asset_type = strategy.asset_type.upper()
        rules_json = json.dumps(
            strategy.rules or {},
            ensure_ascii=False,
            sort_keys=True,
        )

        with self.get_connection() as conn:
            if strategy.is_active:
                conn.execute(
                    "UPDATE strategies SET is_active = 0 WHERE asset_type = ? AND name <> ?",
                    (asset_type, strategy.name),
                )

            conn.execute(
                """INSERT INTO strategies (name, asset_type, rules_json, is_active)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       asset_type = excluded.asset_type,
                       rules_json = excluded.rules_json,
                       is_active = excluded.is_active""",
                (strategy.name, asset_type, rules_json, int(strategy.is_active)),
            )

            row = conn.execute(
                "SELECT id FROM strategies WHERE name = ?",
                (strategy.name,),
            ).fetchone()
            return int(row["id"])

    def get_strategy(self, strategy_id: int) -> Optional[StrategyPreset]:
        """Holt ein Analyse-Preset anhand der ID."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM strategies WHERE id = ?",
                (strategy_id,),
            ).fetchone()
            return self._row_to_strategy(row) if row else None

    def get_strategy_by_name(self, name: str) -> Optional[StrategyPreset]:
        """Holt ein Analyse-Preset anhand des Namens."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM strategies WHERE name = ?",
                (name,),
            ).fetchone()
            return self._row_to_strategy(row) if row else None

    def list_strategies(
        self,
        asset_type: Optional[str] = None,
        active_only: bool = False,
    ) -> List[StrategyPreset]:
        """Listet Analyse-Presets optional gefiltert."""
        query = "SELECT * FROM strategies WHERE 1=1"
        params: List[Any] = []

        if asset_type:
            query += " AND asset_type = ?"
            params.append(asset_type.upper())
        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY asset_type, name"

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_strategy(row) for row in rows]

    def get_active_strategy(self, asset_type: str) -> Optional[StrategyPreset]:
        """Holt das aktive Analyse-Preset fuer einen Asset-Typ."""
        with self.get_connection() as conn:
            row = conn.execute(
                """SELECT * FROM strategies
                   WHERE asset_type = ? AND is_active = 1
                   ORDER BY created_at DESC
                   LIMIT 1""",
                (asset_type.upper(),),
            ).fetchone()
            return self._row_to_strategy(row) if row else None

    def set_active_strategy(self, strategy_id: int) -> Optional[StrategyPreset]:
        """Aktiviert ein Analyse-Preset und deaktiviert andere desselben Asset-Typs."""
        preset = self.get_strategy(strategy_id)
        if preset is None:
            return None

        with self.get_connection() as conn:
            conn.execute(
                "UPDATE strategies SET is_active = 0 WHERE asset_type = ?",
                (preset.asset_type.upper(),),
            )
            conn.execute(
                "UPDATE strategies SET is_active = 1 WHERE id = ?",
                (strategy_id,),
            )

        return self.get_strategy(strategy_id)

    def delete_strategy(self, strategy_id: int):
        """Loescht ein Analyse-Preset."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))

    def _row_to_strategy(self, row) -> StrategyPreset:
        """Konvertiert eine DB-Zeile in ein Analyse-Preset."""
        try:
            rules = json.loads(row["rules_json"]) if row["rules_json"] else {}
        except json.JSONDecodeError:
            rules = {}

        return StrategyPreset(
            id=row["id"],
            name=row["name"],
            asset_type=row["asset_type"],
            rules=rules,
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    # ===== ANALYSE-RUN OPERATIONEN =====

    def save_analysis_run(self, run: AnalysisRun) -> int:
        """Speichert eine protokollierte Preset-Auswertung."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO analysis_runs
                   (symbol, strategy_id, job_id, pattern_class, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    run.symbol.upper(),
                    run.strategy_id,
                    run.job_id,
                    run.pattern_class,
                    run.notes,
                ),
            )
            return cursor.lastrowid

    def get_analysis_runs(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[AnalysisRun]:
        """Holt protokollierte Preset-Auswertungen."""
        query = "SELECT * FROM analysis_runs WHERE 1=1"
        params: List[Any] = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol.upper())
        if strategy_id is not None:
            query += " AND strategy_id = ?"
            params.append(strategy_id)

        query += " ORDER BY evaluated_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_analysis_run(row) for row in rows]

    def _row_to_analysis_run(self, row) -> AnalysisRun:
        """Konvertiert eine DB-Zeile in eine protokollierte Preset-Auswertung."""
        return AnalysisRun(
            id=row["id"],
            symbol=row["symbol"],
            strategy_id=row["strategy_id"],
            job_id=row["job_id"],
            pattern_class=row["pattern_class"],
            notes=row["notes"],
            evaluated_at=row["evaluated_at"],
        )

    # ===== STATISTIKEN =====

    def get_job_counts(self) -> Dict[str, int]:
        """Gibt Job-Zählungen nach Status zurück"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
            ).fetchall()
            return {row['status']: row['count'] for row in rows}

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Holt die neuesten Aktivitäten (Jobs + Ergebnisse)"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT j.id, j.symbol, j.analysis_type, j.status,
                       j.created_at, r.summary
                FROM jobs j
                LEFT JOIN results r ON j.id = r.job_id
                ORDER BY j.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]


# Singleton-Instanz
db = DatabaseManager()
