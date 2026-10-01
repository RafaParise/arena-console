# -*- coding: utf-8 -*-
r"""Perfil (tarefa 6): gaveta propria com "Meu perfil" e "Amigos", e o
apelido que da para trocar -- sem quebrar o arquivo do emulador.

Antes: o apelido so podia ser escolhido na primeira vez (ou apagando o
perfil inteiro), e ia CRU para o arquivo do RetroArch
(netplay_nickname = "..."): uma aspa digitada pelo aluno quebrava a linha,
e uma quebra de linha enfiaria outra opcao do emulador.

Confere, num ARENA isolado (copia temporaria; o dados\ real nao e' tocado):
  - limpar_apelido: sem aspas, barra invertida nem controle, ate 24;
  - /api/config troca o apelido e guarda o limpo;
  - apelido com tentativa de injecao nao cria linha nova no arquivo extra
    (e nenhum valor do arquivo extra quebra linha);
  - a tela: gaveta Perfil com as duas abas, Ajustes sem elas, ids unicos.

Uso: servidor\python\python.exe testes\teste_perfil_apelido.py
"""
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8791


def pedir(caminho, corpo=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, caminho), data=dados,
                                 method="POST" if dados else "GET",
                                 headers={"Content-Type": "application/json", "Host": "127.0.0.1:%d" % PORTA})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    destino = tempfile.mkdtemp(prefix="arena_perfil_")
    servidor = None
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests", "python", "*.log",
                                                          "perfil", "remap_partida", "logs"))
        spec = importlib.util.spec_from_file_location("arena_perfil_teste",
                                                      os.path.join(destino, "servidor", "arena.py"))
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec.loader.exec_module(arena)
        import graficos

        # 1. Limpeza.
        casos = {'Joao "o brabo"': "Joao o brabo", "  Ana   Clara  ": "Ana Clara",
                 'x"\nnetwork_cmd_enable="1': "xnetwork_cmd_enable=1", "a\\b": "ab",
                 "Zé_Ninja!": "Zé_Ninja!", "a" * 40: "a" * 24, "\t\r\n": "", None: ""}
        for bruto, esperado in casos.items():
            confere("limpar_apelido(%r) = %r" % (bruto, esperado), arena.limpar_apelido(bruto) == esperado,
                    repr(arena.limpar_apelido(bruto)))

        # 2. Trocar pelo /api/config.
        servidor = arena.Servidor(("127.0.0.1", PORTA), arena.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        time.sleep(0.4)
        resposta = pedir("/api/config", {"apelido": 'Joao "o brabo"'})
        confere("a resposta traz o apelido limpo", resposta["config"]["apelido"] == "Joao o brabo",
                resposta["config"]["apelido"])
        no_disco = json.load(open(os.path.join(destino, "dados", "config.json"), encoding="utf-8"))
        confere("o config.json guarda o limpo", no_disco.get("apelido") == "Joao o brabo")
        resposta = pedir("/api/config", {"apelido": "Lia"})
        confere("trocar de novo funciona", resposta["config"]["apelido"] == "Lia")

        # 3. Arquivo extra do RetroArch: nada de linha injetada.
        arena.ARQUIVO_OVERRIDE = os.path.join(destino, "override_teste.cfg")
        injetado = 'x"\nnetwork_cmd_enable = "true'
        extras = graficos.opcoes_de_partida(injetado, True)
        caminho = arena.gravar_override(arena.carregar_config(), extras=extras, em_partida=True)
        linhas = open(caminho, encoding="utf-8").read().splitlines()
        comandos = [l for l in linhas if l.startswith("network_cmd_enable")]
        confere("so UMA linha de network_cmd_enable, e desligada", comandos == ['network_cmd_enable = "false"'],
                str(comandos))
        apelido_linha = [l for l in linhas if l.startswith("netplay_nickname")]
        confere("netplay_nickname sem aspa no meio",
                len(apelido_linha) == 1 and apelido_linha[0].count('"') == 2, str(apelido_linha))
        confere("toda linha do arquivo extra e' chave = \"valor\" (ou comentario)",
                all(l.startswith("#") or re.match(r'^[A-Za-z0-9_]+ = "[^"\r\n]*"$', l) for l in linhas),
                str([l for l in linhas if not (l.startswith("#") or re.match(r'^[A-Za-z0-9_]+ = "[^"]*"$', l))][:3]))
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)

    # 4. A tela.
    html = open(os.path.join(RAIZ, "launcher", "index.html"), encoding="utf-8").read()
    js = open(os.path.join(RAIZ, "launcher", "app.js"), encoding="utf-8").read()
    ids = re.findall(r'\bid="([^"]+)"', html)
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    confere("nenhum id repetido na tela", not repetidos, str(repetidos))
    gaveta = html.split('id="gavetaPerfil"', 1)[-1].split("</aside>", 1)[0]
    confere("gaveta Perfil com as abas Meu perfil e Amigos",
            'data-aba="perfil"' in gaveta and 'data-aba="rede"' in gaveta
            and 'data-painel="perfil"' in gaveta and 'data-painel="rede"' in gaveta)
    confere("campo e botao de trocar o apelido na gaveta",
            'id="campoApelido"' in gaveta and 'id="btnTrocarApelido"' in gaveta)
    ajustes = html.split('id="gavetaAjustes"', 1)[-1].split("</aside>", 1)[0]
    confere("Ajustes sem as abas Amigos e Perfil",
            'data-aba="rede"' not in ajustes and 'data-aba="perfil"' not in ajustes)
    confere("botoes do topo ligados (Perfil e Amigos abrem a gaveta)",
            'abrirPerfil("perfil")' in js and 'abrirPerfil("rede")' in js and "trocarApelido()" in js)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Perfil e apelido: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
