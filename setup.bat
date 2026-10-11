@echo off
title ARENA - Configuração Automática
color 0A
cls

echo.
echo ========================================
echo    ARENA - Configuração Automática
echo ========================================
echo.
echo Configurando estrutura do projeto...
echo.

REM Verificar se está na pasta correta
if not exist "ARENA.bat" (
    echo ERRO: Este script deve ser executado na pasta ARENA-unificado
    echo Atualize: jogos/usuarios/SeuNome/
    timeout /t 3 >nul
    exit /b 1
)

echo 1. Verificando estrutura de pastas...

REM Criar pastas necessárias se não existirem
if not exist "jogos" (
    echo    Criando: jogos\
    mkdir "jogos"
)

if not exist "jogos\usuarios" (
    echo    Criando: jogos\usuarios\
    mkdir "jogos\usuarios"
)

if not exist "BIOS" (
    echo    Criando: BIOS\
    mkdir "BIOS"
)

if not exist "BIOS\Super Nintendo" (
    echo    Criando: BIOS\Super Nintendo\
    mkdir "BIOS\Super Nintendo"
)

if not exist "BIOS\PlayStation" (
    echo    Criando: BIOS\PlayStation\
    mkdir "BIOS\PlayStation"
)

if not exist "BIOS\PlayStation 2" (
    echo    Criando: BIOS\PlayStation 2\
    mkdir "BIOS\PlayStation 2"
)

if not exist "emuladores" (
    echo    Criando: emuladores\
    mkdir "emuladores"
)

if not exist "retroarch" (
    echo    Criando: retroarch\
    mkdir "retroarch"
)

if not exist "retroarch\system" (
    echo    Criando: retroarch\system\
    mkdir "retroarch\system"
)

if not exist "servidor" (
    echo    Criando: servidor\
    mkdir "servidor"
)

if not exist "data" (
    echo    Criando: data\
    mkdir "data"
)

echo.
echo 2. Verificando arquivos essenciais...

REM Criar arquivo de controle se não existir
if not exist "data\status.txt" (
    echo Status:Incompleto > "data\status.txt"
    echo    Criado: data\status.txt
)

REM Criar diretório para saves se não existir
if not exist "data\saves" (
    mkdir "data\saves"
    echo    Criado: data\saves\
)

echo.
echo ========================================
echo    CONFIGURAÇÃO CONCLUIDA!
echo ========================================
echo.
echo Estrutura criada com sucesso!
echo.
echo Próximos passos:
echo   1. Adicione jogos em: jogos/usuarios/SeuNome/
echo   2. Adicione BIOS em: BIOS/[console]/[regiao]/
echo   3. Execute: ARENA.bat para iniciar
echo.
pause