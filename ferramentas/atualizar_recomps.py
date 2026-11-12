# -*- coding: utf-8 -*-
r"""Atualiza o catalogo de recomps do ARENA (servidor\recomps.json).

Um "recomp" (recompilacao) e' um jogo de console transformado em programa de
computador de verdade: o codigo da maquina do console virou codigo de PC, e
o jogo roda sem emulador, com resolucao alta, 60 quadros ou mais e controles
modernos (o Zelda 64: Recompiled e o Sonic Unleashed Recompiled sao os mais
conhecidos). Quase todos sao de codigo aberto, publicados nas releases do
GitHub de quem os fez, e precisam da COPIA DO JOGO que a pessoa ja tem (a
ROM ou o disco): o recomp traz so o codigo novo, nunca os dados do jogo.

De onde vem a lista: do catalogo publico do RecompLauncher
(https://recomplauncher.com/pc-catalog-web.json, de elripalda), um lancador
de codigo fechado que faz isso para o Windows e o Linux. O ARENA NAO leva o
lancador junto (regra do projeto: programa fechado vira tecnica nativa):
guarda so os FATOS do catalogo (nome do jogo, repositorio, licenca, o nome
do arquivo da release de cada sistema) e faz o resto sozinho em
servidor\recomps.py, com o mesmo cuidado que o lancador tem: baixar da
release oficial do GitHub, conferir a marca SHA-256, descompactar numa pasta
do ARENA (nada se instala) e abrir com a copia do jogo da pessoa.

Uso:
  servidor\python\python.exe ferramentas\atualizar_recomps.py            baixa o catalogo e regrava
  servidor\python\python.exe ferramentas\atualizar_recomps.py --de X.json  usa um catalogo ja baixado

O que entra: so os recomps com nome de jogo, console que o ARENA conhece e
arquivo de release para Windows ou Linux. O resto (sem jogo de origem, so
para macOS) fica de fora. Cada titulo guarda a ordem de preferencia do
catalogo (o "pick") e depois as estrelas do GitHub.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import baixar  # noqa: E402

URL_CATALOGO = "https://recomplauncher.com/pc-catalog-web.json"
DESTINO = os.path.join(RAIZ, "servidor", "recomps.json")

# O console de origem do catalogo -> o id da plataforma no consoles.json do ARENA.
PLATAFORMA_DA_ORIGEM = {
    "n64": "n64", "x360": "xbox360", "ps1": "ps1", "ps2": "ps2", "ps3": "ps3", "gc": "gamecube", "wii": "wii",
    "snes": "snes", "gba": "gba", "gb": "gameboy", "gbc": "gameboy", "ds": "nds", "dc": "dreamcast",
    "saturn": "saturn", "psp": "psp", "nes": "nes", "vb": "virtualboy", "genesis": "megadrive", "s32x": "sega32x",
    "arcade": "arcade", "cdi": "cdi", "amiga": "amiga", "pc": "pc",
    # Sem plataforma no ARENA (nao ha emulador deles aqui), mas o jogo de PC vale: "xbox", "ps4", "ps5", "switch",
    # "switch2", "wiiu", "3ds", "gg". Ficam de fora.
}

NOME_DA_ORIGEM = {}   # preenchido do catalogo ("origins")


def chave(texto):
    """A chave de comparacao de um titulo: minusculas, sem acento, sem 'the', so letras e numeros.
    'Legend of Zelda, The - Majora's Mask' e "The Legend of Zelda: Majora's Mask" dao a mesma chave."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", texto)   # (USA), [!]: a regiao e as marcas do arquivo
    texto = re.sub(r"\b(the|a|an)\b", " ", texto)
    texto = texto.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", texto)


def recomp_enxuto(app):
    sistemas = [s for s in (app.get("systems") or []) if s in ("windows", "linux")]
    arquivos = {s: v for s, v in (app.get("assets") or {}).items() if s in ("windows", "linux")}
    if not sistemas or not arquivos:
        return None
    origem = app.get("origin") or ""
    plataforma = PLATAFORMA_DA_ORIGEM.get(origem)
    jogo = (app.get("game") or "").strip()
    if not plataforma or not jogo:
        return None
    # A marca SHA-256 do arquivo de cada sistema, com o nome do arquivo a que ela vale (o catalogo a guarda a parte do
    # GitHub: o ARENA confere o download com ela, e nao so com a marca que o proprio GitHub publica).
    marcas = {s: {"nome": v["name"], "sha256": v["sha256"].lower()} for s, v in (app.get("files") or {}).items()
              if s in sistemas and v.get("sha256") and v.get("name")}
    apoio = app.get("support") or {}
    return {
        "id": app["id"],
        "nome": app.get("name") or app["id"],
        "repo": app.get("repo") or "",
        "licenca": app.get("license") or "",
        "jogo": jogo,
        "chave": chave(jogo),
        "origem": origem,
        "plataforma": plataforma,
        "sistemas": sistemas,
        "arquivos": arquivos,
        "marcas": marcas,
        "tag": app.get("tag") or "",
        "versao": app.get("version") or "",
        "tamanho": app.get("size") or "",
        "sdk": apoio.get("sdk") or "none",
        "preparo_facil": apoio.get("easy_setup") == "launcher",
        "estrelas": int(app.get("stars") or 0),
    }


