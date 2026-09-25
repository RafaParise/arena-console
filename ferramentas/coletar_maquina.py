# -*- coding: utf-8 -*-
r"""Retrato da maquina para o perfil-alvo do ARENA.

Mede o que importa para o ARENA rodar bem: processador (inclusive AVX/AVX2),
memoria, discos (com velocidade de verdade), video, sistema, rede e de onde
o ARENA esta rodando. So le -- nao muda nada no Windows nem no ARENA.

REGRAS (pedido do Rafael):
  - Python puro, so biblioteca padrao. Roda com o Python do proprio ARENA.
  - Sem administrador: o que exigir, vira "nao foi possivel medir" e segue.
  - Sem dado pessoal: nada de nome de usuario, nome da maquina ou endereco
    fisico (MAC) em texto. A maquina e' identificada por um codigo
    embaralhado -- DIFERENTE do codigo que o ARENA usa na sincronizacao,
    para nao dar para cruzar um com o outro.
  - Funciona de pen drive, com qualquer letra, e sem internet.

Uso:
    servidor\python\python.exe ferramentas\coletar_maquina.py [pasta_de_saida]

Saida: perfil\<codigo>_<data-hora>\maquina.json (para analise) e
maquina.txt (resumo em portugues).
"""
import ctypes
import datetime
import hashlib
import json
import os
import platform
import random
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_PERFIL = os.path.join(RAIZ, "perfil")
VERSAO_COLETOR = 1
NAO_MEDIU = "nao_foi_possivel_medir"
NO_WINDOWS = sys.platform.startswith("win")


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def falhou(motivo):
    """Marca padrao de "nao deu para medir", com o motivo."""
    return {NAO_MEDIU: True, "motivo": str(motivo)[:200]}


def powershell(comando, limite=25):
    """Roda um comando do PowerShell que ja vem no Windows (nao e' pip nem
    instalacao). Devolve o texto, ou None se falhar ou demorar demais."""
    # Saida em UTF-8 dos dois lados: sem isso "Conexao" com til chega torto.
    comando = "[Console]::OutputEncoding = [Text.Encoding]::UTF8; " + comando
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", comando],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=limite,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def powershell_json(comando, limite=25):
    """Comando que termina em ConvertTo-Json. Sempre devolve lista."""
    saida = powershell(comando + " | ConvertTo-Json -Compress -Depth 3", limite)
    if not saida:
        return None
    try:
        dados = json.loads(saida)
    except ValueError:
        return None
    return dados if isinstance(dados, list) else [dados]


