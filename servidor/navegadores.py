# -*- coding: utf-8 -*-
r"""Em que navegador a tela do ARENA abre (item 11 dos pedidos de 15/10/2026).

Pedido do Rafael: "o arena deve ser possivel rodar em qualquer navegador
padrao que o aluno tenha, e deve ser perfeitamente funcional assim como e' no
edge". A tela e' um site comum (launcher\index.html: HTML, CSS e JavaScript
sem framework), servido pelo proprio ARENA em 127.0.0.1:8777. Qualquer
navegador moderno a abre; o que muda e' o jeito de abrir a janela.

Como o ARENA escolhe (escolher):
  1. o navegador que o aluno escolheu em Ajustes (config "navegador"), se
     ele ainda estiver no computador;
  2. o navegador PADRAO do computador -- o que abre os links. No Windows, o
     registro diz qual e' (UrlAssociations\http\UserChoice -> o ProgId -> o
     programa), sem administrador; no Linux, o xdg-settings (ou, sem ele, o
     mimeapps.list que ele mesmo le);
  3. os outros que achar, na ordem da lista CONHECIDOS (o Edge primeiro:
     vem em todo Windows 10 e 11);
  4. nenhum: o jeito do proprio Python (webbrowser), numa aba. No Linux do
     Chromebook, e' o que abre a tela no Chrome do proprio ChromeOS.

No Linux (item 13, 17/10/2026), o navegador pode estar no sistema (/usr/bin,
/snap/bin, pelo PATH) ou no Flatpak: este deixa um atalho com o nome do
aplicativo ("com.google.Chrome") em exports/bin, que abre como o programa.

Como abre (comando):
  - Chromium (Edge, Chrome, Brave, Vivaldi, Chromium): "--app=", uma janela
    de aplicativo, sem abas nem barra de endereco -- parece um programa;
  - Opera (Chromium tambem, mas que nao garante o "--app"): janela nova;
  - Firefox (e os feitos a partir dele: LibreWolf, Waterfox, Floorp): o
    Firefox tirou o modo aplicativo em 2021 (o "SSB", versao 86); abre uma
    janela nova so para o ARENA ("-new-window").
"""
import os
import re
import shutil
import subprocess
import sys

# (codigo, nome, familia, caminhos dentro de Arquivos de Programas e do
# AppData\Local, nomes do programa). A ordem e' a da escolha 3.
CONHECIDOS = (
    ("edge", "Microsoft Edge", "chromium",
     (r"Microsoft\Edge\Application\msedge.exe",), ("msedge.exe", "microsoft-edge", "microsoft-edge-stable")),
    ("chrome", "Google Chrome", "chromium",
     (r"Google\Chrome\Application\chrome.exe",), ("chrome.exe", "google-chrome", "google-chrome-stable")),
    ("brave", "Brave", "chromium",
     (r"BraveSoftware\Brave-Browser\Application\brave.exe",), ("brave.exe", "brave-browser", "brave")),
    ("vivaldi", "Vivaldi", "chromium",
     (r"Vivaldi\Application\vivaldi.exe",), ("vivaldi.exe", "vivaldi", "vivaldi-stable")),
    ("chromium", "Chromium", "chromium",
     (r"Chromium\Application\chrome.exe",), ("chromium", "chromium-browser")),
    ("opera", "Opera", "opera",
     (r"Programs\Opera\opera.exe", r"Opera\opera.exe", r"Programs\Opera GX\opera.exe"), ("opera.exe", "opera")),
    ("firefox", "Mozilla Firefox", "firefox",
     (r"Mozilla Firefox\firefox.exe",), ("firefox.exe", "firefox", "firefox-esr")),
    ("librewolf", "LibreWolf", "firefox", (r"LibreWolf\librewolf.exe",), ("librewolf.exe", "librewolf")),
    ("waterfox", "Waterfox", "firefox", (r"Waterfox\waterfox.exe",), ("waterfox.exe", "waterfox")),
    ("floorp", "Floorp", "firefox", (r"Ablaze Floorp\floorp.exe",), ("floorp.exe", "floorp")),
)
# O ProgId do navegador padrao (Windows) -> o codigo. Firefox, Vivaldi e
# outros poem um sufixo depois do nome ("FirefoxURL-308046B0AF4A39CB").
PROGIDS = (("msedgehtm", "edge"), ("chromehtml", "chrome"), ("bravehtml", "brave"),
           ("vivaldihtm", "vivaldi"), ("chromiumhtm", "chromium"), ("operastable", "opera"),
           ("operagxstable", "opera"), ("firefoxurl", "firefox"), ("librewolfhtml", "librewolf"),
           ("waterfoxurl", "waterfox"), ("floorpurl", "floorp"))
