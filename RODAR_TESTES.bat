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

REM Orcamentos do notebook-alvo (docs\MAQUINA-ALVO.md secao 7), medidos no
REM modo alvo: o ARENA com os limites do Celeron da escola. Reprova dizendo
REM qual orcamento estourou -- e diz quando a medida nao vale (janela do
REM jogo coberta, bateria, saida de som segurando o ritmo).
echo.
echo   Agora os ORCAMENTOS no modo alvo: o ARENA com os limites do notebook
echo   da escola. Leva uns 8 minutos, abre a tela e um jogo de Super Nintendo
echo   (deixe a janela do jogo na frente).
choice /c SN /n /m "  Rodar agora? [S/N] "
if errorlevel 2 goto :fim
"%PYTHON%" "%~dp0testes\teste_orcamentos_modo_alvo.py"

:fim
echo.
pause
endlocal