def ler_registro(chave, valor):
    """Le um valor do registro do Windows em HKEY_LOCAL_MACHINE (so leitura,
    liberada para qualquer usuario nessas chaves)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, chave) as k:
            return winreg.QueryValueEx(k, valor)[0]
    except OSError:
        return None


def codigo_da_maquina():
    """Codigo embaralhado que identifica a maquina sem revelar nada.

    Mesma ideia do ARENA (hardware.identidade_da_maquina), mas com um
    "sal" diferente: o mesmo computador da um codigo que NAO bate com o
    codigo de sincronizacao dele. Nome, usuario e placa de rede entram no
    embaralhamento e nunca aparecem em texto."""
    import uuid
    pedacos = ["perfil-alvo-do-arena"]
    try:
        pedacos.append(socket.gethostname())
    except OSError:
        pass
    for variavel in ("USERNAME", "COMPUTERNAME"):
        pedacos.append(os.environ.get(variavel, ""))
    try:
        no = uuid.getnode()
        if not (no >> 40) % 2:          # bit 41 ligado = numero inventado
            pedacos.append("%012x" % no)
    except Exception:
        pass
    return hashlib.sha256("|".join(pedacos).encode("utf-8")).hexdigest()[:10].upper()


def pasta_da_coleta(pedida=None):
    """Pasta desta coleta: perfil\\<codigo>_<data-hora>. Guarda o caminho
    em perfil\\ultima_coleta.txt para o medir_arena.py usar a mesma."""
    if pedida:
        os.makedirs(pedida, exist_ok=True)
        return pedida
    nome = "%s_%s" % (codigo_da_maquina(), datetime.datetime.now().strftime("%Y-%m-%d_%H%M"))
    pasta = os.path.join(PASTA_PERFIL, nome)
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(PASTA_PERFIL, "ultima_coleta.txt"), "w", encoding="utf-8") as f:
        f.write(nome)
    return pasta


def etapa(texto):
    print("  - " + texto, flush=True)


# ---------------------------------------------------------------------------
# Processador
# ---------------------------------------------------------------------------

# Codigos da funcao IsProcessorFeaturePresent, conferidos na documentacao
# oficial da Microsoft (learn.microsoft.com, processthreadsapi.h). Ela nao
# pede privilegio nenhum. Os de SSSE3 a AVX512F so sao reconhecidos a partir
# do Windows 10 versao 2004 -- antes disso ela responde "nao" mesmo que o
# processador tenha (anotado no resultado).
INSTRUCOES = {
    "sse": 6, "sse2": 10, "sse3": 13, "ssse3": 36, "sse4_1": 37, "sse4_2": 38,
    "avx": 39, "avx2": 40, "avx512f": 41,
}


def coletar_processador():
    etapa("processador")
    resultado = {}
    chave = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    nome = ler_registro(chave, "ProcessorNameString")
    resultado["nome"] = " ".join(str(nome).split()) if nome else NAO_MEDIU
    mhz = ler_registro(chave, "~MHz")
    resultado["mhz_nominal"] = mhz if mhz else NAO_MEDIU
    resultado["threads"] = os.cpu_count() or NAO_MEDIU

    info = powershell_json("Get-CimInstance Win32_Processor | Select-Object "
                           "NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed")
    if info:
        resultado["nucleos"] = sum(int(p.get("NumberOfCores") or 0) for p in info) or NAO_MEDIU
        resultado["mhz_maximo"] = info[0].get("MaxClockSpeed") or NAO_MEDIU
    else:
        resultado["nucleos"] = NAO_MEDIU

    if NO_WINDOWS:
        presente = ctypes.windll.kernel32.IsProcessorFeaturePresent
        resultado["instrucoes"] = {nome: bool(presente(codigo))
                                   for nome, codigo in INSTRUCOES.items()}
        compilacao = int(ler_registro(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                                      "CurrentBuildNumber") or 0)
        if compilacao and compilacao < 19041:
            resultado["instrucoes_aviso"] = (
                "Windows anterior ao 10 versao 2004: SSSE3 a AVX512F podem "
                "aparecer como ausentes mesmo existindo.")
    else:
        resultado["instrucoes"] = falhou("so no Windows")
    return resultado


# ---------------------------------------------------------------------------
# Memoria
# ---------------------------------------------------------------------------

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def memoria_agora():
    """Memoria do Windows neste instante (MB). Usado tambem pelo medir_arena."""
    estado = _MEMORYSTATUSEX()
    estado.dwLength = ctypes.sizeof(estado)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado)):
        raise OSError("GlobalMemoryStatusEx falhou")
    mb = 1024 * 1024
    return {"total_mb": round(estado.ullTotalPhys / mb),
            "livre_mb": round(estado.ullAvailPhys / mb),
            "em_uso_pct": int(estado.dwMemoryLoad),
            "arquivo_de_paginacao_livre_mb": round(estado.ullAvailPageFile / mb)}


def coletar_memoria():
    etapa("memoria")
    try:
        resultado = memoria_agora()
    except (OSError, AttributeError) as falha:
        return falhou(falha)
    # Pentes de memoria (sem administrador). Com UM pente so, a memoria
    # trabalha em canal simples: a placa de video integrada (a do Celeron)
    # divide essa memoria e perde muito desempenho.
    pentes = powershell_json("Get-CimInstance Win32_PhysicalMemory | Select-Object "
                             "@{n='gb';e={[math]::Round($_.Capacity/1GB,1)}}, "
                             "@{n='mhz';e={if ($_.ConfiguredClockSpeed) {$_.ConfiguredClockSpeed} else {$_.Speed}}}")
    if pentes is None:
        resultado["pentes"] = falhou("consulta de pentes nao respondeu")
    else:
        resultado["pentes"] = [{"gb": p.get("gb"), "mhz": p.get("mhz")} for p in pentes]
        resultado["canal_simples"] = len(pentes) == 1
    return resultado


# ---------------------------------------------------------------------------
# Discos (com velocidade de verdade, sem o cache do Windows)
# ---------------------------------------------------------------------------

TIPOS_DE_UNIDADE = {0: "desconhecido", 1: "sem raiz", 2: "removivel (pen drive/cartao)",
                    3: "fixo (disco interno ou externo)", 4: "rede", 5: "CD/DVD", 6: "RAM"}

GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
CREATE_ALWAYS, OPEN_EXISTING = 2, 3
SEM_CACHE = 0x20000000          # FILE_FLAG_NO_BUFFERING: le/grava direto no disco
GRAVA_DIRETO = 0x80000000       # FILE_FLAG_WRITE_THROUGH
TAMANHO_TESTE = 64 * 1024 * 1024
BLOCO = 1024 * 1024


def _kernel32():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.restype = ctypes.c_void_p
    k.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                              ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    k.WriteFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                            ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
    k.ReadFile.argtypes = k.WriteFile.argtypes
    k.SetFilePointerEx.argtypes = [ctypes.c_void_p, ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint32]
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    k.VirtualAlloc.restype = ctypes.c_void_p
    k.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
    k.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
    return k


def _abrir(k, caminho, acesso, criacao, flags):
    h = k.CreateFileW(caminho, acesso, 0, None, criacao, flags, None)
    if h is None or h == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateFileW falhou")
    return h


def medir_velocidade(pasta):
    """Grava 64 MB e le de volta SEM o cache do Windows (senao mediria a
    memoria, nao o disco), depois faz 200 leituras de 4 KB em pontos
    sorteados. A leitura sorteada e' o que separa disco mecanico (a cabeca
    tem que andar: ~5 a 15 ms cada) de SSD (< 0,5 ms). Apaga o arquivo."""
    k = _kernel32()
    caminho = os.path.join(pasta, "arena_teste_disco_%d.tmp" % os.getpid())
    buffer = k.VirtualAlloc(None, BLOCO, 0x3000, 0x04)   # alinhado a pagina
    if not buffer:
        raise OSError("VirtualAlloc falhou")
    feito = ctypes.c_uint32(0)
    try:
        ctypes.memmove(buffer, os.urandom(BLOCO), BLOCO)
        h = _abrir(k, caminho, GENERIC_WRITE, CREATE_ALWAYS, SEM_CACHE | GRAVA_DIRETO)
        try:
            inicio = time.perf_counter()
            for _ in range(TAMANHO_TESTE // BLOCO):
                if not k.WriteFile(h, buffer, BLOCO, ctypes.byref(feito), None):
                    raise OSError(ctypes.get_last_error(), "WriteFile falhou")
            escrita = time.perf_counter() - inicio
        finally:
            k.CloseHandle(h)

        h = _abrir(k, caminho, GENERIC_READ, OPEN_EXISTING, SEM_CACHE)
        try:
            inicio = time.perf_counter()
            for _ in range(TAMANHO_TESTE // BLOCO):
                if not k.ReadFile(h, buffer, BLOCO, ctypes.byref(feito), None):
                    raise OSError(ctypes.get_last_error(), "ReadFile falhou")
            leitura = time.perf_counter() - inicio

            tempos = []
            for _ in range(200):
                posicao = random.randrange(0, TAMANHO_TESTE // 4096) * 4096
                k.SetFilePointerEx(h, posicao, None, 0)
                t = time.perf_counter()
                if not k.ReadFile(h, buffer, 4096, ctypes.byref(feito), None):
                    raise OSError(ctypes.get_last_error(), "ReadFile 4K falhou")
                tempos.append(time.perf_counter() - t)
        finally:
            k.CloseHandle(h)
    finally:
        k.VirtualFree(buffer, 0, 0x8000)
        try:
            os.remove(caminho)
        except OSError:
            pass

    tempos.sort()
    mb = TAMANHO_TESTE / (1024 * 1024)
    return {"escrita_mb_s": round(mb / escrita, 1),
            "leitura_mb_s": round(mb / leitura, 1),
            "leitura_4k_mediana_ms": round(tempos[len(tempos) // 2] * 1000, 3),
            "leitura_4k_pior_ms": round(tempos[-1] * 1000, 3)}


def palpite_do_disco(tipo, velocidade):
    """Pela latencia da leitura sorteada, nao pelo nome (que mente)."""
    if not isinstance(velocidade, dict) or NAO_MEDIU in velocidade:
        return NAO_MEDIU
    lat = velocidade["leitura_4k_mediana_ms"]
    if tipo == 2:
        return "pen drive ou cartao SD"
    if lat >= 2.0:
        return "disco mecanico (HD)"
    if velocidade["leitura_mb_s"] >= 900:
        return "SSD NVMe"
    return "SSD (SATA ou por USB)"


def info_da_unidade(raiz):
    """Tipo e sistema de arquivos de uma unidade (ex.: 'E:\\')."""
    k = ctypes.windll.kernel32
    tipo = k.GetDriveTypeW(ctypes.c_wchar_p(raiz))
    fs = ctypes.create_unicode_buffer(32)
    ok = k.GetVolumeInformationW(ctypes.c_wchar_p(raiz), None, 0, None, None, None, fs, 32)
    return tipo, (fs.value if ok else NAO_MEDIU)


def coletar_disco(raiz, pasta_teste, rotulo):
    etapa("disco %s (%s) -- grava e le 64 MB, leva alguns segundos" % (raiz, rotulo))
    resultado = {"uso": rotulo, "letra": raiz[:2]}
    try:
        tipo, fs = info_da_unidade(raiz)
        resultado["tipo"] = TIPOS_DE_UNIDADE.get(tipo, str(tipo))
        resultado["sistema_de_arquivos"] = fs
    except (OSError, AttributeError) as falha:
        tipo = 0
        resultado["tipo"] = falhou(falha)
    try:
        uso = shutil.disk_usage(raiz)
        resultado["total_gb"] = round(uso.total / 1024 ** 3, 1)
        resultado["livre_gb"] = round(uso.free / 1024 ** 3, 1)
        livre = uso.free
    except OSError as falha:
        resultado["livre_gb"] = falhou(falha)
        livre = 0
    if livre < 4 * TAMANHO_TESTE:
        resultado["velocidade"] = falhou("pouco espaco livre para o teste de 64 MB")
    else:
        try:
            os.makedirs(pasta_teste, exist_ok=True)
            resultado["velocidade"] = medir_velocidade(pasta_teste)
        except (OSError, AttributeError) as falha:
            resultado["velocidade"] = falhou(falha)
    resultado["palpite"] = palpite_do_disco(tipo, resultado["velocidade"])
    # Segunda opiniao: o que o proprio Windows diz do disco fisico dessa
    # letra (HD/SSD e o tipo de ligacao). Sem administrador.
    letra = raiz[0]
    midia = powershell_json(
        "Get-Partition -DriveLetter %s -ErrorAction Stop | Get-Disk | ForEach-Object { "
        "$d = Get-PhysicalDisk | Where-Object DeviceId -eq $_.Number; "
        "[pscustomobject]@{ tipo = [string]$d.MediaType; ligacao = [string]$d.BusType; modelo = $d.FriendlyName } }" % letra)
    if midia:
        resultado["windows_diz"] = midia[0]
        if midia[0].get("tipo") == "HDD" and "mecanico" not in str(resultado["palpite"]):
            resultado["palpite"] += " (o Windows diz HD mecanico)"
    else:
        resultado["windows_diz"] = falhou("o Windows nao informou o tipo do disco")
    return resultado


# ---------------------------------------------------------------------------
# Video e sistema
# ---------------------------------------------------------------------------

def coletar_video():
    etapa("video")
    placas = powershell_json(
        "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, "
        "@{n='DriverDate';e={if ($_.DriverDate) {$_.DriverDate.ToString('yyyy-MM-dd')}}}, "
        "AdapterRAM, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate")
    if not placas:
        return falhou("consulta de video nao respondeu")
    saida = []
    for p in placas:
        ram = p.get("AdapterRAM")
        saida.append({
            "placa": p.get("Name") or NAO_MEDIU,
            "driver_versao": p.get("DriverVersion") or NAO_MEDIU,
            "driver_data": p.get("DriverDate") or NAO_MEDIU,
            # AdapterRAM e' de 32 bits no Windows: placa com 4 GB ou mais
            # aparece errada. Fica anotado, nao corrigido por palpite.
            "memoria_mb_informada": round(ram / 1024 ** 2) if isinstance(ram, int) and ram > 0 else NAO_MEDIU,
            "resolucao": "%sx%s" % (p.get("CurrentHorizontalResolution"), p.get("CurrentVerticalResolution"))
                         if p.get("CurrentHorizontalResolution") else NAO_MEDIU,
            "hz": p.get("CurrentRefreshRate") or NAO_MEDIU,
            "driver_basico_da_microsoft": "basic display" in str(p.get("Name", "")).lower()
                                          or "vídeo básico" in str(p.get("Name", "")).lower()
                                          or "video basico" in str(p.get("Name", "")).lower(),
        })
    return saida


class _POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


def coletar_sistema():
    etapa("sistema e energia")
    chave = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    compilacao = ler_registro(chave, "CurrentBuildNumber")
    ubr = ler_registro(chave, "UBR")
    nome = ler_registro(chave, "ProductName") or NAO_MEDIU
    # O registro do Windows 11 ainda diz "Windows 10" no nome; a compilacao
    # 22000 ou maior e' que confirma o 11.
    if compilacao and int(compilacao) >= 22000 and isinstance(nome, str):
        nome = nome.replace("Windows 10", "Windows 11")
    arquitetura = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE", "")
    resultado = {
        "windows": nome,
        "versao": ler_registro(chave, "DisplayVersion") or NAO_MEDIU,
        "compilacao": "%s.%s" % (compilacao, ubr) if compilacao else NAO_MEDIU,
        "edicao": ler_registro(chave, "EditionID") or NAO_MEDIU,
        "windows_64_bits": arquitetura.upper() in ("AMD64", "ARM64"),
        "python_do_arena": platform.python_version() + " " + platform.architecture()[0],
    }
    try:
        resultado["usuario_e_administrador"] = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (OSError, AttributeError) as falha:
        resultado["usuario_e_administrador"] = falhou(falha)

    energia = {}
    try:
        estado = _POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(estado)):
            energia["na_tomada"] = {0: False, 1: True}.get(estado.ACLineStatus, NAO_MEDIU)
            energia["bateria_pct"] = (estado.BatteryLifePercent
                                      if estado.BatteryLifePercent != 255 else "sem bateria")
            # Modo "economia de bateria" do Windows ligado.
            energia["economia_de_bateria"] = bool(estado.SystemStatusFlag & 1)
    except (OSError, AttributeError) as falha:
        energia = falhou(falha)
    try:
        # powercfg /getactivescheme so LE o plano ativo: nao pede administrador.
        r = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, timeout=10,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        texto = r.stdout.decode("cp850", "replace").strip()
        energia["plano"] = texto.split("(")[-1].rstrip(")").strip() if "(" in texto else (texto or NAO_MEDIU)
    except (OSError, subprocess.SubprocessError) as falha:
        energia["plano"] = falhou(falha)
    resultado["energia"] = energia
    return resultado


# ---------------------------------------------------------------------------
# Rede
# ---------------------------------------------------------------------------

PORTAS_DO_ARENA = [("tcp", 8777, "servidor do ARENA"), ("tcp", 55435, "partida a dois"),
                   ("udp", 55435, "partida a dois"), ("udp", 55436, "descoberta de colegas")]


def porta_livre(protocolo, porta):
    """Tenta ocupar a porta SO neste computador (127.0.0.1). Abrir para a
    rede faria o Firewall do Windows mostrar a caixa de permissao na tela
    do aluno -- por isso a parte da rede e' lida nas regras do Firewall."""
    tipo = socket.SOCK_STREAM if protocolo == "tcp" else socket.SOCK_DGRAM
    s = socket.socket(socket.AF_INET, tipo)
    try:
        s.bind(("127.0.0.1", porta))
        return True
    except OSError:
        return False
    finally:
        s.close()


