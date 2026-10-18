# -*- coding: utf-8 -*-
r"""
ARENA - a abertura do servidor no Android (item 14).

No Windows, o ARENA.bat abre o servidor\arena.py; no Linux, o ARENA.sh. No
Android, quem abre e' o app do ARENA (android\src\...\ArenaServico.java),
com o Python do APK (ferramentas\python_android.py), e este arquivo vem
antes do arena.py:

  1. o fio com o app (servidor\ponte_android.py): o stdout de verdade fica
     so para os pedidos ao app, e os print() do servidor passam a ir para o
     stderr, que o app grava no registro do Android (o logcat);
  2. a pasta do ARENA que o arena.py enxerga e' a pasta "arena" do app. O
     programa (servidor, launcher, os guias) o app tira do APK; as pastas de
     quem usa (jogos, dados, BIOS, backup e, dentro de retroarch, saves,
     states, system...) viram atalhos para a pasta do ARENA que a pessoa
     escolheu -- no cartao, no pen drive ou na memoria do aparelho: os mesmos
     jogos, saves e BIOS do Windows. Sem pasta escolhida, os atalhos apontam
     para pastas do proprio app. Se o Android nao deixa gravar na pasta
     escolhida (o cartao, nos Android antigos), os jogos e as BIOS vem dela e
     o que se grava (saves, recordes) fica no app;
  3. o que o RetroArch do Android usa da pasta retroarch e que vem no APK (os
     perfis de controle do Android, a tela de toque, as informacoes dos
     nucleos, os filtros de som e imagem e os recursos do menu) sai do APK
     uma vez por versao;
  4. a vez passa ao arena.py, o mesmo do Windows e do Linux.

O que o app conta ao abrir (variaveis do ambiente):
  ARENA_PASTA            a pasta do ARENA escolhida ("" = a do app)
  ARENA_ANDROID_DADOS    a pasta do app para o que e' de quem usa
  ARENA_ANDROID_APK      o APK instalado (de onde saem os nucleos)
  ARENA_ANDROID_ABI      arm64-v8a ou x86_64
  ARENA_ANDROID_RAIZES   a memoria do aparelho e cada cartao ou pen drive
                         (uma por linha), onde procurar a pasta do ARENA
"""
import os
import runpy
import shutil
import sys
import time
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)

import ponte_android  # noqa: E402
import plataforma  # noqa: E402

# As pastas de quem usa, como ficam dentro da pasta do ARENA, e se o ARENA so
# as le (servem mesmo numa pasta em que o Android nao deixa gravar).
PASTAS_DE_QUEM_USA = [
    ("jogos", True), ("BIOS", True), ("dados", False), ("backup", False),
    ("retroarch/system", True), ("retroarch/thumbnails", True), ("retroarch/cheats", True),
    ("retroarch/shaders", True),
    ("retroarch/saves", False), ("retroarch/states", False), ("retroarch/screenshots", False),
    ("retroarch/remaps", False), ("retroarch/config", False), ("retroarch/playlists", False),
    ("retroarch/controles", False),
]
# Do APK (os recursos do RetroArch do Android) para a pasta retroarch do app.
DO_APK = [("assets/autoconfig/android/", "retroarch/autoconfig/android"),
          ("assets/overlays/", "retroarch/overlays"),
          ("assets/info/", "retroarch/info"),
          ("assets/filters/", "retroarch/filters"),
          ("assets/assets/", "retroarch/assets")]
# O retroarch.cfg do Android: o do app (o RetroArch grava nele ao fechar).
# Comeca como o da pasta escolhida ou como o modelo do pacote (o que o APK
# trouxe), e o arena.py acerta os caminhos e os motores a cada abertura.
MODELO_DO_CFG = os.path.join(RAIZ, "retroarch-modelo.cfg")
# O que o retroarch.cfg do Android precisa ter: os recursos do APK quem tira
# e' o ARENA (DO_APK); o RetroArch nao tira de novo.
NO_CFG_DO_ANDROID = {"bundle_assets_extract_enable": "false"}


def caminho(*partes):
    """Um caminho dentro da pasta do ARENA do app, com "/" nos relativos."""
    pedacos = []
    for parte in partes:
        pedacos += parte.split("/")
    return os.path.join(RAIZ, *pedacos)


def abrir_o_fio():
    """O stdout de verdade vira o fio com o app; o que o servidor escreve com
    print() passa a ir para o stderr (o registro do Android)."""
    sys.stdout.flush()
    fio = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
    os.dup2(2, 1)
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    ponte_android.CANAL = fio
    ponte_android.comecar_a_ouvir()


def da_para_gravar(pasta):
    """O Android deixa o app gravar nesta pasta? (o cartao, nos antigos, nao)"""
    teste = os.path.join(pasta, ".arena-teste-%d" % os.getpid())
    try:
        with open(teste, "w", encoding="utf-8") as arquivo:
            arquivo.write("ok")
        os.remove(teste)
        return True
    except OSError:
        return False


def ligar(atalho, alvo):
    """Faz 'atalho' (na pasta do app) apontar para a pasta 'alvo'. Nunca apaga
    nada de ninguem: uma pasta de verdade no lugar do atalho so sai se estiver
    vazia; com arquivos, muda de nome."""
    os.makedirs(os.path.dirname(atalho), exist_ok=True)
    if os.path.islink(atalho):
        if os.readlink(atalho) == alvo:
            return
        os.remove(atalho)            # tira so o atalho: a pasta continua la
    elif os.path.lexists(atalho):
        try:
            os.rmdir(atalho)         # pasta vazia (ou nada)
        except OSError:
            guardada = "%s.antes-%s" % (atalho, time.strftime("%Y%m%d-%H%M%S"))
            os.replace(atalho, guardada)
            print("[ARENA] %s ja tinha arquivos: ficou como %s." % (atalho, guardada))
    # O target_is_directory so vale no Windows (os testes rodam la).
    os.symlink(alvo, atalho, target_is_directory=True)


