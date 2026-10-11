@echo off
color 0A
cls
echo.
echo ========================================
echo    ARENA - Iniciando Servidor Local
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar se Python esta disponivel
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Encontrado Python instalado
    echo Iniciando servidor...
    python server_startup.py
) else (
    REM Verificar se ha Python embutido
    if exist "python_embedded" (
        echo Usando Python embutido
        "python_embedded\python.exe" server_startup.py
    ) else if exist "servidor\python" (
        echo Usando Python do servidor
        "servidor\python\python.exe" server_startup.py
    ) else (
        echo Servidor estatico disponivel
        echo Abra o index.html diretamente
    )
)

pause
