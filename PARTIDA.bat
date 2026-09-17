@echo off
REM ===========================================================================
REM  ARENA - por que a partida a dois nao conecta
REM  Rode nos DOIS computadores. Nao muda nada, so confere e explica.
REM
REM  Para conferir tambem o computador do colega:
REM     arraste este arquivo para o Prompt e digite o endereco dele no fim
REM ===========================================================================

setlocal
title ARENA - diagnostico da partida
cd /d "%~dp0"

set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython
where python >nul 2>&1 && (set "PYTHON=python" & goto :temPython)
where py     >nul 2>&1 && (set "PYTHON=py"     & goto :temPython)

echo.
echo   [ERRO] O Python nao foi encontrado. Veja o documento 1.
echo.
pause
exit /b 1

:temPython
"%PYTHON%" "%~dp0servidor\partida.py" %*
echo.
pause
endlocal