def teste_de_internet():
    """Resolve um nome e pede a pagina de teste da propria Microsoft (a que o
    Windows usa para saber se tem internet), que devolve um texto fixo. Se
    vier outra coisa, e' pagina de login do Wi-Fi (portal cativo)."""
    resultado = {}
    try:
        socket.setdefaulttimeout(5)
        socket.getaddrinfo("www.msftconnecttest.com", 80)
        resultado["dns"] = True
    except OSError:
        resultado["dns"] = False
        resultado["situacao"] = "sem internet (nem o nome resolve)"
        return resultado
    finally:
        socket.setdefaulttimeout(None)
    try:
        with urllib.request.urlopen("http://www.msftconnecttest.com/connecttest.txt", timeout=8) as r:
            corpo = r.read(200).decode("utf-8", "replace").strip()
        resultado["http"] = True
        if corpo == "Microsoft Connect Test":
            resultado["situacao"] = "internet funcionando"
        else:
            resultado["situacao"] = "pagina de login do Wi-Fi (portal) no meio do caminho"
    except Exception as falha:
        resultado["http"] = False
        resultado["situacao"] = "nome resolve, mas a pagina nao abre (%s)" % str(falha)[:80]
    return resultado


def coletar_rede():
    etapa("rede (adaptadores, portas, firewall e internet)")
    rede = {}
    enderecos = powershell_json(
        "Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
        "Where-Object { $_.IPAddress -ne '127.0.0.1' } | ForEach-Object { "
        "$a = Get-NetAdapter -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue; "
        "[pscustomobject]@{ adaptador = $_.InterfaceAlias; descricao = $a.InterfaceDescription; "
        "endereco = $_.IPAddress; mascara_bits = $_.PrefixLength; origem = [string]$_.PrefixOrigin } }")
    rede["adaptadores"] = enderecos if enderecos is not None else falhou("consulta de enderecos nao respondeu")

    # So a categoria (Publica/Privada/Dominio). O nome da rede Wi-Fi nao e'
    # guardado.
    perfis = powershell_json("Get-NetConnectionProfile -ErrorAction SilentlyContinue | "
                             "Select-Object InterfaceAlias, @{n='categoria';e={[string]$_.NetworkCategory}}")
    rede["perfis"] = ([{"adaptador": p.get("InterfaceAlias"), "categoria": p.get("categoria")}
                       for p in perfis] if perfis is not None else falhou("sem resposta"))

    rede["portas"] = [{"protocolo": p, "porta": n, "uso": uso, "livre": porta_livre(p, n)}
                      for p, n, uso in PORTAS_DO_ARENA]

    python_arena = os.path.join(RAIZ, "servidor", "python", "python.exe").lower()
    retroarch = os.path.join(RAIZ, "retroarch", "retroarch.exe").lower()
    regras = powershell_json(
        "Get-NetFirewallApplicationFilter -PolicyStore ActiveStore -ErrorAction Stop | "
        "Where-Object { $_.Program -and ($_.Program.ToLower() -eq '%s' -or $_.Program.ToLower() -eq '%s') } | "
        "ForEach-Object { $r = $_ | Get-NetFirewallRule; [pscustomobject]@{ programa = $_.Program; "
        "direcao = [string]$r.Direction; acao = [string]$r.Action; perfis = [string]$r.Profile; "
        "ligada = [string]$r.Enabled } }" % (python_arena.replace("'", "''"), retroarch.replace("'", "''")),
        limite=60)
    if regras is None:
        rede["firewall"] = falhou("leitura das regras do Firewall nao respondeu (pode exigir mais permissao)")
    else:
        for r in regras:
            r["programa"] = "python do ARENA" if r["programa"].lower() == python_arena else "RetroArch do ARENA"
        rede["firewall"] = regras or "nenhuma regra ainda (o Windows pergunta na primeira vez)"

    rede["internet"] = teste_de_internet()
    return rede


