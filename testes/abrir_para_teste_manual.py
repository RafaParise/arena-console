# -*- coding: utf-8 -*-
r"""Multitap, Fase E (parte com o professor): abre um jogo com N jogadores
EXATAMENTE como o ARENA abriria, para testar com controles de verdade.

Gera o arquivo de partida pela rota /api/jogar numa copia temporaria (com
"<jogo> = N" num jogadores.txt SO da copia -- o seu dados\jogadores.txt nao
e' tocado) e abre o RetroArch de verdade em janela, com esse arquivo. O
registro fica salvo para eu ler depois (porta de cada controle).

Feche o jogo com F10 (como no ARENA).

Uso:
    servidor\python\python.exe testes\abrir_para_teste_manual.py "Mega Bomberman" 4
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import protege_cfg  # noqa: E402
import teste_multitap_por_console as por_console  # noqa: E402
import teste_multitap_regra_de_ouro as regra  # noqa: E402

RAIZ = regra.RAIZ
SAIDA = os.path.join(tempfile.gettempdir(), "arena_teste_manual")


def trabalhador(raiz, porta, titulo):
    sys.path.insert(0, os.path.join(raiz, "servidor"))
    import arena
    capturado = {}

    class SoGuarda:
        def __init__(self, comando, **_):
            capturado["comando"] = comando
            capturado["override"] = open(comando[comando.index("--appendconfig") + 1], encoding="utf-8").read()

        def wait(self):
            return 0

    arena.subprocess.Popen = SoGuarda
    arena.fazer_backup = lambda *a, **k: None
    arena.servidor_alcancavel = lambda *a, **k: False
    arena.limpar_logs_antigos = lambda *a, **k: None
    servidor = arena.Servidor(("127.0.0.1", porta), arena.Manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    req = urllib.request.Request("http://127.0.0.1:%d/api/catalogo" % porta)
    jogos = json.loads(urllib.request.urlopen(req, timeout=30).read())["jogos"]
    jogo = next(j for j in jogos if j["titulo"].lower().startswith(titulo.lower()))
    req = urllib.request.Request("http://127.0.0.1:%d/api/jogar" % porta,
                                 data=json.dumps({"jogo_id": jogo["id"]}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()
    for _ in range(200):
        if capturado and not arena.JOGO_EM_ANDAMENTO["ativo"]:
            break
        time.sleep(0.05)
    capturado["jogo"] = jogo
    servidor.shutdown()
    print(json.dumps(capturado, ensure_ascii=False))


def comando_nucleo(gerado):
    comando = gerado["comando"]
    return comando[comando.index("-L") + 1]


def main():
    titulo, numero = sys.argv[1], int(sys.argv[2])
    copia = tempfile.mkdtemp(prefix="arena_manual_copia_")
    por_console.montar(copia)
    open(os.path.join(copia, "dados", "jogadores.txt"), "w", encoding="utf-8").write("%s = %d\n" % (titulo, numero))
    r = subprocess.run([regra.PYTHON, os.path.abspath(__file__), "--trabalhador", copia, "18795", titulo],
                       capture_output=True, timeout=300)
    gerado = json.loads(r.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
    chaves = dict(re.findall(r'^(\S+) = "(.*)"$', gerado["override"], re.M))
    os.makedirs(SAIDA, exist_ok=True)
    pasta = tempfile.mkdtemp(prefix="jogo_", dir=SAIDA)
    for chave in ("savefile_directory", "savestate_directory", "screenshot_directory",
                  "cache_directory", "playlist_directory", "log_dir"):
        chaves[chave] = pasta
    chaves["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
    chaves["joypad_autoconfig_dir"] = os.path.join(RAIZ, "retroarch", "controles")
    chaves["config_save_on_exit"] = "false"
    if "opcoes_nucleo_partida" in chaves.get("core_options_path", ""):
        # PS1/Saturn: a copia das opcoes (com o multitap) que o ARENA gerou.
        chaves["core_options_path"] = os.path.join(copia, "dados", "opcoes_nucleo_partida.cfg")
    else:
        chaves["core_options_path"] = os.path.join(pasta, "opcoes.cfg")
    if len(sys.argv) > 3 and sys.argv[3] == "rmp":
        # Experimento: o RetroArch ignora input_libretro_device_pN vindo do
        # --appendconfig (Super Bomberman 4 abria com "SNES Joypad" na porta
        # 2). Aqui o tipo vai tambem num remapeamento SO desta partida.
        info = os.path.join(RAIZ, "retroarch", "info",
                            os.path.basename(comando_nucleo(gerado)).replace(".dll", ".info"))
        nome_nucleo = re.search(r'^corename = "(.*)"', open(info, encoding="utf-8").read(), re.M).group(1)
        pasta_rmp = os.path.join(pasta, "remaps", nome_nucleo)
        os.makedirs(pasta_rmp)
        nome_jogo = os.path.splitext(os.path.basename(gerado["jogo"]["arquivo"]))[0]
        with open(os.path.join(pasta_rmp, nome_jogo + ".rmp"), "w", encoding="utf-8") as rmp:
            for chave, valor in sorted(chaves.items()):
                if chave.startswith("input_libretro_device_p"):
                    rmp.write('%s = "%s"\n' % (chave, valor))
        chaves["input_remapping_directory"] = os.path.join(pasta, "remaps")
        print("Experimento rmp: " + os.path.join(pasta_rmp, nome_jogo + ".rmp"))
    cfg = os.path.join(pasta, "partida.cfg")
    open(cfg, "w", encoding="utf-8").write("\n".join('%s = "%s"' % kv for kv in sorted(chaves.items())) + "\n")
    comando = gerado["comando"]
    nucleo = os.path.join(RAIZ, "retroarch", "cores", os.path.basename(comando[comando.index("-L") + 1]))
    jogo = os.path.join(RAIZ, gerado["jogo"]["arquivo"])
    log = os.path.join(pasta, "registro.log")
    print("Jogo: %s | jogadores no cartao: %s" % (gerado["jogo"]["titulo"], gerado["jogo"].get("jogadores_max")))
    print("Arquivo da partida: " + ", ".join("%s=%s" % (k, v) for k, v in sorted(chaves.items())
                                             if k.startswith("input_libretro_device") or k == "input_max_users"))
    print("Abrindo... (feche com F10)")
    subprocess.run([os.path.join(RAIZ, "retroarch", "retroarch.exe"), "-L", nucleo, "--appendconfig", cfg,
                    "--verbose", "--log-file", log, jogo], cwd=os.path.join(RAIZ, "retroarch"))
    print("\nControles no registro:")
    for linha in open(log, encoding="utf-8", errors="replace"):
        if "[Autoconf]" in linha and ("porta" in linha or "port" in linha.lower()):
            print("  " + linha.strip()[:150])
    print("Registro completo: " + log)
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--trabalhador":
        trabalhador(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    else:
        sys.exit(protege_cfg.rodar(main))
