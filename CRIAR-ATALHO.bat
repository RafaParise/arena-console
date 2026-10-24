@echo off
rem Cria o atalho do ARENA, com o icone do supercontrole, na area de trabalho.
rem Dois cliques e pronto. O atalho guarda o caminho desta pasta: se voce mudar a pasta
rem de lugar (ou o pen drive ganhar outra letra), rode este arquivo de novo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\criar_atalho.ps1" %*
if errorlevel 1 (
  echo.
  echo Nao consegui criar o atalho. Chame o professor e mostre esta janela.
) else (
  echo.
  echo Pronto: o atalho ARENA esta na area de trabalho, com o icone do supercontrole.
  echo Se mudar esta pasta de lugar, ou se o pen drive ganhar outra letra, rode este arquivo de novo.
)
pause
