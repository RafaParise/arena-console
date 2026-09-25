# -*- coding: utf-8 -*-
"""Testa a pista da comunidade: zerar netplay_check_frames ajuda o PCSX
ReARMed no Jogar Junto? (ver "Netplay de PS1" no CLAUDE.md - pista NAO
adotada ainda, so pra testar).

netplay_check_frames manda o RetroArch comparar o estado do host com o do
convidado a cada N quadros (600 = a cada ~10s a 60fps), pra pegar
dessincronia. Isso serializa o estado inteiro do nucleo (CPU+GPU+SPU+
memory card no caso do PS1) e manda pela rede - documentado como pesado
o bastante pra travar um instante, e a comunidade recomenda zerar (=
desliga a checagem) pra suavizar em nucleos mais pesados.

Este teste hospeda de verdade e conecta um convidado de verdade (mesmo
jeito que teste_netplay_ps1.py), roda por 25s (mais que um ciclo de 600
quadros) com o valor padrao (600) e depois com 0, e compara:
 1. quantas vezes o log mostra a checagem de CRC acontecendo;
 2. se os dois continuam conectados sem cair.

Mexe de verdade no retroarch.cfg por um instante (RESTAURA no finally) -
e' a unica forma de mudar esse valor sem alterar arena.py so pra medir.

Roda: servidor\\python\\python.exe ferramentas\\teste_netplay_check_frames.py
"""
import ctypes
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def cpu_acumulada_do_processo(pid):
    """Segundos de CPU (usuario+sistema) que o processo ja consumiu, lendo
    direto do Windows (GetProcessTimes) - sem precisar instalar nada."""
    h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        criacao = ctypes.c_ulonglong(0)
        saida = ctypes.c_ulonglong(0)
        kernel = ctypes.c_ulonglong(0)
        usuario = ctypes.c_ulonglong(0)
        ok = ctypes.windll.kernel32.GetProcessTimes(
            h, ctypes.byref(criacao), ctypes.byref(saida),
            ctypes.byref(kernel), ctypes.byref(usuario))
        if not ok:
            return None
        return (kernel.value + usuario.value) / 1e7  # 100ns -> segundos
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def pid_do_retroarch():
    saida = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq retroarch.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True)
    linhas = [l for l in saida.stdout.splitlines() if l.strip()]
    if not linhas:
        return None
    campos = linhas[0].strip('"').split('","')
    try:
        return int(campos[1])
    except (IndexError, ValueError):
        return None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

PASTA_DADOS = os.path.join(RAIZ, "dados")
CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")
PORTA_ARENA = 8777
PORTA_PARTIDA = 55435
DURACAO = 25


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:%d%s" % (PORTA_ARENA, caminho)
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def trocar_check_frames(valor):
    with open(CFG, "r", encoding="utf-8") as f:
        texto = f.read()
    novo = re.sub(r'^netplay_check_frames = "\d+"', 'netplay_check_frames = "%d"' % valor,
                  texto, count=1, flags=re.MULTILINE)
    with open(CFG, "w", encoding="utf-8") as f:
        f.write(novo)


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
    return candidatos[0]  # o do host, criado primeiro


