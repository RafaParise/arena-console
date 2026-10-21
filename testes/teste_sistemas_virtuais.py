# -*- coding: utf-8 -*-
r"""Os testes do ARENA nos sistemas virtuais, com numeros e descontando a
perda (item 15 do plano de 15/10/2026).

Pedido do Rafael: "testes nos sistemas virtuais (Docker e WSL), com numeros e
descontando a perda de rodar dentro de outro sistema".

As mesmas medidas (testes\medidas_virtuais.py) em tres lugares, nesta
maquina:
  W. o Windows de verdade: a base;
  L. o Linux num conteiner do WSL (testes\linux\Dockerfile, pelo WSLC), pela
     parte G do testes\teste_linux.py;
  A. o Android no aparelho virtual (o emulador do AOSP, pela Plataforma de
     Hipervisor do Windows), pelo adb, com o APK de teste instalado.

Em cada um: a velocidade do processador (a mesma conta da nota do ARENA),
o RetroArch sem freio em quatro nucleos (video e som "null": so o trabalho
do emulador) e a gravacao em disco.

Descontando a perda: a razao entre o processador de dentro e o do Windows
(o mesmo Python, a mesma conta) e' quanto o sistema virtual tira. Cada
quadro por segundo medido dentro dele, dividido por essa razao, da' a
estimativa do mesmo nucleo numa maquina de verdade com aquele sistema; e a
comparacao com o Windows diz se o sistema (o RetroArch do Linux, o do
Android) perde ou ganha por si, tirada a maquina virtual.

O video fica de fora das contas de proposito: o do emulador do Android e'
desenhado pelo processador (SwiftShader) e o do conteiner nem tem placa.

Resultado: docs\sistemas_virtuais_bruto.json (e a tabela, para o
docs\SISTEMAS-VIRTUAIS.md).

Uso:
    servidor\python\python.exe testes\teste_sistemas_virtuais.py [W,L,A] [--manter-ligado]
"""
import json
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _pasta in (AQUI, os.path.join(RAIZ, "servidor"), os.path.join(RAIZ, "ferramentas")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

import medidas_virtuais  # noqa: E402

PACOTE = "io.github.rafaparise.arena"
RETROARCH_DO_APK = PACOTE + "/com.retroarch.browser.retroactivity.RetroActivityFuture"
NO_APARELHO = "/data/data/%s/files/medida" % PACOTE


def no_windows():
    return medidas_virtuais.medir_aqui(os.path.join(RAIZ, "retroarch", "retroarch.exe"),
                                       os.path.join(RAIZ, "retroarch", "cores"), ".dll")


def no_linux():
    import limpeza
    import teste_linux
    pasta = tempfile.mkdtemp(prefix="arena_medida_linux_")
    arquivo = os.path.join(pasta, "resultado.json")
    try:
        codigo = teste_linux.pelo_conteiner(["G"], copiar_para=arquivo)
        try:
            with open(arquivo, encoding="utf-8") as entrada:
                dados = json.load(entrada)
        except (OSError, ValueError):
            return {"erro": "o conteiner nao deixou o resultado (codigo %s)" % codigo}
    finally:
        limpeza.apagar_pasta(pasta)
    medidas = dados.get("medidas") or {}
    medidas["falhas_do_teste"] = dados.get("falhas")
    return medidas


# ---------------------------------------------------------------------------
# O Android, pelo adb
# ---------------------------------------------------------------------------

def no_android():
    import teste_android as ta
    processo, ligou = ta.ligar_emulador()
    medidas = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "sistema": "android",
               "emulador_ligou_s": round(ligou, 1), "nucleos": {}}
    if ligou:
        # Ligado agora, a frio: o Android ainda arruma a casa por um tempo
        # (teste_android.py), e a medida sairia mais baixa do que e'.
        time.sleep(30)
    pasta_dos_apks = os.path.join(ta.sdk.BASE, "apk")
    apk_local = os.path.join(pasta_dos_apks, sorted(n for n in os.listdir(pasta_dos_apks)
                                                    if n.endswith("-x86_64-teste.apk"))[-1])
    try:
        # O APK de teste daqui, instalado de novo: os nucleos da medida saem
        # dele (aqui no computador), e o do aparelho tem de ser o mesmo.
        ta.adb("install", "-r", apk_local, segundos=600)
        for permissao in ("READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"):
            ta.adb("shell", "pm", "grant", PACOTE, "android.permission." + permissao)
        # A medida roda como root (o emulador do AOSP deixa): so ela, nada do app.
        ta.adb("root", segundos=60)
        time.sleep(3)
        ta.adb("wait-for-device", segundos=120)
        # O ARENA aberto uma vez tira o Python e o programa do APK.
        ta.adb("shell", "am", "start", "-n", ta.TELA_DO_ARENA)
        if not ta.esperar(lambda: _existe("/data/data/%s/files/python/lib/python313.zip" % PACOTE), 240):
            medidas["erro"] = "o ARENA nao tirou o Python do APK"
            return medidas
        apk = ta.adb_texto("shell", "pm", "path", PACOTE).strip().split(":", 1)[-1]
        bibliotecas = os.path.dirname(apk) + "/lib/x86_64"
        medidas["processador"] = _processador_no_android(ta, bibliotecas)
        medidas["nucleos"] = _retroarch_no_android(ta, apk_local)
        medidas["disco"] = _disco_no_android(ta, bibliotecas)
    finally:
        ta.adb("shell", "am", "force-stop", PACOTE)
        if "--manter-ligado" not in sys.argv:
            ta.desligar_emulador(processo)
    return medidas


