#!/bin/sh
# ===========================================================================
#  ARENA - verificador rapido no Linux (o mesmo que o VERIFICAR.bat).
#  Checa se tudo necessario para rodar o ARENA esta no lugar.
#  Abrir, de dentro da pasta do ARENA:   sh VERIFICAR.sh
#  Para ver todos os detalhes:           sh VERIFICAR.sh --tudo
# ===========================================================================
cd "$(dirname "$0")" || exit 1
. ./servidor/achar_python.sh
printf '\033]0;ARENA - verificador\007'
achar_python || { pausar; exit 1; }

echo
echo "  Verificando..."
echo
if [ "$1" = "--tudo" ]; then
    "$PYTHON" servidor/diagnostico.py
else
    "$PYTHON" servidor/diagnostico.py --so-ver
fi
echo
echo "  ---"
echo "  Para testes automatizados:  sh RODAR_TESTES.sh"
echo
pausar
