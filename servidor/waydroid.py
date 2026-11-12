# -*- coding: utf-8 -*-
r"""Os jogos de Android no ARENA do Linux, pelo Waydroid (13/11/2026).

Por que: a maioria dos alunos so tem celular, e os jogos de Android aparecem no ARENA do celular. Um aluno usa Linux
no computador e pediu os mesmos jogos la. O Waydroid (waydro.id, GPL-3.0) roda um Android inteiro dentro do Linux,
num conteiner: o jogo abre numa janela, sem emulador.

O que o ARENA faz aqui (so a biblioteca padrao):
  - descobre se o Waydroid existe e esta pronto (o arquivo /var/lib/waydroid/waydroid.cfg nasce no "waydroid init");
  - liga a sessao do Android quando precisa ("waydroid session start", sem administrador);
  - le os apps instalados ("waydroid app list") e guarda a lista em dados/, para o ARENA nao ligar o Android so para
    mostrar a lista;
  - abre o jogo ("waydroid app launch <pacote>") e instala os APKs que a pessoa poe na pasta (jogos/pessoais/Android);
  - monta o roteiro de instalacao, que PRECISA de administrador (pacote do sistema e o "waydroid init"). A tela avisa
    antes e o proprio Linux pede a senha (pkexec). E' a irma da excecao do WSL no Windows.

O que NAO da para conferir aqui: o Waydroid precisa do "binder" no nucleo do Linux e de uma sessao Wayland. O WSL do
computador do Rafael nao tem binder, entao os testes sao com respostas simuladas. A tela diz quando falta o binder ou
o Wayland, em vez de tentar e falhar calada.
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time

import plataforma as plataforma_do_sistema

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

CONFIG_DO_WAYDROID = "/var/lib/waydroid/waydroid.cfg"
ARQUIVO_DA_LISTA = os.path.join("dados", "waydroid_jogos.json")
PASTA_DOS_APKS = os.path.join("jogos", "pessoais", "Android")
# Os canais oficiais das imagens do Android (docs.waydro.id: "System OTA" e "Vendor OTA").
OTA_SISTEMA = "https://ota.waydro.id/system"
OTA_FABRICANTE = "https://ota.waydro.id/vendor"
# As versoes do Debian/Ubuntu que o repositorio oficial (repo.waydro.id) atende, em 13/11/2026. So estes nomes entram
# no roteiro: o nome vem do /etc/os-release e nunca vai para o comando sem passar por esta lista.
VERSOES_DO_REPOSITORIO = ("mantic", "focal", "jammy", "kinetic", "lunar", "noble", "oracular", "plucky", "questing",
                          "resolute", "buster", "bookworm", "bullseye", "trixie", "sid")
# Os apps que ja vem no Android do Waydroid (configuracoes, navegador, loja aberta...): nao sao jogos.
DO_SISTEMA = ("android", "com.android.", "com.google.android.", "org.lineageos.", "org.fdroid.", "id.waydro.",
              "com.waydroid.", "org.chromium.", "com.android")

_TRAVA = threading.Lock()
_CACHE = {}
_CACHE_TEMPO = 20.0


def _programa():
    if plataforma_do_sistema.ANDROID or plataforma_do_sistema.WINDOWS:
        return None
    return shutil.which("waydroid")


def _rodar(argumentos, segundos=30):
    """(codigo, texto) de um 'waydroid ...'. Sem o programa, (127, "")."""
    programa = _programa()
    if not programa:
        return 127, ""
    try:
        saida = subprocess.run([programa] + list(argumentos), capture_output=True, timeout=segundos)
    except (OSError, subprocess.SubprocessError) as falha:
        return 1, str(falha)
    return saida.returncode, (saida.stdout + saida.stderr).decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# A situacao: instalado, preparado, ligado, e o que o computador tem (binder e Wayland)
# ---------------------------------------------------------------------------
def tem_binder():
    """O nucleo do Linux tem o 'binder' do Android? (o modulo binder_linux ou o sistema de arquivos binderfs)"""
    if os.path.exists("/dev/binder") or os.path.isdir("/dev/binderfs") or os.path.isdir("/sys/module/binder_linux"):
        return True
    try:
        with open("/proc/filesystems", encoding="utf-8", errors="replace") as arquivo:
            return any(linha.split()[-1] == "binder" for linha in arquivo if linha.split())
    except OSError:
        return False


def tem_wayland(ambiente=None):
    """A sessao grafica e' Wayland? (o Waydroid desenha pelo Wayland; numa sessao X11 a janela nao abre)"""
    ambiente = os.environ if ambiente is None else ambiente
    return bool(ambiente.get("WAYLAND_DISPLAY")) or ambiente.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def sessao_ligada():
    codigo, texto = _rodar(["status"], 15)
    return codigo == 0 and ler_status(texto)


def ler_status(texto):
    """A saida do 'waydroid status' diz 'Session:<TAB>RUNNING' quando o Android esta ligado."""
    achado = re.search(r"^\s*Session:\s*(\w+)", texto or "", re.MULTILINE)
    return bool(achado) and achado.group(1).upper() == "RUNNING"