def rodar_sessao(valor_check_frames):
    trocar_check_frames(valor_check_frames)

    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    time.sleep(3)

    convidado_proc = None
    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"]
                    if "Metal Slug" in j["titulo"] and j["id"].endswith(".cue")), None)
        if not jogo:
            print("FALHOU: Metal Slug X nao esta no catalogo.")
            return None

        momento_host = time.time()
        resp = pedir("/api/jogar", {
            "jogo_id": jogo["id"], "apelido": "hospedeiro", "partida": "hospedar"})
        if not resp.get("ok"):
            print("FALHOU ao hospedar:", resp)
            return None
        time.sleep(3)

        pid_host = pid_do_retroarch()

        core = os.path.join(RAIZ, "retroarch", "cores", "pcsx_rearmed_libretro.dll")
        rom = os.path.join(RAIZ, jogo["arquivo"].replace("/", os.sep))
        exe = os.path.join(RAIZ, "retroarch", "retroarch.exe")
        opcoes = graficos.opcoes_de_partida("convidado", hospedar=False, jogador=2)
        override_convidado = os.path.join(RAIZ, "ferramentas", "_join_checkframes.cfg")
        with open(override_convidado, "w", encoding="utf-8") as f:
            for k, v in opcoes.items():
                f.write('%s = "%s"\n' % (k, v))

        comando = [exe, "-L", core, "--appendconfig", override_convidado,
                  "--connect", "127.0.0.1", "--port", str(PORTA_PARTIDA), rom]
        convidado_proc = subprocess.Popen(comando, cwd=os.path.join(RAIZ, "retroarch"))

        print("check_frames=%d: rodando %ds..." % (valor_check_frames, DURACAO))
        amostras = []
        anterior = cpu_acumulada_do_processo(pid_host) if pid_host else None
        for _ in range(DURACAO):
            time.sleep(1)
            atual = cpu_acumulada_do_processo(pid_host) if pid_host else None
            if anterior is not None and atual is not None:
                amostras.append(round(atual - anterior, 3))
            anterior = atual

        convidado_vivo = convidado_proc.poll() is None
        log_host = log_mais_recente_apos(momento_host)
        texto_log = ""
        if log_host:
            with open(log_host, "r", encoding="utf-8", errors="replace") as f:
                texto_log = f.read()

        linhas_crc = [l for l in texto_log.splitlines()
                     if "crc" in l.lower() or "desync" in l.lower() or
                     "dessincron" in l.lower()]

        print("check_frames=%d: convidado ainda conectado apos %ds: %s" %
              (valor_check_frames, DURACAO, convidado_vivo))
        print("check_frames=%d: linhas de CRC/desync no log: %d" %
              (valor_check_frames, len(linhas_crc)))
        for l in linhas_crc[:10]:
            print("   " + l)
        print("check_frames=%d: CPU do host por segundo: %s" % (valor_check_frames, amostras))

        return {"vivo": convidado_vivo, "linhas_crc": len(linhas_crc), "amostras": amostras}
    finally:
        if convidado_proc is not None:
            convidado_proc.terminate()
            try:
                convidado_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                convidado_proc.kill()
        subprocess.run(["taskkill", "/F", "/IM", "retroarch.exe"], capture_output=True)
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()
        override_convidado = os.path.join(RAIZ, "ferramentas", "_join_checkframes.cfg")
        if os.path.isfile(override_convidado):
            os.remove(override_convidado)


def main():
    original = None
    with open(CFG, "r", encoding="utf-8") as f:
        m = re.search(r'^netplay_check_frames = "(\d+)"', f.read(), re.MULTILINE)
        if m:
            original = int(m.group(1))
    print("Valor original em retroarch.cfg:", original)

    try:
        resultado_600 = rodar_sessao(600)
        time.sleep(2)
        resultado_0 = rodar_sessao(0)
    finally:
        trocar_check_frames(original if original is not None else 600)
        print("retroarch.cfg restaurado para netplay_check_frames = %s" % original)

    if not resultado_600 or not resultado_0:
        print("FALHOU: uma das duas sessoes nao completou.")
        return 1

    def pico(amostras):
        if not amostras:
            return None
        ordenadas = sorted(amostras)
        mediana = ordenadas[len(ordenadas) // 2]
        return {"maximo": max(amostras), "mediana": mediana,
                "diferenca": round(max(amostras) - mediana, 3)}

    print()
    print("Resumo:")
    print("  check_frames=600: conectado=%s, linhas CRC/desync=%d, pico de CPU=%s" %
          (resultado_600["vivo"], resultado_600["linhas_crc"], pico(resultado_600["amostras"])))
    print("  check_frames=0:   conectado=%s, linhas CRC/desync=%d, pico de CPU=%s" %
          (resultado_0["vivo"], resultado_0["linhas_crc"], pico(resultado_0["amostras"])))
    return 0


if __name__ == "__main__":
    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao
    # fechar, e levaria junto as pastas temporarias deste teste).
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "testes"))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main))
