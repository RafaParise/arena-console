#!/bin/sh
# ===========================================================================
#  ARENA - ponto de entrada unico no Linux (o mesmo que o ARENA.bat faz no
#  Windows; item 13 do plano de 15/10/2026).
#
#  Abrir: no terminal, de dentro da pasta do ARENA:    sh ARENA.sh
#  (no gerenciador de arquivos: botao direito na pasta -> "Abrir no
#  terminal"; ou dois cliques no ARENA.desktop, onde o sistema deixa).
#  Atalho no menu de aplicativos deste computador:      sh ARENA.sh --atalho
#
#  Tudo se ancora na pasta onde ESTE arquivo esta: o pen drive pode estar em
#  /media/aluno/PEN, em /run/media/... ou numa pasta da conta.
# ===========================================================================
cd "$(dirname "$0")" || exit 1
RAIZ=$(pwd)
. "$RAIZ/servidor/achar_python.sh"
printf '\033]0;ARENA - servidor local\007'      # o titulo da janela do terminal

echo
echo "  ARENA"
echo "  Iniciando. Nao feche esta janela enquanto estiver jogando."
echo

# --- 0. So o Linux de 64 bits (Intel e AMD, ou ARM) --------------------------
#  O RetroArch e o Python que vem junto sao do Linux x86-64. Desde 14/11/2026
#  o ARM de 64 bits (TV Box com Armbian, Raspberry Pi 4 e 5, Chromebook ARM
#  com Linux) tambem abre, com o RetroArch de retroarch/linux-aarch64 (o
#  ferramentas/preparar_linux.py --arm64 poe la) ou o instalado no sistema.
#  Sem nenhum dos dois, o ARENA do navegador e' o melhor caminho.
ARM64=""
case "$(uname -m)" in
    x86_64|amd64) ;;
    aarch64|arm64)
        ARM64=1
        if [ ! -f "$RAIZ/retroarch/linux-aarch64/retroarch" ] && ! command -v retroarch >/dev/null 2>&1; then
            echo "  [ERRO] Este computador e' ARM de 64 bits ($(uname -m)), e esta pasta"
            echo "  nao tem o RetroArch dele (retroarch/linux-aarch64/retroarch)."
            echo
            echo "  Como resolver, escolha uma das tres:"
            echo "    a) Copie o ARENA preparado para ARM (no computador de quem monta o"
            echo "       pacote: ferramentas/preparar_linux.py --arm64)."
            echo "    b) Instale o RetroArch neste Linux: sudo apt install retroarch"
            echo "    c) Abra o ARENA do navegador: o arquivo ARENA-CHROMEBOOK.html,"
            echo "       nesta mesma pasta (guia 1, Parte C)."
            echo
            pausar
            exit 1
        fi ;;
    *)
        echo "  [ERRO] Este computador e' $(uname -m), e o ARENA do Linux e' para"
        echo "  processador de 64 bits (x86-64 da Intel e da AMD, ou ARM de 64 bits)."
        echo
        echo "  Neste computador, abra o ARENA do Chromebook, que roda no navegador:"
        echo "  o arquivo ARENA-CHROMEBOOK.html, nesta mesma pasta (guia 1, Parte C)."
        echo
        pausar
        exit 1 ;;
esac

# --- Atalho no menu (so quando pedido) --------------------------------------
if [ "$1" = "--atalho" ]; then
    MENU="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$MENU" || exit 1
    # O caminho vai entre aspas, com as barras e o $ protegidos (regra dos
    # arquivos .desktop do freedesktop).
    PROTEGIDO=$(printf '%s' "$RAIZ/ARENA.sh" | sed -e 's/[\\"`$]/\\\\&/g')
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Name=ARENA"
        echo "Comment=Os jogos do ARENA desta pasta: $RAIZ"
        echo "Exec=sh \"$PROTEGIDO\""
        echo "Icon=applications-games"
        echo "Terminal=true"
        echo "Categories=Game;"
    } > "$MENU/arena.desktop"
    echo "  Pronto: o ARENA aparece no menu de aplicativos deste computador."
    echo "  (Ele abre o ARENA desta pasta: $RAIZ)"
    exit 0
fi

# --- 1 e 2. O Python (o que veio junto ou o do computador) ------------------
achar_python || { pausar; exit 1; }

