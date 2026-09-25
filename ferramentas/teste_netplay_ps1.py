# -*- coding: utf-8 -*-
"""Testa Jogar Junto de PS1 (Metal Slug X) de ponta a ponta:
hospeda pelo ARENA de verdade (API /api/jogar), entra com uma segunda
instancia do RetroArch conectando em 127.0.0.1, confere a conexao real.

Roda: servidor\\python\\python.exe ferramentas\\teste_netplay_ps1.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

PASTA_DADOS = os.path.join(RAIZ, "dados")
PORTA_ARENA = 8777
PORTA_PARTIDA = 55435


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:%d%s" % (PORTA_ARENA, caminho)
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def log_mais_recente_apos(momento):
    candidatos = []
    for nome in os.listdir(PASTA_DADOS):
        if nome.endswith(".log"):
            caminho = os.path.join(PASTA_DADOS, nome)
            if os.path.getmtime(caminho) >= momento - 1:
                candidatos.append(caminho)
    if not candidatos:
        return None
    candidatos.sort(key=os.path.getmtime)
    return candidatos[-1]


def main():
    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"]
                    if "Metal Slug" in j["titulo"] and j["id"].endswith(".cue")),
                   None)
        if not jogo:
            print("FALHOU: Metal Slug X nao esta no catalogo.")
            return 1

        momento_host = time.time()
        resp = pedir("/api/jogar", {
            "jogo_id": jogo["id"], "apelido": "hospedeiro", "partida": "hospedar"})
        print("Resposta do host:", resp)
        if not resp.get("ok"):
            print("FALHOU ao hospedar.")
            return 1

        time.sleep(6)

        log_host = log_mais_recente_apos(momento_host)
        if not log_host:
            print("FALHOU: nenhum log novo do host.")
            return 1
        with open(log_host, "r", encoding="utf-8", errors="replace") as f:
            texto_host_antes = f.read()
        if "nao tem suporte para Netplay" in texto_host_antes:
            print("FALHOU: o host recusou o netplay.")
            print(texto_host_antes)
            return 1
        print("Host abriu sem recusar netplay. BIOS/nucleo:")
        for linha in texto_host_antes.splitlines():
            if "bios" in linha.lower() or "core" in linha.lower():
                print("  " + linha)

        # Entra como convidado, com uma segunda instancia manual.
        core = os.path.join(RAIZ, "retroarch", "cores", "pcsx_rearmed_libretro.dll")
        rom = os.path.join(RAIZ, jogo["arquivo"].replace("/", os.sep))
        exe = os.path.join(RAIZ, "retroarch", "retroarch.exe")
        opcoes = graficos.opcoes_de_partida("convidado", hospedar=False, jogador=2)
        override_convidado = os.path.join(RAIZ, "ferramentas", "_join_ps1.cfg")
        with open(override_convidado, "w", encoding="utf-8") as f:
            for k, v in opcoes.items():
                f.write('%s = "%s"\n' % (k, v))

        comando = [exe, "-L", core, "--appendconfig", override_convidado,
                  "--connect", "127.0.0.1", "--port", str(PORTA_PARTIDA), rom]
        convidado_proc = subprocess.Popen(comando, cwd=os.path.join(RAIZ, "retroarch"))
        print("Convidado rodando, PID", convidado_proc.pid)
        time.sleep(6)
        vivo = convidado_proc.poll() is None
        print("convidado vivo apos 6s:", vivo)

        with open(log_host, "r", encoding="utf-8", errors="replace") as f:
            texto_host_depois = f.read()
        novo_trecho = texto_host_depois[len(texto_host_antes):]
        print("--- o que apareceu no log do host depois do convidado entrar ---")
        print(novo_trecho if novo_trecho.strip() else "(nada novo)")

        ok = "jogador 2" in novo_trecho.lower() or "convidado" in novo_trecho.lower()

        convidado_proc.terminate()
        try:
            convidado_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            convidado_proc.kill()
        os.remove(override_convidado)

        if not ok:
            print("FALHOU: nao vi confirmacao de conexao no log do host.")
            return 1
        print("OK: convidado conectou e entrou como jogador 2.")
        return 0
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "retroarch.exe"],
                       capture_output=True)
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
