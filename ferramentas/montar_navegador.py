# -*- coding: utf-8 -*-
r"""Gera launcher\navegador\dados.js: o que o ARENA no navegador precisa saber.

Por que existe (17/10/2026, item 12 do plano de 15/10): no Chromebook o ARENA
roda dentro do Chrome, sem o Python. Aberta do pen drive (file://), a pagina
nao pode ler os .json do servidor (o Chrome nao deixa fetch em file://).
Entao esta ferramenta junta, num script so, o que o servidor sabe e a versao
do navegador usa do mesmo jeito:

  - os consoles (servidor\consoles.json), com o nucleo de navegador de cada um;
  - as opcoes do RetroArch que o ARENA manda em todo jogo (arena.BASE_COMUM:
    as teclas, o menu em portugues, a gravacao e a transmissao desligadas),
    sem as que so existem no Windows;
  - as opcoes de cada nucleo pela nota da maquina (graficos.json, as mesmas
    do Windows: servidor\graficos.py, opcoes_finais_do_nucleo);
  - as BIOS de cada console (servidor\bios_catalogo.py), a configuracao
    padrao, as etiquetas de desempenho e os jogos da biblioteca livre.

Tudo o que sai daqui e' fixo (nada desta maquina: nem caminho, nem
processador). O teste servidor\tests\test_navegador_dados.py avisa quando
alguem muda o servidor e esquece de rodar esta ferramenta.

Uso:
    servidor\python\python.exe ferramentas\montar_navegador.py            (grava)
    servidor\python\python.exe ferramentas\montar_navegador.py --conferir (so diz se mudou)
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "servidor")
SAIDA = os.path.join(RAIZ, "launcher", "navegador", "dados.js")
SAIDA_LIVRES = os.path.join(RAIZ, "launcher", "navegador", "livres.js")
PASTA_LIVRES = os.path.join(RAIZ, "testes", "jogos_livres")

# Opcoes do BASE_COMUM que nao valem no navegador: o som do Windows (WASAPI),
# o registro em arquivo e as pastas (o quadro do jogo poe as dele) e o
# config_save_on_exit (no navegador nada e' gravado por cima da configuracao).
FORA_DO_NAVEGADOR = {"audio_driver", "log_to_file", "log_to_file_timestamp", "input_remapping_directory",
                     "joypad_autoconfig_dir", "config_save_on_exit"}
NOTAS = (1, 2, 3, 4, 5)

# A pasta de cada nucleo dentro de retroarch/saves e retroarch/states: o
# "corename" do .info dele (o mesmo nome no Windows e no navegador; conferido
# com retroarch/info pelo servidor/tests/test_navegador_dados.py). E' por isso
# que o save do Chromebook e o do Windows sao o mesmo arquivo no pen drive.
PASTA_DO_NUCLEO = {
    "ardens": "Ardens", "fbneo": "FinalBurn Neo", "fceumm": "FCEUmm", "gambatte": "Gambatte",
    "gearcoleco": "Gearcoleco", "gearsystem": "Gearsystem", "genesis_plus_gx": "Genesis Plus GX", "gw": "GW",
    "handy": "Handy", "jaxe": "JAXE", "lowresnx": "lowresnx", "mednafen_ngp": "Beetle NeoPop",
    "mednafen_pce_fast": "Beetle PCE Fast", "mednafen_vb": "Beetle VB", "mednafen_wswan": "Beetle WonderSwan",
    "mgba": "mGBA", "o2em": "O2EM", "opera": "Opera", "pcsx_rearmed": "PCSX-ReARMed", "picodrive": "PicoDrive",
    "scummvm": "ScummVM", "snes9x": "Snes9x", "tamalibretro": "TamaLIBretro", "theodore": "theodore",
    "tic80": "TIC-80", "uw8": "MicroW8", "uzem": "uzem", "vecx": "vecx", "vice_x128": "VICE x128",
    "vice_x64": "VICE x64", "vice_xpet": "VICE xpet", "vice_xplus4": "VICE xplus4", "vice_xvic": "VICE xvic",
    "wasm4": "WASM-4",
}
# Quando o nucleo do navegador e' outro (PS1: PCSX ReARMed no lugar do
# SwanStation; PC Engine: a versao rapida do Beetle PCE), o save do Windows
# vale tambem: o cartao de memoria do PS1 e' o mesmo arquivo de 128 KB nos
# dois (servidor/graficos.py, levar_cartao_do_ps1). So vale quando o nucleo
# do navegador ainda nao tem save daquele jogo: nunca troca um que ja existe.
PASTAS_PARECIDAS = {"PCSX-ReARMed": ["SwanStation"], "Beetle PCE Fast": ["Beetle PCE"]}


def _ler_json(nome):
    with open(os.path.join(SERVIDOR, nome), encoding="utf-8") as arquivo:
        return json.load(arquivo)


def montar():
    """O texto do dados.js (sempre o mesmo para o mesmo servidor)."""
    if SERVIDOR not in sys.path:
        sys.path.insert(0, SERVIDOR)
    import arena
    import bios_catalogo
    import graficos

    consoles = _ler_json("consoles.json")
    no_navegador = [p for p in consoles["plataformas"] if p.get("core_navegador")]
    opcoes_nucleo = {}
    for nucleo in sorted({p["core_navegador"] for p in no_navegador}):
        opcoes_nucleo[nucleo] = {str(n): graficos.opcoes_finais_do_nucleo(nucleo, n, nota_gpu=min(n, 3))
                                 for n in NOTAS}
    bios = {}
    for entrada in bios_catalogo.CATALOGO:
        if entrada["console"] not in {p["id"] for p in no_navegador}:
            continue
        bios.setdefault(entrada["console"], []).append({
            "id": entrada["id"],
            "destino": entrada.get("destino") or entrada.get("nome"),
            "aceitos": bios_catalogo.nomes_aceitos(entrada),
            "nivel": entrada["nivel"],
            "grupo": entrada.get("grupo"),
            "pasta": entrada.get("pasta"),
            "o_que": entrada.get("o_que", ""),
        })
    livres = _ler_json("biblioteca_livre.json").get("jogos", [])
    dados = {
        "versao": arena.VERSAO,
        "retroarch": "1.22.2",
        "consoles": consoles["plataformas"],
        "preferencia": consoles.get("preferencia", {}),
        "base_retroarch": {k: v for k, v in arena.BASE_COMUM.items() if k not in FORA_DO_NAVEGADOR},
        "opcoes_nucleo": opcoes_nucleo,
        "bios": bios,
        "config_padrao": arena.config_padrao(),
        "perfis": dict([("automatico", arena.PERFIL_AUTOMATICO)] +
                       [(c, {"rotulo": v["rotulo"], "resumo": v["resumo"]})
                        for c, v in arena.PERFIS_GRAFICOS.items()]),
        "etiquetas": arena.CLASSES_ETIQUETA,
        "velocidade_por_custo": {str(k): v for k, v in arena.VELOCIDADE_POR_CUSTO.items()},
        "biblioteca_livre": livres,
        "formato_da_imagem": graficos.regra_do_formato(),
        "pasta_do_nucleo": PASTA_DO_NUCLEO,
        "pastas_parecidas": PASTAS_PARECIDAS,
    }
    return ("// Gerado por ferramentas\\montar_navegador.py a partir do servidor: nao edite a mao.\n"
            "// (servidor\\consoles.json, arena.py, graficos.json, bios_catalogo.py, biblioteca_livre.json)\n"
            "window.ARENA_DADOS = %s;\n" % json.dumps(dados, ensure_ascii=False, indent=1, sort_keys=True))


def montar_livres():
    """O texto do livres.js: os jogos livres dos testes (testes\\jogos_livres,
    todos de licenca livre: MIT, CC0, Unlicense) cujo console abre no
    navegador, embutidos em base64. Vem no pacote (nao no git: e' copia dos
    arquivos que ja estao la) para o Chromebook ter jogo na primeira abertura
    e para o "Testar este Chromebook" medir sem pen drive. Cada um confere
    com a marca SHA-256 da lista.json."""
    import base64
    import hashlib
    consoles = {p["id"]: p for p in _ler_json("consoles.json")["plataformas"]}
    with open(os.path.join(PASTA_LIVRES, "lista.json"), encoding="utf-8") as arquivo:
        lista = json.load(arquivo)["arquivos"]
    jogos = []
    for item in sorted(lista, key=lambda i: i["origem"]):
        if not (consoles.get(item["console"]) or {}).get("core_navegador"):
            continue
        with open(os.path.join(PASTA_LIVRES, *item["origem"].split("/")), "rb") as arquivo:
            dados = arquivo.read()
        if hashlib.sha256(dados).hexdigest() != item["sha256"]:
            raise ValueError("%s: a marca nao confere com a lista.json" % item["origem"])
        jogos.append({"arquivo": item["origem"], "titulo": item["jogo"], "plataforma": item["console"],
                      "autor": item["autor"], "licenca": item["licenca"], "fonte": item["fonte"],
                      "bytes": len(dados), "dados": base64.b64encode(dados).decode("ascii")})
    return ("// Gerado por ferramentas\\montar_navegador.py (testes\\jogos_livres): nao edite a mao.\n"
            "window.ARENA_LIVRES = %s;\n" % json.dumps(jogos, ensure_ascii=False, indent=1))


def gravar_se_mudou(caminho, conteudo):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            # O git do Windows pode trocar LF por CRLF no checkout: tanto faz.
            if arquivo.read().replace("\r\n", "\n") == conteudo:
                print("%s ja estava em dia." % os.path.basename(caminho))
                return
    except OSError:
        pass
    temporario = caminho + ".gravando"
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(conteudo)
    os.replace(temporario, caminho)
    print("Gravado %s (%d KB)." % (caminho, len(conteudo.encode("utf-8")) // 1024))


def principal():
    texto = montar()
    if "--conferir" in sys.argv:
        try:
            with open(SAIDA, encoding="utf-8") as arquivo:
                atual = arquivo.read().replace("\r\n", "\n")
        except OSError:
            atual = ""
        print("dados.js em dia." if atual == texto else "dados.js desatualizado: rode ferramentas\\montar_navegador.py")
        return 0 if atual == texto else 1
    gravar_se_mudou(SAIDA, texto)
    gravar_se_mudou(SAIDA_LIVRES, montar_livres())
    return 0


if __name__ == "__main__":
    sys.exit(principal())
