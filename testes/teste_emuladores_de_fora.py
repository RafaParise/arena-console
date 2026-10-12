# -*- coding: utf-8 -*-
r"""Fase 5 da auditoria 3: os consoles dos emuladores de fora (GameCube e
Wii no Dolphin, PS3 no RPCS3, Xbox 360 no Xenia) abrem um jogo da pasta?

O PS2 tem teste proprio (testes\teste_ps2_todos_os_jogos.py, todos os jogos e
os tres niveis de qualidade). Aqui, um jogo de cada console, aberto com a
MESMA linha de comando do ARENA (graficos.comando_externo) e a configuracao
que o emulador ja tem (a ultima que o ARENA gravou). Passa quando, em ate
90 s, o processo continua vivo e alguma janela dele mostra que o jogo esta
rodando: o nome do jogo, o codigo do disco, ou o contador de quadros (FPS)
no titulo. Mede tambem o tempo ate isso e a memoria do emulador.

Nada da configuracao de verdade muda: os arquivos de configuracao (.ini,
.yml, .toml, .json, .cfg) de cada emulador sao guardados antes e devolvidos
depois (o emulador e' fechado a forca, sem gravar ao sair). O cache que o
emulador cria (sombras, por exemplo) fica, como fica numa partida.

Uso: servidor\python\python.exe testes\teste_emuladores_de_fora.py [console]
"""
import ctypes
import json
import os
import re
import subprocess
import sys
import time
from ctypes import wintypes

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

ESPERA = 90
EXTENSOES = (".rvz", ".iso", ".gcm", ".wbfs", ".ciso", ".gcz", ".wia", ".chd", ".xex", ".zar")
# O jogo de cada console (o primeiro que houver, se este nao estiver): os
# que o professor ja jogou com o ARENA (25 e 26/09/2026).
PREFERIDOS = {"gamecube": "smash bros. melee", "wii": "new super mario bros",
              "ps3": "rayman legends", "xbox360": "gears of war judgment"}
CONFIGURACOES = (".ini", ".yml", ".yaml", ".toml", ".json", ".cfg")
PULAR_PASTAS = {"dev_hdd0", "dev_hdd1", "dev_flash", "dev_flash2", "dev_flash3", "cache", "shaderCache",
                "shadercache", "Cache", "Logs", "log", "logs", "screenshots", "content", "games"}

user32 = ctypes.WinDLL("user32", use_last_error=True)
_PROCURAR = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [wintypes.HWND]


class _Processo(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Processo)]
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Processo)]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def processos_da_arvore(pid):
    """O processo e os filhos dele (o Xenia e o RPCS3 podem abrir outro).
    Pela lista de processos do Windows (sem o wmic, que o Windows 11 tirou)."""
    filhos = {}
    foto = kernel32.CreateToolhelp32Snapshot(0x2, 0)          # TH32CS_SNAPPROCESS
    if foto and foto != wintypes.HANDLE(-1).value:
        try:
            item = _Processo()
            item.dwSize = ctypes.sizeof(_Processo)
            ok = kernel32.Process32FirstW(foto, ctypes.byref(item))
            while ok:
                filhos.setdefault(item.th32ParentProcessID, []).append(item.th32ProcessID)
                ok = kernel32.Process32NextW(foto, ctypes.byref(item))
        finally:
            kernel32.CloseHandle(foto)
    todos, fila = {pid}, [pid]
    while fila:
        for filho in filhos.get(fila.pop(), []):
            if filho not in todos:
                todos.add(filho)
                fila.append(filho)
    return todos


def titulos(pids):
    achados = []

    def cada(hwnd, _):
        dono = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(dono))
        if dono.value in pids and user32.IsWindowVisible(hwnd):
            texto = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, texto, 512)
            if texto.value:
                achados.append(texto.value)
        return True
    user32.EnumWindows(_PROCURAR(cada), 0)
    return achados


def memoria_mb(pids):
    total = 0
    for pid in pids:
        saida = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/FO", "CSV", "/NH"],
                               capture_output=True, text=True).stdout
        m = re.search(r'"([\d.,\s]+) K"', saida)
        if m:
            total += int(re.sub(r"\D", "", m.group(1)) or 0)
    return round(total / 1024)


def jogo_rodando(titulo, jogo):
    """O titulo de alguma janela diz que o jogo esta rodando?"""
    palavras = [p for p in re.findall(r"[A-Za-z]{5,}", os.path.splitext(os.path.basename(jogo))[0])
                if p.lower() not in ("europe", "japan", "world", "brazil", "edition")]
    baixo = titulo.lower()
    return ("fps" in baixo or bool(re.search(r"\([A-Z0-9]{6}\)|\[[A-Z]{4}\d{5}\]|<[0-9A-F]{8}>", titulo))
            or any(p.lower() in baixo for p in palavras[:2]))


