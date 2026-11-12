# -*- coding: utf-8 -*-
r"""Jogos de PC no ARENA (12/11/2026): os jogos de computador, de qualquer sistema.

O console "PC" (consoles.json, id "pc") junta os jogos feitos para computador:
  - o programa do jogo na pasta jogos\...\PC (o .exe do Windows, o AppImage, o
    programa ou o .sh do Linux), inclusive a pasta inteira de um jogo (o ARENA
    acha o programa principal e ignora desinstalador, ajudante e instalador);
  - os jogos que ja estao instalados neste computador pela Steam, pela GOG
    (GOG Galaxy ou pasta "GOG Games"), pela Epic e pelo Heroic, lidos dos
    arquivos que esses programas gravam (nada de registro, nada de senha):
    aparecem na lista com a origem "Instalados no computador" e abrem pelo
    atalho de cada loja.

"Em qualquer sistema": o jogo roda onde foi feito; onde nao foi, o ARENA usa a
camada de compatibilidade que ja estiver no computador, e diz quando nao ha:
  - jogo do Windows no Linux: pelo Wine (ou o Proton da Steam) que estiver
    instalado; sem ele, a mensagem explica;
  - jogo do Linux no Windows: pelo WSL, se ja estiver instalado com uma
    distribuicao; sem ele, a mensagem explica;
  - no Android nao ha como rodar jogo de PC (processador e sistema
    diferentes): o console fica marcado "sem versao neste aparelho".
Nada disso e' emulacao que o ARENA traz: e' o que a maquina ja tem. O ARENA
nao instala nem pede administrador.
"""
import glob
import json
import os
import re
import shutil
import struct
import subprocess

import plataforma as plataforma_do_sistema

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
ID = "pc"
ORIGEM_INSTALADOS = "computador"
# Os jogos de Android instalados no celular (consoles.json, id "android"): so no ARENA do celular.
ID_ANDROID = "android"
ORIGEM_APARELHO = "aparelho"

# Programas que estao na pasta de um jogo e nao sao o jogo.
RE_NAO_E_O_JOGO = re.compile(r"unins|uninstall|crash|redist|vcredist|dxsetup|dxwebsetup|^setup|updater|update|dotnet|"
                             r"7z|unrar|python|java\b|node\b|ffmpeg|launcherhelper|report|config\b|settings\b|"
                             r"ue4prereq|easyanticheat|eac", re.IGNORECASE)
# O que a Steam instala e nao e' jogo: as ferramentas dela (Proton, runtimes) e programas comprados na loja
# (o Lossless Scaling, que o ARENA usa por conta propria; o Wallpaper Engine...). O appmanifest nao diz o tipo.
RE_NAO_E_JOGO_DA_LOJA = re.compile(r"^(proton|steam linux runtime|steamworks|sniper|soldier|scout)|lossless scaling|"
                                   r"wallpaper engine|steamvr|soundtrack|dedicated server|\bsdk\b|redistributable|"
                                   r"3dmark|benchmark|rpg maker|blender|obs studio", re.IGNORECASE)
# O atalho de loja que o ARENA aceita abrir: steam://rungameid/<numero> ou o da Epic com o nome do jogo (letras,
# numeros, ponto, hifen e sublinhado) e os parametros fixos do proprio ARENA.
RE_ATALHO_SEGURO = re.compile(r"^(steam://rungameid/\d+|com\.epicgames\.launcher://apps/[A-Za-z0-9._-]+"
                              r"\?action=launch&silent=true)$")
RE_NOME_SEGURO = re.compile(r"^[A-Za-z0-9._-]+$")
EXTENSOES_WINDOWS = (".exe",)
EXTENSOES_LINUX = (".appimage", ".x86_64", ".sh")


class NaoDaParaAbrir(Exception):
    """Por que o jogo nao abre neste sistema, em frase para o aluno."""


# ---------------------------------------------------------------------------
# Que tipo de programa e' este arquivo?
# ---------------------------------------------------------------------------

def tipo_do_programa(caminho):
    """'windows' (programa PE do Windows), 'dos' (programa MZ puro, dos anos 80 e 90), 'linux' (ELF, AppImage),
    'script' (.sh) ou '' (nao e' programa). Le so o cabecalho."""
    baixo = caminho.lower()
    if baixo.endswith(".sh"):
        return "script"
    if baixo.endswith(".appimage"):
        return "linux"
    try:
        with open(caminho, "rb") as arquivo:
            cabecalho = arquivo.read(64)
            if cabecalho[:4] == b"\x7fELF":
                return "linux"
            if cabecalho[:2] != b"MZ" or len(cabecalho) < 64:
                return ""
            deslocamento = struct.unpack("<I", cabecalho[60:64])[0]
            if deslocamento < 64 or deslocamento > 4096:
                return "dos"
            arquivo.seek(deslocamento)
            assinatura = arquivo.read(4)
    except (OSError, struct.error):
        return ""
    if assinatura == b"PE\x00\x00":
        return "windows"
    # LE/LX (DOS4GW e OS/2) e NE (Windows 3.x) continuam no DOSBox.
    return "dos"