def _existe(caminho):
    import teste_android as ta
    return "sim" in ta.adb_texto("shell", "test -f %s && echo sim" % caminho)


def _python_no_android(ta, bibliotecas, codigo):
    """Roda 'codigo' no Python do APK (como root: so a medida, nada do app)."""
    casa = "/data/data/%s/files" % PACOTE
    linha = ("cd %s/arena/servidor && PYTHONHOME=%s/python LD_LIBRARY_PATH=%s %s/libarenapython.so -c '%s'"
             % (casa, casa, bibliotecas, bibliotecas, codigo))
    return ta.adb_texto("shell", linha, segundos=300).strip()


def _processador_no_android(ta, bibliotecas):
    saida = _python_no_android(ta, bibliotecas, "import hardware,json;"
                               "print(json.dumps(hardware.velocidade_de_um_nucleo(rodadas=21)))")
    try:
        return json.loads(saida.splitlines()[-1])
    except (ValueError, IndexError):
        return {"erro": saida[-300:]}


def _disco_no_android(ta, bibliotecas):
    saida = _python_no_android(ta, bibliotecas, "import hardware,json;"
                               "print(json.dumps(hardware.medir_velocidade(\"%s\")))" % NO_APARELHO)
    try:
        return json.loads(saida.splitlines()[-1])
    except (ValueError, IndexError):
        return {"erro": saida[-300:]}


