# -*- coding: utf-8 -*-
r"""Monta o APK do ARENA para Android (item 14 do plano de 15/10/2026).

Pedido do Rafael: "o ARENA se tornar um aplicativo de Android tambem com um
apk no github para download ... sempre a ideia e' baixar e ja usar, simples
e rapido". O APK do ARENA e':

  - o RetroArch 1.22.2 OFICIAL para Android (o RetroArch.apk do libretro, o
    mesmo RetroArch do Windows, do Linux e do Chromebook): muda o nome do
    aplicativo, o icone, a tela que abre primeiro e uma peca so, a
    biblioteca do RetroArch (lib\<abi>\libretroarch-activity.so), compilada
    do codigo oficial da mesma versao com o remendo do ARENA
    (ferramentas\compilar_retroarch_android.py): com ele, o Android recebe a
    mesma linha de comando do Windows e do Linux, e o jogo em rede junto;
  - o SERVIDOR do ARENA, o mesmo do Windows e do Linux (servidor\), com o
    Python 3.13.16 do Android (ferramentas\python_android.py), que o
    ArenaServico.java roda no aparelho, e a tela de sempre do ARENA
    (launcher\) num WebView, falando com ele em http://127.0.0.1:8777;
  - de reserva, se o servidor nao abrir no aparelho, o servidor dentro da
    pagina do ARENA do Chromebook (launcher\navegador), com a ponte da
    ArenaActivity.java para abrir cada jogo no RetroArch nativo;
  - os nucleos do Android de cada console do ARENA (62 dos 63: o do Java ME
    precisa de Java, que o Android nao tem), as BIOS livres e os jogos livres
    dos testes (testes\jogos_livres), para a primeira abertura ja ter jogo.

Um APK por tipo de processador: arm64-v8a (quase todo celular e tablet de
hoje) e x86_64 (Chromebook Intel e o emulador dos testes).

Passo a passo (cada download confere a marca SHA-256):
  1. o RetroArch.apk e o apktool (o desmontador e remontador de APK, codigo
     aberto) vao para o cache de quem monta;
  2. os nucleos do Android sao do "nightly" do libretro (o 1.22.2 do
     Android nao publica nucleo separado): vale o conjunto conferido, com a
     marca de cada zip em ferramentas\android_nucleos.json (um nightly novo
     so entra com --atualizar-nucleos, depois de alguem conferir);
  3. o apktool desmonta o RetroArch.apk sem tocar no codigo dele (-s): o
     AndroidManifest.xml ganha o nome do ARENA (o pacote
     io.github.rafaparise.arena, para conviver com um RetroArch instalado), a
     ArenaActivity como a tela que abre, e sai o que o ARENA nao usa (os
     bancos de dados de jogos, os filtros de tela e os temas de menu, uns
     280 MB);
  4. a ArenaActivity e' compilada com o javac e o d8 do SDK do Android
     (ferramentas\preparar_android.py), sem o Android Studio, e a biblioteca
     do RetroArch troca pela remendada (compilada uma vez e guardada);
  5. o apktool remonta, o zipalign alinha e o apksigner assina com a chave do
     ARENA. A chave fica FORA do git, em %LOCALAPPDATA%\ARENA-android\
     assinatura: guarde-a bem. Sem ela, a versao seguinte do APK nao instala
     por cima (seria preciso desinstalar, e os recordes do aparelho iriam
     junto).

Os APKs ficam em %LOCALAPPDATA%\ARENA-android\apk.

Uso:
    servidor\python\python.exe ferramentas\montar_android.py [--abi arm64-v8a|x86_64] [--teste]
                                                             [--atualizar-nucleos]
--teste  o APK deixa o teste ler o console da pagina (chrome://inspect)
"""
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import compilar_retroarch_android as retroarch_remendado  # noqa: E402
import python_android  # noqa: E402  (o Python do Android e o lancador)
import limpeza  # noqa: E402
import preparar_android as sdk  # noqa: E402  (o JDK e o SDK do Android, em %LOCALAPPDATA%\ARENA-android)
import preparar_linux  # noqa: E402  (o cache e o download com a marca)

