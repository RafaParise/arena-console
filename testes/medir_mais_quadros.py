# -*- coding: utf-8 -*-
r"""Medida (11/11/2026): o que cada programa de quadros a mais entrega NESTA maquina, no PS2 do PCSX2.

Pergunta do Rafael: o ARENA deve saber qual programa (Lossless Scaling ou MFG Super Motion) beneficia qual
maquina, e nunca diminuir o desempenho. Aqui, com o PresentMon (contador de quadros da Microsoft, gratis; precisa
do terminal de administrador), o mesmo jogo em tres jeitos, na mesma partida:
  - sem nada (o PCSX2 entrega so os quadros novos, como o ARENA configura com geracao de quadros);
  - com o MFG Super Motion (as opcoes que o ARENA escolhe para esta maquina);
  - com o Lossless Scaling (o perfil "ARENA", geracao de quadros LSFG 3 seguindo a tela).
Para cada um: quadros por segundo do PROPRIO jogo (se cair, e' regresso) e da janela que vai para a tela.
Resultado em docs\mais_quadros_medido.json. A configuracao dos emuladores volta como estava (protege_cfg).

Uso (terminal de administrador): servidor\python\python.exe testes\medir_mais_quadros.py
"""
import csv
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
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import graficos  # noqa: E402
import hardware  # noqa: E402
import lossless  # noqa: E402
import mfg  # noqa: E402

PCSX2 = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2")
EXE = os.path.join(PCSX2, "pcsx2-qt.exe")
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "PS2", "Black (BR).iso")
PRESENTMON = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ferramentas-arena", "presentmon",
                          "PresentMon-2.6.0-x64.exe")
SEGUNDOS = 20


def medir(pasta, nome):
    """Quadros por segundo de cada programa durante SEGUNDOS (PresentMon)."""
    arquivo = os.path.join(pasta, nome + ".csv")
    subprocess.run([PRESENTMON, "--output_file", arquivo, "--timed", str(SEGUNDOS), "--terminate_after_timed",
                    "--stop_existing_session", "--no_console_stats"], capture_output=True, timeout=SEGUNDOS + 40)
    enviados, na_tela = {}, {}
    try:
        with open(arquivo, newline="", encoding="utf-8-sig", errors="replace") as lido:
            for linha in csv.DictReader(lido):
                programa = (linha.get("Application") or "?").lower()
                enviados[programa] = enviados.get(programa, 0) + 1
                if (linha.get("MsUntilDisplayed") or "NA") != "NA":
                    na_tela[programa] = na_tela.get(programa, 0) + 1
    except OSError:
        return {}
    # Quadros por segundo de cada programa: os enviados e os que chegaram a tela.
    return {programa: {"enviados": round(n / float(SEGUNDOS), 1),
                       "na_tela": round(na_tela.get(programa, 0) / float(SEGUNDOS), 1)}
            for programa, n in enviados.items() if n >= SEGUNDOS and programa != "dwm.exe"}


def main():
    if not (os.path.isfile(EXE) and os.path.isfile(JOGO) and os.path.isfile(PRESENTMON)):
        print("Falta o PCSX2, o Black (BR).iso ou o PresentMon nesta maquina.")
        return 1
    pasta = tempfile.mkdtemp(prefix="arena_medir_quadros_")
    resultado = {"feito_em": time.strftime("%Y-%m-%d %H:%M"), "jogo": "Black (PS2)", "segundos_por_medida": SEGUNDOS}
    capacidade = hardware.capacidade(None, RAIZ)
    info = hardware.resumo(RAIZ)
    integrada = bool(info.get("gpu", {}).get("integrada", True))
    hz = lossless.frequencia_da_tela()
    resultado["maquina"] = {"placa": info.get("gpu", {}).get("nome"), "integrada": integrada,
                            "nota": capacidade["nota"], "nota_gpu": capacidade["nota_gpu"], "hz": hz}
    graficos.escrever_config_pcsx2(EXE, nota=capacidade["nota"], nota_gpu=capacidade.get("nota_gpu_de_fora"),
                                   cartoes=graficos.preparar_portatil_pcsx2(EXE), integrada=integrada,
                                   so_quadros_novos=True)
    jogo = subprocess.Popen([EXE, "-batch", "-fullscreen", "--", JOGO], cwd=PCSX2)
    try:
        time.sleep(35)
        resultado["sem_nada"] = medir(pasta, "sem_nada")
        print("sem nada:", resultado["sem_nada"], flush=True)

        achado = mfg.achar(RAIZ)
        if achado:
            opcoes = mfg.escolher_opcoes(mfg.placas(achado["motor"]), capacidade["nota_gpu"], integrada, hz, False)
            sessao = mfg.Sessao(achado["motor"], opcoes, os.path.join(pasta, "mfg.cfg"), registrar=lambda _: None)
            largura, altura = hardware.tamanho_da_tela()
            sessao.comecar(jogo.pid, largura * altura, ainda_aberto=lambda: jogo.poll() is None)
            time.sleep(15)
            resultado["mfg"] = medir(pasta, "mfg")
            resultado["mfg_opcoes"] = mfg.descrever(opcoes)
            resultado["mfg_linhas"] = [l for l in sessao.ultimas if l.startswith(("@source", "@error", "@mfg"))]
            sessao.parar()
            print("MFG:", resultado["mfg"], resultado["mfg_linhas"], flush=True)
            time.sleep(5)

        achado_ls = lossless.achar(RAIZ)
        if achado_ls and achado_ls.get("licenca"):
            gravou, motivo = lossless.gravar_perfil(lossless.trocas_para_o_externo(
                "pcsx2-qt.exe", capacidade.get("nota_gpu_de_fora"), hz))
            if gravou and lossless.abrir(achado_ls["executavel"]):
                time.sleep(25)
                resultado["lossless"] = medir(pasta, "lossless")
                print("Lossless:", resultado["lossless"], flush=True)
                lossless.fechar_o_que_o_arena_abriu()
            else:
                resultado["lossless"] = "nao abriu: %s" % motivo
        time.sleep(3)
        resultado["sem_nada_de_novo"] = medir(pasta, "sem_nada_de_novo")
        print("sem nada, de novo:", resultado["sem_nada_de_novo"], flush=True)
    finally:
        jogo.terminate()
        try:
            jogo.wait(20)
        except subprocess.TimeoutExpired:
            jogo.kill()
        limpeza.apagar_pasta(pasta)
    with open(os.path.join(RAIZ, "docs", "mais_quadros_medido.json"), "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main, emuladores=True))
