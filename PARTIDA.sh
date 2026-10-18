#!/bin/sh
# ===========================================================================
#  ARENA - por que a partida a dois nao conecta (o mesmo que o PARTIDA.bat).
#  Rode nos DOIS computadores. Nao muda nada, so confere e explica.
#
#  Para conferir tambem o computador do colega, ponha o endereco dele no fim:
#     sh PARTIDA.sh 192.168.0.12
# ===========================================================================
cd "$(dirname "$0")" || exit 1
. ./servidor/achar_python.sh
printf '\033]0;ARENA - diagnostico da partida\007'
achar_python || { pausar; exit 1; }
"$PYTHON" servidor/partida.py "$@"
echo
pausar
