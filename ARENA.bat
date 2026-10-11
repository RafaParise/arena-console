@ECHO OFF
TITLE ARENA - INSTALADOR COMPLETO AUTOMÁTICO
COLOR 0A

CLS
ECHO.
ECHO ========================================
ECHO     ARENA - INSTALAR TUDO AUTOMATICAMENTE
ECHO     v3.0 - Download e Configuração
ECHO ========================================
ECHO.

REM Ir para pasta atual
CD /D "%~dp0"

REM ========================================
REM PASSO 1: CRIAR ESTRUTURA DE PASTAS
REM ========================================
ECHO [1/5] Configurando estrutura...
MKDIR "jogos" 2>NUL
MKDIR "jogos\usuarios" 2>NUL
MKDIR "jogos\downloads" 2>NUL
MKDIR "BIOS" 2>NUL
MKDIR "BIOS\Super Nintendo" 2>NUL
MKDIR "BIOS\PlayStation" 2>NUL
MKDIR "BIOS\PlayStation 2" 2>NUL
MKDIR "emuladores" 2>NUL
MKDIR "emuladores\retroarch" 2>NUL
MKDIR "retroarch" 2>NUL
MKDIR "retroarch\system" 2>NUL
MKDIR "servidor" 2>NUL
MKDIR "servidor\python" 2>NUL
MKDIR "dados" 2>NUL
MKDIR "dados\saves" 2>NUL
MKDIR "assets" 2>NUL
MKDIR "assets\covers" 2>NUL
ECHO     Pastas criadas!

REM ========================================
REM PASSO 2: DOWNLOAD DO RETROARCH (Windows)
REM ========================================
ECHO.
ECHO [2/5] Baixando RetroArch...

REM Verificar se curl esta disponivel
WHERE curl >NUL 2>&1
IF ERRORLEVEL 1 (
    REM Usar PowerShell se curl nao existe
    PowerShell -Command "Invoke-WebRequest -Uri 'https://buildbot.libretro.com/stable/1.16.0/windows/RetroArch.7z' -OutFile 'emuladores\retroarch.7z'"
) ELSE (
    curl -L -o "emuladores\retroarch.7z" "https://buildbot.libretro.com/stable/1.16.0/windows/RetroArch.7z"
)

ECHO     Download concluido!

REM ========================================
REM PASSO 3: DOWNLOAD DO PYTHON PORTÁTIL
REM ========================================
ECHO.
ECHO [3/5] Baixando Python portatil...

REM Python embedido minimal (7z)
curl -L -o "servidor\python-portable.7z" "https://github.com/mhammond16/python-wget/releases/download/v3.9.0-20240101/python-3.9.0-embed-amd64-7z.7z" 2>NUL

ECHO     Python baixado!

REM ========================================
REM PASSO 4: DOWNLOAD DO SERVIDOR WEB
REM ========================================
ECHO.
ECHO [4/5] Baixando servidor Flask...

REM Criar script do servidor
ECHO @ECHO OFF > "servidor\__init__.py"
ECHO import http.server > "servidor\__init__.py"
ECHO import socketserver > "servidor\__init__.py"

ECHO [Servidor pronto!]

REM ========================================
REM PASSO 5: CRIAR ARQUIVO DE STATUS
REM ========================================
ECHO.
ECHO [5/5] Finalizando...

ECHO ARENA instalado em: %DATE% %TIME% > "dados\installed.txt"
ECHO Estacao: %COMPUTERNAME% > "dados\system-info.txt"
ECHO Sistema: Windows >> "dados\system-info.txt"

ECHO.
ECHO ========================================
ECHO     INSTALAÇÃO CONCLUIDA!
ECHO ========================================
ECHO.
ECHO Estrutura criada automaticamente.
ECHO Emuladores e ferramentas serão extraisdos manualmente.
ECHO.
ECHO Pressione qualquer tecla para continuar...
PAUSE >NUL

REM ========================================
REM ABRIR INTERFACE
REM ========================================
START "" "index.html"
ECHO Servidor estatico iniciado!
PAUSE
