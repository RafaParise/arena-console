# ===========================================================================
#  ARENA - acha o Python para os arquivos .sh do Linux (item 13 do plano de
#  15/10/2026). E' o mesmo trecho do comeco de cada .bat do Windows.
#
#  Uso, de dentro da pasta do ARENA:
#      . servidor/achar_python.sh
#      achar_python || exit 1        # deixa o programa em $PYTHON
#
#  1. O Python que veio junto (servidor/python-linux, o 3.13 portatil).
#     No pen drive FAT32 o Linux nao deixa executar programa nenhum (nao ha
#     a permissao de executar). Entao vai uma copia dele para a pasta de
#     cache da conta (~/.cache/arena), uma vez so, e ele roda de la. Os
#     jogos, os saves e o resto do ARENA continuam no pen drive.
#  2. Nao veio junto (ou nao roda)? O Python do computador, 3.11 ou mais novo.
# ===========================================================================

pausar() {
    # So com alguem na frente da janela (no terminal); sem ele, segue.
    if [ -t 0 ]; then
        printf "  Aperte Enter para fechar esta janela."
        read -r _resposta
    fi
}

achar_python() {
    PYTHON=""
    _origem="$PWD/servidor/python-linux"
    if [ -f "$_origem/bin/python3.13" ]; then
        if [ -x "$_origem/bin/python3.13" ] && "$_origem/bin/python3.13" -c "" 2>/dev/null; then
            PYTHON="$_origem/bin/python3.13"
            return 0
        fi
        _cache="${XDG_CACHE_HOME:-$HOME/.cache}/arena"
        _marca=$(wc -c < "$_origem/lib/libpython3.13.so.1.0" 2>/dev/null | tr -d ' ')
        _copia="$_cache/python-3.13-$_marca"
        if ! "$_copia/bin/python3.13" -c "" 2>/dev/null; then
            echo "  Preparando o Python na pasta da conta (so na primeira vez)..."
            rm -rf "$_copia.copiando"
            if mkdir -p "$_cache" && cp -R "$_origem" "$_copia.copiando" \
                && chmod -R u+rwX "$_copia.copiando" && chmod u+x "$_copia.copiando/bin/python3.13"; then
                # As copias de um Python antigo (de outro pacote) saem.
                for _velha in "$_cache"/python-3.13-*; do
                    case "$_velha" in
                        "$_copia.copiando") ;;
                        *) rm -rf "$_velha" ;;
                    esac
                done
                mv "$_copia.copiando" "$_copia"
            fi
        fi
        if "$_copia/bin/python3.13" -c "" 2>/dev/null; then
            PYTHON="$_copia/bin/python3.13"
            return 0
        fi
    fi
    for _nome in python3.13 python3.12 python3.11 python3; do
        if command -v "$_nome" >/dev/null 2>&1 \
            && "$_nome" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
            PYTHON=$(command -v "$_nome")
            return 0
        fi
    done
    echo "  [ERRO] O Python nao foi encontrado."
    echo
    echo "  Como resolver, escolha uma das duas:"
    echo "    a) Copie de novo a pasta do ARENA inteira: tem que existir o arquivo"
    echo "       servidor/python-linux/bin/python3.13"
    echo "    b) Instale o Python 3 neste computador (no Ubuntu e no Mint ele ja vem;"
    echo "       no Debian: sudo apt install python3)"
    echo
    return 1
}
