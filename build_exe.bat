@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python wurde nicht gefunden. Bitte Python 3.9+ installieren.
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] PyInstaller ist nicht installiert.
    echo Bitte ausfuehren: python -m pip install pyinstaller
    pause
    exit /b 1
)

echo [INFO] Bereinige alte Build-Artefakte...
powershell -NoProfile -Command "Get-ChildItem -LiteralPath 'build','dist' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force"

echo [INFO] Baue FinancialProof.exe als Windows-Launcher...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name FinancialProof ^
  --specpath build ^
  --icon "%cd%\FinancialProof.ico" ^
  financialproof_launcher.py

if errorlevel 1 (
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

if exist "dist\FinancialProof.exe" copy /Y "dist\FinancialProof.exe" "FinancialProof.exe" >nul

echo.
echo [OK] Build fertig: dist\FinancialProof.exe
echo [OK] Kopie aktualisiert: FinancialProof.exe
echo [HINWEIS] Der Launcher erwartet eine lokale Python-Umgebung mit den Abhaengigkeiten aus requirements.txt.