TAMANHO_DA_JANELA = "1180,760"
# Linux: o nome de cada navegador no Flatpak (o "flatpak run <nome>").
FLATPAK = {"edge": ("com.microsoft.Edge",), "chrome": ("com.google.Chrome",), "brave": ("com.brave.Browser",),
           "vivaldi": ("com.vivaldi.Vivaldi",),
           "chromium": ("org.chromium.Chromium", "io.github.ungoogled_software.ungoogled_chromium"),
           "opera": ("com.opera.Opera",), "firefox": ("org.mozilla.firefox",),
           "librewolf": ("io.gitlab.librewolf-community",), "waterfox": ("net.waterfox.waterfox",),
           "floorp": ("one.ablaze.floorp",)}


def _pastas_do_flatpak():
    """Onde o Flatpak deixa o atalho de cada aplicativo: o da conta e o do
    computador."""
    dados = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return [os.path.join(dados, "flatpak", "exports", "bin"), "/var/lib/flatpak/exports/bin"]


def _pastas_de_programas():
    pastas = []
    for variavel in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "LOCALAPPDATA"):
        valor = os.environ.get(variavel)
        if valor and valor not in pastas:
            pastas.append(valor)
    return pastas


def _do_registro_windows():
    """{codigo: programa} dos navegadores que o Windows lista
    (StartMenuInternet, na conta e na maquina), sem administrador."""
    achados = {}
    if os.name != "nt":
        return achados
    import winreg
    for raiz in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            lista = winreg.OpenKey(raiz, r"SOFTWARE\Clients\StartMenuInternet")
        except OSError:
            continue
        with lista:
            for i in range(64):
                try:
                    nome = winreg.EnumKey(lista, i)
                except OSError:
                    break
                try:
                    with winreg.OpenKey(lista, nome + r"\shell\open\command") as chave:
                        comando = winreg.QueryValueEx(chave, "")[0]
                except OSError:
                    continue
                programa = programa_do_comando(comando)
                codigo = codigo_do_programa(programa)
                if codigo and programa and os.path.isfile(programa):
                    achados.setdefault(codigo, programa)
    return achados


def programa_do_comando(comando):
    """'"C:\\...\\chrome.exe" --single-argument %1' -> 'C:\\...\\chrome.exe'."""
    comando = (comando or "").strip()
    if comando.startswith('"'):
        fim = comando.find('"', 1)
        return comando[1:fim] if fim > 0 else comando.strip('"')
    achado = re.match(r"(.+?\.exe)\b", comando, re.I)
    return achado.group(1) if achado else comando.split(" ")[0]


def codigo_do_programa(programa):
    """O codigo da lista CONHECIDOS pelo nome do programa, ou None. O caminho
    pode ser do Windows ou do Linux (com \\ ou /), no Flatpak inclusive."""
    caminho = (programa or "").lower().replace("\\", "/")
    nome = caminho.rsplit("/", 1)[-1]
    if nome == "chrome.exe" and "/chromium/" in caminho:
        return "chromium"
    for codigo, _nome, _familia, _caminhos, nomes in CONHECIDOS:
        if nome in nomes or nome in [n.lower() for n in FLATPAK.get(codigo, ())]:
            return codigo
    return None


def instalados():
    """[{codigo, nome, familia, programa}] dos navegadores deste computador."""
    achados = {}
    if os.name == "nt":
        for codigo, _nome, _familia, caminhos, _nomes in CONHECIDOS:
            for base in _pastas_de_programas():
                for relativo in caminhos:
                    caminho = os.path.join(base, relativo)
                    if codigo not in achados and os.path.isfile(caminho):
                        achados[codigo] = caminho
        for codigo, programa in _do_registro_windows().items():
            achados.setdefault(codigo, programa)
    else:
        for codigo, _nome, _familia, _caminhos, nomes in CONHECIDOS:
            for nome in nomes:
                if not nome.endswith(".exe") and codigo not in achados:
                    caminho = shutil.which(nome)
                    if caminho:
                        achados[codigo] = caminho
            for pasta in _pastas_do_flatpak():
                for aplicativo in FLATPAK.get(codigo, ()):
                    caminho = os.path.join(pasta, aplicativo)
                    if codigo not in achados and os.path.isfile(caminho) and os.access(caminho, os.X_OK):
                        achados[codigo] = caminho
    lista = []
    for codigo, nome, familia, _caminhos, _nomes in CONHECIDOS:
        if codigo in achados:
            lista.append({"codigo": codigo, "nome": nome, "familia": familia,
                          "programa": achados[codigo]})
    return lista


