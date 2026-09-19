@echo off
REM ===========================================================================
REM  ARENA - rodar testes automatizados
REM  Executa o suite de testes sem depender de Python externo.
REM ===========================================================================

setlocal
title ARENA - testes
cd /d "%~dp0"

set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython

where python >nul 2>&1 && (set "PYTHON=python" & goto :temPython)
where py >nul 2>&1 && (set "PYTHON=py" & goto :temPython)

echo.
echo   [AVISO] Python nao encontrado. Usando python.exe embutido no servidor.
echo   Os testes exigem Python 3.11+. Se falharem, rode com o Python do sistema.
echo.

:temPython
"%PYTHON%" "%~dp0servidor\tests\run.py"

echo.
pause
endlocal