def situacao(forcar=False):
    """{"instalado", "preparado", "binder", "wayland", "pronto"}. Guardada por 20 s (o painel atualiza sozinho)."""
    agora = time.monotonic()
    with _TRAVA:
        guardada = _CACHE.get("situacao")
        if guardada and not forcar and agora - guardada[0] < _CACHE_TEMPO:
            return dict(guardada[1])
    instalado = bool(_programa())
    estado = {
        "instalado": instalado,
        "preparado": instalado and os.path.isfile(CONFIG_DO_WAYDROID),
        "binder": tem_binder() if plataforma_do_sistema.LINUX else False,
        "wayland": tem_wayland(),
    }
    estado["pronto"] = estado["preparado"] and estado["binder"]
    with _TRAVA:
        _CACHE["situacao"] = (agora, estado)
    return dict(estado)


def pronto():
    """O console "Jogos de Android" vale neste Linux?"""
    return plataforma_do_sistema.LINUX and not plataforma_do_sistema.ANDROID and situacao()["pronto"]


def esquecer():
    with _TRAVA:
        _CACHE.clear()


# ---------------------------------------------------------------------------
# Ligar o Android, ler os jogos, abrir um jogo, instalar os APKs
# ---------------------------------------------------------------------------
def ligar_sessao(espera=60):
    """Liga o Android do Waydroid (sem administrador) e espera ele ficar pronto. True se ligou."""
    if sessao_ligada():
        return True
    programa = _programa()
    if not programa:
        return False
    try:
        subprocess.Popen([programa, "session", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return False
    limite = time.monotonic() + espera
    while time.monotonic() < limite:        # so enquanto a pessoa espera o jogo abrir (no maximo 'espera' s)
        time.sleep(2)
        if sessao_ligada():
            return True
    return False


def ler_lista(texto):
    """A saida do 'waydroid app list' (Name:, packageName:, categories:) -> [{"pacote", "nome"}], sem os apps do
    sistema e so os que aparecem no menu (categoria LAUNCHER)."""
    apps, atual, categorias = [], None, False
    for linha in (texto or "").splitlines():
        if linha.startswith("Name:"):
            if atual:
                apps.append(atual)
            atual, categorias = {"nome": linha[5:].strip(), "pacote": "", "categorias": []}, False
        elif atual is not None and linha.startswith("packageName:"):
            atual["pacote"] = re.sub(r"[^A-Za-z0-9._]", "", linha[12:].strip())
        elif atual is not None and linha.startswith("categories:"):
            categorias = True
        elif atual is not None and categorias and linha.strip():
            atual["categorias"].append(linha.strip())
    if atual:
        apps.append(atual)
    jogos = []
    for app in apps:
        pacote = app["pacote"]
        if not pacote or pacote.startswith(DO_SISTEMA) or pacote == "android":
            continue
        if app["categorias"] and not any(c.endswith(".LAUNCHER") for c in app["categorias"]):
            continue
        jogos.append({"pacote": pacote, "nome": app["nome"] or pacote})
    return sorted(jogos, key=lambda j: j["nome"].lower())


def _caminho_da_lista(raiz):
    return os.path.join(raiz, ARQUIVO_DA_LISTA)


def jogos(raiz=RAIZ, ligar=False):
    """Os jogos do Android do Linux. Com o Android ligado, le de novo e guarda; desligado, usa a ultima lista
    guardada (ligar o Android so para mostrar a lista pesaria). 'ligar=True' liga antes (botao Atualizar)."""
    if not _programa():
        return []
    if ligar:
        ligar_sessao()
    if sessao_ligada():
        codigo, texto = _rodar(["app", "list"], 40)
        if codigo == 0:
            lista = ler_lista(texto)
            _guardar_lista(raiz, lista)
            return lista
    try:
        with open(_caminho_da_lista(raiz), encoding="utf-8") as arquivo:
            guardada = json.load(arquivo)
        return [j for j in guardada if isinstance(j, dict) and j.get("pacote")]
    except (OSError, ValueError):
        return []


def _guardar_lista(raiz, lista):
    caminho = _caminho_da_lista(raiz)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = "%s.%d.%d.tmp" % (caminho, os.getpid(), threading.get_ident())
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(lista, arquivo, ensure_ascii=False, indent=1)
    os.replace(temporario, caminho)        # gravacao atomica, como o resto do ARENA


def abrir(pacote):
    """Abre o jogo numa janela do Linux. (True, "") ou (False, a frase para a tela)."""
    pacote = re.sub(r"[^A-Za-z0-9._]", "", str(pacote or ""))
    programa = _programa()
    if not pacote or not programa:
        return False, "Falta o Android do ARENA neste Linux: abra Equipamentos e clique em Instalar."
    if not tem_wayland():
        return False, ("O Android do Linux só abre numa sessão Wayland. Saia da conta e, na tela de entrada, clique na "
                       "engrenagem e escolha a opção com Wayland (no Ubuntu, \"Ubuntu\", sem \"Xorg\").")
    if not ligar_sessao():
        return False, ("O Android do Linux não ligou. Abra Equipamentos e confira a linha \"Jogos de Android no "
                       "Linux\"; se continuar, reinicie o computador.")
    try:
        subprocess.Popen([programa, "app", "launch", pacote], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    except OSError as falha:
        return False, "O Linux não abriu o Android (%s). Confira em Equipamentos." % falha
    return True, ""


def apks_da_pasta(raiz=RAIZ):
    pasta = os.path.join(raiz, PASTA_DOS_APKS)
    try:
        return sorted(os.path.join(pasta, nome) for nome in os.listdir(pasta) if nome.lower().endswith(".apk"))
    except OSError:
        return []


def instalar_apks(raiz=RAIZ):
    """Instala no Android do Linux os APKs da pasta jogos/pessoais/Android que ainda nao entraram (lembra pelo nome e
    pelo tamanho, em dados/). Devolve quantos entraram."""
    marca = os.path.join(raiz, "dados", "waydroid_apks.json")
    try:
        with open(marca, encoding="utf-8") as arquivo:
            ja = json.load(arquivo)
    except (OSError, ValueError):
        ja = {}
    novos = 0
    for caminho in apks_da_pasta(raiz):
        chave = os.path.basename(caminho)
        tamanho = os.path.getsize(caminho)
        if ja.get(chave) == tamanho:
            continue
        codigo, _texto = _rodar(["app", "install", caminho], 180)
        if codigo == 0:
            ja[chave] = tamanho
            novos += 1
    if novos:
        os.makedirs(os.path.dirname(marca), exist_ok=True)
        temporario = "%s.%d.%d.tmp" % (marca, os.getpid(), threading.get_ident())
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(ja, arquivo, ensure_ascii=False, indent=1)
        os.replace(temporario, marca)
    return novos


# ---------------------------------------------------------------------------
# A instalacao (com administrador, avisada antes): o roteiro e quem pede a senha
# ---------------------------------------------------------------------------
def ler_os_release(texto):
    dados = {}
    for linha in (texto or "").splitlines():
        if "=" in linha and not linha.startswith("#"):
            chave, valor = linha.split("=", 1)
            dados[chave.strip()] = valor.strip().strip('"').strip("'")
    return dados


def _os_release():
    for caminho in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            with open(caminho, encoding="utf-8", errors="replace") as arquivo:
                return ler_os_release(arquivo.read())
        except OSError:
            continue
    return {}


def roteiro_de_instalacao(sistema=None, tem=shutil.which):
    """O roteiro (sh) que instala o Waydroid e prepara o Android, ou None com o motivo. (roteiro, motivo)."""
    sistema = _os_release() if sistema is None else sistema
    preparar = ("waydroid init -c %s -v %s\n"
                "systemctl enable --now waydroid-container\n") % (OTA_SISTEMA, OTA_FABRICANTE)
    if tem("apt-get"):
        versao = ""
        for chave in ("UBUNTU_CODENAME", "DEBIAN_CODENAME", "VERSION_CODENAME"):
            if sistema.get(chave):
                versao = sistema[chave].lower()
                break
        repositorio = ""
        if versao in VERSOES_DO_REPOSITORIO:
            # Igual ao roteiro oficial (repo.waydro.id), escrito aqui para nao rodar um script baixado como
            # administrador: a chave do repositorio e a linha do apt. So entra se o sistema ainda nao tem o pacote.
            repositorio = (
                "if ! apt-cache policy waydroid | grep -q 'Candidate: [0-9]'; then\n"
                "  apt-get install -y curl ca-certificates\n"
                "  curl --proto '=https' --tlsv1.2 -Sf https://repo.waydro.id/waydroid.gpg "
                "--output /usr/share/keyrings/waydroid.gpg\n"
                "  echo 'deb [signed-by=/usr/share/keyrings/waydroid.gpg] https://repo.waydro.id/ %s main' "
                "> /etc/apt/sources.list.d/waydroid.list\n"
                "  apt-get update\n"
                "fi\n") % versao
        return ("set -e\nexport DEBIAN_FRONTEND=noninteractive\napt-get update\n" + repositorio +
                "apt-get install -y waydroid\n" + preparar), ""
    if tem("dnf"):
        return "set -e\ndnf install -y waydroid\n" + preparar, ""
    if tem("xbps-install"):
        return "set -e\nxbps-install -Sy waydroid\n" + preparar, ""
    return None, ("Este Linux não tem o Waydroid no instalador do sistema. Peça a quem cuida do computador para "
                  "instalar o Waydroid (docs.waydro.id) e depois volte aqui.")


def comando_com_administrador(roteiro):
    """O pkexec mostra a janela da senha do proprio Linux. Sem ele, None."""
    pkexec = shutil.which("pkexec")
    return [pkexec, "/bin/sh", "-c", roteiro] if pkexec and roteiro else None