RETROARCH_APK = {
    "endereco": "https://buildbot.libretro.com/stable/1.22.2/android/RetroArch.apk",
    "arquivo": os.path.join("android", "RetroArch.apk"),
    "sha256": "2eca60b3a540697cd7676edea2fbabdfaf54c3ae958584168231981099d2868a",   # baixado em 18/10/2026
    "tamanho": 198332624,
}
APKTOOL = {
    "endereco": "https://github.com/iBotPeaches/Apktool/releases/download/v3.0.3/apktool_3.0.3.jar",
    "arquivo": os.path.join("android", "apktool_3.0.3.jar"),
    "sha256": "dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423",   # a do GitHub
    "tamanho": 15478013,
}
PACOTE = "io.github.rafaparise.arena"
ABIS = ["arm64-v8a", "x86_64"]
NIGHTLY = "https://buildbot.libretro.com/nightly/android/latest/%s/%s.zip"
ARQUIVO_DOS_NUCLEOS = os.path.join(RAIZ, "ferramentas", "android_nucleos.json")
# O nucleo que tem outro nome no Android (o mesmo de launcher\navegador\android.js).
OUTRO_NOME = {"mupen64plus_next_libretro": "mupen64plus_next_gles3_libretro",
              "mame_libretro": "mamearcade_libretro"}
# Do RetroArch.apk, o que o ARENA nao usa: os bancos de dados de jogos, os
# filtros de tela (os do ARENA sao do Vulkan; no Android vale a escala do
# RetroArch), as molduras, os temas de menu do XMB e do Ozone (o ARENA usa o
# RGUI) e os efeitos.
FORA_DO_APK = [os.path.join("assets", "database"), os.path.join("assets", "shaders"),
               os.path.join("assets", "overlays", "borders"), os.path.join("assets", "overlays", "effects"),
               os.path.join("assets", "overlays", "ipad"), os.path.join("assets", "overlays", "misc"),
               os.path.join("assets", "assets", "xmb"), os.path.join("assets", "assets", "ozone")]
# A tela do ARENA que vai no APK: o launcher, menos os nucleos do navegador
# (no APK quem joga e' o RetroArch nativo).
FORA_DA_TELA = ["nucleos", "*.wasm.js", "__pycache__"]
# O servidor que vai no APK: o mesmo do pacote, sem os testes e sem o Python
# do Windows e o do Linux (o do Android vem pelo python_android).
FORA_DO_SERVIDOR = ["tests", "python", "python-linux", "__pycache__", "*.pyc", "*.pyo", "*.log", "*.tmp",
                    "achar_python.sh"]
# Da raiz do ARENA: os guias, a licenca e os creditos (o servidor mostra os guias).
DA_RAIZ_NO_APK = ["LEIA-ME.md", "1-COMECAR.md", "2-JOGOS.md", "3-IMAGEM-SOM-CONTROLE.md", "4-SAVES.md",
                  "5-AMIGOS.md", "6-RECURSOS-E-REPARO.md", "LICENSE", "TERCEIROS.md", "CREDITOS.md"]
PASTA_DOS_LIVRES = os.path.join(RAIZ, "testes", "jogos_livres")
SAIDA = os.path.join(sdk.BASE, "apk")
ASSINATURA = os.path.join(sdk.BASE, "assinatura")


def ferramenta(nome):
    return os.path.join(sdk.SDK, "build-tools", "35.0.0", nome)


def rodar(comando, **extras):
    """Roda e para tudo com a explicacao se der errado."""
    feito = subprocess.run(comando, capture_output=True, text=True, errors="replace", env=sdk.ambiente(), **extras)
    if feito.returncode != 0:
        raise SystemExit("Falhou: %s\n%s" % (" ".join(str(c) for c in comando)[:300],
                                             (feito.stdout + feito.stderr)[-3000:]))
    return feito


def java():
    return os.path.join(sdk.JDK, "bin", "java.exe")


def marca(caminho):
    return preparar_linux.marca(caminho)


# ---------------------------------------------------------------------------
# Os nucleos do Android
# ---------------------------------------------------------------------------

def nucleos_do_arena():
    """{nome do .so do Android: id do console} dos nucleos que o ARENA usa."""
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        plataformas = json.load(arquivo)["plataformas"]
    nomes = {}
    for p in plataformas:
        for campo in ("core", "core_netplay"):
            if p.get(campo):
                base = os.path.splitext(p[campo])[0]
                nomes.setdefault((OUTRO_NOME.get(base, base)) + "_android.so", p["id"])
    return nomes


