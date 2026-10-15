# -*- coding: utf-8 -*-
r"""As BIOS que o organizador instala abrem os jogos de verdade?

Achado de 03/10/2026: o Sega CD e o Saturn nao abriam jogo nenhum ("Unable to
open CD BIOS", "Cannot open BIOS file") e os BS F-ZERO de Satellaview
tambem nao (falta o BS-X.bin). O Rafael trouxe os pacotes das BIOS; o
servidor\bios.py as reconhece e instala. Aqui, cada uma e' posta a prova
abrindo um jogo no RetroArch:

  1. num ARENA de mentira (temporario), os pacotes vao para as prateleiras
     da pasta BIOS, como uma pessoa faria, e o organizar() instala;
  2. cada jogo abre com essa pasta de sistema (--max-frames-ss: foto da
     tela): o registro nao pode reclamar de BIOS, e a foto nao pode ser
     tela preta;
  3. os BS F-ZERO abrem com o BS-X que o organizador instalou;
  4. o BS F-Zero Deluxe (feito para abrir sem o BS-X?) e' aberto SEM o
     BS-X tambem -- se abrir, o aviso do cartao nao pode pedir a BIOS.

Uso: servidor\python\python.exe testes\teste_bios_consoles.py [--fotos=<pasta>]
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_multitap as base  # noqa: E402
import bios  # noqa: E402

P = os.path.join(RAIZ, "jogos", "pessoais")
# (rotulo, arquivo do jogo, nucleo, quadros) -- o Saturn e o Dreamcast passam
# pela abertura da BIOS antes do jogo.
JOGOS = [
    ("Sega CD (Europa) com bios_CD_E.bin", os.path.join(P, "Sega CD", "Sonic CD (Europe).chd"),
     "genesis_plus_gx", 900),
    ("Saturn (EUA) com mpr-17933.bin", os.path.join(P, "Sega Saturn", "Saturn Bomberman",
                                                   "Saturn Bomberman (USA) (1S).cue"), "mednafen_saturn", 600),
    # 15/10/2026: sem a renderizacao em thread (graficos.json), o quadro 1500
    # caia na tela preta entre a BIOS e a abertura; no 2500 a abertura aparece.
    ("Dreamcast com dc_boot.bin", os.path.join(P, "Dreamcast", "Marvel vs. Capcom - Clash of Super Heroes (Europe)",
                                               "Marvel vs. Capcom - Clash of Super Heroes (Europe).cue"),
     "flycast", 2500),
    ("Satellaview: BS F-ZERO com o BS-X", os.path.join(P, "Super Nintendo", "BS F-ZERO (J).smc"), "snes9x", 900),
    ("Satellaview: BS F-ZERO Grand Prix 2 com o BS-X",
     os.path.join(P, "Super Nintendo", "BS F-ZERO Grand Prix 2 (J) [h1].smc"), "snes9x", 900),
    ("BS F-Zero Deluxe com o BS-X", os.path.join(P, "Super Nintendo", "BS F-Zero Deluxe (1.0) [NTSC-USA].sfc"),
     "snes9x", 900),
]
RE_BIOS_RUIM = re.compile(r"Unable to open CD BIOS|Cannot open BIOS|BIOS not found|Could not (open|load) BIOS|"
                          r"Failed to (open|load) BIOS|ROM loading failed|Falha ao carregar o conte|"
                          r"Failed to load content", re.I)


def achar(nome, onde):
    for atual, _subpastas, arquivos in os.walk(onde):
        if nome in arquivos:
            return os.path.join(atual, nome)
    return None


def abrir(jogo, nucleo, quadros, sistema, pasta):
    os.makedirs(pasta)
    cfg = base.config_base(pasta, {"audio_enable": "false"})
    texto = open(cfg, encoding="utf-8").read()
    texto = re.sub(r'^system_directory = ".*"$', lambda _m: 'system_directory = "%s"' % sistema, texto, flags=re.M)
    open(cfg, "w", encoding="utf-8").write(texto)
    foto, registro = os.path.join(pasta, "foto.png"), os.path.join(pasta, "ra.log")
    try:
        subprocess.run([base.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll"),
                        "--appendconfig", cfg, "--verbose", "--log-file", registro, "--max-frames=%d" % quadros,
                        "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                       cwd=os.path.dirname(base.RETROARCH), timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass
    log = open(registro, encoding="utf-8", errors="ignore").read() if os.path.isfile(registro) else ""
    return (foto if os.path.isfile(foto) else None), log


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    destino_fotos = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--fotos=")), "")
    pasta = tempfile.mkdtemp(prefix="arena_bios_jogos_")
    try:
        print("1. As BIOS nas prateleiras, e o organizar() instala")
        raiz = os.path.join(pasta, "ARENA")
        sistema = os.path.join(raiz, "retroarch", "system")
        os.makedirs(sistema)
        procura = [os.path.join(RAIZ, "BIOS"), os.path.join(RAIZ, "retroarch", "system"),
                   os.path.join(os.path.dirname(RAIZ), "ARENA-alunos", "retroarch", "system")]
        pacotes = {"segamegacdbios.zip": "Sega CD", "segasaturnbios.zip": "Sega Saturn", "dc_boot.zip": "Dreamcast",
                   "BS-X BIOS (English) [No DRM] [2016 v1.3].sfc": "Super Nintendo (Satellaview)"}
        for nome, prateleira in pacotes.items():
            origem = next((achar(nome, lugar) for lugar in procura if achar(nome, lugar)), None)
            confere("o arquivo %s existe" % nome, bool(origem))
            if origem:
                os.makedirs(os.path.join(raiz, "BIOS", prateleira), exist_ok=True)
                shutil.copy2(origem, os.path.join(raiz, "BIOS", prateleira, nome))
        feito = bios.organizar(raiz, os.path.join(RAIZ, "retroarch", "info"))
        instaladas = sorted({i["id"] for i in feito["instaladas"]})
        confere("instaladas: Sega CD (3), Saturn (2), Dreamcast e BS-X",
                {"segacd-eua", "segacd-europa", "segacd-japao", "saturn-eua-europa", "saturn-japao",
                 "dreamcast-boot", "snes-bsx"} <= set(instaladas), instaladas)
        bsx = next((i for i in feito["itens"] if i["id"] == "snes-bsx"), {})
        print("     (BS-X: %s, %s)" % (bsx.get("estado"), bsx.get("arquivo")))

        print("2. Cada jogo abre com essas BIOS")
        resultados = {}
        for numero, (rotulo, jogo, nucleo, quadros) in enumerate(JOGOS):
            if not os.path.isfile(jogo):
                confere("%s: o jogo existe" % rotulo, False, jogo)
                continue
            foto, log = abrir(jogo, nucleo, quadros, sistema, os.path.join(pasta, "jogo%d" % numero))
            ruins = [l.strip()[:140] for l in log.splitlines() if RE_BIOS_RUIM.search(l)]
            tamanho = os.path.getsize(foto) if foto else 0
            resultados[rotulo] = (tamanho, ruins)
            confere("%s: abre, sem reclamar de BIOS" % rotulo, foto is not None and not ruins,
                    {"foto": tamanho, "registro": ruins[:3]})
            confere("%s: a tela não está preta" % rotulo, tamanho > 6000, tamanho)
            if destino_fotos and foto:
                os.makedirs(destino_fotos, exist_ok=True)
                shutil.copy2(foto, os.path.join(destino_fotos, "bios_jogo%d.png" % numero))

        print("3. BS F-Zero Deluxe SEM o BS-X")
        sem_bsx = os.path.join(pasta, "sem_bsx")
        os.makedirs(sem_bsx)
        deluxe = JOGOS[-1][1]
        foto, log = abrir(deluxe, "snes9x", 900, sem_bsx, os.path.join(pasta, "deluxe_sem"))
        ruins = [l.strip()[:140] for l in log.splitlines() if RE_BIOS_RUIM.search(l)]
        tamanho = os.path.getsize(foto) if foto else 0
        abre_sozinho = foto is not None and not ruins and tamanho > 6000
        print("     (sem o BS-X: foto %d bytes, registro %s)" % (tamanho, ruins[:2]))
        if destino_fotos and foto:
            shutil.copy2(foto, os.path.join(destino_fotos, "bios_deluxe_sem_bsx.png"))
        aviso = bios.aviso_do_jogo("snes", os.path.basename(deluxe), sem_bsx, "Super Nintendo", deluxe)
        if abre_sozinho:
            confere("o Deluxe abre sem o BS-X: o cartão não pede a BIOS", aviso is None, aviso)
        else:
            confere("o Deluxe precisa do BS-X: o cartão pede a BIOS", aviso is not None, aviso)
        # Os de verdade (cabecalho de Satellaview) continuam pedindo.
        bs = JOGOS[3][1]
        confere("o BS F-ZERO sem o BS-X: o cartão pede a BIOS",
                bios.aviso_do_jogo("snes", os.path.basename(bs), sem_bsx, "Super Nintendo", bs) is not None)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("BIOS abrindo jogos de verdade: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
