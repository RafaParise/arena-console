# -*- coding: utf-8 -*-
r"""Paridade das FUNCOES entre as versoes, medida por busca no codigo (sem pip, sem agentes):

  - as rotas /api/ que a tela (launcher\app.js) chama, as que o servidor atende (servidor\arena.py) e as que a versao
    web do Chromebook atende (launcher\navegador\*.js): o que a tela chama e o navegador nao atende;
  - os elementos que a tela marca "so Windows" (data-so-windows) e a regra que os esconde;
  - as chamadas do Windows no servidor (ctypes.windll, os.startfile, powershell, taskkill, winreg...) e se o arquivo
    tem alguma guarda de sistema (WINDOWS/NO_WINDOWS/ANDROID/os.name/sys.platform) em volta.

Uso: servidor\python\python.exe ferramentas\paridade_de_funcoes.py [--saida docs\auditoria5\paridade_de_funcoes.json]
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROTA = re.compile(r"/api/[a-z0-9_\-]+(?:/[a-z0-9_\-]+)*")
WINDOWS_ONLY = re.compile(r"ctypes\.windll|os\.startfile|powershell|taskkill|tasklist|winreg|wmic|\bwindll\b|msvcrt|CREATE_NO_WINDOW|STARTUPINFO")
GUARDA = re.compile(r"NO_WINDOWS|WINDOWS\b|ANDROID|os\.name|sys\.platform|platform\.system|plataforma_do_sistema")


def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8", errors="replace") as arquivo:
        return arquivo.read()


def main():
    analise = argparse.ArgumentParser()
    analise.add_argument("--saida", default=os.path.join(RAIZ, "docs", "auditoria5", "paridade_de_funcoes.json"))
    argumentos = analise.parse_args()

    tela = set(ROTA.findall(ler("launcher/app.js")))
    servidor_texto = ler("servidor/arena.py")
    servidor = set(re.findall(r'caminho\s*(?:==|in\s*\(?)\s*\(?"(/api/[^"]+)"', servidor_texto))
    servidor |= set(re.findall(r'"(/api/[a-z0-9_\-/]+)"', servidor_texto))
    navegador_texto = "".join(ler("launcher/navegador/" + n) for n in os.listdir(os.path.join(RAIZ, "launcher", "navegador"))
                              if n.endswith(".js") and n not in ("dados.js", "livres.js"))
    navegador = set(ROTA.findall(navegador_texto))

    html = ler("launcher/index.html")
    so_windows = []
    for achado in re.finditer(r"<(\w+)([^>]*data-so-windows[^>]*)>", html):
        marca = re.search(r'(?:id|data-aba|data-painel)="([^"]+)"', achado.group(2))
        so_windows.append("%s %s" % (achado.group(1), marca.group(1) if marca else "(sem id)"))
    regra = re.findall(r"[^\n]*so-windows[^\n]*|[^\n]*soWindows[^\n]*", ler("launcher/app.js"))

    usos = []
    for pasta in ("servidor",):
        for nome in sorted(os.listdir(os.path.join(RAIZ, pasta))):
            if not nome.endswith(".py"):
                continue
            texto = ler(pasta + "/" + nome)
            achados = sorted(set(m.group(0) for m in WINDOWS_ONLY.finditer(texto)))
            if achados:
                usos.append({"arquivo": pasta + "/" + nome, "chamadas": achados, "tem_guarda_de_sistema": bool(GUARDA.search(texto))})

    resultado = {
        "rotas_da_tela": len(tela),
        "rotas_do_servidor": len(servidor),
        "a_tela_chama_e_o_servidor_nao_tem": sorted(r for r in tela if r not in servidor and not any(s.startswith(r) for s in servidor)),
        "a_tela_chama_e_o_navegador_nao_atende": sorted(r for r in tela if r not in navegador),
        "elementos_so_windows_na_tela": so_windows,
        "regra_que_esconde_so_windows": [linha.strip()[:160] for linha in regra][:8],
        "arquivos_do_servidor_com_chamada_do_windows": usos,
    }
    os.makedirs(os.path.dirname(argumentos.saida), exist_ok=True)
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print("Tela chama %d rotas; servidor atende %d; navegador (web) atende %d." % (len(tela), len(servidor), len(navegador)))
    print("A tela chama e o servidor nao tem: %s" % (resultado["a_tela_chama_e_o_servidor_nao_tem"] or "nenhuma"))
    print("A tela chama e o navegador nao atende (%d): %s" % (len(resultado["a_tela_chama_e_o_navegador_nao_atende"]),
                                                              ", ".join(resultado["a_tela_chama_e_o_navegador_nao_atende"][:40])))
    print("Elementos so Windows na tela (%d): %s" % (len(so_windows), "; ".join(so_windows)))
    sem_guarda = [u for u in usos if not u["tem_guarda_de_sistema"]]
    print("Arquivos do servidor com chamada do Windows: %d (sem nenhuma guarda de sistema: %s)" % (
        len(usos), ", ".join(u["arquivo"] for u in sem_guarda) or "nenhum"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
