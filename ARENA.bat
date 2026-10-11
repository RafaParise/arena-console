@ECHO OFF
TITLE ARENA - Console de Jogos Portátil
COLOR 0A
SETLOCAL EnableDelayedExpansion

CLS
ECHO.
ECHO ========================================
ECHO     ARENA - Console de Jogos
ECHO     Configuração Automática Total
ECHO ========================================
ECHO.

REM ========================================
REM PASSO 1: CONFIGURAÇÃO DE PASTAS AUTOMÁTICA
REM ========================================
ECHO Configurando estrutura do projeto...

REM Detectar pasta atual
CD /D "%~dp0"

REM Criar pastas necessárias (sempre)
IF NOT EXIST "jogos" (
    MKDIR "jogos" >NUL 2>&1
    ECHO   Criado: jogos)

IF NOT EXIST "jogos\usuarios" (
    MKDIR "jogos\usuarios" >NUL 2>&1
    ECHO   Criado: jogos\usuarios)

IF NOT EXIST "BIOS" (
    MKDIR "BIOS" >NUL 2>&1
    ECHO   Criado: BIOS)

IF NOT EXIST "BIOS\Super Nintendo" MKDIR "BIOS\Super Nintendo" >NUL 2>&1
IF NOT EXIST "BIOS\PlayStation" MKDIR "BIOS\PlayStation" >NUL 2>&1
IF NOT EXIST "BIOS\PlayStation 2" MKDIR "BIOS\PlayStation 2" >NUL 2>&1

IF NOT EXIST "emuladores" (
    MKDIR "emuladores" >NUL 2>&1
    ECHO   Criado: emuladores)

IF NOT EXIST "retroarch" (
    MKDIR "retroarch" >NUL 2>&1
    ECHO   Criado: retroarch)

IF NOT EXIST "retroarch\system" MKDIR "retroarch\system" >NUL 2>&1

IF NOT EXIST "servidor" (
    MKDIR "servidor" >NUL 2>&1
    ECHO   Criado: servidor)

IF NOT EXIST "dados" (
    MKDIR "dados" >NUL 2>&1
    ECHO   Criado: dados)

IF NOT EXIST "dados\saves" MKDIR "dados\saves" >NUL 2>&1

REM Criar arquivo de status
IF NOT EXIST "dados\status.txt" (
    ECHO Status: Ativo > "dados\status.txt"
)

ECHO.
ECHO Estrutura configurada com sucesso!
ECHO.

REM ========================================
REM PASSO 2: INICIAR O SERVIDOR/APLICAÇÃO
REM ========================================
ECHO ========================================
ECHO     INICIANDO ARENA
ECHO ========================================
ECHO.

REM Verificar se há um index ou sistema web
IF EXIST "index.html" (
    START "" "index.html" 2>NUL
    ECHO Servidor web iniciado!
) ELSE (
    ECHO.
    ECHO ARENA esta pronto para uso!
    ECHO.
    ECHO Pastas criadas:
    ECHO   - jogos/usuarios/ (adicione seus jogos aqui)
    ECHO   - BIOS/[console]/[regiao]/ (adicione BIOS aqui)
    ECHO   - dados/saves/ (saves automáticos)
    ECHO.
)

REM ========================================
REM PASSO 3: MENSAGEM FINAL
REM ========================================
ECHO ========================================
ECHO    CONFIGURAÇÃO CONCLUIDA!
ECHO ========================================
ECHO.
ECHO Pronto para usar!
ECHO.
ECHO Para sair: Feche esta janela
ECHO.
PAUSE >NUL
EXIT