def guardar_configuracoes(pasta):
    guardados = {}
    for atual, subpastas, nomes in os.walk(pasta):
        subpastas[:] = [s for s in subpastas if s not in PULAR_PASTAS]
        for nome in nomes:
            if nome.lower().endswith(CONFIGURACOES):
                caminho = os.path.join(atual, nome)
                try:
                    if os.path.getsize(caminho) <= 2 * 1024 * 1024:
                        with open(caminho, "rb") as arquivo:
                            guardados[caminho] = arquivo.read()
                except OSError:
                    pass
    return guardados


def devolver_configuracoes(guardados):
    devolvidos = 0
    for caminho, dados in guardados.items():
        try:
            with open(caminho, "rb") as arquivo:
                if arquivo.read() == dados:
                    continue
        except OSError:
            pass
        with open(caminho, "wb") as arquivo:
            arquivo.write(dados)
        devolvidos += 1
    return devolvidos


def escolher_jogo(plataforma):
    pasta = os.path.join(RAIZ, "jogos", "pessoais", plataforma["pasta"])
    jogos = []
    for atual, _sub, nomes in os.walk(pasta):
        for nome in sorted(nomes):
            if nome.lower().endswith(EXTENSOES):
                jogos.append(os.path.join(atual, nome))
    preferido = PREFERIDOS.get(plataforma["id"], "")
    return next((j for j in jogos if preferido and preferido in os.path.basename(j).lower()), jogos[0] if jogos else None)


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        plataformas = json.load(arquivo)["plataformas"]
    falhas, resultado = [], []
    for plataforma in plataformas:
        if not plataforma.get("externo") or plataforma["id"] == "ps2":
            continue
        if filtro and filtro not in (plataforma["id"] + " " + plataforma["nome"]).lower():
            continue
        exe, dados = graficos.achar_externo(plataforma)
        jogo = escolher_jogo(plataforma)
        if not exe or not jogo:
            print("  [--] %-12s pulado: %s" % (plataforma["nome"], "sem o emulador" if not exe else "sem jogo na pasta"))
            continue
        falta = graficos.falta_para_o_externo(dados["nome"], exe)
        if falta:
            print("  [--] %-12s pulado: %s" % (plataforma["nome"], falta[:90]))
            continue
        pasta_emulador = os.path.dirname(exe)
        guardados = guardar_configuracoes(pasta_emulador)
        comando = graficos.comando_externo(exe, dados, jogo)
        inicio = time.monotonic()
        processo = subprocess.Popen(comando, cwd=pasta_emulador)
        ok, titulo, segundos, mb = False, "", None, None
        try:
            while time.monotonic() - inicio < ESPERA:
                time.sleep(2)
                if processo.poll() is not None:
                    break
                pids = processos_da_arvore(processo.pid)
                for texto in titulos(pids):
                    if jogo_rodando(texto, jogo):
                        ok, titulo = True, texto
                        segundos = round(time.monotonic() - inicio, 1)
                        break
                if ok:
                    time.sleep(8)                 # e continua vivo depois de 8 s?
                    ok = processo.poll() is None
                    mb = memoria_mb(processos_da_arvore(processo.pid)) if ok else None
                    break
            if not ok and processo.poll() is None:
                titulo = " | ".join(titulos(processos_da_arvore(processo.pid)))
        finally:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
            try:
                processo.wait(15)
            except subprocess.TimeoutExpired:
                pass
            time.sleep(3)
            devolvidos = devolver_configuracoes(guardados)
        print("  [%s] %-12s %-48s %s" % (
            "OK" if ok else "FALHOU", plataforma["nome"], os.path.basename(jogo)[:48],
            ("%.1f s, %s MB, janela: %s" % (segundos, mb, titulo[:90])) if ok
            else ("fechou sozinho" if processo.returncode not in (None, 1) and not titulo else "janela: %s" % titulo[:120])),
            flush=True)
        if devolvidos:
            print("        (%d arquivo(s) de configuracao devolvido(s) como estavam)" % devolvidos)
        resultado.append({"console": plataforma["nome"], "emulador": dados["nome"], "jogo": os.path.basename(jogo),
                          "abre": ok, "segundos": segundos, "memoria_mb": mb, "janela": titulo})
        if not ok:
            falhas.append(plataforma["nome"])

    destino = os.path.join(RAIZ, "docs", "auditoria3", "emuladores_de_fora.json")
    if resultado and not filtro:
        with open(destino, "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print()
    if not resultado:
        print("FALHOU: nenhum console de emulador de fora com jogo e emulador para testar.")
        return 1
    if falhas:
        print("FALHOU: %d de %d (%s)" % (len(falhas), len(resultado), ", ".join(falhas)))
        return 1
    print("Emuladores de fora: %d de %d abriram o jogo." % (len(resultado), len(resultado)))
    return 0


if __name__ == "__main__":
    # Os cartoes de memoria, saves e perfis de verdade tambem (Fase 8 da
    # auditoria 3): ligar um jogo grava neles (o historico no cartao do PS2).
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import protege_cfg
    sys.exit(protege_cfg.rodar(main, emuladores=True))
