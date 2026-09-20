@echo off
REM ===========================================================================
REM  ARENA - verificador rapido
REM  Checa se tudo necessario para rodar o ARENA esta no lugar.
REM  Para ver todos os detalhes:  python servidor\diagnostico.py
REM  Para rodar os testes:        python servidor\tests\run.py
REM ===========================================================================

setlocal
title ARENA - verificador
cd /d "%~dp0"

set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython

where python >nul 2>&1 && (set "PYTHON=python" & goto :temPython)
where py >nul 2>&1 && (set "PYTHON=py" & goto :temPython)

echo.
echo   [AVISO] Python nao encontrado. Usando python.exe embutido no servidor.
echo.

:temPython

echo.
echo   Verificando...
echo.

"%PYTHON%" "%~dp0servidor\diagnostico.py" --so-ver

echo.
echo   ---
echo   Para testes automatizados clique em:  RODAR_TESTES.bat
echo.

pause
endlocal
