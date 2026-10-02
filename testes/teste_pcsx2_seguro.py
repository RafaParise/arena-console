# -*- coding: utf-8 -*-
r"""PCSX2 sem configuracao que "pode quebrar a renderizacao".

Achado de 02/10/2026 (Rafael, Crash Nitro Kart a 3 jogadores): o mapa do
quarto quadro coberto por texturas da corrida e o "P1" em cima do kart
virando blocos vermelhos e pretos esticados. O Crash Nitro Kart e'
"perfeito" (compat 5) no banco de jogos do proprio PCSX2 -- com a
configuracao padrao. O registro do PCSX2 avisava a cada jogo:
  "A filtragem trilinear nao esta definida como automatica. Isto pode
   quebrar a renderizacao em alguns jogos."
  "O mapeamento de mip esta desativado. Isso pode prejudicar a
   renderizacao em alguns jogos."
(as duas tinham sido mudadas na tela do PCSX2), e o "Mais leve" do ARENA
gravava a pre-carga de texturas em "Nenhuma" -- que o PCSX2 avisa que
deixa MAIS LENTO ("Texture Preloading is not Full, this may reduce
performance").

  1. logica: em toda qualidade, mipmapping ligado, trilinear automatico,
     filtro bilinear do PS2, leitura "Precisa", pre-carga completa e
     mistura nunca abaixo da basica; o 16:9 escolhido na tela continua;
  2. PCSX2 de verdade (copia isolada, sem os cartoes de memoria) abre o
     Crash Nitro Kart com as escolhas do Rafael (Mais leve, grafico
     original, Vulkan): o jogo comeca e o registro nao reclama de mais
     nada alem do motor de video escolhido a mao; no automatico, de nada.

Uso: servidor\python\python.exe testes\teste_pcsx2_seguro.py [--sem-pcsx2]
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, AQUI)
import graficos  # noqa: E402
import limpeza  # noqa: E402

PASTA_PCSX2 = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2")
INI_REAL = os.path.join(PASTA_PCSX2, "inis", "PCSX2.ini")
JOGO = os.path.join(RAIZ, "jogos", "pessoais", "PS2", "Crash Nitro Kart (USA).chd")

ESPERADO = {"hw_mipmap": "true", "TriFilter": "-1", "filter": "2", "HWDownloadMode": "0",
            "texture_preloading": "2"}


def ler_gs(caminho):
    valores, dentro = {}, False
    for linha in open(caminho, encoding="utf-8", errors="replace"):
        limpo = linha.strip()
        if limpo.startswith("["):
            dentro = limpo == "[EmuCore/GS]"
        elif dentro and " = " in limpo:
            chave, valor = limpo.split(" = ", 1)
            valores[chave] = valor
    return valores


def _icone(texto):
    """O PCSX2 abre cada aviso com um icone da fonte dele (caractere de uso
    privado, entre U+E000 e U+F8FF)."""
    return bool(texto) and "\ue000" <= texto[0] <= "\uf8ff"


def avisos_perigosos(registro):
    """Os avisos da mensagem na tela do PCSX2 ("OSD [unsafe_settings_warning]"):
    a primeira linha e as seguintes que comecam com o icone de aviso."""
    linhas = [re.sub(r"^\[\s*[\d,.]+\]\s?", "", linha) for linha in registro.splitlines()]
    for numero, texto in enumerate(linhas):
        if "OSD [unsafe_settings_warning]:" not in texto:
            continue
        avisos = [texto.split("]:", 1)[1].strip()]
        for seguinte in linhas[numero + 1:]:
            if not _icone(seguinte.strip()):
                break
            avisos.append(seguinte.strip())
        return [aviso[1:].strip() if _icone(aviso) else aviso for aviso in avisos if aviso]
    return []


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    base = tempfile.mkdtemp(prefix="arena_pcsx2_seguro_")
    try:
        # 1. Logica, partindo do PCSX2.ini de verdade (so leitura) -------------
        print("1. Valores seguros em toda qualidade")
        original = open(INI_REAL, encoding="utf-8", errors="replace").read()
        casos = [("leve", True, True), (None, False, True), (None, False, False),
                 ("bonito", False, False), ("leve", False, False), (None, True, True)]
        for numero, (preset, modesto, integrada) in enumerate(casos):
            pasta = os.path.join(base, "logica%d" % numero)
            os.makedirs(os.path.join(pasta, "inis"))
            ini = os.path.join(pasta, "inis", "PCSX2.ini")
            texto = original.replace("hw_mipmap = true", "hw_mipmap = false")
            texto = re.sub(r"(?m)^accurate_blending_unit = \d+", "accurate_blending_unit = 0", texto)
            open(ini, "w", encoding="utf-8").write(texto)
            graficos.escrever_config_pcsx2(os.path.join(pasta, "pcsx2-qt.exe"), nota=4, nota_gpu=3,
                                           modesto=modesto, preset=preset, integrada=integrada,
                                           motor="vulkan", jogadores=4, controles_xinput=[])
            gs = ler_gs(ini)
            nome = "preset %s, original %s, integrada %s" % (preset or "automatico", modesto, integrada)
            errados = {k: gs.get(k) for k, v in ESPERADO.items() if gs.get(k) != v}
            confere(nome + ": mipmap, trilinear, filtro, leitura e pre-carga seguros", not errados, errados)
            confere(nome + ": mistura nunca abaixo da basica", gs.get("accurate_blending_unit", "1") != "0",
                    gs.get("accurate_blending_unit"))
            if "AspectRatio = 16:9" in original:
                confere(nome + ": o 16:9 da tela do PCSX2 continua", gs.get("AspectRatio") == "16:9")

        # 2. PCSX2 de verdade ----------------------------------------------------
        if "--sem-pcsx2" in sys.argv or not os.path.isfile(JOGO):
            print("\n2. (pulado: %s)" % ("--sem-pcsx2" if "--sem-pcsx2" in sys.argv else "sem o jogo"))
        else:
            print("\n2. PCSX2 de verdade abre o Crash Nitro Kart sem reclamar")
            copia = os.path.join(base, "PCSX2")
            shutil.copytree(PASTA_PCSX2, copia, ignore=shutil.ignore_patterns(
                "memcards", "cache", "logs", "snaps", "sstates", "covers", "videos"))
            os.makedirs(os.path.join(copia, "memcards"), exist_ok=True)
            exe = os.path.join(copia, "pcsx2-qt.exe")
            registro = os.path.join(copia, "logs", "emulog.txt")
            for motor, permitidos in (("vulkan", 1), ("automatico", 0)):
                graficos.escrever_config_pcsx2(exe, nota=4, nota_gpu=3, modesto=True, preset="leve",
                                               integrada=True, motor=motor, jogadores=4, controles_xinput=[])
                ini = os.path.join(copia, "inis", "PCSX2.ini")
                texto = graficos._trocar_chaves_ini(open(ini, encoding="utf-8").read(),
                                                    "Logging", {"EnableFileLogging": "true"})
                open(ini, "w", encoding="utf-8").write(texto)
                if os.path.exists(registro):
                    os.remove(registro)
                janela = subprocess.STARTUPINFO()
                janela.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                janela.wShowWindow = 7             # minimizada, sem roubar o foco
                processo = subprocess.Popen([exe, JOGO], cwd=copia, startupinfo=janela)
                lido, comecou = "", False
                fim = time.monotonic() + 60
                while time.monotonic() < fim:
                    time.sleep(1)
                    try:
                        lido = open(registro, encoding="utf-8", errors="replace").read()
                    except OSError:
                        continue
                    if "is executing" in lido and "GameDB: Enabled" in lido:
                        comecou = True
                        time.sleep(3)
                        lido = open(registro, encoding="utf-8", errors="replace").read()
                        break
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
                try:
                    processo.wait(15)
                except subprocess.TimeoutExpired:
                    pass
                avisos = avisos_perigosos(lido)
                confere("motor %s: o Crash Nitro Kart comecou (correcoes do banco de jogos aplicadas)" % motor,
                        comecou, lido[-300:])
                confere("motor %s: o PCSX2 reclama de %d coisa(s) (no maximo %d)" % (motor, len(avisos), permitidos),
                        len(avisos) <= permitidos, avisos)
                for aviso in avisos:
                    print("        aviso do PCSX2: %s" % aviso)
                time.sleep(2)
    finally:
        limpeza.apagar_pasta(base)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("PCSX2 seguro: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