def codigo_do_progid(progid):
    """"FirefoxURL-308046B0AF4A39CB" -> "firefox"; desconhecido -> None."""
    baixo = (progid or "").lower()
    for prefixo, codigo in PROGIDS:
        if baixo.startswith(prefixo):
            return codigo
    return None


def padrao_do_computador():
    """O codigo do navegador padrao (o que abre os links), ou None."""
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations"
                                r"\http\UserChoice") as chave:
                progid = winreg.QueryValueEx(chave, "ProgId")[0]
        except OSError:
            return None
        codigo = codigo_do_progid(progid)
        if codigo:
            return codigo
        # ProgId que nao esta na lista: o programa que ele abre.
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid + r"\shell\open\command") as chave:
                return codigo_do_programa(programa_do_comando(winreg.QueryValueEx(chave, "")[0]))
        except OSError:
            return None
    try:
        saida = subprocess.run(["xdg-settings", "get", "default-web-browser"], capture_output=True,
                               text=True, timeout=5).stdout.strip().lower()
    except (OSError, subprocess.SubprocessError):
        saida = ""
    saida = saida or (_padrao_do_mimeapps() or "").lower()
    if not saida:
        return None
    for codigo, _nome, _familia, _caminhos, nomes in CONHECIDOS:
        if (any(n.replace(".exe", "") in saida for n in nomes) or codigo in saida
                or any(a.lower() in saida for a in FLATPAK.get(codigo, ()))):
            return codigo
    return None


def _padrao_do_mimeapps():
    """Linux sem o xdg-settings: o navegador que abre os links, do
    mimeapps.list ("x-scheme-handler/http=firefox.desktop"), ou None. A
    ordem e' a da especificacao do freedesktop: a conta antes do computador."""
    casa = os.path.expanduser("~")
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(casa, ".config")
    dados = os.environ.get("XDG_DATA_HOME") or os.path.join(casa, ".local", "share")
    for lista in (os.path.join(config, "mimeapps.list"), os.path.join(dados, "applications", "mimeapps.list"),
                  "/etc/xdg/mimeapps.list", "/usr/share/applications/mimeapps.list"):
        try:
            with open(lista, encoding="utf-8", errors="replace") as arquivo:
                secao = ""
                for linha in arquivo:
                    linha = linha.strip()
                    if linha.startswith("["):
                        secao = linha
                    elif secao == "[Default Applications]" and linha.startswith("x-scheme-handler/http="):
                        valor = linha.split("=", 1)[1].split(";")[0].strip()
                        if valor:
                            return valor
        except OSError:
            continue
    return None


def escolher(preferido="automatico", lista=None, padrao=None):
    """O navegador que vale: {codigo, nome, familia, programa} ou None."""
    lista = instalados() if lista is None else lista
    por_codigo = {n["codigo"]: n for n in lista}
    if preferido and preferido != "automatico" and preferido in por_codigo:
        return por_codigo[preferido]
    padrao = padrao_do_computador() if padrao is None else padrao
    if padrao in por_codigo:
        return por_codigo[padrao]
    return lista[0] if lista else None


def comando(navegador, endereco):
    """A linha de comando que abre a tela neste navegador."""
    programa, familia = navegador["programa"], navegador["familia"]
    if familia == "chromium":
        return [programa, "--app=" + endereco, "--window-size=" + TAMANHO_DA_JANELA,
                "--disable-features=Translate,AutofillServerCommunication"]
    if familia == "firefox":
        return [programa, "-new-window", endereco]
    return [programa, "--new-window", endereco]


def abrir(endereco, preferido="automatico"):
    """Abre a tela do ARENA. Devolve o codigo do navegador usado, ou "aba"."""
    navegador = escolher(preferido)
    if navegador:
        try:
            subprocess.Popen(comando(navegador, endereco), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return navegador["codigo"]
        except OSError:
            pass
    import webbrowser
    webbrowser.open(endereco)
    return "aba"


if __name__ == "__main__":
    import json
    print(json.dumps({"padrao": padrao_do_computador(), "instalados": instalados(),
                      "escolhido": escolher()}, ensure_ascii=False, indent=1))
    sys.exit(0)
