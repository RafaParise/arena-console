# -*- coding: utf-8 -*-
r"""Multitap, Fase D (teste 1): para cada console do mapa, o arquivo da
partida sai com EXATAMENTE a chave e o valor certos.

Pela rota /api/jogar de verdade, numa copia temporaria do ARENA (mesma
montagem de testes\teste_multitap_regra_de_ouro.py), com um
dados\jogadores.txt de teste e o RetroArch trocado por um falso que imita
a gravacao do retroarch.cfg ao fechar. Os cartuchos de Mega Drive levam o
cabecalho real (so os primeiros 512 bytes), porque e' ele que decide o
adaptador. Confere, caso a caso:
  - as chaves do arquivo da partida (adaptador, portas, controles lidos,
    limite de conexoes);
  - as opcoes de nucleo da COPIA (PS1, Saturn) -- e que sem adaptador de
    opcao a partida continua no arquivo de opcoes de sempre;
  - o numero e o motivo que o cartao mostra;
  - que o retroarch.cfg volta a ter nas portas o que tinha antes.

Uso:
    servidor\python\python.exe testes\teste_multitap_por_console.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import teste_multitap_regra_de_ouro as regra  # noqa: E402

RAIZ = regra.RAIZ
PYTHON = regra.PYTHON
CHAVES_CFG = (["input_libretro_device_p%d" % n for n in range(1, 13)] +
              ["input_player%d_analog_dpad_mode" % n for n in range(3, 13)] +
              ["input_max_users", "core_options_path"])

JOGADORES_TXT = """\
Super Bomberman 4 = 5
Contra = 4
Mega Bomberman = 4
Micro Machines 2 = 4
Sonic the Hedgehog 3 = 4
CTR = 4
Saturn Bomberman = 10
GoldenEye = 4
Kof97 = 6
"""

# (titulo no catalogo, modo, chaves esperadas no arquivo da partida,
#  opcoes esperadas na copia de opcoes de nucleo (vazio = sem copia),
#  jogadores no cartao, motivo esperado (trecho) ou "")
CASOS = [
    ("Super Bomberman 4", "hospedar",
     {"input_libretro_device_p2": "257", "input_max_users": "5", "netplay_max_connections": "4"}, {}, 5, ""),
    ("Super Bomberman 4", "sozinho",
     {"input_libretro_device_p2": "257", "input_max_users": "5"}, {}, 5, ""),
    ("Contra", "hospedar",
     {"input_libretro_device_p3": "513", "input_libretro_device_p4": "513",
      "input_max_users": "4", "netplay_max_connections": "3"}, {}, 4, ""),
    ("Mega Bomberman", "hospedar",
     {"input_libretro_device_p1": "1537", "input_max_users": "4", "netplay_max_connections": "3"}, {}, 4, ""),
    ("Micro Machines 2 Turbo Tournament", "sozinho",
     {"input_libretro_device_p1": "1", "input_max_users": "4"}, {}, 4, ""),
    ("Sonic the Hedgehog 3", "sozinho", {"input_max_users": "2"}, {}, 2, "cartucho"),
    ("CTR Crash Team Racing", "hospedar",
     {"input_max_users": "4", "netplay_max_connections": "3",
      "input_libretro_device_p3": "517", "input_libretro_device_p4": "517"},
     {"pcsx_rearmed_multitap": "port 1"}, 4, ""),
    ("CTR Crash Team Racing", "sozinho",
     {"input_max_users": "4", "input_libretro_device_p3": "517", "input_libretro_device_p4": "517"},
     {"swanstation_ControllerPorts_MultitapMode": "Port1Only"}, 4, ""),
    ("Saturn Bomberman", "hospedar",
     {"input_max_users": "10", "netplay_max_connections": "9",
      "input_libretro_device_p5": "517", "input_libretro_device_p10": "517"},
     {"beetle_saturn_multitap_port1": "enabled", "beetle_saturn_multitap_port2": "enabled"}, 10, ""),
    ("GoldenEye 007", "sozinho",
     {"input_max_users": "4", "input_libretro_device_p3": "1", "input_libretro_device_p4": "1"}, {}, 4, ""),
    # FBNeo: desde 26/09/2026 aceita ate 4 (fliperama de 4, como o Turtles in
    # Time); o numero de cada jogo vem do jogadores.txt. Pedindo 6, o nucleo
    # limita a 4 e o cartao explica (antes: Neo Geo limitado a 2).
    ("Kof97", "sozinho", {"input_max_users": "4"}, {}, 4, "até 4"),
]


def montar(destino):
    regra.montar(destino, None)
    # Cartucho de Mega Drive: so o cabecalho real (512 bytes), nao o jogo.
    origem = os.path.join(RAIZ, "jogos", "pessoais", "Mega Drive")
    alvo = os.path.join(destino, "jogos", "pessoais", "Mega Drive")
    if os.path.isdir(origem):
        for nome in os.listdir(origem):
            if nome.lower().endswith(".md"):
                open(os.path.join(alvo, nome), "wb").write(open(os.path.join(origem, nome), "rb").read(0x200))
    os.makedirs(os.path.join(destino, "dados"), exist_ok=True)
    open(os.path.join(destino, "dados", "jogadores.txt"), "w", encoding="utf-8").write(JOGADORES_TXT)


def trabalhador(raiz, porta):
    sys.path.insert(0, os.path.join(raiz, "servidor"))
    import arena

    cfg_real = os.path.join(raiz, "retroarch", "retroarch.cfg")

    class RetroArchFalso:
        def __init__(self, comando, **_):
            self.override = comando[comando.index("--appendconfig") + 1]

        def wait(self):
            novas = dict(re.findall(r'^(\S+) = "(.*)"$', open(self.override, encoding="utf-8").read(), re.M))
            linhas = [l for l in open(cfg_real, encoding="utf-8", errors="replace").read().splitlines()
                      if l.split("=", 1)[0].strip() not in novas]
            linhas += ['%s = "%s"' % item for item in sorted(novas.items())]
            open(cfg_real, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
            return 0

    arena.subprocess.Popen = RetroArchFalso
    arena.fazer_backup = lambda *a, **k: None
    arena.servidor_alcancavel = lambda *a, **k: False
    arena.limpar_logs_antigos = lambda *a, **k: None
    arena.VIGIA["online"] = False
    arena.controles.contar_controles = lambda: 0   # nao depende do que esta plugado
    # A copia nao leva BIOS nenhuma; aqui vale o console com a BIOS, como na
    # pasta de verdade. O PS1 sem BIOS (pelo PCSX ReARMed) tem teste proprio:
    # servidor	ests	est_ps1_sem_bios.py (14/10/2026).
    if hasattr(arena.bios, "tem_a_bios"):
        arena.bios.tem_a_bios = lambda *a, **k: True
    if hasattr(arena, "chegar_na_partida"):
        arena.chegar_na_partida = lambda *a, **k: False   # sem anfitriao de verdade
    servidor = arena.Servidor(("127.0.0.1", porta), arena.Manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    def pedir(caminho, corpo=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    _, catalogo = pedir("/api/catalogo")
    jogos = catalogo.get("jogos", [])
    saida = []
    for titulo, modo, *_ in CASOS:
        jogo = next((j for j in jogos if j["titulo"] == titulo), None)
        if not jogo:
            saida.append({"titulo": titulo, "modo": modo, "erro": "jogo nao esta no catalogo"})
            continue
        corpo = {"jogo_id": jogo["id"]}
        if modo != "sozinho":
            corpo.update({"partida": modo, "endereco": "127.0.0.1"})
        antes = regra_valores(cfg_real)
        copia = os.path.join(raiz, "dados", "opcoes_nucleo_partida.cfg")
        if os.path.exists(copia):
            os.remove(copia)
        status, resposta = pedir("/api/jogar", corpo)
        for _ in range(200):
            if not arena.JOGO_EM_ANDAMENTO["ativo"]:
                break
            time.sleep(0.05)
        texto = open(arena.ARQUIVO_OVERRIDE, encoding="utf-8").read()
        chaves = dict(re.findall(r'^(\S+) = "(.*)"$', texto, re.M))
        nucleo = {}
        if chaves.get("core_options_path", "").endswith("opcoes_nucleo_partida.cfg") and os.path.exists(copia):
            nucleo = dict(re.findall(r'^(\S*multitap\S*) = "(.*)"$', open(copia, encoding="utf-8").read(), re.M | re.I))
        # O RetroArch IGNORA o tipo de porta vindo do --appendconfig (provado
        # com os controles na mao): o que vale e' o .rmp da pasta de remap.
        rmp = {}
        pasta_rmp = chaves.get("input_remapping_directory", "")
        for base, _, arquivos in os.walk(pasta_rmp if pasta_rmp.startswith(raiz) else os.devnull):
            for nome in arquivos:
                if nome.endswith(".rmp"):
                    rmp.update(re.findall(r'^(input_libretro_device_p\d+) = "(.*)"$',
                                          open(os.path.join(base, nome), encoding="utf-8").read(), re.M))
        saida.append({"titulo": titulo, "modo": modo, "status": status, "chaves": chaves, "rmp": rmp,
                      "nucleo": nucleo, "core_options_path": chaves.get("core_options_path", ""),
                      "cartao": jogo.get("jogadores_max"), "motivo": jogo.get("motivo_jogadores", ""),
                      "cfg_antes": antes, "cfg_depois": regra_valores(cfg_real)})
    servidor.shutdown()
    print(json.dumps(saida, ensure_ascii=False))


def regra_valores(cfg):
    valores = dict.fromkeys(CHAVES_CFG)
    for linha in open(cfg, encoding="utf-8", errors="replace"):
        chave, _, valor = linha.partition("=")
        if chave.strip() in valores:
            valores[chave.strip()] = valor.strip().strip('"')
    return valores


def principal():
    pasta = tempfile.mkdtemp(prefix="arena_multitap_console_")
    try:
        montar(pasta)
        r = subprocess.run([PYTHON, os.path.abspath(__file__), "--trabalhador", pasta, "18793"],
                           capture_output=True, timeout=900)
        linhas = r.stdout.decode("utf-8", "replace").strip().splitlines()
        try:
            resultados = json.loads(linhas[-1])
        except (IndexError, ValueError):
            print("FALHOU: a copia nao respondeu.\n%s" % (r.stdout + r.stderr).decode("utf-8", "replace")[-3000:])
            return 1
        falhas = []
        for (titulo, modo, esperadas, nucleo_esperado, cartao, motivo), res in zip(CASOS, resultados):
            nome = "%s | %s" % (titulo, modo)
            if res.get("erro") or res.get("status") != 200:
                falhas.append("%s: %s" % (nome, res.get("erro") or "status %s" % res.get("status")))
                print("[FALHOU] %s" % nome)
                continue
            erros = ["%s=%r (esperado %r)" % (k, res["chaves"].get(k), v)
                     for k, v in esperadas.items() if res["chaves"].get(k) != v]
            erros += ["no .rmp %s=%r (esperado %r)" % (k, res["rmp"].get(k), v)
                      for k, v in esperadas.items()
                      if k.startswith("input_libretro_device_p") and res["rmp"].get(k) != v]
            if res["nucleo"] != nucleo_esperado:
                erros.append("opcoes de nucleo %r (esperado %r)" % (res["nucleo"], nucleo_esperado))
            if not nucleo_esperado and "opcoes_nucleo_partida" in res["core_options_path"]:
                erros.append("usou a copia de opcoes sem precisar")
            if res["cartao"] != cartao:
                erros.append("cartao %r (esperado %r)" % (res["cartao"], cartao))
            if (motivo and motivo not in res["motivo"]) or (not motivo and res["motivo"]):
                erros.append("motivo %r" % res["motivo"])
            # Portas 1 e 2 e input_max_users: toda partida reescreve, desde
            # sempre. core_options_path: toda partida grava o da pasta dela;
            # so conta como vazamento quando a partida usou a COPIA.
            vazou = {k: (res["cfg_antes"][k], res["cfg_depois"][k]) for k in CHAVES_CFG
                     if not k.endswith(("_p1", "_p2")) and k != "input_max_users"
                     and (k != "core_options_path" or nucleo_esperado)
                     and res["cfg_antes"][k] != res["cfg_depois"][k]}
            if vazou:
                erros.append("vazou para o retroarch.cfg %s" % vazou)
            print("[%s] %-45s cartao=%s %s" % ("OK" if not erros else "FALHOU", nome[:45], res["cartao"],
                                                 ", ".join("%s=%s" % (k, res["chaves"].get(k)) for k in esperadas)
                                                 + ("  nucleo=%s" % res["nucleo"] if res["nucleo"] else "")))
            for e in erros:
                print("         " + e)
                falhas.append("%s: %s" % (nome, e))
        print("\n%d caso(s), %d falha(s)." % (len(CASOS), len(falhas)))
        print("RESULTADO:", "PASSOU" if not falhas else "FALHOU")
        return 1 if falhas else 0
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--trabalhador":
        trabalhador(sys.argv[2], int(sys.argv[3]))
    else:
        sys.exit(principal())
