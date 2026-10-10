@echo off
REM Script para criar o pacote de download final do ARENA
REM Executar com permissões de administrador se necessário

echo ==========================================
echo GERANDO PACOTE DE DOWNLOAD FINAL DO ARENA
echo ==========================================
echo.

REM 1. Ir para a pasta do projeto
cd /d "C:\Projetos\Criador De Apps Pedagogicos\ARENA\ARENA-unificado"

REM 2. Mostrar o que será removido
echo Pastas que serão removidas:
echo   - retroarch\
echo   - emuladores\
echo   - dados\
echo   - perfil\
echo   - backup\
echo.
echo Pressione qualquer tecla para continuar...
pause >nul

REM 3. Remover pastas pesadas (mas Manter backups)
echo.
echo Removendo arquivos temporários...
del /q *.log 2>nul
del /q *.tmp 2>nul
del /q ARENA-troca.json 2>nul

REM 4. Criar diretório para download
set DOWNLOAD_DIR=..\are.na_download
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

REM 5. Copiar arquivos essenciais
echo.
echo Copiando arquivos essenciais...
xcopy /E /I /Y "C:\Projetos\Criador De Apps Pedagogicos\ARENA\ARENA-unificado" "%DOWNLOAD_DIR%\ARENA\" ^
    /EXCLUDE:excluir.txt

echo.
echo ==========================================
echo PROCESSO CONCLUÍDO
echo ==========================================
echo.
echo Próximos passos:
echo 1. Entre na pasta: %DOWNLOAD_DIR%
echo 2. Compacte a pasta ARENA como ARENA-download.zip
echo 3. Faça upload para OneDrive/Google Drive
echo 4. Crie GitHub Release e anexe o ZIP
echo.
pause

:end