# ---------------------------------------------------------------------------
# Instalacao (de onde o ARENA esta rodando)
# ---------------------------------------------------------------------------

def marcado_como_da_internet(caminho):
    """O Windows marca arquivo baixado da internet com um "anexo" escondido
    chamado Zone.Identifier (ZoneId=3 = internet). E' essa marca que faz o
    SmartScreen bloquear o .bat. So existe em disco NTFS."""
    try:
        with open(caminho + ":Zone.Identifier", "r", encoding="utf-8", errors="replace") as f:
            texto = f.read()
    except OSError:
        return False
    return "ZoneId=3" in texto or "ZoneId=4" in texto


def coletar_instalacao():
    etapa("de onde o ARENA esta rodando")
    raiz_unidade = os.path.splitdrive(RAIZ)[0] + "\\"
    resultado = {"letra": raiz_unidade[:2], "tamanho_do_caminho": len(RAIZ)}
    try:
        tipo, fs = info_da_unidade(raiz_unidade)
        resultado["tipo"] = TIPOS_DE_UNIDADE.get(tipo, str(tipo))
        resultado["sistema_de_arquivos"] = fs
    except (OSError, AttributeError) as falha:
        resultado["tipo"] = falhou(falha)
        fs = ""
    arquivos = [n for n in os.listdir(RAIZ) if n.lower().endswith(".bat")]
    arquivos += [os.path.join("retroarch", "retroarch.exe"),
                 os.path.join("servidor", "python", "python.exe")]
    marcados = [n for n in arquivos if os.path.isfile(os.path.join(RAIZ, n))
                and marcado_como_da_internet(os.path.join(RAIZ, n))]
    resultado["bloqueados_pela_internet"] = marcados
    if fs and fs.upper() != "NTFS":
        resultado["bloqueio_aviso"] = ("Disco %s nao guarda a marca de 'veio da internet'; "
                                       "a checagem so vale em NTFS." % fs)
    return resultado


