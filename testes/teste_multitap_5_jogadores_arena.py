# -*- coding: utf-8 -*-
r"""Multitap, Fase D (teste 2): 1 hospedeiro + 4 convidados no mesmo
computador, com o arquivo de partida que o ARENA GERA -- nao montado a mao.

Por que este teste existe: o teste antigo (teste_netplay_5_jogadores.py)
montava o arquivo da partida por conta propria, com multitap=True, e por
isso o "257" estava la. No ARENA de verdade as opcoes de controle
escreviam "1" por cima, e o adaptador nunca chegava (achado da Fase B).
Teste que nao passa pelo caminho real prova o caminho errado.

Como:
  1. Numa copia temporaria do ARENA (com "Super Bomberman 4 = 5" no
     jogadores.txt), chama o /api/jogar de verdade 5 vezes -- hospedar e
     entrar como jogador 2, 3, 4 e 5 -- com o RetroArch trocado por um
     falso que so GUARDA o arquivo de partida e o comando gerados.
  2. Abre 5 RetroArch de verdade com esses arquivos, trocando SO as pastas
     (saves, estados, registro) para cada um ter a sua.
  3. Le o registro de cada um: quem entrou e em qual jogador, e se o nucleo
     recebeu o Multitap na porta 2.

Uso:
    servidor\python\python.exe testes\teste_multitap_5_jogadores_arena.py
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
import protege_cfg  # noqa: E402
import teste_multitap_regra_de_ouro as regra  # noqa: E402

RAIZ = regra.RAIZ
PYTHON = regra.PYTHON
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
JOGO_TITULO = "Super Bomberman 4"
PAPEIS = [("hospedeiro", "hospedar", 1, "Anfitriao"), ("convidado2", "entrar", 2, "Jogador2"),
          ("convidado3", "entrar", 3, "Jogador3"), ("convidado4", "entrar", 4, "Jogador4"),
          ("convidado5", "entrar", 5, "Jogador5")]
PASTAS_DA_INSTANCIA = ("savefile_directory", "savestate_directory", "screenshot_directory",
                       "cache_directory", "playlist_directory", "log_dir")


# --- 1. o que o ARENA gera (processo separado, dentro da copia) -----------

def trabalhador(raiz, porta):
    sys.path.insert(0, os.path.join(raiz, "servidor"))
    import arena
    capturados = []

    class RetroArchQueSoGuarda:
        def __init__(self, comando, **_):
            override = comando[comando.index("--appendconfig") + 1]
            capturados.append({"comando": comando,
                               "override": open(override, encoding="utf-8").read()})

        def wait(self):
            return 0

    arena.subprocess.Popen = RetroArchQueSoGuarda
    arena.fazer_backup = lambda *a, **k: None
    arena.servidor_alcancavel = lambda *a, **k: False
    arena.limpar_logs_antigos = lambda *a, **k: None
    arena.VIGIA["online"] = False
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
    jogo = next(j for j in catalogo["jogos"] if j["titulo"] == JOGO_TITULO)
    saida = []
    for nome, modo, jogador, apelido in PAPEIS:
        corpo = {"jogo_id": jogo["id"], "partida": modo, "apelido": apelido,
                 "endereco": "127.0.0.1", "jogador": jogador}
        status, resposta = pedir("/api/jogar", corpo)
        for _ in range(200):
            if not arena.JOGO_EM_ANDAMENTO["ativo"]:
                break
            time.sleep(0.05)
        saida.append({"nome": nome, "status": status, "papel": resposta.get("papel"),
                      **(capturados[-1] if capturados else {})})
    servidor.shutdown()
    print(json.dumps(saida, ensure_ascii=False))


# --- 2 e 3. abrir de verdade e ler os registros ---------------------------

def registro(pasta):
    nomes = sorted(n for n in os.listdir(pasta) if n.startswith("retroarch") and n.endswith(".log"))
    if not nomes:
        return ""
    return open(os.path.join(pasta, nomes[-1]), encoding="utf-8", errors="ignore").read()


def esperar(pasta, texto, limite):
    inicio = time.monotonic()
    while time.monotonic() - inicio < limite:
        if texto.lower() in registro(pasta).lower():
            return round(time.monotonic() - inicio, 2)
        time.sleep(0.3)
    return None


def main():
    copia = tempfile.mkdtemp(prefix="arena_5j_copia_")
    execucao = tempfile.mkdtemp(prefix="arena_5j_execucao_")
    processos = []
    try:
        regra.montar(copia, None)
        open(os.path.join(copia, "dados", "jogadores.txt"), "w", encoding="utf-8").write(
            "%s = 5\n" % JOGO_TITULO)
        r = subprocess.run([PYTHON, os.path.abspath(__file__), "--trabalhador", copia, "18794"],
                           capture_output=True, timeout=300)
        try:
            gerados = json.loads(r.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
        except (IndexError, ValueError):
            print("FALHOU: a copia nao respondeu.\n%s" % (r.stdout + r.stderr).decode("utf-8", "replace")[-3000:])
            return 1

        print("O que o ARENA gerou para cada um:")
        falhas = []
        for g in gerados:
            chaves = dict(re.findall(r'^(\S+) = "(.*)"$', g.get("override", ""), re.M))
            print("  %-11s status=%s papel=%-10s p2=%s max_users=%s conexoes=%s pede_jogador=%s" % (
                g["nome"], g["status"], g.get("papel"), chaves.get("input_libretro_device_p2"),
                chaves.get("input_max_users"), chaves.get("netplay_max_connections"),
                [k[-1] for k, v in chaves.items() if k.startswith("netplay_request_device_p") and v == "true"]))
            if g["status"] != 200 or chaves.get("input_libretro_device_p2") != "257":
                falhas.append("%s: o ARENA nao gerou o Multitap (p2=%s)" % (g["nome"], chaves.get("input_libretro_device_p2")))
            g["chaves"] = chaves

        # Abre os 5 com o que o ARENA gerou. Troca so as pastas e o registro
        # (cada instancia precisa das suas), e o caminho do nucleo e do jogo
        # (na copia eles sao arquivos vazios).
        nucleo = os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll")
        jogo = next(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo", n)
                    for n in os.listdir(os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo"))
                    if n.startswith(JOGO_TITULO))
        pasta_host = None
        for g in gerados:
            pasta = os.path.join(execucao, g["nome"])
            os.makedirs(pasta)
            chaves = dict(g["chaves"])
            for chave in PASTAS_DA_INSTANCIA:
                chaves[chave] = pasta
            chaves["system_directory"] = os.path.join(RAIZ, "retroarch", "system")
            chaves["core_options_path"] = os.path.join(pasta, "opcoes.cfg")
            chaves.update({"log_to_file": "true", "log_verbosity": "true", "frontend_log_level": "0",
                           "video_fullscreen": "false", "config_save_on_exit": "false"})
            cfg = os.path.join(pasta, "partida.cfg")
            open(cfg, "w", encoding="utf-8").write("\n".join('%s = "%s"' % kv for kv in sorted(chaves.items())) + "\n")
            comando = g["comando"]
            argumentos = comando[comando.index("--appendconfig") + 2:-1]  # --host / --connect ...
            processo = subprocess.Popen([RETROARCH, "-L", nucleo, "--appendconfig", cfg] + argumentos + [jogo],
                                        cwd=os.path.dirname(RETROARCH), stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            processos.append((g["nome"], processo, pasta))
            if g["nome"] == "hospedeiro":
                pasta_host = pasta
                time.sleep(10)
            else:
                apelido = next(p[3] for p in PAPEIS if p[0] == g["nome"])
                t = esperar(pasta_host, "%s se juntou" % apelido, 20)
                print("  %s entrou: %s" % (g["nome"], ("%.1f s" % t) if t is not None else "NAO"))
                time.sleep(2)
        time.sleep(8)

        print("\nNo registro de cada um:")
        for (nome, processo, pasta), (_, _, jogador, _) in zip(processos, PAPEIS):
            texto = registro(pasta)
            entrou = re.search(r"Você se juntou como jogador (\d+)", texto)
            porta2 = re.search(r"(?i)(multitap|257)", "\n".join(
                l for l in texto.splitlines() if "port" in l.lower() or "device" in l.lower() or "dispositivo" in l.lower()))
            vivo = processo.poll() is None
            print("  %-11s vivo=%s entrou_como=%s multitap_no_registro=%s" % (
                nome, vivo, entrou.group(1) if entrou else "-", bool(porta2)))
            if not vivo:
                falhas.append("%s: fechou sozinho" % nome)
            if not entrou or int(entrou.group(1)) != jogador:
                falhas.append("%s: nao ganhou o jogador %d" % (nome, jogador))
        print("\n%s" % ("\n".join("FALHA: " + f for f in falhas) if falhas else "Os 5 entraram, cada um no seu jogador."))
        print("RESULTADO:", "PASSOU" if not falhas else "FALHOU")
        return 1 if falhas else 0
    finally:
        for _, processo, _ in processos:
            try:
                processo.terminate()
            except OSError:
                pass
        time.sleep(2)
        for _, processo, _ in processos:
            if processo.poll() is None:
                processo.kill()
        shutil.rmtree(copia, ignore_errors=True)
        shutil.rmtree(execucao, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--trabalhador":
        trabalhador(sys.argv[2], int(sys.argv[3]))
    else:
        sys.exit(protege_cfg.rodar(main))
