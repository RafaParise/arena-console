@echo off
cls
echo ==========================================
echo SYNCRONIZADOR DE PROJETOS - ARENA
echo ==========================================
echo.

REM Muda para a pasta do projeto ARENA
cd /d "C:\Projetos\Criador De Apps Pedagogicos\ARENA\ARENA-unificado"

echo 1. Verificando status do Git...
git status --short
echo.

echo 2. Baixando mudanças do GitHub...
git pull origin auditoria
echo.

echo 3. Adicionando arquivos...
git add -A
echo.

echo 4. Criando commit local...
set DATA=%date:~6,4%-%date:~3,2%-%date:~0,2% %time:~0,8%
git commit -m "Backup automatico - %DATA%"
echo.

echo 5. Enviando para o GitHub...
git push origin auditoria
echo.

echo 6. Atualizando status...
python sync_github.py --status
echo.

echo ==========================================
echo SINCRONIZACAO CONCLUIDA
echo ==========================================
pause