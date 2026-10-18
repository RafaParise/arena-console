#!/bin/sh
# A bateria de testes do ARENA no Linux, dentro do conteiner (item 13 do
# plano de 15/10/2026). O ARENA de verdade fica montado SO DE LEITURA em
# /arena: nada do Linux grava na pasta do Windows. Os testes rodam numa copia
# em /tmp/arena; as pastas grandes (jogos, emuladores, nucleos, BIOS) entram
# por atalho, porque os testes so as leem.
#
# No Windows, de dentro da pasta do ARENA (WSLC, sem administrador):
#   container.exe build -t arena-linux testes\linux
#   container.exe run --rm -v "<pasta do ARENA>:/arena:ro" arena-linux sh /arena/testes/linux/bateria.sh
set -e
ORIGEM=${1:-/arena}
COPIA=/tmp/arena
rm -rf "$COPIA"
mkdir -p "$COPIA"
for item in "$ORIGEM"/* "$ORIGEM"/.[!.]*; do
    [ -e "$item" ] || continue
    nome=$(basename "$item")
    case "$nome" in
        jogos|emuladores|BIOS|backup|.git|ARENA-remake--master|"ARENA - Versão antiga para implementar"|"Lossless Scaling")
            ln -s "$item" "$COPIA/$nome" ;;
        retroarch)
            # So os arquivos de configuracao viram copia (os testes gravam
            # neles); o resto (nucleos, system...) entra por atalho.
            mkdir "$COPIA/retroarch"
            for parte in "$item"/*; do
                case "$(basename "$parte")" in
                    *.cfg|*.opt) cp -a "$parte" "$COPIA/retroarch/" ;;
                    *) ln -s "$parte" "$COPIA/retroarch/$(basename "$parte")" ;;
                esac
            done ;;
        *)
            cp -a "$item" "$COPIA/" ;;
    esac
done
cd "$COPIA"
exec servidor/python-linux/bin/python3.13 -X utf8 servidor/tests/run.py