# ---------------------------------------------------------------------------
# Barreiras de lentidao (o mesmo diagnostico que o ARENA usa)
# ---------------------------------------------------------------------------

def coletar_barreiras(dados):
    """Usa servidor\\barreiras.py -- o MESMO codigo que o ARENA usa na tela,
    para o coletor e o ARENA nunca discordarem. Aqui ele ainda recebe o
    resultado do teste de disco (HD mecanico), que o ARENA nao mede."""
    etapa("o que deixa esta maquina lenta (programas, servicos, telemetria...)")
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    try:
        import barreiras
        windows = next((d for d in dados.get("discos", []) if d.get("uso") == "onde esta o Windows"),
                       (dados.get("discos") or [{}])[0])
        mecanico = "mecanico" in str(windows.get("palpite", ""))
        resultado = barreiras.diagnosticar(disco_mecanico=mecanico)
        # No retrato fica so o que ajuda a decidir: sem a lista de processos
        # inteira (so os 15 mais pesados, ja cortados no modulo).
        return resultado
    except Exception as falha:
        return falhou(falha)


# ---------------------------------------------------------------------------
# Resumo em portugues
# ---------------------------------------------------------------------------

def _v(valor, sufixo=""):
    if isinstance(valor, dict) and valor.get(NAO_MEDIU):
        return "nao foi possivel medir (%s)" % valor.get("motivo", "")
    if valor == NAO_MEDIU:
        return "nao foi possivel medir"
    return "%s%s" % (valor, sufixo)


