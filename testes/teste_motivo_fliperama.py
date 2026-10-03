# -*- coding: utf-8 -*-
r"""Por que o fliperama nao abriu -- com o MAME e o FBNeo DE VERDADE.

Achado de 02/10/2026 (Rafael): "o ARENA nao reconhece o motivo do kof2002
nao rodar, porque para o ARENA esta tudo certo, mas nao roda". Causa: o
kof2002.zip dele foi feito para outro emulador (kof2k2_c1.rom...) e a BIOS
do Neo Geo estava como neogeo.mame.zip (o MAME so procura neogeo.zip). O
MAME dizia tudo isso no registro, e o ARENA ficava calado.

Este teste monta, numa pasta temporaria, um kof2002.zip do mesmo jeito (os
nomes do zip dele, conteudo inventado) e a BIOS com o nome errado, abre no
RetroArch da pasta com o MAME e com o FBNeo, e confere que o
servidor\motivo_do_erro.py entende o registro de verdade:
  - MAME, BIOS como neogeo.mame.zip: "renomeie ... para neogeo.zip" e
    "Faltam 13 arquivos do jogo", "outra versao ou feito para outro emulador";
  - MAME, BIOS renomeada: a parte da BIOS some, a do jogo fica;
  - FBNeo: tambem diz o que falta.
Nada da pasta de jogos e' tocado: a BIOS e' copiada para o temporario.

Uso: servidor\python\python.exe testes\teste_motivo_fliperama.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402
import motivo_do_erro  # noqa: E402
import protege_cfg  # noqa: E402

RA = os.path.join(RAIZ, "retroarch")
NOMES_DO_ZIP_DO_RAFAEL = (["kof2k2_c%d.rom" % n for n in range(1, 9)]
                          + ["kof2K2_M1.ROM", "kof2k2_p1.rom", "kof2k2_p2.rom", "kof2k2_s1.rom",
                             "kof2K2_V1.ROM", "kof2K2_V2.ROM", "kof2K2_V3.ROM", "kof2K2_V4.ROM",
                             "readme.html"])


def achar_bios():
    """A BIOS do Neo Geo para o MAME (a da pasta, com qualquer um dos dois nomes)."""
    for caminho in (os.path.join(RAIZ, "jogos", "pessoais", "Arcade", "neogeo.mame.zip"),
                    os.path.join(RA, "system", "neogeo.mame.zip"),
                    os.path.join(RAIZ, "jogos", "pessoais", "Arcade", "neogeo.zip")):
        if os.path.isfile(caminho):
            return caminho
    return None


def abrir(pasta, nucleo, jogo):
    """Abre o jogo no RetroArch da pasta (15 s no maximo) e devolve o registro."""
    dados = os.path.join(pasta, "dados")
    os.makedirs(dados, exist_ok=True)
    desde = time.time()
    registro = os.path.join(dados, "retroarch__%s.log" % time.strftime("%Y_%m_%d__%H_%M_%S"))
    extra = os.path.join(pasta, "extra.cfg")
    with open(extra, "w", encoding="utf-8") as f:
        f.write('config_save_on_exit = "false"\naudio_enable = "false"\nvideo_fullscreen = "false"\n'
                'savefile_directory = "%s"\nsavestate_directory = "%s"\nscreenshot_directory = "%s"\n'
                % (pasta, pasta, pasta))
    subprocess.run([os.path.join(RA, "retroarch.exe"), "-L", os.path.join(RA, "cores", nucleo),
                    "--appendconfig", extra, "--verbose", "--log-file", registro, "--max-frames=600",
                    jogo], cwd=RA, timeout=240, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    achado = motivo_do_erro.registro_da_partida(dados, desde)
    return motivo_do_erro.ler(achado) if achado else ""


def main():
    falhas = []

    def confere(nome, ok, detalhe=""):
        print("  %s %s%s" % ("OK  " if ok else "FALHOU", nome, (" -- " + detalhe) if detalhe and not ok else ""))
        if not ok:
            falhas.append(nome)

    for nucleo in ("mame_libretro.dll", "fbneo_libretro.dll"):
        if not os.path.isfile(os.path.join(RA, "cores", nucleo)):
            print("Sem o nucleo %s nesta pasta: teste nao roda." % nucleo)
            return 1
    bios = achar_bios()
    if not bios:
        print("Sem a BIOS do Neo Geo do MAME nesta pasta (neogeo.mame.zip): teste nao roda.")
        return 1

    raiz_temp = tempfile.mkdtemp(prefix="arena_motivo_fliperama_")
    try:
        arcade = os.path.join(raiz_temp, "ARENA", "Arcade")
        os.makedirs(arcade)
        jogo = os.path.join(arcade, "kof2002.zip")
        with zipfile.ZipFile(jogo, "w") as z:
            for n, nome in enumerate(NOMES_DO_ZIP_DO_RAFAEL):
                z.writestr(nome, bytes([n]) * 4096)
        shutil.copy2(bios, os.path.join(arcade, "neogeo.mame.zip"))

        print("1. MAME, com a BIOS como neogeo.mame.zip (o caso do Rafael)")
        r = motivo_do_erro.analisar(abrir(os.path.join(raiz_temp, "ARENA"), "mame_libretro.dll", jogo),
                                    jogo, "mame_libretro.dll")
        confere("o ARENA percebeu que nao abriu", bool(r))
        if r:
            print("     " + r["texto"])
            confere("manda renomear a BIOS", r["renomear"] == ("neogeo.mame.zip", "neogeo.zip"), str(r["renomear"]))
            confere("conta os 13 arquivos do jogo que faltam", "Faltam 13 arquivos do jogo" in r["texto"])
            confere("diz que o zip e' de outro emulador", "outra versão ou feito para outro emulador" in r["texto"])

        print("2. MAME, com a BIOS renomeada para neogeo.zip")
        os.replace(os.path.join(arcade, "neogeo.mame.zip"), os.path.join(arcade, "neogeo.zip"))
        time.sleep(1.1)
        r = motivo_do_erro.analisar(abrir(os.path.join(raiz_temp, "ARENA"), "mame_libretro.dll", jogo),
                                    jogo, "mame_libretro.dll")
        confere("continua sem abrir (o zip e' o problema)", bool(r))
        if r:
            confere("a parte da BIOS sumiu", "BIOS" not in r["texto"], r["texto"])
            confere("a parte do jogo ficou", "Faltam 13 arquivos do jogo" in r["texto"], r["texto"])

        print("3. FBNeo, o mesmo zip")
        time.sleep(1.1)
        r = motivo_do_erro.analisar(abrir(os.path.join(raiz_temp, "ARENA"), "fbneo_libretro.dll", jogo),
                                    jogo, "fbneo_libretro.dll")
        confere("o FBNeo tambem diz o que falta", bool(r) and r["texto"].startswith("FBNeo não abriu")
                and "Faltam" in r["texto"], r["texto"] if r else "nada")
    finally:
        limpeza.apagar_pasta(raiz_temp)

    print()
    print("RESULTADO: %s" % ("tudo certo" if not falhas else "%d falha(s)" % len(falhas)))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