def e_jogo_de_windows(caminho):
    return tipo_do_programa(caminho) == "windows"


def programa_principal(pasta, arquivos):
    """Numa pasta com varios programas (o jogo e seus ajudantes), o que e' o jogo: fora os que nunca sao
    (unins000.exe, UnityCrashHandler64.exe, vcredist...), o que tem o nome da pasta; senao, o maior."""
    candidatos = []
    for nome in arquivos:
        baixo = nome.lower()
        if RE_NAO_E_O_JOGO.search(os.path.splitext(baixo)[0]):
            continue
        if baixo.endswith(EXTENSOES_WINDOWS + EXTENSOES_LINUX):
            candidatos.append(nome)
    if len(candidatos) <= 1:
        return candidatos
    chave_pasta = re.sub(r"[^a-z0-9]", "", os.path.basename(pasta).lower())
    com_o_nome = [n for n in candidatos if re.sub(r"[^a-z0-9]", "", os.path.splitext(n)[0].lower()) == chave_pasta]
    if com_o_nome:
        return com_o_nome[:1]
    try:
        return [max(candidatos, key=lambda n: os.path.getsize(os.path.join(pasta, n)))]
    except OSError:
        return candidatos[:1]


def so_o_jogo(pasta, arquivos):
    """Os arquivos de uma pasta de jogo de PC que o indexador deve olhar: o programa principal e o que nao e'
    programa (os outros programas da pasta ficam de fora)."""
    programas = programa_principal(pasta, arquivos)
    return [n for n in arquivos if n in programas or not n.lower().endswith(EXTENSOES_WINDOWS + EXTENSOES_LINUX)]


# ---------------------------------------------------------------------------
# Os jogos instalados neste computador (Steam, GOG, Epic, Heroic)
# ---------------------------------------------------------------------------

def _ler(caminho, codificacao="utf-8"):
    try:
        with open(caminho, "r", encoding=codificacao, errors="replace") as arquivo:
            return arquivo.read()
    except OSError:
        return ""


