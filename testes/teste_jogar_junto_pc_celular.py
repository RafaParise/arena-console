# -*- coding: utf-8 -*-
"""Jogar Junto ENTRE VERSOES: o celular (ARENA do Android) hospeda e o computador (RetroArch do Windows) entra, no mesmo
jogo (Super Bomberman 4, Super Nintendo, snes9x nos dois). Pedido do Rafael (25/10/2026): "jogar do celular como player 2
em uma partida hospedada no pc ou vice versa [...] em qualquer versao".

Como: o celular recebe o pedido pela API do proprio ARENA (/api/jogar, partida "hospedar"), pelo celular_arena.py; o computador abre
o RetroArch com os MESMOS argumentos e opcoes que o /api/jogar montaria (graficos.argumentos_de_partida e opcoes_de_partida),
numa pasta temporaria, sem tocar em dados\\, saves nem no override real. Vale com o celular no cabo e na mesma rede Wi-Fi do computador.

Uso:  servidor\\python\\python.exe testes\\teste_jogar_junto_pc_celular.py [--pc-hospeda]
Mede: se o outro lado entra (o log do RetroArch de quem hospeda diz "se juntou"), quanto leva e se os dois seguem vivos depois.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import celular_arena as ca  # noqa: E402
import celular_mao  # noqa: E402
import teste_netplay_5_jogadores as n5  # noqa: E402  (montar_override, carregar_modulos e as constantes do jogo)

TITULO = "Super Bomberman 4"
ATRASO = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--atraso=")), "0"))      # quadros de folga do lado do PC
PORTA = n5.PORTA_PARTIDA


def ip_do_celular(celular):
    saida = celular.shell("ip -f inet addr show wlan0")
    for linha in saida.splitlines():
        if "inet " in linha:
            return linha.split()[1].split("/")[0]
    raise SystemExit("O celular nao esta no Wi-Fi (sem IP na wlan0).")


def ip_do_computador():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.18.4", 9))
        return s.getsockname()[0]
    finally:
        s.close()


def log_do_pc(pasta):
    nomes = sorted(n for n in os.listdir(pasta) if n.startswith("retroarch__") and n.endswith(".log"))
    if not nomes:
        return ""
    with open(os.path.join(pasta, nomes[-1]), encoding="utf-8", errors="ignore") as arquivo:
        return arquivo.read()


def main():
    pc_hospeda = "--pc-hospeda" in sys.argv
    pelo_cabo = "--cabo" in sys.argv        # a partida (TCP) vai pelo cabo USB (adb forward/reverse) em vez do Wi-Fi
    celular = celular_mao.Celular()
    ip_celular, ip_pc = ip_do_celular(celular), ip_do_computador()
    if pelo_cabo:
        if pc_hospeda:
            celular.texto("reverse", "tcp:%d" % PORTA, "tcp:%d" % PORTA)          # o 127.0.0.1 do celular chega no PC
            ip_pc = "127.0.0.1"
        else:
            celular.texto("forward", "tcp:%d" % PORTA, "tcp:%d" % PORTA)          # o 127.0.0.1 do PC chega no celular
            ip_celular = "127.0.0.1"
    print("celular %s, computador %s; hospeda: %s" % (ip_celular, ip_pc, "o computador" if pc_hospeda else "o celular"), flush=True)
    arena, graficos = n5.carregar_modulos()
    pagina = ca.abrir(segundos=120)
    resultado = {"hospeda": "pc" if pc_hospeda else "celular", "ip_celular": ip_celular, "ip_pc": ip_pc}
    pasta = tempfile.mkdtemp(prefix="arena_pc_celular_")
    pc = None
    try:
        jogos = [j for j in ca.catalogo(pagina) if j["titulo"] == TITULO and j["plataforma"] == "snes"]
        if not jogos:
            raise SystemExit("O celular nao tem o %s (Super Nintendo)." % TITULO)
        jogo_id = jogos[0]["id"]

        def comando_do_pc(hospedar):
            opcoes = graficos.opcoes_de_partida(apelido="PC", hospedar=hospedar, jogador=1 if hospedar else 2, multitap=False, atraso=ATRASO, proximo_livre="--auto" in sys.argv)
            argumentos = graficos.argumentos_de_partida(hospedar, endereco=ip_celular, porta=PORTA)
            cfg = os.path.join(pasta, "override.cfg")
            n5.montar_override(cfg, pasta, arena, graficos, opcoes)
            return [n5.RETROARCH, "-L", n5.CORE, "--appendconfig", cfg] + argumentos + [n5.JOGO]

        def abrir_pc(hospedar):
            return subprocess.Popen(comando_do_pc(hospedar), cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        corpo_celular = {"jogo_id": jogo_id, "id": jogo_id, "partida": "entrar" if pc_hospeda else "hospedar"}
        if pc_hospeda:
            corpo_celular.update({"endereco": ip_pc, "jogador": 2})
            pc = abrir_pc(True)
            time.sleep(8)
        t0 = time.monotonic()
        resposta = ca.pedir(pagina, "/api/jogar", corpo_celular)
        resultado["resposta_do_celular"] = {k: resposta.get(k) for k in ("ok", "erro", "aviso", "papel")} if isinstance(resposta, dict) else str(resposta)
        print("celular:", resultado["resposta_do_celular"], flush=True)
        if not pc_hospeda:
            time.sleep(16)                                   # o RetroArch do celular precisa abrir e escutar
            pc = abrir_pc(False)
        fim = time.monotonic() + 40
        entrou = None
        while time.monotonic() < fim and entrou is None:
            texto = log_do_pc(pasta).lower()
            # o PC hospedando tambem escreve "Voce se juntou como jogador 1": so vale a linha do OUTRO lado (jogador 2)
            if "[netplay]" in texto and ("juntou como o jogador 2" in texto or "juntou como jogador 2" in texto):
                entrou = round(time.monotonic() - t0, 1)
            time.sleep(1)
        # quanto tempo a partida aguenta? olha o log do computador a cada segundo, por ate 45 s depois da entrada
        caiu = None
        if entrou is not None:
            inicio = time.monotonic()
            while time.monotonic() - inicio < 45 and caiu is None:
                if "desconect" in log_do_pc(pasta).lower() or "disconnect" in log_do_pc(pasta).lower():
                    caiu = round(time.monotonic() - inicio, 1)
                time.sleep(1)
        resultado["caiu_depois_de_s"] = caiu            # None = ainda de pe depois de 45 s
        resultado["pc_vivo_depois"] = pc.poll() is None
        linhas = [l.strip() for l in log_do_pc(pasta).splitlines() if "[netplay]" in l.lower()]
        resultado["pc_netplay"] = linhas[-25:]
        registro = ca.pedir(pagina, "/api/android/registro")
        texto_celular = chr(10).join(str(l) for l in registro.get("linhas", [])) if isinstance(registro, dict) else ""
        resultado["celular_netplay"] = [l.strip() for l in texto_celular.splitlines() if "netplay" in l.lower()][-25:]
        resultado["celular_registro_campos"] = sorted(registro) if isinstance(registro, dict) else None
        resultado["celular_registro_cauda"] = [l.strip() for l in texto_celular.splitlines()][-30:]
        estado = ca.pedir(pagina, "/api/estado")
        resultado["celular_jogo_em_andamento"] = (estado or {}).get("jogo_em_andamento")
        resultado["entrou_em_s"] = entrou
        print(json.dumps(resultado, ensure_ascii=False, indent=2), flush=True)
        with open(os.path.join(RAIZ, "docs", "jogar_junto_pc_celular_bruto.json"), "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
        return 0 if entrou is not None and resultado["pc_vivo_depois"] else 1
    finally:
        if pc is not None and pc.poll() is None:
            pc.kill()
        pagina.fechar()
        if pelo_cabo:
            celular.texto("forward", "--remove", "tcp:%d" % PORTA)
            celular.texto("reverse", "--remove", "tcp:%d" % PORTA)
        # fecha o jogo do celular: o RetroArch dele e' o processo do app; abrir o ARENA de novo o traz de volta
        celular.shell("am force-stop io.github.rafaparise.arena")
        time.sleep(2)
        celular.shell("am start -n io.github.rafaparise.arena/.ArenaActivity")


if __name__ == "__main__":
    sys.exit(main())
