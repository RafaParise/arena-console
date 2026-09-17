@echo off
REM ===========================================================================
REM  ARENA - ponto de entrada unico
REM
REM  %~dp0 e a pasta onde ESTE arquivo esta, com a barra no final.
REM  Tudo abaixo se ancora nela, entao a letra do drive pode mudar
REM  (E:, G:, F:) que continua funcionando. Nao existe caminho fixo aqui.
REM ===========================================================================

setlocal enabledelayedexpansion
title ARENA - servidor local
cd /d "%~dp0"

echo.
echo   ARENA
echo   Iniciando. Nao feche esta janela enquanto estiver jogando.
echo.

REM --- 1. Python que veio junto na pasta -------------------------------------
set "PYTHON=%~dp0servidor\python\python.exe"
if exist "%PYTHON%" goto :temPython

REM --- 2. Nao veio junto? Tenta o Python instalado no computador --------------
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
    goto :temPython
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py"
    goto :temPython
)

echo   [ERRO] O Python nao foi encontrado.
echo.
echo   Como resolver, escolha uma das duas:
echo     a^) Descompacte o pacote "python embeddable" em servidor\python
echo        de modo que exista o arquivo servidor\python\python.exe
echo     b^) Instale o Python neste computador, marcando "Add to PATH"
echo.
pause
exit /b 1

:temPython

REM --- 3. Confere se o RetroArch esta no lugar --------------------------------
if not exist "%~dp0retroarch\retroarch.exe" (
    echo   [AVISO] retroarch.exe nao encontrado em .\retroarch
    echo           O ARENA vai abrir, mas nenhum jogo vai iniciar.
    echo.
)

REM --- 4. Sobe o servidor. Ele abre o navegador sozinho -----------------------
"%PYTHON%" "%~dp0servidor\arena.py"
set "SAIDA=%errorlevel%"

echo.
if not "%SAIDA%"=="0" (
    echo   O ARENA fechou com erro. A mensagem acima explica o motivo.
) else (
    echo   ARENA encerrado.
)
pause
endlocal