def ler_lista_dos_nucleos():
    try:
        with open(ARQUIVO_DOS_NUCLEOS, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return {}


def nucleos_do_android(abi, atualizar):
    """{nome do .so: caminho no cache} dos nucleos desta ABI. Confere cada zip
    com a marca de ferramentas\\android_nucleos.json; com 'atualizar', baixa o
    nightly de agora e grava as marcas novas."""
    lista = ler_lista_dos_nucleos()
    marcas = lista.get(abi, {})
    pasta = os.path.join(preparar_linux.CACHE, "android-nucleos", abi)
    os.makedirs(pasta, exist_ok=True)
    saida, faltam = {}, []
    for nome in sorted(nucleos_do_arena()):
        zip_cache = os.path.join(pasta, nome + ".zip")
        conferida = marcas.get(nome, {}).get("sha256")
        if atualizar and (not os.path.isfile(zip_cache) or marca(zip_cache) != conferida):
            try:
                with urllib.request.urlopen(NIGHTLY % (abi, nome), timeout=120) as resposta:
                    conteudo = resposta.read()
            except OSError:
                faltam.append(nome)
                marcas.pop(nome, None)
                continue
            with open(zip_cache + ".baixando", "wb") as arquivo:
                arquivo.write(conteudo)
            os.replace(zip_cache + ".baixando", zip_cache)
            marcas[nome] = {"sha256": marca(zip_cache), "tamanho": os.path.getsize(zip_cache)}
        if nome not in marcas:
            faltam.append(nome)
            continue
        if not os.path.isfile(zip_cache):
            try:
                with urllib.request.urlopen(NIGHTLY % (abi, nome), timeout=120) as resposta, \
                        open(zip_cache + ".baixando", "wb") as arquivo:
                    shutil.copyfileobj(resposta, arquivo, 1 << 20)
                os.replace(zip_cache + ".baixando", zip_cache)
            except OSError:
                faltam.append(nome)
                continue
        if marca(zip_cache) != marcas[nome]["sha256"]:
            raise SystemExit("O %s (%s) mudou no nightly desde a conferencia (ferramentas\\android_nucleos.json).\n"
                             "Confira e rode de novo com --atualizar-nucleos. Nada foi montado." % (nome, abi))
        so = os.path.join(pasta, nome)
        if not os.path.isfile(so) or os.path.getmtime(so) < os.path.getmtime(zip_cache):
            with zipfile.ZipFile(zip_cache) as pacote:
                dados = pacote.read(nome)
            if dados[:4] != b"\x7fELF":
                raise SystemExit("%s nao e' um nucleo do Android." % nome)
            with open(so, "wb") as arquivo:
                arquivo.write(dados)
        saida[nome] = so
    if atualizar:
        lista[abi] = marcas
        lista["_leia"] = ["Os nucleos do Android do ARENA: o nightly do libretro (o 1.22.2 do Android nao publica "
                          "nucleo separado), com a marca SHA-256 de cada zip conferida. Um nightly novo so entra "
                          "pelo ferramentas\\montar_android.py --atualizar-nucleos."]
        lista["conferido_em"] = time.strftime("%Y-%m-%d")
        with open(ARQUIVO_DOS_NUCLEOS, "w", encoding="utf-8", newline="\n") as arquivo:
            json.dump(lista, arquivo, ensure_ascii=False, indent=1, sort_keys=True)
            arquivo.write("\n")
    return saida, faltam


# ---------------------------------------------------------------------------
# O icone (o monstrinho da capa do ARENA)
# ---------------------------------------------------------------------------

def gravar_png(caminho, largura, altura, pontos):
    cru = bytearray()
    for y in range(altura):
        cru.append(0)
        for r, g, b in pontos[y * largura:(y + 1) * largura]:
            cru += bytes((r, g, b))

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)

    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
                      + bloco(b"IDAT", zlib.compress(bytes(cru), 9)) + bloco(b"IEND", b""))


