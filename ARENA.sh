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

# --- 0. So o Linux de 64 bits dos processadores Intel e AMD -----------------
#  O RetroArch e o Python que vem junto sao do Linux x86-64. No Chromebook de
#  processador ARM (e no Raspberry Pi), o ARENA que roda e' o do navegador.
case "$(uname -m)" in
    x86_64|amd64) ;;
    *)
        echo "  [ERRO] Este computador e' $(uname -m), e o ARENA do Linux e' para"
        echo "  processador Intel ou AMD de 64 bits (x86-64)."
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
if [ ! -f "$RAIZ/retroarch/RetroArch-Linux-x86_64.AppImage" ]; then
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
QUEDAS=0
while :; do
    "$PYTHON" "$RAIZ/servidor/arena.py"
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
    sleep 2
done

echo
if [ "$SAIDA" != 0 ] && [ "$SAIDA" != 130 ]; then
    echo "  O ARENA fechou com erro. A mensagem acima explica o motivo."
else
    echo "  ARENA encerrado."
fi
pausar
