from __future__ import annotations

import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List, Optional


APP_NAME = "FinancialProof"
SCRIPT_NAME = "app.py"


def _project_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _show_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    except Exception:
        print(message, file=sys.stderr)


def _python_command() -> Optional[List[str]]:
    for candidate in ("pythonw.exe", "python.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved]
    launcher = shutil.which("py.exe") or shutil.which("py")
    if launcher:
        return [launcher, "-3"]
    return None


def _streamlit_available(python_cmd: List[str]) -> bool:
    check = python_cmd + ["-c", "import streamlit"]
    try:
        result = subprocess.run(
            check,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def main() -> int:
    base_dir = _project_dir()
    app_script = base_dir / SCRIPT_NAME
    if not app_script.exists():
        _show_error(f"{SCRIPT_NAME} wurde nicht gefunden:\n{app_script}")
        return 1

    python_cmd = _python_command()
    if not python_cmd:
        _show_error(
            "Python wurde nicht gefunden.\n"
            "Bitte Python 3.9+ installieren und die Abhängigkeiten aus requirements.txt einrichten."
        )
        return 1

    if not _streamlit_available(python_cmd):
        _show_error(
            "Streamlit wurde in der gefundenen Python-Umgebung nicht gefunden.\n"
            "Bitte im Projektordner ausführen: python -m pip install -r requirements.txt"
        )
        return 1

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    command = python_cmd + [
        "-m",
        "streamlit",
        "run",
        str(app_script),
        "--server.headless",
        "false",
    ]

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            command,
            cwd=str(base_dir),
            env=env,
            creationflags=creationflags,
        )
    except FileNotFoundError as exc:
        _show_error(f"Start fehlgeschlagen:\n{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