def _retroarch_no_android(ta, apk_local):
    """O RetroArch do APK sem freio, nos mesmos nucleos (os do APK, tirados
    de 'apk_local', o arquivo aqui do computador) e jogos."""
    import bios
    import limpeza
    resultado = {}
    local = tempfile.mkdtemp(prefix="arena_medida_android_")
    try:
        sistema = os.path.join(local, "system")
        os.makedirs(sistema)
        bios.instalar_livres(sistema)
        ta.adb("shell", "rm", "-rf", NO_APARELHO)
        ta.adb("shell", "mkdir", "-p", NO_APARELHO)
        ta.adb("push", sistema, NO_APARELHO + "/", segundos=300)
        # O controle do proprio Android (a medida de 21/10 foi assim).
        opcoes = medidas_virtuais.cfg_sem_freio(local, NO_APARELHO + "/system", controle=None)
        with open(opcoes, encoding="utf-8") as arquivo:
            texto = arquivo.read().replace(local.replace("\\", "/"), NO_APARELHO).replace(local, NO_APARELHO)
        # A pasta "info" do RetroArch e' a do Windows: no aparelho, fica a do APK.
        texto = "".join(l for l in texto.replace("\\", "/").splitlines(True) if not l.startswith("libretro_info_path"))
        cfg = os.path.join(local, "medida.cfg")
        with open(cfg, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(texto)
        ta.adb("push", cfg, NO_APARELHO + "/medida.cfg")
        for pasta in ("saves", "states", "fotos", "cache"):
            ta.adb("shell", "mkdir", "-p", "%s/%s" % (NO_APARELHO, pasta))
        for console, nucleo, jogo in medidas_virtuais.jogos_da_medida():
            no_apk = "assets/arena-nucleos/x86_64/%s_android.so" % nucleo
            # O nucleo sai do APK aqui no computador: o unzip do Android
            # deixava o arquivo cheio de zeros ("bad ELF magic"), o RetroArch
            # abria sem jogo e a medida contava quadros do menu (21/10/2026).
            copia = os.path.join(local, os.path.basename(no_apk))
            with zipfile.ZipFile(apk_local) as pacote, pacote.open(no_apk) as de, open(copia, "wb") as para:
                shutil.copyfileobj(de, para)
            ta.adb("shell", "mkdir", "-p", NO_APARELHO + "/" + os.path.dirname(no_apk))
            ta.adb("push", copia, NO_APARELHO + "/" + no_apk, segundos=120)
            ta.adb("push", jogo, NO_APARELHO + "/" + os.path.basename(jogo))
            dono = ta.adb_texto("shell", "stat", "-c", "%u:%g", "/data/data/" + PACOTE).strip()
            ta.adb("shell", "chown", "-R", dono, NO_APARELHO)
            nucleo_no_aparelho = "%s/%s" % (NO_APARELHO, no_apk)
            rom = "%s/%s" % (NO_APARELHO, os.path.basename(jogo))

            def comando(quadros, nucleo_no_aparelho=nucleo_no_aparelho, rom=rom):
                return ["--config", NO_APARELHO + "/medida.cfg", "-L", nucleo_no_aparelho,
                        "--max-frames=%d" % quadros, rom]
            resultado[console] = dict(_fps_no_android(ta, comando), nucleo=nucleo)
    finally:
        limpeza.apagar_pasta(local)
    return resultado


HORA_DO_LOGCAT = re.compile(r"^\d\d-\d\d (\d\d):(\d\d):(\d\d)\.(\d{3})")


def _hora(linha):
    """Os segundos do dia de uma linha do logcat (o formato de sempre)."""
    achou = HORA_DO_LOGCAT.match(linha)
    if not achou:
        return None
    h, m, s, ms = (int(x) for x in achou.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0


def _segundos_no_android(ta, argumentos, limite=300):
    """Abre o RetroArch do APK com a linha de comando (o extra ARGS) e mede
    quanto o jogo rodou, pelo registro do RetroArch no logcat (cada linha tem
    a hora, em milissegundos): do "[Core] Geometry" (o jogo comecou) ao
    "Unloading game" (acabaram os quadros do --max-frames). O processo do app
    nao serve para medir: depois do --max-frames, o Android o deixa vivo, e a
    conta pelo fim dele saia errada (21/10/2026). O app fecha inteiro antes e
    depois de cada rodada."""
    ta.adb("shell", "am", "force-stop", PACOTE)
    ta.adb("logcat", "-c")
    roteiro = "/data/local/tmp/arena_medida.sh"
    linhas = ["ARGS=$(printf '%%s\\n' %s)" % " ".join("'%s'" % a for a in ["--verbose"] + list(argumentos)),
              "am start -n %s --es ARGS \"$ARGS\" --es DATADIR /data/user/0/%s --es SDCARD /sdcard "
              "--es EXTERNAL /sdcard/Android/data/%s/files >/dev/null" % (RETROARCH_DO_APK, PACOTE, PACOTE)]
    local = os.path.join(tempfile.mkdtemp(prefix="arena_roteiro_"), "medida.sh")
    with open(local, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    ta.adb("push", local, roteiro)
    ta.adb("shell", "sh", roteiro)
    fim = time.monotonic() + limite
    registro = []
    while time.monotonic() < fim:
        registro = ta.adb_texto("logcat", "-d", "-s", "RetroArch", segundos=60).splitlines()
        if any("Unloading game" in l for l in registro):
            break
        time.sleep(1)
    ta.adb("shell", "am", "force-stop", PACOTE)
    comeco = next((_hora(l) for l in registro if "[Core] Geometry" in l), None)
    final = next((_hora(l) for l in registro if "Unloading game" in l), None)
    if comeco is None or final is None:
        return None
    return (final - comeco) % 86400                 # passando da meia-noite


def _fps_no_android(ta, comando):
    """A mesma conta do Windows e do Linux (medidas_virtuais.fps_sem_freio),
    com o tempo medido pelo adb."""
    return medidas_virtuais.fps_sem_freio(comando, medir=lambda argumentos: _segundos_no_android(ta, argumentos))


# ---------------------------------------------------------------------------
# As contas
# ---------------------------------------------------------------------------

def contas(medidas):
    """A perda de cada sistema virtual (o processador de dentro / o do
    Windows) e, por nucleo, o medido, o estimado sem a perda e a razao com o
    Windows."""
    base = medidas.get("W") or {}
    ops_base = (base.get("processador") or {}).get("operacoes_por_segundo")
    tabela = {}
    for sistema, dados in medidas.items():
        ops = (dados.get("processador") or {}).get("operacoes_por_segundo")
        perda = round(ops / ops_base, 3) if ops and ops_base else None
        linha = {"processador_relativo_ao_windows": perda, "nucleos": {}}
        for console, medida in (dados.get("nucleos") or {}).items():
            fps = medida.get("fps")
            do_windows = ((base.get("nucleos") or {}).get(console) or {}).get("fps")
            estimado = round(fps / perda, 1) if fps and perda else None
            linha["nucleos"][console] = {
                "medido_fps": fps, "estimado_sem_a_perda_fps": estimado,
                "medido_sobre_windows": round(fps / do_windows, 3) if fps and do_windows else None,
                "estimado_sobre_windows": round(estimado / do_windows, 3) if estimado and do_windows else None}
        tabela[sistema] = linha
    return tabela


def principal():
    escolha = next((a for a in sys.argv[1:] if not a.startswith("--")), "W,L,A").upper()
    partes = [p for p in "WLA" if p in escolha]
    saida = os.path.join(RAIZ, "docs", "sistemas_virtuais_bruto.json")
    try:
        with open(saida, encoding="utf-8") as arquivo:
            anterior = json.load(arquivo).get("medidas", {})
    except (OSError, ValueError):
        anterior = {}
    medidas = dict(anterior)
    for parte, medir in (("W", no_windows), ("L", no_linux), ("A", no_android)):
        if parte in partes:
            print("== %s" % {"W": "Windows", "L": "Linux (conteiner do WSL)", "A": "Android (emulador)"}[parte],
                  flush=True)
            try:
                medidas[parte] = medir()
            except Exception as erro:   # um sistema que falha nao leva embora as medidas dos outros
                import traceback
                traceback.print_exc()
                medidas[parte] = {"erro": "%s: %s" % (type(erro).__name__, erro)}
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "medidas": medidas, "contas": contas(medidas)}
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print(json.dumps(resultado["contas"], ensure_ascii=False, indent=1))
    print("Resultado: %s" % saida)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
