@echo off
REM ===========================================================================
REM  ARENA - verificar e reparar
REM  Confere a instalacao e conserta o que der para consertar sozinho.
REM  Nunca apaga jogo, save nem save state.
REM ===========================================================================

setlocal
title ARENA - verificar e reparar
cd /d "%~dp0"

set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython
where python >nul 2>&1 && (set "PYTHON=python" & goto :temPython)
where py     >nul 2>&1 && (set "PYTHON=py"     & goto :temPython)

echo.
echo   [ERRO] O Python nao foi encontrado.
echo   Veja o documento 2 - INSTALACAO, passo 2.
echo.
pause
exit /b 1

:temPython
"%PYTHON%" "%~dp0servidor\diagnostico.py" %*
echo.
pause
endlocal
