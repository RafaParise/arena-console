# -*- coding: utf-8 -*-
r"""Mais quadros de verdade (11/11/2026): o patch de 60 quadros do PS2 e o motor do MFG Super Motion.

1. PS2: o ARENA identifica o Black (serial e CRC do ISO), liga o patch "60 FPS" do PCSX2 e o PCSX2 diz no
   registro "Enabled patch: 60 FPS". No fim, o ARENA tira a linha que pos e o arquivo do jogo some.
2. MFG Super Motion (se estiver instalado): o RetroArch abre um jogo livre em tela cheia sem borda, o ARENA
   abre o motor com as opcoes que ele escolheu para esta maquina, o motor pega a janela do jogo ("@source")
   e, no "stop", devolve a janela e sai sozinho.
A configuracao dos emuladores volta como estava (protege_cfg, emuladores=True); os registros do ARENA vao para
uma pasta temporaria.

Uso:
    servidor\python\python.exe testes\teste_mais_quadros.py
"""
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
import quadros_ps2  # noqa: E402

PCSX2 = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2")
EXE = os.path.join(PCSX2, "pcsx2-qt.exe")
JOGO_PS2 = os.path.join(RAIZ, "jogos", "pessoais", "PS2", "Black (BR).iso")
REGISTRO_PCSX2 = os.path.join(PCSX2, "logs", "emulog.txt")
JOGO_LIVRE = os.path.join(AQUI, "jogos_livres", "MSX", "noborunoca.rom")
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
FALHAS = []


def confere(nome, ok, detalhe=None):
    print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
    if not ok:
        FALHAS.append(nome)


def parte_ps2(dados):
    print("PS2: o patch de 60 quadros do PCSX2")
    if not (os.path.isfile(EXE) and os.path.isfile(JOGO_PS2)):
        print("  pulado: falta o PCSX2 ou o Black (BR).iso nesta maquina")
        return
    identificado = quadros_ps2.identificar(JOGO_PS2, dados)
    confere("serial e CRC tirados do ISO", identificado == ("SLUS-21376", "5C891FF1"), identificado)
    if not identificado:
        return
    serial, crc = identificado
    nome = quadros_ps2.aplicar(PCSX2, serial, crc, True, dados)
    confere("patch de 60 quadros ligado", nome == "60 FPS", nome)
    graficos.escrever_config_pcsx2(EXE, nota=4, nota_gpu=4, cartoes=graficos.preparar_portatil_pcsx2(EXE))
    ini = os.path.join(PCSX2, "inis", "PCSX2.ini")
    with open(ini, encoding="utf-8") as arquivo:
        texto = graficos._trocar_chaves_ini(arquivo.read(), "Logging", {"EnableFileLogging": "true"})
    with open(ini, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    if os.path.exists(REGISTRO_PCSX2):
        os.remove(REGISTRO_PCSX2)
    processo = subprocess.Popen([EXE, "-batch", "-fullscreen", "--", JOGO_PS2], cwd=PCSX2)
    registro = ""
    try:
        limite = time.monotonic() + 90
        while time.monotonic() < limite and "Enabled patch" not in registro:
            time.sleep(2)
            try:
                with open(REGISTRO_PCSX2, encoding="utf-8", errors="replace") as arquivo:
                    registro = arquivo.read()
            except OSError:
                pass
        time.sleep(3)
    finally:
        processo.terminate()
        try:
            processo.wait(20)
        except subprocess.TimeoutExpired:
            processo.kill()
    confere("o PCSX2 ligou o patch (registro)", "Enabled patch: 60 FPS" in registro)
    confere("o PCSX2 escreveu o serial e o CRC", quadros_ps2.ler_do_registro(registro) == identificado)
    quadros_ps2.aplicar(PCSX2, serial, crc, False, dados)
    confere("no fim, o arquivo do jogo saiu", not os.path.exists(
        os.path.join(PCSX2, "gamesettings", "%s_%s.ini" % (serial, crc))))


def parte_mfg(dados):
    print("MFG Super Motion: o motor com a janela do RetroArch")
    achado = mfg.achar(RAIZ)
    if not achado:
        print("  pulado: o MFG Super Motion nao esta instalado nesta maquina")
        return
    capacidade = hardware.capacidade(None, RAIZ)
    info = hardware.resumo(RAIZ)
    integrada = bool(info.get("gpu", {}).get("integrada", True))
    opcoes = mfg.escolher_opcoes(mfg.placas(achado["motor"]), capacidade["nota_gpu"], integrada,
                                 lossless.frequencia_da_tela(), True)
    print("  opcoes escolhidas para esta maquina: %s" % mfg.descrever(opcoes))
    cfg = os.path.join(dados, "retroarch_teste.cfg")
    with open(cfg, "w", encoding="utf-8") as arquivo:
        arquivo.write('video_fullscreen = "true"\nvideo_windowed_fullscreen = "true"\nconfig_save_on_exit = "false"\n'
                      'system_directory = "%s"\n' % os.path.join(RAIZ, "retroarch", "system").replace("\\", "/"))
    jogo = subprocess.Popen([RETROARCH, "-c", cfg, "-L", os.path.join(RAIZ, "retroarch", "cores", "bluemsx_libretro.dll"),
                             JOGO_LIVRE], cwd=os.path.dirname(RETROARCH))
    falas = []
    sessao = mfg.Sessao(achado["motor"], opcoes, os.path.join(dados, "mfg_partida.cfg"), registrar=falas.append)
    largura, altura = hardware.tamanho_da_tela()
    sessao.comecar(jogo.pid, largura * altura, ainda_aberto=lambda: jogo.poll() is None)
    try:
        limite = time.monotonic() + 60
        while time.monotonic() < limite and not any("@state running" in l for l in sessao.ultimas):
            time.sleep(1)
        time.sleep(5)
        confere("o motor pegou a janela do jogo", any(l.startswith("@source") for l in sessao.ultimas),
                [l for l in sessao.ultimas if l.startswith("@source")][:1])
        confere("o motor esta rodando", any("@state running" in l for l in sessao.ultimas))
        confere("nada de erro do motor", not any(l.startswith("@error") for l in sessao.ultimas),
                [l for l in sessao.ultimas if l.startswith("@error")][:2])
        processo = sessao.processo
        confere("o ARENA fechou o motor no fim", sessao.parar())
        confere("o motor saiu sozinho com o stop", processo is not None and processo.poll() is not None)
        confere("o jogo seguiu aberto depois do motor", jogo.poll() is None)
    finally:
        sessao.parar()
        jogo.terminate()
        try:
            jogo.wait(15)
        except subprocess.TimeoutExpired:
            jogo.kill()
    for fala in falas:
        print("   ", fala)


def main():
    dados = tempfile.mkdtemp(prefix="arena_mais_quadros_")
    try:
        parte_ps2(dados)
        parte_mfg(dados)
    finally:
        limpeza.apagar_pasta(dados)
    print("RESULTADO: %s" % ("tudo certo" if not FALHAS else "falhou: " + ", ".join(FALHAS)))
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main, emuladores=True))