def escrever_resumo(dados):
    L = []
    L.append("RETRATO DA MAQUINA - ARENA")
    L.append("Codigo da maquina: %s   (embaralhado, nao revela nome nem usuario)" % dados["codigo_maquina"])
    L.append("Coletado em: %s" % dados["coletado_em"])
    L.append("")

    c = dados["processador"]
    L.append("PROCESSADOR")
    L.append("  %s" % _v(c.get("nome")))
    L.append("  %s nucleos, %s threads, %s MHz" % (_v(c.get("nucleos")), _v(c.get("threads")),
                                                 _v(c.get("mhz_nominal"))))
    inst = c.get("instrucoes")
    if isinstance(inst, dict) and NAO_MEDIU not in inst:
        L.append("  AVX: %s   AVX2: %s   SSE4.2: %s" % (
            "sim" if inst["avx"] else "NAO", "sim" if inst["avx2"] else "NAO",
            "sim" if inst["sse4_2"] else "NAO"))
        if not inst["avx2"]:
            L.append("  ! Sem AVX2: emuladores pesados (PS2, PS3, Xbox 360) podem nem abrir.")
    if c.get("instrucoes_aviso"):
        L.append("  ! " + c["instrucoes_aviso"])
    L.append("")

    m = dados["memoria"]
    L.append("MEMORIA")
    if NAO_MEDIU in m:
        L.append("  " + _v(m))
    else:
        L.append("  %s MB no total, %s MB livres agora (%s%% em uso com o Windows aberto)" % (
            m["total_mb"], m["livre_mb"], m["em_uso_pct"]))
        pentes = m.get("pentes")
        if isinstance(pentes, list) and pentes:
            L.append("  %d pente(s): %s" % (len(pentes), ", ".join(
                "%s GB a %s MHz" % (p["gb"], p["mhz"]) for p in pentes)))
            if m.get("canal_simples"):
                L.append("  ! Um pente so (canal simples): o video integrado perde desempenho.")
    L.append("")

    L.append("DISCOS")
    for d in dados["discos"]:
        L.append("  %s  %s - %s, %s" % (d["letra"], d["uso"], _v(d.get("tipo")),
                                       _v(d.get("sistema_de_arquivos"))))
        L.append("      livre: %s" % _v(d.get("livre_gb"), " GB"))
        vel = d.get("velocidade")
        if isinstance(vel, dict) and NAO_MEDIU not in vel:
            L.append("      grava %s MB/s, le %s MB/s, leitura sorteada %s ms  ->  %s" % (
                vel["escrita_mb_s"], vel["leitura_mb_s"], vel["leitura_4k_mediana_ms"], d["palpite"]))
        else:
            L.append("      velocidade: %s" % _v(vel))
        wd = d.get("windows_diz")
        if isinstance(wd, dict) and not wd.get(NAO_MEDIU):
            L.append("      o Windows diz: %s, ligado por %s (%s)" % (
                wd.get("tipo") or "?", wd.get("ligacao") or "?", wd.get("modelo") or "?"))
        if str(d.get("sistema_de_arquivos", "")).upper() == "FAT32":
            L.append("      ! FAT32: jogo acima de 4 GB nao cabe.")
    L.append("")

    L.append("VIDEO")
    video = dados["video"]
    if isinstance(video, list):
        for p in video:
            L.append("  %s  (driver %s de %s, %s a %s Hz)" % (
                p["placa"], p["driver_versao"], p["driver_data"], p["resolucao"], p["hz"]))
            if p["driver_basico_da_microsoft"]:
                L.append("  ! Driver basico da Microsoft: sem driver de video de verdade.")
    else:
        L.append("  " + _v(video))
    L.append("")

    s = dados["sistema"]
    L.append("SISTEMA")
    L.append("  %s %s (compilacao %s), %s" % (_v(s["windows"]), _v(s["versao"]), _v(s["compilacao"]),
                                              "64 bits" if s["windows_64_bits"] else "32 BITS"))
    L.append("  Usuario e administrador: %s" % (
        "sim" if s.get("usuario_e_administrador") is True else
        "nao" if s.get("usuario_e_administrador") is False else _v(s.get("usuario_e_administrador"))))
    e = s.get("energia", {})
    if isinstance(e, dict) and NAO_MEDIU not in e:
        L.append("  Energia: %s, plano \"%s\"%s" % (
            "na tomada" if e.get("na_tomada") is True else "NA BATERIA" if e.get("na_tomada") is False else "?",
            _v(e.get("plano")), ", economia de bateria LIGADA" if e.get("economia_de_bateria") else ""))
    L.append("")

    r = dados["rede"]
    L.append("REDE")
    if isinstance(r["adaptadores"], list):
        for a in r["adaptadores"]:
            L.append("  %s: %s/%s  (%s)" % (a.get("adaptador"), a.get("endereco"),
                                           a.get("mascara_bits"), a.get("descricao") or "-"))
    else:
        L.append("  adaptadores: " + _v(r["adaptadores"]))
    if isinstance(r["perfis"], list):
        for p in r["perfis"]:
            L.append("  Rede de %s marcada como: %s%s" % (
                p["adaptador"], p["categoria"],
                "  ! Publica: o Firewall fecha mais, e liberar pede senha de administrador"
                if str(p["categoria"]).lower().startswith("public") else ""))
    ocupadas = [p for p in r["portas"] if not p["livre"]]
    L.append("  Portas do ARENA: %s" % ("todas livres" if not ocupadas else
             "OCUPADAS: " + ", ".join("%s %d" % (p["protocolo"], p["porta"]) for p in ocupadas)))
    fw = r["firewall"]
    if isinstance(fw, list):
        # O Windows cria uma regra por protocolo (TCP/UDP): agrupa as iguais.
        vistas = {}
        for regra in fw:
            chave = "%s: %s, %s, redes %s%s" % (
                regra["programa"], "entrada" if regra["direcao"] == "Inbound" else "saida",
                "LIBERADO" if regra["acao"] == "Allow" else "BLOQUEADO", regra["perfis"],
                "" if regra["ligada"] == "True" else " (regra desligada)")
            vistas[chave] = vistas.get(chave, 0) + 1
        for chave, n in vistas.items():
            L.append("  Firewall: %s%s" % (chave, " (%d regras)" % n if n > 1 else ""))
        if not any(regra["programa"] == "python do ARENA" for regra in fw):
            L.append("  Firewall: python do ARENA sem regra ainda (o Windows pergunta ao ligar a rede)")
    else:
        L.append("  Firewall: %s" % _v(fw))
    L.append("  Internet: %s" % r["internet"].get("situacao"))
    L.append("")

    i = dados["instalacao"]
    L.append("INSTALACAO")
    L.append("  ARENA na unidade %s - %s, %s (caminho com %s letras)" % (
        i["letra"], _v(i.get("tipo")), _v(i.get("sistema_de_arquivos")), i["tamanho_do_caminho"]))
    if i["bloqueados_pela_internet"]:
        L.append("  ! Marcados como vindos da internet (o Windows pode bloquear): %s"
                 % ", ".join(i["bloqueados_pela_internet"]))
        L.append("    Como liberar: guia 1, SmartScreen.")
    else:
        L.append("  Nenhum .bat marcado como vindo da internet.")
    if i.get("bloqueio_aviso"):
        L.append("  (%s)" % i["bloqueio_aviso"])
    L.append("")

    b = dados.get("barreiras", {})
    L.append("O QUE DEIXA ESTA MAQUINA LENTA")
    if b.get(NAO_MEDIU):
        L.append("  " + _v(b))
    elif not b.get("barreiras"):
        L.append("  Nada encontrado. Maquina sem barreiras conhecidas.")
    else:
        for item in b["barreiras"]:
            L.append("  [%s] %s" % (item["gravidade"].upper(), item["titulo"]))
            L.append("      achado: %s" % item["achado"])
            L.append("      o que fazer (%s): %s" % (item["quem"], item["acao"]))
    f = b.get("fatos", {}) if isinstance(b, dict) else {}
    if f:
        L.append("  (ligado ha %s h; %s programas instalados; %s na inicializacao; leitura em %s s)" % (
            f.get("ligado_ha_horas", "?"), f.get("programas_instalados", "?"),
            len([x for x in f.get("inicializacao") or [] if not x.get("desligado")]), b.get("segundos", "?")))
    if b.get("nao_deu_para_ler"):
        L.append("  nao deu para ler: %s" % "; ".join(b["nao_deu_para_ler"]))
    L.append("")
    L.append("Tempo da coleta: %s s" % dados["duracao_s"])
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------