def gerar_icones(res):
    """O icone do ARENA: o monstrinho da capa (docs\\imagens\\arena-capa.png),
    num quadrado do ceu estrelado dela, ampliado sem borrar (pixel art)."""
    from gravar_fundo_gif import ler_png
    with open(os.path.join(RAIZ, "docs", "imagens", "arena-capa.png"), "rb") as arquivo:
        largura, _altura, pontos = ler_png(arquivo.read())
    x0, y0, lado = 84, 280, 112                     # o monstrinho fica em x 88-191, y 296-375
    recorte = [pontos[(y0 + y) * largura + x0 + x][:3] for y in range(lado) for x in range(lado)]

    def ampliar(tamanho):
        return [recorte[(y * lado // tamanho) * lado + (x * lado // tamanho)] for y in range(tamanho)
                for x in range(tamanho)]
    # O icone comum (48 a 192) e a frente do icone adaptavel (108 a 432).
    for pasta, comum, frente in (("mipmap-mdpi", 48, 108), ("mipmap-hdpi", 72, 162), ("mipmap-xhdpi", 96, 216),
                                 ("mipmap-xxhdpi", 144, 324), ("mipmap-xxxhdpi", 192, 432)):
        gravar_png(os.path.join(res, pasta, "ic_launcher.png"), comum, comum, ampliar(comum))
        gravar_png(os.path.join(res, pasta, "ic_launcher_foreground.png"), frente, frente, ampliar(frente))
    fundo = recorte[0]
    cores = os.path.join(res, "values", "colors.xml")
    with open(cores, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    texto = re.sub(r'(<color name="ic_launcher_background">)[^<]*(</color>)',
                   r"\g<1>#%02x%02x%02x\g<2>" % fundo, texto)
    with open(cores, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)


# ---------------------------------------------------------------------------
# A tela do ARENA, os dados do Android e as BIOS livres
# ---------------------------------------------------------------------------

def dados_do_android():
    """O android_dados.js: as opcoes de cada nucleo do ARENA (as mesmas do
    Windows, graficos.opcoes_finais_do_nucleo), para todos os nucleos (o
    dados.js do navegador so tem as dos nucleos do navegador)."""
    import arena  # noqa: F401  (carrega o graficos.json como o servidor)
    import graficos
    import montar_navegador
    opcoes = {}
    for nome in sorted(nucleos_do_arena()):
        curto = nome.replace("_libretro_android.so", "")
        for windows, android in OUTRO_NOME.items():
            if android.replace("_libretro", "") == curto:
                curto = windows.replace("_libretro", "")
        opcoes[curto] = {str(n): graficos.opcoes_finais_do_nucleo(curto, n, nota_gpu=min(n, 3))
                         for n in montar_navegador.NOTAS}
    return ("// Gerado por ferramentas\\montar_android.py (so no APK): nao edite a mao.\n"
            "window.ARENA_ANDROID_DADOS = %s;\n" % json.dumps({"opcoes_nucleo": opcoes}, ensure_ascii=False,
                                                              sort_keys=True))


def por_a_tela(assets, teste):
    destino = os.path.join(assets, "arena", "launcher")
    shutil.copytree(os.path.join(RAIZ, "launcher"), destino, ignore=shutil.ignore_patterns(*FORA_DA_TELA))
    with open(os.path.join(destino, "navegador", "android_dados.js"), "w", encoding="utf-8") as arquivo:
        arquivo.write(dados_do_android())
    if not os.path.isfile(os.path.join(destino, "navegador", "livres.js")):
        raise SystemExit("Falta o launcher\\navegador\\livres.js (os jogos livres que vem junto): rode antes o "
                         "ferramentas\\montar_navegador.py.")
    if teste:
        os.makedirs(os.path.join(assets, "arena", "android"), exist_ok=True)
        with open(os.path.join(assets, "arena", "android", "depurar"), "w", encoding="utf-8") as arquivo:
            arquivo.write("o APK de teste: chrome://inspect le o console da pagina\n")


def por_o_servidor(assets):
    """O servidor do ARENA (servidor\\), os guias e o modelo do retroarch.cfg
    (o do pacote dos alunos, sem nada de quem usou: montar_versao_alunos)."""
    destino = os.path.join(assets, "arena")
    shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                    ignore=shutil.ignore_patterns(*FORA_DO_SERVIDOR))
    for nome in DA_RAIZ_NO_APK:
        if os.path.isfile(os.path.join(RAIZ, nome)):
            shutil.copyfile(os.path.join(RAIZ, nome), os.path.join(destino, nome))
    cfg = os.path.join(RAIZ, "retroarch", "retroarch.cfg")
    if os.path.isfile(cfg):
        import montar_versao_alunos
        montar_versao_alunos.limpar_retroarch_cfg(cfg, os.path.join(destino, "retroarch-modelo.cfg"))


def por_os_jogos_livres(assets):
    """Os jogos livres dos testes (licenca MIT, CC0 ou Unlicense, cada um com a
    marca da lista.json) na pasta do console de cada um, com a licenca ao
    lado: o servidor do Android os poe na pasta jogos do app quando nao ha
    pasta do ARENA escolhida (android_inicio.py). Fica de fora o console sem
    nucleo no Android (o Java ME) e o arquivo que o console nao abre direto."""
    with open(os.path.join(PASTA_DOS_LIVRES, "lista.json"), encoding="utf-8") as arquivo:
        lista = json.load(arquivo)["arquivos"]
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        consoles = {p["id"]: p for p in json.load(arquivo)["plataformas"]}
    postos = 0
    for item in lista:
        console = consoles.get(item["console"]) or {}
        if not console.get("pasta") or "freej2me" in str(console.get("core", "")):
            continue
        origem = os.path.join(PASTA_DOS_LIVRES, *item["origem"].split("/"))
        extensao = os.path.splitext(origem)[1].lower()
        if extensao not in [e.lower() for e in console.get("extensoes", [])] or marca(origem) != item["sha256"]:
            continue
        pasta = os.path.join(assets, "arena-livres", console["pasta"])
        os.makedirs(pasta, exist_ok=True)
        shutil.copyfile(origem, os.path.join(pasta, os.path.basename(origem)))
        licenca = os.path.join(PASTA_DOS_LIVRES, *item.get("licenca_arquivo", "").split("/"))
        if item.get("licenca_arquivo") and os.path.isfile(licenca):
            shutil.copyfile(licenca, os.path.join(pasta, "LICENCA - %s.txt" % os.path.splitext(
                os.path.basename(origem))[0]))
        postos += 1
    return postos


def por_as_bios_livres(assets):
    """As BIOS livres (servidor\\bios_livres) no lugar delas dentro da pasta
    system (o "destino" da lista.json): a ArenaActivity copia as que faltam.
    As marcas das copias antigas ("sha256_antigos") vao para
    arena-bios-antigas.txt (destino, tab, marca): so essas ela troca."""
    pasta = os.path.join(RAIZ, "servidor", "bios_livres")
    with open(os.path.join(pasta, "lista.json"), encoding="utf-8") as arquivo:
        lista = json.load(arquivo)
    antigas = []
    for item in lista.get("arquivos", []):
        origem = os.path.join(pasta, *item["origem"].split("/"))
        if os.path.isfile(origem) and marca(origem) == item["sha256"]:
            alvo = os.path.join(assets, "arena-bios", *item["destino"].split("/"))
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            shutil.copyfile(origem, alvo)
            antigas += ["%s\t%s\n" % (item["destino"], antiga) for antiga in item.get("sha256_antigos", ())]
    with open(os.path.join(assets, "arena-bios-antigas.txt"), "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.writelines(antigas)


# ---------------------------------------------------------------------------
# O manifesto, o codigo, a assinatura
# ---------------------------------------------------------------------------

# O servidor do ARENA (ArenaServico.java), no mesmo processo da tela.
SERVICO_DO_ARENA = '''        <service android:exported="false" android:name="io.github.rafaparise.arena.ArenaServico" android:process=":tela"/>
'''
# O que o servidor pede ao Android alem do RetroArch: ficar aberto durante o
# jogo (o aviso na barra), receber os avisos da rede do Jogar Junto (o Wi-Fi
# joga fora os de grupo sem a trava) e, no Android 11 em diante, gravar no
# cartao e no pen drive (o "Acesso a todos os arquivos", que a pessoa liga).
PERMISSOES_DO_SERVIDOR = '''    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE"/>
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE"/>
'''
# O WebView so fala sem HTTPS com o servidor do proprio aparelho.
REDE_DO_ARENA = '''<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">127.0.0.1</domain>
    </domain-config>
</network-security-config>
'''

ATIVIDADE_DO_ARENA = '''        <activity android:configChanges="keyboard|keyboardHidden|navigation|orientation|screenLayout|screenSize|smallestScreenSize|uiMode" android:exported="true" android:label="ARENA" android:launchMode="singleTask" android:name="io.github.rafaparise.arena.ArenaActivity" android:process=":tela" android:screenOrientation="sensorLandscape" android:theme="@android:style/Theme.Black.NoTitleBar.Fullscreen">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
                <category android:name="android.intent.category.LEANBACK_LAUNCHER"/>
            </intent-filter>
        </activity>
'''


def ajustar_manifesto(pasta, versao_nome, versao_codigo):
    caminho = os.path.join(pasta, "AndroidManifest.xml")
    with open(caminho, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    trocas = [
        ('package="com.retroarch"', 'package="%s"' % PACOTE),
        ('android:authorities="com.retroarch.documents"', 'android:authorities="%s.documents"' % PACOTE),
        # O icone que abre e' o do ARENA; o menu do RetroArch continua la dentro.
        ('''            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
                <category android:name="android.intent.category.LEANBACK_LAUNCHER"/>
                <category android:name="tv.ouya.intent.category.GAME"/>
            </intent-filter>
''', ""),
        # As telas do RetroArch so abrem por dentro do ARENA. No RetroArch
        # oficial elas ficam abertas a qualquer app do aparelho, e a do jogo
        # aceita o caminho de um nucleo: outro app faria o RetroArch do ARENA
        # carregar um programa dele, com a permissao de arquivos do ARENA.
        ('<activity android:exported="true" android:launchMode="singleInstance" '
         'android:name="com.retroarch.browser.mainmenu.MainMenuActivity">',
         '<activity android:exported="false" android:launchMode="singleInstance" '
         'android:name="com.retroarch.browser.mainmenu.MainMenuActivity">'),
        ('android:exported="true" android:launchMode="singleInstance" '
         'android:name="com.retroarch.browser.retroactivity.RetroActivityFuture"',
         'android:exported="false" android:launchMode="singleInstance" '
         'android:name="com.retroarch.browser.retroactivity.RetroActivityFuture"'),
        ('<activity android:exported="true" android:name="com.retroarch.browser.debug.CoreSideloadActivity"/>',
         '<activity android:exported="false" android:name="com.retroarch.browser.debug.CoreSideloadActivity"/>'),
        ("    </application>", ATIVIDADE_DO_ARENA + SERVICO_DO_ARENA + "    </application>"),
        ('    <uses-permission android:name="android.permission.VIBRATE"/>\n',
         '    <uses-permission android:name="android.permission.VIBRATE"/>\n' + PERMISSOES_DO_SERVIDOR),
        # O WebView so fala sem HTTPS com o 127.0.0.1; e nada do app vai para a
        # copia na nuvem do Android: o apelido e os recordes (dados de aluno)
        # ficam no aparelho (a sincronizacao do ARENA e' que leva).
        ('<application android:allowAudioPlaybackCapture="true" android:allowBackup="true" ',
         '<application android:allowAudioPlaybackCapture="true" android:allowBackup="false" '
         'android:networkSecurityConfig="@xml/arena_rede" '),
    ]
    for velho, novo in trocas:
        if texto.count(velho) != 1:
            raise SystemExit("O AndroidManifest.xml do RetroArch mudou (nao achei %r). Nada foi montado." % velho[:60])
        texto = texto.replace(velho, novo)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    os.makedirs(os.path.join(pasta, "res", "xml"), exist_ok=True)
    with open(os.path.join(pasta, "res", "xml", "arena_rede.xml"), "w", encoding="utf-8") as arquivo:
        arquivo.write(REDE_DO_ARENA)
    nomes = os.path.join(pasta, "res", "values", "strings.xml")
    with open(nomes, encoding="utf-8") as arquivo:
        texto = arquivo.read().replace('<string name="app_name">RetroArch</string>', '<string name="app_name">ARENA</string>')
    with open(nomes, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    yml = os.path.join(pasta, "apktool.yml")
    with open(yml, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    texto = re.sub(r"minSdkVersion: \S+", "minSdkVersion: 24", texto)
    texto = re.sub(r"versionCode: \S+", "versionCode: %d" % versao_codigo, texto)
    texto = re.sub(r"versionName: \S+", "versionName: %s" % versao_nome, texto)
    with open(yml, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)


def compilar_java(trabalho):
    """A ArenaActivity: javac (Java 8) contra o android.jar, d8 para o dex."""
    fontes = []
    for atual, _subs, nomes in os.walk(os.path.join(RAIZ, "android", "src")):
        fontes += [os.path.join(atual, n) for n in nomes if n.endswith(".java")]
    classes = os.path.join(trabalho, "classes")
    dex = os.path.join(trabalho, "dex")
    os.makedirs(classes)
    os.makedirs(dex)
    android_jar = os.path.join(sdk.SDK, "platforms", "android-35", "android.jar")
    rodar([os.path.join(sdk.JDK, "bin", "javac.exe"), "--release", "8", "-encoding", "UTF-8", "-Xlint:-options",
           "-cp", android_jar, "-d", classes] + fontes)
    arquivos = [os.path.join(a, n) for a, _s, ns in os.walk(classes) for n in ns if n.endswith(".class")]
    rodar(sdk.linha_do_bat(ferramenta("d8.bat"), ["--min-api", "24", "--lib", android_jar, "--output", dex]
                           + arquivos))
    return os.path.join(dex, "classes.dex")


def chave_de_assinatura():
    """(arquivo da chave, segredo dela). Cria na primeira vez, fora do git."""
    chave = os.path.join(ASSINATURA, "arena.jks")
    arquivo_do_segredo = os.path.join(ASSINATURA, "segredo.txt")
    if not os.path.isfile(chave):
        os.makedirs(ASSINATURA, exist_ok=True)
        segredo = hashlib.sha256(os.urandom(32)).hexdigest()[:32]   # sorteado aqui, nunca no git
        rodar([os.path.join(sdk.JDK, "bin", "keytool.exe"), "-genkeypair", "-keystore", chave, "-alias", "arena",
               "-keyalg", "RSA", "-keysize", "4096", "-validity", "36500", "-storepass", segredo, "-keypass", segredo,
               "-dname", "CN=ARENA, OU=Desenvolvimento de Sistemas, O=RafaParise, C=BR"])
        with open(arquivo_do_segredo, "w", encoding="utf-8") as arquivo:
            arquivo.write(segredo)
        with open(os.path.join(ASSINATURA, "LEIA.txt"), "w", encoding="utf-8") as arquivo:
            arquivo.write("A chave que assina o APK do ARENA (ferramentas\\montar_android.py).\n"
                          "GUARDE UMA COPIA destes dois arquivos fora deste computador. Sem eles, o\n"
                          "proximo APK nao instala por cima do anterior (seria preciso desinstalar,\n"
                          "e o que o aparelho guardou iria junto). NUNCA ponha no git nem no GitHub.\n")
    with open(arquivo_do_segredo, encoding="utf-8") as arquivo:
        return chave, arquivo.read().strip()


def versao_do_arena():
    """("2026.10.18", 20261018): a versao do servidor e o numero do Android."""
    import arena
    versao = str(arena.VERSAO)
    digitos = re.sub(r"\D", "", versao)[:8] or time.strftime("%Y%m%d")
    return versao, int(digitos)


# ---------------------------------------------------------------------------
# Montar
# ---------------------------------------------------------------------------

def montar_apk(abi, teste, atualizar, trabalho):
    nucleos, faltam = nucleos_do_android(abi, atualizar)
    if not nucleos:
        raise SystemExit("Nenhum nucleo do Android para %s: rode com --atualizar-nucleos na primeira vez." % abi)
    pasta = os.path.join(trabalho, "ra-" + abi)
    print("  desmontando o RetroArch.apk (%s)..." % abi, flush=True)
    rodar([java(), "-jar", preparar_linux.baixado(APKTOOL), "d", "-s", "-f", "-o", pasta,
           preparar_linux.baixado(RETROARCH_APK)])
    versao, codigo = versao_do_arena()
    ajustar_manifesto(pasta, "%s (RetroArch 1.22.2)" % versao.replace(" ", "_"), codigo)
    for parte in FORA_DO_APK:
        if os.path.isdir(os.path.join(pasta, parte)):
            limpeza.apagar_pasta(os.path.join(pasta, parte))
    for outra in os.listdir(os.path.join(pasta, "lib")):
        if outra != abi:
            limpeza.apagar_pasta(os.path.join(pasta, "lib", outra))
    # A biblioteca do RetroArch: a do codigo oficial com o remendo do ARENA.
    shutil.copyfile(retroarch_remendado.biblioteca(abi), os.path.join(pasta, "lib", abi, "libretroarch-activity.so"))
    gerar_icones(os.path.join(pasta, "res"))
    assets = os.path.join(pasta, "assets")
    por_a_tela(assets, teste)
    por_o_servidor(assets)
    livres = por_os_jogos_livres(assets)
    por_as_bios_livres(assets)
    modulos = python_android.por_no_apk(pasta, abi)
    print("  servidor do ARENA, Python %s (%d modulos nativos) e %d jogos livres" % (python_android.VERSAO, modulos,
                                                                                    livres), flush=True)
    destino_nucleos = os.path.join(assets, "arena-nucleos", abi)
    os.makedirs(destino_nucleos)
    for nome, caminho in nucleos.items():
        shutil.copyfile(caminho, os.path.join(destino_nucleos, nome))
    dex = compilar_java(os.path.join(trabalho, "java-" + abi))
    print("  remontando (%d nucleos)..." % len(nucleos), flush=True)
    sem_assinar = os.path.join(trabalho, "sem-assinar-%s.apk" % abi)
    rodar([java(), "-jar", preparar_linux.baixado(APKTOOL), "b", pasta, "-o", sem_assinar])
    # O codigo do ARENA entra como um segundo dex, ao lado do do RetroArch
    # (o Android carrega os dois), sem mexer no dele.
    with zipfile.ZipFile(sem_assinar, "a", compression=zipfile.ZIP_DEFLATED) as apk:
        if "classes2.dex" in apk.namelist():
            raise SystemExit("O RetroArch.apk ja tem um classes2.dex: o ARENA precisa de outro nome.")
        apk.write(dex, "classes2.dex")
    alinhado = os.path.join(trabalho, "alinhado-%s.apk" % abi)
    rodar([ferramenta("zipalign.exe"), "-p", "-f", "4", sem_assinar, alinhado])
    chave, segredo = chave_de_assinatura()
    os.makedirs(SAIDA, exist_ok=True)
    final = os.path.join(SAIDA, "ARENA-%s-%s%s.apk" % (versao.replace(" ", "_"), abi, "-teste" if teste else ""))
    rodar(sdk.linha_do_bat(ferramenta("apksigner.bat"), ["sign", "--ks", chave, "--ks-pass", "pass:" + segredo,
                                                         "--out", final, alinhado]))
    rodar(sdk.linha_do_bat(ferramenta("apksigner.bat"), ["verify", final]))
    print("  pronto: %s (%.0f MB)%s" % (final, os.path.getsize(final) / 1048576,
                                         ("; sem nucleo no Android: %s" % ", ".join(faltam)) if faltam else ""),
          flush=True)
    return final


def principal():
    abis = [sys.argv[sys.argv.index("--abi") + 1]] if "--abi" in sys.argv else ABIS
    teste = "--teste" in sys.argv
    atualizar = "--atualizar-nucleos" in sys.argv
    for necessario in (os.path.join(sdk.JDK, "bin", "java.exe"), ferramenta("zipalign.exe"),
                       os.path.join(sdk.SDK, "platforms", "android-35", "android.jar")):
        if not os.path.isfile(necessario):
            raise SystemExit("Falta o SDK do Android: rode antes o ferramentas\\preparar_android.py.")
    trabalho = tempfile.mkdtemp(prefix="arena_apk_")
    try:
        print("Montando o APK do ARENA...", flush=True)
        for abi in abis:
            montar_apk(abi, teste, atualizar, trabalho)
        return 0
    finally:
        limpeza.apagar_pasta(trabalho)


if __name__ == "__main__":
    sys.exit(principal())
