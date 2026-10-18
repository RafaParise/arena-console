#!/bin/sh
# ===========================================================================
#  ARENA - rodar os testes automatizados no Linux (o mesmo que o
#  RODAR_TESTES.bat). Os mesmos testes do Windows, sem Python de fora.
#  Abrir, de dentro da pasta do ARENA:   sh RODAR_TESTES.sh
# ===========================================================================
cd "$(dirname "$0")" || exit 1
. ./servidor/achar_python.sh
printf '\033]0;ARENA - testes\007'
achar_python || { pausar; exit 1; }
"$PYTHON" servidor/tests/run.py
# Os orcamentos do notebook-alvo (docs/MAQUINA-ALVO.md, secao 7) medem o
# ARENA preso aos limites do Celeron da escola por um recurso do Windows (o
# Job Object, ferramentas/modo_alvo.py): no Linux ficam de fora.
echo
pausar