def coletar(pasta=None):
    inicio = time.time()
    pasta = pasta_da_coleta(pasta)
    print("Retrato da maquina (%s)..." % os.path.basename(pasta), flush=True)
    dados = {"versao_coletor": VERSAO_COLETOR,
             "codigo_maquina": codigo_da_maquina(),
             "coletado_em": datetime.datetime.now().isoformat(timespec="seconds")}
    dados["processador"] = coletar_processador()
    dados["memoria"] = coletar_memoria()
    raiz_arena = os.path.splitdrive(RAIZ)[0] + "\\"
    raiz_windows = os.environ.get("SystemDrive", "C:") + "\\"
    dados["discos"] = [coletar_disco(raiz_arena, pasta, "onde esta o ARENA")]
    if raiz_windows.lower() != raiz_arena.lower():
        dados["discos"].append(coletar_disco(
            raiz_windows, os.environ.get("TEMP") or raiz_windows, "onde esta o Windows"))
    dados["video"] = coletar_video()
    dados["sistema"] = coletar_sistema()
    dados["rede"] = coletar_rede()
    dados["instalacao"] = coletar_instalacao()
    dados["barreiras"] = coletar_barreiras(dados)
    dados["duracao_s"] = round(time.time() - inicio, 1)

    with open(os.path.join(pasta, "maquina.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    texto = escrever_resumo(dados)
    with open(os.path.join(pasta, "maquina.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    return pasta, texto


if __name__ == "__main__":
    if not NO_WINDOWS:
        print("Este coletor e' para Windows.")
        sys.exit(1)
    pasta, texto = coletar(sys.argv[1] if len(sys.argv) > 1 else None)
    print()
    print(texto)
    print("Arquivos em: %s" % pasta)
