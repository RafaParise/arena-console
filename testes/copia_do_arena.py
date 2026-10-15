# -*- coding: utf-8 -*-
r"""Uma COPIA do ARENA numa pasta temporaria, para os testes que abrem jogo
pelo caminho inteiro: o servidor de verdade, a rota /api/jogar, o RetroArch.

A pasta da copia tem "Pedagógicos" no nome (o ARENA do Rafael mora numa
assim). Nada do ARENA de verdade e' tocado: nem os dados, nem os saves. O
servidor da copia roda com o Python do ARENA de verdade: um python.exe novo,
numa pasta nova, faria o Firewall do Windows perguntar (o servidor escuta a
descoberta de colegas, UDP 55436). E escuta noutra porta (PORTA, pela
ARENA_PORTA do servidor): o ARENA de verdade pode estar aberto ao lado, na
8777, e nenhum pedido do teste chega a ele.

Usado por testes\teste_java_me_pelo_arena.py e testes\teste_jeitos_pelo_arena.py.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PORTA = 8787          # a da copia; a do ARENA de verdade e' a 8777

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


def montar(destino, nucleos, jogos, sistema=(), java=False):
    r"""A copia minima: servidor (sem o Python e os testes), tela, RetroArch
    (o programa, os 'nucleos' com a ficha de cada um e a configuracao), os
    arquivos de 'sistema' (BIOS do professor, para o teste do jeito original),
    o Java (se 'java') e os 'jogos' ({pasta em jogos\pessoais: [arquivos ou
    pastas]})."""
    for pasta in ("servidor", "launcher"):
        shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
    ra, ra_d = os.path.join(RAIZ, "retroarch"), os.path.join(destino, "retroarch")
    for pasta in ("cores", "info", "system"):
        os.makedirs(os.path.join(ra_d, pasta))
    for nome in os.listdir(ra):
        if nome.lower().endswith((".dll", ".exe")) or nome.lower() in ("retroarch.cfg", "retroarch.default.cfg"):
            shutil.copyfile(os.path.join(ra, nome), os.path.join(ra_d, nome))
    for nucleo in nucleos:
        shutil.copyfile(os.path.join(ra, "cores", nucleo), os.path.join(ra_d, "cores", nucleo))
        info = os.path.join(ra, "info", nucleo[:-4] + ".info")
        if os.path.isfile(info):
            shutil.copyfile(info, os.path.join(ra_d, "info", os.path.basename(info)))
    for origem in sistema:
        shutil.copyfile(origem, os.path.join(ra_d, "system", os.path.basename(origem)))
    if java:
        shutil.copytree(os.path.join(RAIZ, "emuladores", "Java"), os.path.join(destino, "emuladores", "Java"))
    for pasta, itens in jogos.items():
        alvo = os.path.join(destino, "jogos", "pessoais", pasta)
        os.makedirs(alvo, exist_ok=True)
        for item in itens:
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(alvo, os.path.basename(item)))
            else:
                shutil.copyfile(item, os.path.join(alvo, os.path.basename(item)))
    os.makedirs(os.path.join(destino, "dados"))


def porta_ocupada():
    """Ja ha um servidor na porta da copia (um teste anterior que ficou aberto)?"""
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/api/estado" % PORTA, timeout=1)
        return True
    except OSError:
        return False


def subir_servidor(copia, registro):
    """Abre o servidor da copia (sem a janela, na PORTA) e espera ele responder."""
    with open(registro, "w", encoding="utf-8") as saida:
        processo = subprocess.Popen([os.path.join(RAIZ, "servidor", "python", "python.exe"),
                                     os.path.join(copia, "servidor", "arena.py")], cwd=copia,
                                    env=dict(os.environ, ARENA_SEM_JANELA="1", PYTHONIOENCODING="utf-8",
                                             ARENA_PORTA=str(PORTA)),
                                    stdin=subprocess.DEVNULL, stdout=saida, stderr=subprocess.STDOUT)
    esperar(responde, 60)
    return processo


def pedir(rota, corpo=None, espera=10):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA, rota), data=dados,
                                    method="GET" if corpo is None else "POST",
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=espera) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def responde():
    try:
        return bool(pedir("/api/estado", espera=2))
    except OSError:
        return False


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


def jogos_do_console(no, plataforma):
    """Os jogos do catalogo (a resposta do /api/catalogo) deste console."""
    if isinstance(no, dict):
        if no.get("plataforma") == plataforma and no.get("id"):
            return [no]
        no = list(no.values())
    if isinstance(no, list):
        return [j for item in no for j in jogos_do_console(item, plataforma)]
    return []


def foto_da_janela(pid, arquivo):
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "& {" + FOTO_DA_JANELA + "} -Id %d -Foto '%s'" % (pid, arquivo.replace("'", "''"))],
                   capture_output=True, text=True)


def fechar_pela_janela(pasta_retroarch, limite=30):
    """Fecha o RetroArch como o aluno fecha (a janela recebe o "fechar").
    True se fechou."""
    for pid in processos("retroarch", pasta_retroarch):
        subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True)
    return esperar(lambda: not processos("retroarch", pasta_retroarch), limite)


def derrubar(copia):
    """Fecha a forca tudo o que a copia abriu (fim do teste)."""
    for nome in ("retroarch", "javaw"):
        for pid in processos(nome, copia):
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)


def nova_pasta():
    trabalho = tempfile.mkdtemp(prefix="arena_copia_Pedagógicos_")
    return trabalho, os.path.join(trabalho, "ARENA")
