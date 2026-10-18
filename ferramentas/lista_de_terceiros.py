# -*- coding: utf-8 -*-
r"""Escreve o TERCEIROS.md: os programas de outros projetos que o pacote do
ARENA leva, cada um com a licenca e o endereco do codigo-fonte.

Por que existe: o pacote para baixar (GitHub, Releases) leva o RetroArch, os
nucleos, o PCSX2, o Dolphin, o RPCS3, o Xenia, o Python embutido e as BIOS
livres (servidor\bios_livres\lista.json). Cada um
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
    ("Arquivos de apoio do núcleo Dolphin do RetroArch (Sys)",
     "GPL-2.0 ou posterior (dolphin-emu\\license.txt); as fontes do GameCube, feitas da Droid Sans, "
     "Apache 2.0 (Sys\\GC\\font-licenses.txt)",
     "https://github.com/libretro/dolphin", "retroarch\\system\\dolphin-emu"),
    ("RPCS3 (PlayStation 3)", "GPL-2.0", "https://github.com/RPCS3/rpcs3", "emuladores\\RPCS3"),
    ("Xenia Canary (Xbox 360)", "BSD-3-Clause", "https://github.com/xenia-canary/xenia-canary",
     "emuladores\\Xenia"),
    ("Java do Java ME: OpenJDK 21 (Eclipse Temurin), reduzido com o jlink",
     "GPL-2.0 com a exceção Classpath (os textos vão em emuladores\\Java\\legal)",
     "https://github.com/adoptium/temurin21-binaries", "emuladores\\Java"),
    ("RetroArch 1.22.2 para navegador (WebAssembly), o do ARENA do Chromebook: o build oficial do libretro "
     "(buildbot.libretro.com/stable/1.22.2/emscripten), só convertido para abrir do pen drive "
     "(ferramentas\\preparar_nucleos_navegador.py)",
     "GPL-3.0 (o RetroArch); cada núcleo, a licença dele (tabela do Chromebook, abaixo)",
     "https://github.com/libretro/RetroArch", "launcher\\navegador\\nucleos"),
    # O mesmo pen drive no Linux (item 13, 18/10/2026).
    ("Python 3.13 para Linux (python-build-standalone, o do uv)", "PSF License (o Python); BSD-3-Clause "
     "(a montagem)", "https://github.com/astral-sh/python-build-standalone", "servidor\\python-linux"),
    ("RetroArch 1.22.2 para Linux (o AppImage oficial do libretro)", "GPL-3.0",
     "https://github.com/libretro/RetroArch", "retroarch\\RetroArch-Linux-x86_64.AppImage"),
    ("libgomp do GCC 8 (Debian 10), que o núcleo do Dreamcast pede no Linux",
     "GPL-3.0 com a exceção das bibliotecas do GCC", "https://archive.debian.org/debian/pool/main/g/gcc-8/",
     "retroarch\\bibliotecas-linux\\libgomp.so.1"),
    ("libjack.so.0 vazia: escrita pelo ARENA, sem nada do JACK (só os nomes das funções, que devolvem 0; "
     "ferramentas\\jack_vazio.py)", "GPL-3.0 (a do ARENA)", "https://github.com/RafaParise/arena-console",
     "retroarch\\bibliotecas-linux\\libjack.so.0"),
    ("PCSX2 2.8.2 para Linux (AppImage oficial)", "GPL-3.0 ou posterior", "https://github.com/PCSX2/pcsx2",
     "emuladores\\PCSX2\\PCSX2"),
    ("RPCS3 0.0.42 para Linux (AppImage oficial)", "GPL-2.0", "https://github.com/RPCS3/rpcs3",
     "emuladores\\RPCS3\\RPCS3"),
    ("Xenia Canary para Linux (AppImage oficial)", "BSD-3-Clause", "https://github.com/xenia-canary/xenia-canary",
     "emuladores\\Xenia\\Xenia"),
    ("Java do Java ME para Linux: o mesmo OpenJDK 21 (Eclipse Temurin), reduzido com o jlink",
     "GPL-2.0 com a exceção Classpath (os textos vão em emuladores\\Java\\linux\\legal)",
     "https://github.com/adoptium/temurin21-binaries", "emuladores\\Java\\linux"),
]

# O que o ARENA usa e nao distribui (o Lossless Scaling, de quem comprou).
NAO_VEM = [
    "Não vem no ARENA, mas o ARENA usa se estiver no computador de quem comprou:",
    "o **Lossless Scaling** (programa pago, da Steam). Ele não é distribuído",
    "aqui de jeito nenhum; o `servidor\\lossless.py` só o acha, ajusta o perfil",
    "\"ARENA\" dele e o abre junto com o jogo (guia 3, \"Lossless Scaling\"). O",
    "`.gitignore` e o montador do pacote barram a pasta dele.",
]

# Nucleos cujo codigo-fonte NAO fica no GitHub do libretro.
FONTE_FORA_DO_LIBRETRO = {
    "freej2me_libretro.dll": "https://github.com/TASEmulators/freej2me-plus/tree/8f87bf1497e7a9738a32d1909379376a1faca7dd",
    "freej2me_libretro.so": "https://github.com/TASEmulators/freej2me-plus/tree/8f87bf1497e7a9738a32d1909379376a1faca7dd",
}


def ler_info(caminho):
    dados = {}
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for linha in f:
            m = re.match(r'\s*(\w+)\s*=\s*"(.*)"\s*$', linha)
            if m:
                dados[m.group(1)] = m.group(2)
    return dados


def nucleos(pasta_retroarch, extensao=".dll"):
    """(nome do arquivo, nome de exibicao, licenca, versao) dos nucleos da
    pasta: os do Windows (.dll) ou, com extensao=".so", os do Linux."""
    saida = []
    cores = os.path.join(pasta_retroarch, "cores")
    for nome in sorted(os.listdir(cores)) if os.path.isdir(cores) else []:
        if not nome.lower().endswith("_libretro" + extensao):
            continue
        info = os.path.join(pasta_retroarch, "info", nome[:-len(extensao)] + ".info")
        dados = ler_info(info) if os.path.isfile(info) else {}
        saida.append((nome, dados.get("display_name", nome), dados.get("license", "ver o projeto"),
                      dados.get("display_version", "")))
    return saida


def bios_livres():
    """Os projetos da servidor\\bios_livres\\lista.json (as BIOS livres que o
    pacote leva), na ordem do nome."""
    import json
    try:
        with open(os.path.join(RAIZ, "servidor", "bios_livres", "lista.json"), encoding="utf-8") as f:
            projetos = json.load(f).get("projetos", {})
    except (OSError, ValueError):
        return []
    return [projetos[nome] for nome in sorted(projetos)]


def do_chromebook():
    """(nucleos, jogos) do ARENA do Chromebook: cada nucleo do navegador
    (consoles.json -> core_navegador) com os consoles e a licenca do .info
    dele, e os jogos livres que vem junto (os de testes\\jogos_livres com
    console no navegador, os mesmos do launcher\\navegador\\livres.js)."""
    import json
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as f:
        plataformas = json.load(f)["plataformas"]
    consoles = {}
    for p in plataformas:
        if p.get("core_navegador"):
            consoles.setdefault(p["core_navegador"], []).append(p["nome"])
    nucleos_web = []
    for nucleo in sorted(consoles):
        info = os.path.join(RAIZ, "retroarch", "info", nucleo + "_libretro.info")
        dados = ler_info(info) if os.path.isfile(info) else {}
        nucleos_web.append((dados.get("display_name", nucleo), nucleo, ", ".join(consoles[nucleo]),
                            dados.get("license", "ver o projeto")))
    nomes = {p["id"]: p["nome"] for p in plataformas if p.get("core_navegador")}
    try:
        with open(os.path.join(RAIZ, "testes", "jogos_livres", "lista.json"), encoding="utf-8") as f:
            jogos = [dict(j, console_nome=nomes[j["console"]]) for j in json.load(f)["arquivos"]
                     if j["console"] in nomes]
    except (OSError, ValueError, KeyError):
        jogos = []
    return nucleos_web, sorted(jogos, key=lambda j: j["origem"])


def montar(pasta):
    if os.path.isdir(os.path.join(pasta, "retroarch", "cores")) and pasta != RAIZ:
        lista = nucleos(os.path.join(pasta, "retroarch"))
        lista_linux = nucleos(os.path.join(pasta, "retroarch"), ".so")
    else:
        sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
        import montar_versao_alunos as montador
        usados, _pastas = montador.nucleos_usados()
        lista = [n for n in nucleos(os.path.join(RAIZ, "retroarch")) if n[0].lower() in usados]
        usados_linux = {os.path.splitext(n)[0] + ".so" for n in usados}
        lista_linux = [n for n in nucleos(os.path.join(RAIZ, "retroarch"), ".so") if n[0].lower() in usados_linux]
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
        "Nenhum jogo vai no pacote, nem BIOS ou firmware das empresas: são de quem",
        "tem o console. Vão só as **BIOS livres** da tabela abaixo, escritas do zero",
        "por voluntários para qualquer um copiar.",
        "",
        "## Programas",
        "",
        "| Programa | Licença | Código-fonte | Pasta |",
        "|---|---|---|---|",
    ]
    for nome, licenca, fonte, onde in PROGRAMAS:
        linhas.append("| %s | %s | <%s> | `%s` |" % (nome, licenca, fonte, onde))
    linhas += [""] + NAO_VEM
    livres = bios_livres()
    linhas += [
        "",
        "## BIOS livres (%d)" % len(livres),
        "",
        "Ficam em `servidor\\bios_livres`, sem mudança nenhuma, com o texto da",
        "licença ao lado; a `lista.json` dessa pasta guarda a marca (SHA-256) de",
        "cada arquivo. O ARENA as copia para `retroarch\\system` só onde falta.",
        "",
        "| BIOS | Console | Licença | Código-fonte | Pasta |",
        "|---|---|---|---|---|",
    ]
    for projeto in livres:
        linhas.append("| %s %s | %s | %s | <%s> | `servidor\\bios_livres\\%s` |" % (
            projeto["nome"], projeto.get("versao", ""), projeto.get("console", ""), projeto.get("licenca", ""),
            projeto.get("codigo_fonte") or projeto.get("site", ""), projeto["nome"]))
    linhas += [
        "",
        "## Núcleos do RetroArch (%d)" % len(lista),
        "",
        "Cada núcleo é o emulador de um console. A licença vem do arquivo `.info`",
        "do próprio núcleo (`retroarch\\info`). Os de licença **não comercial**",
        "(Non-commercial) podem ser usados e distribuídos de graça, como aqui,",
        "mas não vendidos. O código-fonte de todos está em",
        "<https://github.com/libretro> (um repositório por núcleo), menos os",
        "que a lista depois da tabela aponta.",
        "",
        "| Núcleo | Arquivo | Versão | Licença |",
        "|---|---|---|---|",
    ]
    for arquivo, exibicao, licenca, versao in lista:
        linhas.append("| %s | `%s` | %s | %s |" % (exibicao.replace("|", "/"), arquivo, versao or "—",
                                                  licenca.replace("|", " / ")))
    fora = [(arquivo, FONTE_FORA_DO_LIBRETRO[arquivo.lower()]) for arquivo, _e, _l, _v in lista
            if arquivo.lower() in FONTE_FORA_DO_LIBRETRO]
    if fora:
        linhas += ["", "Código-fonte fora do libretro:", ""]
        linhas += ["- `%s`: <%s>" % par for par in fora]
    if lista_linux:
        linhas += [
            "",
            "## Núcleos do RetroArch no Linux (%d)" % len(lista_linux),
            "",
            "Os mesmos núcleos, na versão para Linux do mesmo RetroArch 1.22.2 (o",
            "`RetroArch_cores.7z` do libretro): ficam ao lado dos do Windows, em",
            "`retroarch\\cores`, com a mesma licença (o mesmo `.info`) e o mesmo",
            "código-fonte. Só a extensão muda: `.so` no lugar de `.dll`.",
            "",
            "| Núcleo | Arquivo | Licença |",
            "|---|---|---|",
        ]
        for arquivo, exibicao, licenca, _versao in lista_linux:
            linhas.append("| %s | `%s` | %s |" % (exibicao.replace("|", "/"), arquivo, licenca.replace("|", " / ")))
    nucleos_web, jogos = do_chromebook()
    linhas += [
        "",
        "## Núcleos do ARENA no Chromebook (%d)" % len(nucleos_web),
        "",
        "No Chromebook, o ARENA roda dentro do navegador (`ARENA-CHROMEBOOK.html`),",
        "com estes núcleos na versão que o libretro compila para WebAssembly, do",
        "mesmo RetroArch 1.22.2: dois arquivos cada um em `launcher\\navegador\\nucleos`",
        "(o programa e o emulador compactado). A licença é a do mesmo núcleo",
        "(o `.info` dele); o código-fonte, o repositório dele em",
        "<https://github.com/libretro>.",
        "",
        "| Núcleo | Arquivos | Consoles | Licença |",
        "|---|---|---|---|",
    ]
    for exibicao, nucleo, consoles, licenca in nucleos_web:
        linhas.append("| %s | `%s.js`, `%s.wasm.js` | %s | %s |" % (
            exibicao.replace("|", "/"), nucleo, nucleo, consoles, licenca.replace("|", " / ")))
    if jogos:
        linhas += [
            "",
            "## Jogos livres que vêm junto no Chromebook (%d)" % len(jogos),
            "",
            "Para o Chromebook ter jogo na primeira vez e para o \"Testar este",
            "Chromebook\" medir sem pen drive, vão embutidos em",
            "`launcher\\navegador\\livres.js` estes jogos de licença livre (os mesmos de",
            "`testes\\jogos_livres`, conferidos pela marca SHA-256 da `lista.json`):",
            "",
            "| Jogo | Console | Autor | Licença | Código-fonte |",
            "|---|---|---|---|---|",
        ]
        for j in jogos:
            linhas.append("| %s | %s | %s | %s | <%s> |" % (j["jogo"], j["console_nome"], j["autor"], j["licenca"],
                                                       j["fonte"]))
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
