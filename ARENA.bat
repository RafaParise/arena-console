@ECHO OFF
TITLE ARENA - Instalador e Servidor Portátil
COLOR 0A

CLS
ECHO.
ECHO ========================================
ECHO     ARENA - CONSOLE DE JOGOS RETRO
ECHO     INSTALADOR COMPLETO v2.0
ECHO ========================================
ECHO.

REM ============================================================
REM PASSO 1: CONFIGURAÇÃO DE PASTAS AUTOMÁTICA
REM ============================================================
ECHO [+] Configurando estrutura...

CD /D "%~dp0"

REM Criar pastas necessárias
FOR %%F IN ("jogos" "jogos\usuarios" "BIOS" "BIOS\Super Nintendo" "BIOS\PlayStation" "BIOS\PlayStation 2" "emuladores" "retroarch" "retroarch\system" "servidor" "dados" "dados\saves") DO (
    IF NOT EXIST "%%F" MKDIR "%%F" >NUL 2>&1
)

REM Criar arquivo de status
IF NOT EXIST "dados\status.txt" ECHO Status: Ativo > "dados\status.txt"

ECHO   Pastas criadas com sucesso!

REM ============================================================
REM PASSO 2: VERIFICAR/BAIXAR PYTHON PORTÁTIL
REM ============================================================
ECHO.
ECHO [+] Verificando Python...

IF EXIST "python-portable" (
    ECHO   Python portátil encontrado
    SET PYTHON_EXE=python-portable\python.exe
    GOTO INICIAR
)

IF EXIST "servidor\python.exe" (
    ECHO   Python do servidor encontrado
    SET PYTHON_EXE=servidor\python.exe
    GOTO INICIAR
)

REM Verificar Python do sistema
PYTHON --version >NUL 2>&1
IF NOT ERRORLEVEL 1 (
    ECHO   Python do sistema detectado
    SET PYTHON_EXE=python
    GOTO INICIAR
)

ECHO   Python não encontrado - o servidor estatico estara disponivel
GOTO ABRIR_INTERFACE

:INICIAR
ECHO   Python localizado: !PYTHON_EXE!

REM ============================================================
REM PASSO 3: INICIAR SERVIDOR WEB
REM ============================================================
ECHO.
ECHO [+] Iniciando servidor local...
ECHO.

START "" /B !PYTHON_EXE! -c "import http.server; import socketserver; PORT=8000; Handler=http.server.SimpleHTTPRequestHandler; httpd=socketserver.TCPServer(('',PORT),Handler); print(f'Servidor started at http://localhost:{PORT}'); httpd.serve_forever()" 2>NUL

TIMEOUT /T 2 >NUL

REM ============================================================
REM PASSO 4: ABRIR INTERFACE
REM ============================================================
:ABRIR_INTERFACE
START "" "http://localhost:8000" 2>NUL

ECHO.
ECHO ========================================
ECHO     ARENA INICIADO COM SUCESSO!
ECHO ========================================
ECHO.
ECHO Servidor rodando em: http://localhost:8000
ECHO.
ECHO Pastas criadas:
ECHO   - jogos/usuarios/
ECHO   - BIOS/[console]/[regiao]/
ECHO   - dados/saves/
ECHO.
ECHO Para adicionar jogos:
ECHO   Cole arquivos em: jogos/usuarios/SeuNome/
ECHO.
ECHO Pressione Ctrl+C para parar o servidor
ECHO.

REM Manter janela aberta
:LOOP
TIMEOUT /T 60 >NUL
GOTO LOOP