# --- 3. Confere se o RetroArch esta no lugar --------------------------------
if [ -n "$ARM64" ]; then
    if [ ! -d "$RAIZ/retroarch/cores-aarch64" ]; then
        echo "  [AVISO] Falta a pasta retroarch/cores-aarch64 (os emuladores do ARM)."
        echo "          O ARENA vai abrir, mas os jogos so iniciam com os nucleos dela."
        echo
    fi
elif [ ! -f "$RAIZ/retroarch/RetroArch-Linux-x86_64.AppImage" ]; then
    echo "  [AVISO] RetroArch-Linux-x86_64.AppImage nao encontrado em ./retroarch"
    echo "          O ARENA vai abrir, mas nenhum jogo vai iniciar."
    echo
fi

# --- 4. Sobe o servidor. Ele abre o navegador sozinho -----------------------
#  Se o servidor CAIR (o sistema fecha o Python por uma falha grave, sem
#  mensagem), esta janela reabre o servidor sozinha, ate 3 vezes, como o
#  ARENA.bat. A tela que ja estava aberta se reconecta sozinha; por isso a
#  reabertura nao abre outra janela (ARENA_REABERTO=1). O motivo da queda
#  fica em dados/logs. Codigo 0 = fechou do jeito normal; 1 = erro com
#  explicacao na tela (repetir nao adianta); 130 = Ctrl+C nesta janela.
#  Qualquer outro numero = queda.
trap 'echo; echo "  ARENA encerrado."; exit 0' INT

# O servidor nativo (Rust, 14/11/2026, docs/MIGRACAO-RUST.md) vai na frente: abre a porta e a tela na hora e abre o
# Python atras. No pen drive que nao deixa executar (FAT32), vai uma copia para a pasta de cache da conta, como o
# Python. Sem ele (ou com ARENA_SEM_NATIVO=1, ou depois de uma queda), so o Python, como antes.
NATIVO=""
achar_nativo() {
    case "$(uname -m)" in
        aarch64|arm64) _nativo="$RAIZ/servidor/arena-nativo-linux-aarch64" ;;
        *)             _nativo="$RAIZ/servidor/arena-nativo-linux-x86_64" ;;
    esac
    [ -f "$_nativo" ] || return 1
    [ -x "$_nativo" ] || chmod u+x "$_nativo" 2>/dev/null
    if [ -x "$_nativo" ] && [ ! -d "$_nativo" ]; then
        NATIVO="$_nativo"
    else
        _cache="${XDG_CACHE_HOME:-$HOME/.cache}/arena"
        _copia="$_cache/arena-nativo-$(wc -c < "$_nativo" | tr -d ' ')"
        if [ ! -x "$_copia" ]; then
            mkdir -p "$_cache" && cp "$_nativo" "$_copia.copiando" && chmod u+x "$_copia.copiando" \
                && mv "$_copia.copiando" "$_copia"
        fi
        [ -x "$_copia" ] && NATIVO="$_copia"
    fi
    [ -n "$NATIVO" ]
}
[ -z "$ARENA_SEM_NATIVO" ] && achar_nativo

QUEDAS=0
while :; do
    if [ -n "$NATIVO" ]; then
        "$NATIVO" "$PYTHON" "$RAIZ/servidor/arena.py"
    else
        "$PYTHON" "$RAIZ/servidor/arena.py"
    fi
    SAIDA=$?
    case "$SAIDA" in
        0|1|130) break ;;
    esac
    QUEDAS=$((QUEDAS + 1))
    echo
    echo "  [QUEDA] O servidor do ARENA caiu - codigo $SAIDA."
    echo "          O motivo ficou anotado em dados/logs/queda-do-servidor.txt"
    if [ "$QUEDAS" -gt 3 ]; then
        echo "          Caiu $QUEDAS vezes seguidas: nao vou reabrir de novo."
        echo "          Feche esta janela e abra o ARENA.sh outra vez."
        break
    fi
    echo "          Reabrindo sozinho, tentativa $QUEDAS de 3. A tela volta sozinha."
    echo
    ARENA_REABERTO=1
    export ARENA_REABERTO
    NATIVO=""        # a reabertura vai so com o Python (se o problema for o nativo, o ARENA abre como sempre)
    sleep 2
done

echo
if [ "$SAIDA" != 0 ] && [ "$SAIDA" != 130 ]; then
    echo "  O ARENA fechou com erro. A mensagem acima explica o motivo."
else
    echo "  ARENA encerrado."
fi
pausar