def montar_as_pastas(escolhida, privada):
    """Os atalhos das pastas de quem usa (ver o topo). Devolve se a pasta
    escolhida so deixa ler."""
    if escolhida and not os.path.isdir(escolhida):
        print("[ARENA] A pasta do ARENA escolhida (%s) nao esta no aparelho agora: "
              "abrindo com a pasta do app." % escolhida)
        escolhida = ""
    gravar = bool(escolhida) and da_para_gravar(escolhida)
    if escolhida and not gravar:
        print("[ARENA] O Android nao deixa gravar em %s: os jogos e as BIOS vem de la; os saves e os "
              "recordes ficam no app." % escolhida)
    for relativo, so_de_ler in PASTAS_DE_QUEM_USA:
        alvo = None
        if escolhida and (gravar or so_de_ler):
            alvo = os.path.join(escolhida, *relativo.split("/"))
            if not os.path.isdir(alvo):
                try:
                    os.makedirs(alvo, exist_ok=True)
                except OSError:
                    alvo = None
        if alvo is None:
            alvo = os.path.join(privada, *relativo.split("/"))
            os.makedirs(alvo, exist_ok=True)
        ligar(caminho(relativo), alvo)
    ponte_android.ESTADO.update({"pasta": escolhida, "so_leitura": bool(escolhida) and not gravar})
    return bool(escolhida) and not gravar


def tirar_do_apk(apk):
    """Os recursos do RetroArch do Android (DO_APK), uma vez por APK. Nunca
    apaga: so poe (ou troca) os arquivos que vieram nele."""
    marca = caminho("retroarch", ".arena-do-apk")
    desta = ponte_android.marca_do_apk()
    try:
        with open(marca, encoding="utf-8") as arquivo:
            if arquivo.read().strip() == desta:
                return 0
    except OSError:
        pass
    postos = 0
    try:
        with zipfile.ZipFile(apk) as pacote:
            for item in pacote.infolist():
                for origem, destino in DO_APK:
                    if not item.filename.startswith(origem) or item.is_dir():
                        continue
                    relativo = item.filename[len(origem):]
                    if not relativo or ".." in relativo.split("/"):
                        continue
                    alvo = caminho(destino, relativo)
                    os.makedirs(os.path.dirname(alvo), exist_ok=True)
                    with pacote.open(item) as de, open(alvo + ".parcial", "wb") as para:
                        shutil.copyfileobj(de, para, 1 << 16)
                    os.replace(alvo + ".parcial", alvo)
                    postos += 1
    except (OSError, zipfile.BadZipFile) as falha:
        print("[ARENA] Nao consegui tirar do APK os recursos do RetroArch: %s" % falha)
        return postos
    with open(marca, "w", encoding="utf-8") as arquivo:
        arquivo.write(desta)
    return postos


def preparar_o_cfg(escolhida):
    """O retroarch.cfg do app: na primeira vez, o da pasta escolhida ou o
    modelo; e sempre com o que o Android precisa (NO_CFG_DO_ANDROID)."""
    cfg = caminho("retroarch", "retroarch.cfg")
    if not os.path.isfile(cfg):
        de_la = os.path.join(escolhida, "retroarch", "retroarch.cfg") if escolhida else ""
        for origem in (de_la, MODELO_DO_CFG):
            if origem and os.path.isfile(origem):
                shutil.copyfile(origem, cfg)
                break
    try:
        with open(cfg, encoding="utf-8", errors="replace") as arquivo:
            linhas = arquivo.readlines()
    except OSError:
        linhas = []
    faltam = dict(NO_CFG_DO_ANDROID)
    for i, linha in enumerate(linhas):
        chave = linha.split("=", 1)[0].strip()
        if chave in faltam:
            linhas[i] = '%s = "%s"\n' % (chave, faltam.pop(chave))
    linhas += ['%s = "%s"\n' % (chave, valor) for chave, valor in faltam.items()]
    with open(cfg + ".parcial", "w", encoding="utf-8") as arquivo:
        arquivo.writelines(linhas)
    os.replace(cfg + ".parcial", cfg)


def preparar():
    escolhida = os.environ.get("ARENA_PASTA", "").strip()
    privada = os.environ.get("ARENA_ANDROID_DADOS") or os.path.join(os.path.dirname(RAIZ), "arena-dados")
    for pasta in ("cores", "cache", "autoconfig"):
        os.makedirs(caminho("retroarch", pasta), exist_ok=True)
    montar_as_pastas(escolhida, privada)
    # A marca de que o RetroArch veio no APK (plataforma.executavel_do_retroarch).
    with open(caminho("retroarch", plataforma.RETROARCH_DO_ANDROID), "w", encoding="utf-8") as arquivo:
        arquivo.write("O RetroArch do Android vem dentro do APK do ARENA (android/retroarch/arena-args.patch).\n")
    postos = tirar_do_apk(ponte_android.APK)
    if postos:
        print("[ARENA] Recursos do RetroArch do Android postos: %d arquivos." % postos)
    preparar_o_cfg(ponte_android.ESTADO.get("pasta") or "")


def principal():
    abrir_o_fio()
    try:
        preparar()
    except Exception:
        import traceback
        traceback.print_exc()
        print("[ARENA] A pasta do ARENA no aparelho nao ficou pronta: o app tenta de novo.")
        sys.stdout.flush()
        os._exit(3)
    sys.argv = [os.path.join(AQUI, "arena.py")]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    principal()
