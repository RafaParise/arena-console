# -*- coding: utf-8 -*-
"""Matriz de paridade dos CONSOLES entre as versoes do ARENA (Windows, Linux, Android arm64 e x86_64, navegador).

Para cada console de servidor\\consoles.json diz se o nucleo (ou o emulador de fora) existe em cada versao:
  Windows : retroarch\\cores\\<nucleo>.dll (ou o emulador de fora, em emuladores\\)
  Linux   : retroarch\\cores\\<nucleo>.so
  Android : a marca do nucleo em ferramentas\\android_nucleos.json (por ABI)
  Navegador (Chromebook sem instalar): o console tem "core_navegador"
Uso:  servidor\\python\\python.exe ferramentas\\matriz_de_paridade.py [--md]
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))

import montar_android  # noqa: E402

OUTRO_NOME = montar_android.OUTRO_NOME   # nomes diferentes no Android (mupen64plus_next_gles3, mamearcade...)


def nomes_android(plataforma):
    """Os .so do Android que este console usa (mesma regra de montar_android.nucleos_do_arena)."""
    no_android = plataforma.get("android") if isinstance(plataforma.get("android"), dict) else {}
    achados = []
    for nucleo in (plataforma.get("core"), plataforma.get("core_netplay"), (plataforma.get("livre") or {}).get("core"),
                   no_android.get("core"), no_android.get("core_netplay"), (no_android.get("livre") or {}).get("core")):
        if nucleo:
            base = os.path.splitext(nucleo)[0]
            achados.append(OUTRO_NOME.get(base, base) + "_android.so")
    return achados


def montar():
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        plataformas = json.load(arquivo)["plataformas"]
    with open(os.path.join(RAIZ, "ferramentas", "android_nucleos.json"), encoding="utf-8") as arquivo:
        marcas = json.load(arquivo)
    pasta = os.path.join(RAIZ, "retroarch", "cores")
    existentes = set(os.listdir(pasta)) if os.path.isdir(pasta) else set()
    linhas = []
    for p in plataformas:
        externo = p.get("externo")
        nucleo = p.get("core") or ""
        win = bool(externo) or (nucleo in existentes)
        linux = bool(externo) or (nucleo.replace(".dll", ".so") in existentes)
        so = nomes_android(p)
        a64 = bool(so) and all(n in marcas.get("arm64-v8a", {}) for n in so)
        ax = bool(so) and all(n in marcas.get("x86_64", {}) for n in so)
        if externo and not so:
            a64 = ax = False
        linhas.append({"id": p["id"], "nome": p["nome"], "windows": win, "linux": linux, "android_arm64": a64,
                       "android_x86_64": ax, "navegador": bool(p.get("core_navegador")), "externo": bool(externo)})
    return linhas


def principal(argumentos):
    linhas = montar()
    colunas = ("windows", "linux", "android_arm64", "android_x86_64", "navegador")
    if "--md" in argumentos:
        print("| Console | Windows | Linux | Android arm64 | Android x86_64 | Navegador |")
        print("|---|---|---|---|---|---|")
        for l in linhas:
            print("| %s%s | %s |" % (l["nome"], " (de fora)" if l["externo"] else "",
                                    " | ".join("sim" if l[c] else "**não**" for c in colunas)))
    faltas = {c: [l["id"] for l in linhas if not l[c]] for c in colunas}
    print("# %d consoles" % len(linhas), file=sys.stderr)
    for c in colunas:
        print("# sem %s (%d): %s" % (c, len(faltas[c]), ", ".join(faltas[c])), file=sys.stderr)


if __name__ == "__main__":
    principal(sys.argv[1:])
