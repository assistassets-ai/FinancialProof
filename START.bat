@echo off
chcp 65001 >nul
title FinancialProof - Starten...

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                   FINANCIALPROOF                          ║
echo  ║           Historische Markt- und Musteranalyse            ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

REM Zum Skript-Verzeichnis wechseln
cd /d "%~dp0"

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert oder nicht im PATH.
    echo          Bitte installiere Python 3.9+ von https://python.org
    echo.
    pause
    exit /b 1
)

REM Prüfen ob venv existiert
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Virtuelle Umgebung wird erstellt...
    python -m venv venv
    if errorlevel 1 (
        echo [FEHLER] Konnte virtuelle Umgebung nicht erstellen.
        pause
        exit /b 1
    )
    echo [OK] Virtuelle Umgebung erstellt.
    echo.
)

REM Virtuelle Umgebung aktivieren
call venv\Scripts\activate.bat

REM Prüfen ob Abhängigkeiten installiert sind
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo [INFO] Abhängigkeiten werden installiert...
    echo        Dies kann einige Minuten dauern...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [FEHLER] Konnte Abhängigkeiten nicht installieren.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Abhängigkeiten installiert.
    echo.
)

REM Prüfen ob .env existiert
if not exist ".env" (
    if exist "env.example" (
        echo [WARNUNG] Keine .env Datei gefunden.
        echo           Kopiere env.example nach .env und passe die Werte an.
        echo.
        copy env.example .env >nul
        echo [INFO] .env wurde aus env.example erstellt.
        echo        API-Keys werden in der App lokal gespeichert.
        echo.
    )
)

REM Streamlit App starten
echo [START] FinancialProof wird gestartet...
echo         Browser öffnet sich automatisch unter http://localhost:8501
echo.
echo         Zum Beenden: Strg+C drücken
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

streamlit run app.py

REM Nach Beendigung
echo.
echo [ENDE] FinancialProof wurde beendet.
pause
