# -*- coding: utf-8 -*-
r"""Escreve o TERCEIROS.md: os programas de outros projetos que o pacote do
ARENA leva, cada um com a licenca e o endereco do codigo-fonte.

Por que existe: o pacote para baixar (GitHub, Releases) leva o RetroArch, os
nucleos, o PCSX2, o Dolphin, o RPCS3, o Xenia e o Python embutido. Cada um
tem a sua licenca, e as do tipo GPL pedem que quem distribui diga onde esta
o codigo-fonte. A licenca de cada nucleo vem do proprio arquivo .info dele
(retroarch\info), entao a lista acompanha os nucleos que a versao leva.

Uso:
    servidor\python\python.exe ferramentas\lista_de_terceiros.py [pasta do pacote] [--saida=<arquivo.md>]

Sem pasta, le o ARENA desta pasta (os nucleos que o montador levaria).
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROGRAMAS = [
    ("Python 3.13 (versão embutida)", "PSF License", "https://www.python.org/downloads/source/",
     "servidor\\python"),
    ("RetroArch", "GPL-3.0", "https://github.com/libretro/RetroArch", "retroarch"),
    ("Recursos do RetroArch (menu, sons)", "CC BY 4.0", "https://github.com/libretro/retroarch-assets",
     "retroarch\\assets"),
    ("Filtros de tela do RetroArch (slang-shaders)", "licença de cada filtro, no cabeçalho do arquivo",
     "https://github.com/libretro/slang-shaders", "retroarch\\shaders"),
    ("Perfis de controle do RetroArch (autoconfig)", "a do repositório",
     "https://github.com/libretro/retroarch-joypad-autoconfig", "retroarch\\autoconfig"),
    ("PCSX2 (PlayStation 2)", "GPL-3.0 ou posterior", "https://github.com/PCSX2/pcsx2", "emuladores\\PCSX2"),
    ("Dolphin (GameCube e Wii)", "GPL-2.0 ou posterior", "https://github.com/dolphin-emu/dolphin",
     "emuladores\\Dolphin"),
    ("RPCS3 (PlayStation 3)", "GPL-2.0", "https://github.com/RPCS3/rpcs3", "emuladores\\RPCS3"),
    ("Xenia Canary (Xbox 360)", "BSD-3-Clause", "https://github.com/xenia-canary/xenia-canary",
     "emuladores\\Xenia"),
]


def ler_info(caminho):
    dados = {}
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for linha in f:
            m = re.match(r'\s*(\w+)\s*=\s*"(.*)"\s*$', linha)
            if m:
                dados[m.group(1)] = m.group(2)
    return dados


def nucleos(pasta_retroarch):
    """(nome do arquivo, nome de exibicao, licenca, versao) dos nucleos da pasta."""
    saida = []
    cores = os.path.join(pasta_retroarch, "cores")
    for nome in sorted(os.listdir(cores)) if os.path.isdir(cores) else []:
        if not nome.lower().endswith("_libretro.dll"):
            continue
        info = os.path.join(pasta_retroarch, "info", nome[:-4] + ".info")
        dados = ler_info(info) if os.path.isfile(info) else {}
        saida.append((nome, dados.get("display_name", nome), dados.get("license", "ver o projeto"),
                      dados.get("display_version", "")))
    return saida


def montar(pasta):
    if os.path.isdir(os.path.join(pasta, "retroarch", "cores")) and pasta != RAIZ:
        lista = nucleos(os.path.join(pasta, "retroarch"))
    else:
        sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
        import montar_versao_alunos as montador
        usados, _pastas = montador.nucleos_usados()
        lista = [n for n in nucleos(os.path.join(RAIZ, "retroarch")) if n[0].lower() in usados]
    linhas = [
        "# Programas de outros projetos",
        "",
        "O ARENA (o código desta pasta: `servidor\\`, `launcher\\`, os `.bat`, os guias",
        "e as ferramentas) é software livre sob a **GPL-3.0** (arquivo `LICENSE`).",
        "",
        "O pacote para baixar leva também os programas abaixo, **sem mudança",
        "nenhuma**, cada um com a sua licença. O ARENA só escreve a configuração",
        "deles antes de abrir um jogo. O código-fonte de cada um está no endereço",
        "da tabela; se precisar da versão exata que foi no pacote, peça pelas",
        "*Issues* do repositório do ARENA.",
        "",
        "Nenhum jogo, BIOS ou firmware vai no pacote: são de quem tem o console.",
        "",
        "## Programas",
        "",
        "| Programa | Licença | Código-fonte | Pasta |",
        "|---|---|---|---|",
    ]
    for nome, licenca, fonte, onde in PROGRAMAS:
        linhas.append("| %s | %s | <%s> | `%s` |" % (nome, licenca, fonte, onde))
    linhas += [
        "",
        "## Núcleos do RetroArch (%d)" % len(lista),
        "",
        "Cada núcleo é o emulador de um console. A licença vem do arquivo `.info`",
        "do próprio núcleo (`retroarch\\info`). Os de licença **não comercial**",
        "(Non-commercial) podem ser usados e distribuídos de graça, como aqui,",
        "mas não vendidos. O código-fonte de todos está em",
        "<https://github.com/libretro> (um repositório por núcleo).",
        "",
        "| Núcleo | Arquivo | Versão | Licença |",
        "|---|---|---|---|",
    ]
    for arquivo, exibicao, licenca, versao in lista:
        linhas.append("| %s | `%s` | %s | %s |" % (exibicao.replace("|", "/"), arquivo, versao or "—",
                                                  licenca.replace("|", " / ")))
    linhas.append("")
    return "\n".join(linhas)


def principal():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = os.path.abspath(args[0]) if args else RAIZ
    destino = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--saida=")),
                   os.path.join(pasta, "TERCEIROS.md"))
    texto = montar(pasta)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(texto)
    print("Escrito:", destino, "(%d linhas)" % texto.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
