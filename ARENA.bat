@echo off
title ARENA - Console de Jogos Portatil
color 0A
cls

echo.
echo ========================================
echo    ARENA - Console de Jogos Portatil
echo    v1.0 - Setup Automatico
echo ========================================
echo.
echo Iniciando configuracao...
echo.

REM Executar setup automatico
if exist "setup.bat" (
    call setup.bat
) else (
    echo Setup nao encontrado!
    timeout /t 2 >nul
)

echo.
echo ========================================
echo    INICIANDO ARENA
echo ========================================
echo.

REM Aguardar antes de continuar
timeout /t 1 >nul

echo Pronto! O ARENA esta configurado e pronto para uso!
echo.
echo Para adicionar jogos:
echo   jogos/usuarios/SeuNome/
echo.
echo Para adicionar BIOS:
echo   BIOS/[console]/[regiao]/
echo.
pause
