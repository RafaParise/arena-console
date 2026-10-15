# -*- coding: utf-8 -*-
r"""Java ME pelo ARENA de verdade (15/10/2026): o caminho inteiro, como o aluno
usa -- o servidor do ARENA, a rota /api/jogar, o RetroArch, o Java que vem
no ARENA e a ponte sem acento.

Monta uma COPIA do ARENA numa pasta temporaria com "Pedagógicos" no nome (o
ARENA do Rafael mora numa assim): o servidor (que roda com o Python do ARENA
de verdade), a tela, o RetroArch (programa, o nucleo do Java ME e a
configuracao), o Java (emuladores\Java) e um jogo. Nada do ARENA de verdade
e' tocado: nem os dados, nem os saves.

  1. JOGO NORMAL: abre pela rota /api/jogar, fotografa a janela, fecha como
     o aluno fecha (a janela recebe o "fechar"). Confere: a imagem, o Java
     que fechou junto, a ponte sem acento no registro do ARENA, os dados do
     jogo gravados na pasta certa (retroarch\saves da copia) e nenhuma
     pasta com o nome estragado ("PedagÃ³gicos") criada.
  2. QUEDA: abre de novo e derruba o RetroArch a forca. O Java do jogo tem
     que fechar junto (a caixa do Windows, servidor\processos.py).

Uso:
    servidor\python\python.exe testes\teste_java_me_pelo_arena.py [jogo.jar]
(sem jogo: o Shooter, livre, de testes\jogos_livres)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402

PORTA = 8777
# A foto do CONTEUDO da janela (PrintWindow com PW_RENDERFULLCONTENT): vale
# mesmo com outra janela por cima. A primeira versao fotografava a tela, e um
# aviso do Windows na frente do jogo passou por "imagem do jogo".
FOTO_DA_JANELA = r"""
param([int]$Id, [string]$Foto)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class JanelaArena {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, D, B; }
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out R r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
[JanelaArena]::SetProcessDPIAware() | Out-Null
$p = Get-Process -Id $Id
$r = New-Object JanelaArena+R
[JanelaArena]::GetClientRect($p.MainWindowHandle, [ref]$r) | Out-Null
$bmp = New-Object System.Drawing.Bitmap ($r.D - $r.L), ($r.B - $r.T)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$dc = $g.GetHdc()
[JanelaArena]::PrintWindow($p.MainWindowHandle, $dc, 3) | Out-Null
$g.ReleaseHdc($dc)
$bmp.Save($Foto, [System.Drawing.Imaging.ImageFormat]::Png)
"""


def copiar_arena(destino, jogo):
    """A copia minima do ARENA que abre um jogo de Java ME."""
    # Sem o Python embutido: o servidor da copia roda com o do ARENA de
    # verdade. Um python.exe novo, numa pasta nova, faz o Firewall do Windows
    # perguntar (o servidor escuta a descoberta de colegas, UDP 55436).
    for pasta in ("servidor", "launcher"):
        shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
    ra, ra_d = os.path.join(RAIZ, "retroarch"), os.path.join(destino, "retroarch")
    os.makedirs(os.path.join(ra_d, "cores"))
    os.makedirs(os.path.join(ra_d, "info"))
    os.makedirs(os.path.join(ra_d, "system"))
    for nome in os.listdir(ra):
        if nome.lower().endswith((".dll", ".exe")) or nome.lower() in ("retroarch.cfg", "retroarch.default.cfg"):
            shutil.copyfile(os.path.join(ra, nome), os.path.join(ra_d, nome))
    shutil.copyfile(os.path.join(ra, "cores", "freej2me_libretro.dll"),
                    os.path.join(ra_d, "cores", "freej2me_libretro.dll"))
    shutil.copyfile(os.path.join(ra, "info", "freej2me_libretro.info"),
                    os.path.join(ra_d, "info", "freej2me_libretro.info"))
    shutil.copytree(os.path.join(RAIZ, "emuladores", "Java"), os.path.join(destino, "emuladores", "Java"))
    pasta_jogo = os.path.join(destino, "jogos", "pessoais", "J2ME")
    os.makedirs(pasta_jogo)
    shutil.copyfile(jogo, os.path.join(pasta_jogo, os.path.basename(jogo)))
    os.makedirs(os.path.join(destino, "dados"))


def pedir(rota, corpo=None, espera=10):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, rota), data=dados,
                                    method="GET" if corpo is None else "POST",
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=espera) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def processos(nome, pasta):
    """Os PIDs dos processos 'nome' cujo programa esta dentro de 'pasta'."""
    comando = ("Get-Process %s -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '%s*' } "
               "| ForEach-Object { $_.Id }" % (nome, pasta.replace("'", "''")))
    saida = subprocess.run(["powershell", "-NoProfile", "-Command", comando],
                           capture_output=True, text=True).stdout
    return [int(p) for p in saida.split()]


def esperar(condicao, limite):
    fim = time.time() + limite
    while time.time() < fim:
        resultado = condicao()
        if resultado:
            return resultado
        time.sleep(0.5)
    return condicao()


def jogos_j2me(no):
    if isinstance(no, dict):
        if no.get("plataforma") == "j2me" and no.get("id"):
            return [no]
        no = list(no.values())
    if isinstance(no, list):
        return [j for item in no for j in jogos_j2me(item)]
    return []


def main():
    jogo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
        os.path.join(AQUI, "jogos_livres", "J2ME", "shooter.jar")
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/api/estado" % PORTA, timeout=1)
        print("O ARENA de verdade esta aberto (porta %d): feche-o antes deste teste." % PORTA)
        return 1
    except OSError:
        pass
    temporaria = tempfile.gettempdir()
    antes_temp = set(os.listdir(temporaria))
    trabalho = tempfile.mkdtemp(prefix="arena_java_me_Pedagógicos_")
    copia = os.path.join(trabalho, "ARENA")
    falhas = []
    servidor = None
    registro = os.path.join(trabalho, "servidor.log")

    def confere(nome, ok, detalhe=""):
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    try:
        print("Copiando o ARENA para %s ..." % copia, flush=True)
        copiar_arena(copia, jogo)
        with open(registro, "w", encoding="utf-8") as saida:
            servidor = subprocess.Popen([os.path.join(RAIZ, "servidor", "python", "python.exe"),
                                         os.path.join(copia, "servidor", "arena.py")], cwd=copia,
                                        env=dict(os.environ, ARENA_SEM_JANELA="1", PYTHONIOENCODING="utf-8"),
                                        stdout=saida, stderr=subprocess.STDOUT)
        confere("o servidor da copia abriu", bool(esperar(lambda: _responde(), 60)))
        pedir("/api/indexar", {}, espera=60)
        achados = esperar(lambda: jogos_j2me(pedir("/api/catalogo", espera=30)), 60)
        confere("o jogo aparece no console Java ME", bool(achados))
        if not achados:
            return 1
        jar_na_system = os.path.join(copia, "retroarch", "system", "freej2me-lr.jar")
        java = os.path.join(copia, "emuladores", "Java")
        retroarch = os.path.join(copia, "retroarch")

        # 1. Jogo normal.
        print("1. Jogo normal (fecha pela janela)", flush=True)
        pedir("/api/jogar", {"jogo_id": achados[0]["id"]})
        ra = esperar(lambda: processos("retroarch", retroarch), 30)
        confere("o RetroArch da copia abriu", bool(ra))
        # A metade Java vai para a system antes do jogo, mesmo com a arrumacao
        # das BIOS da abertura ainda rodando (o primeiro jogo abria sem ela).
        confere("o ARENA pos a metade Java do emulador na system", os.path.isfile(jar_na_system))
        javaw = esperar(lambda: processos("javaw", java), 40)
        confere("o Java do ARENA abriu o jogo (sem Java instalado no caminho)", bool(javaw))
        time.sleep(20)                 # aberturas do jogo (logo da empresa, menu)
        foto = os.path.join(trabalho, "java_me.png")
        if ra:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "& {" + FOTO_DA_JANELA + "} -Id %d -Foto '%s'" % (ra[0], foto.replace("'", "''"))],
                           capture_output=True, text=True)
        ok, detalhe = imagem_de_verdade(foto)
        confere("a janela mostra o jogo", ok, detalhe)
        if os.path.isfile(foto):
            guardada = os.path.join(temporaria, "arena_java_me_foto.png")
            shutil.copyfile(foto, guardada)
            print("     foto: %s" % guardada)
        for pid in ra:
            subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True)      # o "fechar" da janela
        confere("o RetroArch fechou pela janela", esperar(lambda: not processos("retroarch", retroarch), 30))
        confere("o Java fechou junto", esperar(lambda: not processos("javaw", java), 10))
        time.sleep(2)
        texto = open(registro, encoding="utf-8", errors="replace").read()
        confere("o jogo abriu pela ponte sem acento", "Pasta com acento: o jogo abre por" in texto)
        confs = [os.path.join(atual, nome) for atual, _pastas, nomes in os.walk(os.path.join(retroarch, "saves"))
                 for nome in nomes if nome == "game.conf"]
        confere("os dados do jogo ficaram em retroarch\\saves da copia", bool(confs),
                os.path.relpath(confs[0], copia) if confs else "nenhum game.conf")
        estragadas = [n for n in set(os.listdir(temporaria)) - antes_temp if "Ã" in n]
        confere("nenhuma pasta com o nome estragado (PedagÃ³gicos)", not estragadas, estragadas)

        # 2. Queda.
        print("2. Queda (o RetroArch derrubado a forca)", flush=True)
        pedir("/api/jogar", {"jogo_id": achados[0]["id"]})
        ra = esperar(lambda: processos("retroarch", retroarch), 30)
        javaw = esperar(lambda: processos("javaw", java), 40)
        confere("abriu de novo (RetroArch e Java)", bool(ra and javaw))
        time.sleep(5)
        for pid in ra:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        sobrou = esperar(lambda: not processos("javaw", java), 10)
        confere("o Java do jogo fechou junto com a queda (a caixa do Windows)", sobrou)
    finally:
        if servidor and servidor.poll() is None:
            servidor.kill()
            servidor.wait()
        for nome in ("retroarch", "javaw"):
            for pid in processos(nome, copia):
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        time.sleep(1)
        if falhas and os.path.isfile(registro):
            print("--- registro do servidor (fim) ---")
            for linha in open(registro, encoding="utf-8", errors="replace").read().splitlines()[-25:]:
                print("   ", linha[:200])
        limpeza.apagar_pasta(trabalho)
    if falhas:
        print("\nFALHAS: %d" % len(falhas))
        return 1
    print("\nTudo certo.")
    return 0


def _responde():
    try:
        return bool(pedir("/api/estado", espera=2))
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