def montar(catalogo):
    apps = {}
    for app in catalogo.get("apps") or []:
        enxuto = recomp_enxuto(app)
        if enxuto:
            apps[enxuto["id"]] = enxuto
    # A ordem de preferencia por titulo: o "pick" do catalogo primeiro, depois as estrelas.
    escolhidos = {}
    for titulo in catalogo.get("titles") or []:
        pick = (titulo.get("pick") or "").split(":", 1)[-1]
        for posicao, app_id in enumerate([pick] + [a for a in titulo.get("pc") or [] if a != pick]):
            if app_id in apps:
                escolhidos.setdefault(app_id, posicao)
    for app in apps.values():
        app["ordem"] = escolhidos.get(app["id"], 99)
    por_chave = {}
    for app in apps.values():
        por_chave.setdefault((app["plataforma"], app["chave"]), []).append(app["id"])
    for lista in por_chave.values():
        lista.sort(key=lambda i: (apps[i]["ordem"], -apps[i]["estrelas"], i))
    return {
        "_leia": ("Catalogo de recomps (jogos de console recompilados para PC), feito por "
                  "ferramentas\\atualizar_recomps.py a partir do catalogo publico do RecompLauncher "
                  "(recomplauncher.com, de elripalda). So fatos: nome, repositorio, licenca e o nome do arquivo da "
                  "release de cada sistema. O ARENA baixa cada recomp da release oficial do GitHub de quem o fez "
                  "(servidor\\recomps.py); nada do lancador vem junto."),
        "fonte": URL_CATALOGO,
        "versao_do_catalogo": catalogo.get("catalogVersion"),
        "catalogo_de": catalogo.get("updated") or "",
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "origens": {o["id"]: o["name"] for o in catalogo.get("origins") or [] if o["id"] in PLATAFORMA_DA_ORIGEM},
        "por_titulo": {"%s|%s" % k: v for k, v in sorted(por_chave.items())},
        "recomps": dict(sorted(apps.items())),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Atualiza servidor\\recomps.json")
    parser.add_argument("--de", help="um pc-catalog-web.json ja baixado")
    parser.add_argument("--para", default=DESTINO, help="onde gravar (padrao: servidor\\recomps.json)")
    a = parser.parse_args(argv)
    if a.de:
        with open(a.de, "r", encoding="utf-8") as arquivo:
            catalogo = json.load(arquivo)
    else:
        codigo, bruto = baixar.rodar(URL_CATALOGO, 120)
        if codigo != 0 or not bruto:
            sys.exit("Nao consegui baixar o catalogo (%s): codigo %s" % (URL_CATALOGO, codigo))
        catalogo = json.loads(bruto.decode("utf-8"))
    dados = montar(catalogo)
    # Um recomp por linha: o arquivo fica legivel no diff do git e com um terco do tamanho do JSON indentado.
    cabecalho = {k: v for k, v in dados.items() if k not in ("por_titulo", "recomps")}
    texto_do_cabecalho = json.dumps(cabecalho, ensure_ascii=False, indent=1)
    linhas = [texto_do_cabecalho[:texto_do_cabecalho.rfind("}")].rstrip() + ","]   # sem a chave que fecha
    linhas.append(' "por_titulo": {')
    itens = list(dados["por_titulo"].items())
    linhas += ['  %s: %s%s' % (json.dumps(k), json.dumps(v), "," if n < len(itens) - 1 else "") for n, (k, v) in enumerate(itens)]
    linhas.append(' },')
    linhas.append(' "recomps": {')
    itens = list(dados["recomps"].items())
    linhas += ['  %s: %s%s' % (json.dumps(k), json.dumps(v, ensure_ascii=False, separators=(",", ":")),
                               "," if n < len(itens) - 1 else "") for n, (k, v) in enumerate(itens)]
    linhas.append(' }')
    linhas.append('}')
    texto = "\n".join(linhas)
    json.loads(texto)   # o arquivo gravado tem que ser JSON valido
    temporario = a.para + ".tmp"
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto + "\n")
    os.replace(temporario, a.para)
    por_plataforma = {}
    for r in dados["recomps"].values():
        por_plataforma[r["plataforma"]] = por_plataforma.get(r["plataforma"], 0) + 1
    print("%d recomps de %d titulos gravados em %s (%d KB)" % (
        len(dados["recomps"]), len(dados["por_titulo"]), a.para, os.path.getsize(a.para) // 1024))
    print("por console: " + ", ".join("%s %d" % kv for kv in sorted(por_plataforma.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
