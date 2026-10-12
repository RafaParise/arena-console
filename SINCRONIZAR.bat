@echo off
REM ===========================================================================
REM  ARENA - sincronizar com o GitHub (para quem desenvolve o ARENA)
REM  Puxa o que os outros computadores enviaram e envia o que foi feito aqui.
REM  Nunca junta sozinho o que nao tem commit. Detalhes: docs\SINCRONIZAR-COM-O-GITHUB.md
REM  Tambem:  SINCRONIZAR.bat estado | puxar | enviar
REM ===========================================================================

setlocal
title ARENA - sincronizar com o GitHub
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"

set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython
where python >nul 2>&1 && (set "PYTHON=python" & goto :temPython)
where py >nul 2>&1 && (set "PYTHON=py" & goto :temPython)
echo.
echo   Python nao encontrado (nem o embutido, em servidor\python).
echo.
pause
exit /b 1

:temPython
echo.
"%PYTHON%" "%~dp0ferramentas\sincronizar_github.py" %*
echo.
pause
endlocal
