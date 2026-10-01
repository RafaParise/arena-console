@echo off
REM ===========================================================================
REM  ARENA - coleta do perfil desta maquina
REM
REM  Roda os dois coletores em sequencia:
REM    1. ferramentas\coletar_maquina.py  - retrato da maquina (~15 s)
REM    2. ferramentas\medir_arena.py      - o ARENA rodando nela (~6 min)
REM  e guarda tudo em perfil\<codigo>_<data-hora>\ (um .json para analise e
REM  um .txt em portugues para ler na hora).
REM
REM  Nao precisa de internet nem de administrador, e nao muda nada do ARENA.
REM  Tudo se ancora em %~dp0 (a pasta deste arquivo): funciona com qualquer
REM  letra de pen drive.
REM ===========================================================================

setlocal
title ARENA - coleta do perfil desta maquina
cd /d "%~dp0"

echo.
echo   ARENA - COLETA DO PERFIL DESTA MAQUINA
echo.
echo   Leva uns 6 minutos. O ARENA abre e fecha sozinho, e no meio um jogo
echo   de Super Nintendo roda por uns 70 segundos: e de proposito. Deixe a
echo   janela do jogo NA FRENTE e nao use o computador ate o fim. No fim,
echo   6 perguntas rapidas (e mais algumas, se voce ja jogou outros
echo   consoles neste notebook).
echo.
echo   Antes de comecar: FECHE o ARENA, se estiver aberto, e ligue o
echo   notebook NA TOMADA (na bateria o resultado nao vale).
echo   Nada pessoal e coletado (nem nome, nem usuario).
echo.
pause

if /i "%PROCESSOR_ARCHITECTURE%"=="x86" if not defined PROCESSOR_ARCHITEW6432 (
    echo.
    echo   [ERRO] Este Windows e de 32 bits: o Python do ARENA ^(64 bits^) nao
    echo   roda aqui. Anote isso: esta maquina nao serve para o ARENA.
    echo.
    pause
    exit /b 1
)

set "PYTHON=%~dp0servidor\python\python.exe"
if not exist "%PYTHON%" (
    echo.
    echo   [ERRO] Nao achei servidor\python\python.exe. A coleta usa o Python
    echo   do proprio ARENA; confira se a pasta do ARENA esta completa.
    echo.
    pause
    exit /b 1
)

echo.
echo   === 1 de 2: retrato da maquina ===
echo.
"%PYTHON%" "%~dp0ferramentas\coletar_maquina.py"
if errorlevel 1 echo   [AVISO] O retrato da maquina terminou com erro; seguindo mesmo assim.

echo.
echo   === 2 de 2: o ARENA rodando nesta maquina ===
echo.
"%PYTHON%" "%~dp0ferramentas\medir_arena.py"
if errorlevel 1 echo   [AVISO] As medicoes terminaram com erro; o que deu para medir foi salvo.

set "PASTA="
if exist "%~dp0perfil\ultima_coleta.txt" set /p PASTA=<"%~dp0perfil\ultima_coleta.txt"

echo.
echo   ======================================================================
echo   Pronto. Os resultados ficaram em:
echo     %~dp0perfil\%PASTA%
echo.
echo   maquina.txt e arena.txt = resumo em portugues, para ler agora
echo   (o arena.txt termina na tabela de tetos: medido, teto, passou).
echo   maquina.json e arena.json = para analise depois.
echo   Leve a pasta perfil inteira no pen drive.
echo   ======================================================================
echo.
pause
endlocal