def _pastas_da_steam():
    """As pastas 'steamapps' da Steam (a principal e as bibliotecas extras do libraryfolders.vdf)."""
    raizes = []
    if plataforma_do_sistema.WINDOWS:
        for base in (os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", ""),
                     os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
            if base:
                raizes.append(os.path.join(base, "Steam"))
    else:
        casa = os.path.expanduser("~")
        raizes += [os.path.join(casa, ".steam", "steam"), os.path.join(casa, ".local", "share", "Steam"),
                   os.path.join(casa, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam")]
    pastas = []
    for raiz in raizes:
        steamapps = os.path.join(raiz, "steamapps")
        if not os.path.isdir(steamapps):
            continue
        pastas.append(steamapps)
        for caminho in re.findall(r'"path"\s+"([^"]+)"', _ler(os.path.join(steamapps, "libraryfolders.vdf"))):
            extra = os.path.join(caminho.replace("\\\\", "\\"), "steamapps")
            if os.path.isdir(extra) and extra not in pastas:
                pastas.append(extra)
    return pastas


def jogos_da_steam(pastas=None):
    """Os jogos instalados pela Steam: um por appmanifest_*.acf (o nome, o appid e a pasta). Ferramentas da propria
    Steam (Proton, Steamworks, redistribuiveis) ficam de fora."""
    jogos = []
    for steamapps in (pastas if pastas is not None else _pastas_da_steam()):
        for manifesto in sorted(glob.glob(os.path.join(steamapps, "appmanifest_*.acf"))):
            texto = _ler(manifesto)
            nome = re.search(r'"name"\s+"([^"]*)"', texto)
            appid = re.search(r'"appid"\s+"(\d+)"', texto)
            pasta = re.search(r'"installdir"\s+"([^"]*)"', texto)
            if not (nome and appid and pasta):
                continue
            if RE_NAO_E_JOGO_DA_LOJA.search(nome.group(1)):
                continue
            jogos.append({"titulo": nome.group(1), "loja": "steam", "chave": appid.group(1),
                          "pasta": os.path.join(steamapps, "common", pasta.group(1)),
                          "abrir": "steam://rungameid/%s" % appid.group(1)})
    return jogos


def jogos_da_gog(pastas=None):
    """Os jogos da GOG: cada um traz um goggame-<id>.info (JSON) na propria pasta, com o nome e o programa."""
    jogos = []
    if pastas is None:
        pastas = []
        if plataforma_do_sistema.WINDOWS:
            for base in (os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", ""), "C:\\"):
                for nome in ("GOG Galaxy\\Games", "GOG Games"):
                    pastas.append(os.path.join(base, nome))
        else:
            pastas += [os.path.join(os.path.expanduser("~"), "GOG Games"), os.path.join(os.path.expanduser("~"), "Games")]
    for raiz in pastas:
        if not os.path.isdir(raiz):
            continue
        for info in sorted(glob.glob(os.path.join(raiz, "*", "goggame-*.info"))):
            try:
                dados = json.loads(_ler(info, "utf-8-sig") or "{}")
            except ValueError:
                continue
            tarefa = next((t for t in dados.get("playTasks") or [] if t.get("isPrimary") and t.get("path")), None)
            if not dados.get("name") or not tarefa:
                continue
            jogos.append({"titulo": dados["name"], "loja": "gog", "chave": str(dados.get("gameId") or ""),
                          "pasta": os.path.dirname(info),
                          "abrir": os.path.join(os.path.dirname(info), tarefa["path"].replace("/", os.sep)),
                          "argumentos": str(tarefa.get("arguments") or "")})
    return jogos


def jogos_da_epic(pasta=None):
    """Os jogos da Epic Games: um .item (JSON) por jogo em ProgramData\\Epic\\EpicGamesLauncher\\Data\\Manifests."""
    if pasta is None:
        if not plataforma_do_sistema.WINDOWS:
            return []
        pasta = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests")
    jogos = []
    for item in sorted(glob.glob(os.path.join(pasta, "*.item"))):
        try:
            dados = json.loads(_ler(item, "utf-8-sig") or "{}")
        except ValueError:
            continue
        if not dados.get("DisplayName") or not dados.get("AppName") or dados.get("bIsIncompleteInstall"):
            continue
        if not RE_NOME_SEGURO.match(str(dados["AppName"])):
            continue   # nome de jogo com caractere estranho: nao vira atalho
        jogos.append({"titulo": dados["DisplayName"], "loja": "epic", "chave": dados["AppName"],
                      "pasta": dados.get("InstallLocation") or "",
                      "abrir": "com.epicgames.launcher://apps/%s?action=launch&silent=true" % dados["AppName"]})
    return jogos


def jogos_do_heroic(pasta=None):
    """Os jogos instalados pelo Heroic (Linux e Windows): installed.json da GOG e da Epic (legendary)."""
    if pasta is None:
        casa = os.path.expanduser("~")
        pasta = (os.path.join(os.environ.get("APPDATA", ""), "heroic") if plataforma_do_sistema.WINDOWS
                 else os.path.join(casa, ".config", "heroic"))
    jogos = []
    for arquivo in (os.path.join(pasta, "gog_store", "installed.json"), os.path.join(pasta, "legendaryConfig", "legendary", "installed.json")):
        try:
            dados = json.loads(_ler(arquivo) or "{}")
        except ValueError:
            continue
        itens = dados.get("installed") if isinstance(dados, dict) and "installed" in dados else dados
        if isinstance(itens, dict):
            itens = list(itens.values())
        for item in itens or []:
            if not isinstance(item, dict):
                continue
            titulo = item.get("title") or item.get("appName") or item.get("app_name")
            pasta_jogo = item.get("install_path") or ""
            if not titulo or not pasta_jogo:
                continue
            programa = item.get("executable") or ""
            jogos.append({"titulo": titulo, "loja": "heroic", "chave": str(item.get("appName") or item.get("app_name") or ""),
                          "pasta": pasta_jogo, "abrir": os.path.join(pasta_jogo, programa) if programa else ""})
    return [j for j in jogos if j["abrir"]]


LOJAS = {"steam": "Steam", "gog": "GOG", "epic": "Epic Games", "heroic": "Heroic"}


def instalados_no_computador():
    """Todos os jogos instalados pelas lojas, sem repetir (o mesmo jogo pela GOG e pelo Heroic entra uma vez)."""
    vistos = set()
    todos = []
    for jogo in jogos_da_steam() + jogos_da_gog() + jogos_da_epic() + jogos_do_heroic():
        chave_ = re.sub(r"[^a-z0-9]", "", jogo["titulo"].lower())
        if chave_ in vistos:
            continue
        vistos.add(chave_)
        todos.append(jogo)
    return todos


def entradas_do_manifesto(plataforma):
    """Os jogos instalados neste computador no formato do manifesto do ARENA (servidor\\indexador.py). A origem e'
    'computador'; o 'arquivo' e' o atalho da loja ou o programa (nao fica na pasta jogos). Nada no Android."""
    if plataforma_do_sistema.ANDROID:
        return []
    entradas = []
    for jogo in instalados_no_computador():
        tamanho_mb = 0.0
        identificacao = "computador/%s/%s" % (jogo["loja"], re.sub(r"[^a-z0-9._-]", "_", (jogo["chave"] or jogo["titulo"]).lower()))
        entradas.append({
            "id": identificacao,
            "titulo": jogo["titulo"],
            "plataforma": plataforma["id"],
            "plataforma_nome": plataforma["nome"],
            "arquivo": jogo["abrir"],
            "origem": ORIGEM_INSTALADOS,
            "origem_rotulo": "Instalado pela %s" % LOJAS.get(jogo["loja"], jogo["loja"]),
            "loja": jogo["loja"],
            "pasta_do_jogo": jogo["pasta"],
            "argumentos_do_jogo": jogo.get("argumentos", ""),
            "pede_placar": False,
            "jogadores_do_jogo": 1, "jogadores_max": 1, "rede_propria": False, "motivo_jogadores": "",
            "tamanho_mb": tamanho_mb, "ambiguo": False, "discorda": None, "discorda_nome": None,
            "avisos": [], "capa": None, "capa_nome": None, "romset": None,
        })
    return entradas


def entradas_do_aparelho(plataforma, jogos=None):
    """Os jogos de Android instalados no celular, no formato do manifesto (o 'arquivo' e' android://<pacote>). So no
    ARENA do celular; 'jogos' (lista de {"pacote", "nome"}) serve aos testes."""
    if jogos is None:
        if not plataforma_do_sistema.ANDROID:
            return []
        import ponte_android
        jogos = ponte_android.jogos_do_aparelho()
    entradas = []
    for jogo in jogos:
        pacote = re.sub(r"[^A-Za-z0-9._]", "", str(jogo.get("pacote") or ""))
        if not pacote:
            continue
        entradas.append({
            "id": "aparelho/%s" % pacote.lower(),
            "titulo": str(jogo.get("nome") or pacote),
            "plataforma": plataforma["id"],
            "plataforma_nome": plataforma["nome"],
            "arquivo": "android://" + pacote,
            "origem": ORIGEM_APARELHO,
            "origem_rotulo": "Instalado no celular",
            "loja": "android",
            "pede_placar": False,
            "jogadores_do_jogo": 1, "jogadores_max": 1, "rede_propria": False, "motivo_jogadores": "",
            "tamanho_mb": 0.0, "ambiguo": False, "discorda": None, "discorda_nome": None,
            "avisos": [], "capa": None, "capa_nome": None, "romset": None,
        })
    return entradas


def pacote_do_arquivo(arquivo):
    """android://com.exemplo.jogo -> com.exemplo.jogo ("" se nao for um jogo do aparelho)."""
    arquivo = str(arquivo or "")
    return re.sub(r"[^A-Za-z0-9._]", "", arquivo[len("android://"):]) if arquivo.startswith("android://") else ""


# ---------------------------------------------------------------------------
# Como abrir (o sistema do jogo e o sistema da maquina)
# ---------------------------------------------------------------------------

def wine():
    """O Wine do Linux, ou o Proton da Steam (o 'proton' do script), ou None."""
    if plataforma_do_sistema.WINDOWS:
        return None
    for nome in ("wine", "wine64", "wine-stable"):
        caminho = shutil.which(nome)
        if caminho:
            return [caminho]
    for steamapps in _pastas_da_steam():
        for proton in sorted(glob.glob(os.path.join(steamapps, "common", "Proton*", "proton")), reverse=True):
            return [proton, "run"]
    return None


def wsl():
    """O WSL do Windows com uma distribuicao instalada, ou None. (So lista; nao instala nada.)"""
    if not plataforma_do_sistema.WINDOWS:
        return None
    programa = shutil.which("wsl.exe") or shutil.which("wsl")
    if not programa:
        return None
    try:
        saida = subprocess.run([programa, "-l", "-q"], capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    texto = saida.stdout.decode("utf-16-le", "replace") if b"\x00" in saida.stdout else saida.stdout.decode("utf-8", "replace")
    distribuicoes = [l.strip() for l in texto.splitlines() if l.strip() and "docker" not in l.lower()]
    return programa if saida.returncode == 0 and distribuicoes else None


def caminho_no_wsl(caminho):
    """C:\\Jogos\\x -> /mnt/c/Jogos/x."""
    caminho = os.path.abspath(caminho)
    unidade, resto = os.path.splitdrive(caminho)
    return "/mnt/%s%s" % (unidade.rstrip(":").lower(), resto.replace("\\", "/"))


def comando_para(caminho, argumentos="", sistema_atual=None, tipo=None):
    """A linha de comando que abre o jogo 'caminho' nesta maquina, e um aviso ("" quando nao ha). Lanca
    NaoDaParaAbrir quando o sistema do jogo nao e' o da maquina e nao ha camada de compatibilidade aqui."""
    sistema_atual = sistema_atual or plataforma_do_sistema.nome_do_sistema()
    if sistema_atual == "android":
        raise NaoDaParaAbrir("Jogo de PC não roda no celular: o processador e o sistema são outros. Abra no computador.")
    extras = [a for a in re.split(r"\s+", argumentos.strip()) if a] if argumentos else []
    if caminho.startswith(("steam://", "com.epicgames.launcher://")):
        if not RE_ATALHO_SEGURO.match(caminho):
            raise NaoDaParaAbrir("O atalho deste jogo tem caracteres estranhos; o ARENA não o abre. Abra pela loja.")
        if sistema_atual == "windows":
            # Pelo ShellExecute (url.dll), nunca pelo "cmd /c start": o cmd leria o '&' do endereco como outro comando.
            return [shutil.which("rundll32") or "rundll32", "url.dll,FileProtocolHandler", caminho], ("A %s abre o jogo; o ARENA não acompanha o tempo jogado."
                                                         % ("Steam" if caminho.startswith("steam") else "Epic"))
        return [shutil.which("xdg-open") or "xdg-open", caminho], "A Steam abre o jogo; o ARENA não acompanha o tempo jogado."
    tipo = tipo or tipo_do_programa(caminho)
    if tipo == "windows":
        if sistema_atual == "windows":
            return [caminho] + extras, ""
        camada = wine()
        if camada:
            return camada + [caminho] + extras, "Jogo do Windows aberto pelo %s." % ("Proton" if "proton" in camada[0].lower() else "Wine")
        raise NaoDaParaAbrir("Este é um jogo do Windows, e este Linux não tem o Wine (nem o Proton da Steam). "
                             "Instale o Wine pelo gerenciador de pacotes, ou use a versão para Linux do jogo.")
    if tipo in ("linux", "script"):
        if sistema_atual in ("linux", "chromeos"):
            programa = plataforma_do_sistema.programa_que_roda(caminho, "jogo-pc") if tipo == "linux" else caminho
            return (["sh", programa] if tipo == "script" else [programa]) + extras, ""
        camada = wsl()
        if camada:
            return [camada, "-e", "sh", "-c", 'cd "$(dirname "$1")" && exec "$1" "${@:2}"', "sh", caminho_no_wsl(caminho)] + extras, \
                "Jogo do Linux aberto pelo WSL (sem aceleração de vídeo garantida)."
        raise NaoDaParaAbrir("Este é um jogo do Linux, e este Windows não tem o WSL com uma distribuição instalada. "
                             "Use a versão para Windows do jogo, ou abra no computador com Linux.")
    if tipo == "dos":
        raise NaoDaParaAbrir("Este programa é do MS-DOS: ponha o jogo na pasta MS-DOS, que ele abre pelo DOSBox.")
    raise NaoDaParaAbrir("Este arquivo não é um programa de jogo que o ARENA saiba abrir.")


def externo_para(jogo, caminho):
    """O dicionario de 'emulador de fora' (jogo["externo"]) que o executar_jogo usa para abrir um jogo de PC: o
    programa (ou a camada: Wine, WSL, o atalho da loja) e os argumentos. Devolve (externo, aviso)."""
    comando, aviso = comando_para(caminho, jogo.get("argumentos_do_jogo", ""))
    pasta = jogo.get("pasta_do_jogo") or (os.path.dirname(caminho) if os.path.isabs(caminho) else "")
    # "loja": quem abre o jogo e' a loja (Steam, GOG, Epic), nao o ARENA: o Mais quadros nao acharia a janela dele.
    return ({"caminho": comando[0], "dados": {"nome": "PC", "argumentos": comando[1:], "ambiente": {},
                                             "loja": jogo.get("origem") == ORIGEM_INSTALADOS,
                                             "pasta_trabalho": pasta if os.path.isdir(pasta) else ""}},
            aviso)
