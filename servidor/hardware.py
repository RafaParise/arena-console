# -*- coding: utf-8 -*-
"""
ARENA - Identificacao da maquina
=================================
Descobre processador, memoria, tipo de disco e sistema operacional.

Tudo pela biblioteca padrao e pelas APIs do proprio Windows. Nada de
'pip install', nada de programa externo, nada de 'wmic' (que foi removido
das versoes recentes do Windows).
"""

import ctypes
import os
import platform
import socket
import sys
import time


# ---------------------------------------------------------------------------
# Memoria RAM
# ---------------------------------------------------------------------------

class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def memoria():
    """Devolve total e livre de RAM em GB."""
    try:
        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return {
            "total_gb": round(status.ullTotalPhys / (1024 ** 3), 1),
            "livre_gb": round(status.ullAvailPhys / (1024 ** 3), 1),
        }
    except Exception:
        return {"total_gb": 4.0, "livre_gb": 1.0}


# ---------------------------------------------------------------------------
# Processador
# ---------------------------------------------------------------------------

def processador():
    """Nome comercial do processador.

    Le direto do registro do Windows, onde a propria BIOS gravou o nome.
    E instantaneo e nao depende de programa externo.
    """
    nome = ""
    if sys.platform.startswith("win"):
        try:
            import winreg
            chave = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            nome = winreg.QueryValueEx(chave, "ProcessorNameString")[0].strip()
            winreg.CloseKey(chave)
        except Exception:
            nome = ""

    if not nome:
        nome = platform.processor() or "Processador desconhecido"

    # O nome vem cheio de espacos duplos e sufixos inuteis.
    nome = " ".join(nome.split())
    for lixo in (" CPU", "(R)", "(TM)", "(r)", "(tm)"):
        nome = nome.replace(lixo, "")
    return " ".join(nome.split())


def nucleos():
    """Nucleos logicos. E o numero que importa para decidir o perfil."""
    return os.cpu_count() or 2


# ---------------------------------------------------------------------------
# Disco
# ---------------------------------------------------------------------------

TIPOS_DISCO = {
    0: "desconhecido",
    1: "inexistente",
    2: "removivel",
    3: "fixo",
    4: "rede",
    5: "CD",
    6: "memoria",
}


def medir_velocidade(pasta, amostras=3):
    """Mede a velocidade real de escrita e leitura na pasta do ARENA.

    A versao anterior errava feio: media UMA amostra de 1 MB e incluia o
    fsync no cronometro. Dois problemas com isso no Windows:

      1. fsync nao e velocidade, e uma barreira. Ele manda o disco parar
         tudo e confirmar a gravacao. Um NVMe rapidissimo pode levar 200 ms
         nessa confirmacao e ainda assim gravar a 3 GB/s.
      2. Criar um arquivo novo acorda o antivirus. O Defender varre o
         arquivo no fechamento, e isso entra na conta. Estavamos medindo o
         antivirus, nao o disco.

    Agora: grava 2 MB em blocos, cronometra SO a gravacao, faz o fsync
    depois e cronometra separado. Repete algumas vezes e fica com a MELHOR
    amostra - a pior sempre e ruido de outro programa mexendo no disco.
    """
    caminho = os.path.join(pasta, ".arena_teste_velocidade")
    bloco = os.urandom(1024 * 1024)
    blocos = 8                       # 8 MB por amostra
    megabytes = (len(bloco) * blocos) / (1024.0 * 1024.0)

    melhor_escrita = melhor_leitura = None
    latencia = None

    try:
        for tentativa in range(max(1, amostras)):
            # ---- escrita ----
            # O fsync ENTRA na conta de proposito. Sem ele mediriamos a
            # memoria do Windows, nao o disco: 8 MB cabem no cache e
            # qualquer pen drive pareceria rapidissimo. Com 8 MB o custo
            # fixo do fsync se dilui e sobra a velocidade de verdade.
            with open(caminho, "wb", buffering=0) as arquivo:
                inicio = time.perf_counter()
                for _ in range(blocos):
                    arquivo.write(bloco)
                so_escrita = time.perf_counter() - inicio
                os.fsync(arquivo.fileno())
                escrita = time.perf_counter() - inicio
                espera = (escrita - so_escrita) * 1000

            # ---- leitura ----
            inicio = time.perf_counter()
            with open(caminho, "rb", buffering=0) as arquivo:
                while arquivo.read(len(bloco)):
                    pass
            leitura = time.perf_counter() - inicio

            if melhor_escrita is None or escrita < melhor_escrita:
                melhor_escrita, latencia = escrita, espera
            if melhor_leitura is None or leitura < melhor_leitura:
                melhor_leitura = leitura

            # Ja ficou claro que e rapido: nao precisa insistir.
            if tentativa == 0 and escrita < 0.08:
                continue
            # Ja ficou claro que e lento: parar poupa o pen drive.
            if escrita > 1.2:
                break
    except OSError:
        return None
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass

    return {
        "escrita_mbs": round(megabytes / max(melhor_escrita, 1e-6), 1),
        "leitura_mbs": round(megabytes / max(melhor_leitura, 1e-6), 1),
        "escrita_ms": round(melhor_escrita * 1000, 1),
        # Quanto o disco demora para CONFIRMAR uma gravacao. Alto aqui com
        # velocidade alta acima e normal: e barreira, nao lentidao.
        "confirmacao_ms": round(latencia, 1) if latencia is not None else None,
    }


def disco(pasta):
    """Tipo, velocidade e espaco do disco onde o ARENA esta rodando."""
    tipo = "desconhecido"
    unidade = ""

    if sys.platform.startswith("win"):
        try:
            unidade = os.path.splitdrive(os.path.abspath(pasta))[0]
            codigo = ctypes.windll.kernel32.GetDriveTypeW(unidade + "\\")
            tipo = TIPOS_DISCO.get(codigo, "desconhecido")
        except Exception:
            pass

    medida = medir_velocidade(pasta)

    # Classificacao por VELOCIDADE, em MB/s. A versao anterior classificava
    # por tempo total incluindo o fsync, e por isso chamava um NVMe de
    # "disco lento".
    if medida is None:
        classe, mbs = "nao medido", None
    else:
        mbs = medida["escrita_mbs"]
        if mbs >= 150:
            classe = "muito_rapido"
        elif mbs >= 45:
            classe = "rapido"
        elif mbs >= 15:
            classe = "medio"
        else:
            classe = "lento"

    livre_gb = total_gb = usado_pct = None
    try:
        import shutil
        uso = shutil.disk_usage(pasta)
        livre_gb = round(uso.free / (1024 ** 3), 1)
        total_gb = round(uso.total / (1024 ** 3), 1)
        usado_pct = round(100.0 * (uso.total - uso.free) / max(uso.total, 1))
    except Exception:
        pass

    # Texto da tela. Nunca dizer "pen drive" quando o Windows informou que
    # o disco e fixo: era isso que fazia um SSD interno parecer removivel.
    NOMES = {
        "muito_rapido": "SSD rapido (NVMe)",
        "rapido": "SSD",
        "medio": "Disco intermediario",
        "lento": "Disco lento",
        "nao medido": "Disco",
    }
    if tipo == "removivel":
        descricao = {
            "muito_rapido": "Midia removivel rapida",
            "rapido": "Midia removivel rapida",
            "medio": "Pen drive ou cartao",
            "lento": "Pen drive lento",
        }.get(classe, "Midia removivel")
    elif tipo == "rede":
        descricao = "Unidade de rede"
    else:
        descricao = NOMES.get(classe, "Disco")

    if mbs:
        descricao += " (%s MB/s)" % (int(mbs) if mbs >= 10 else mbs)

    return {
        "unidade": unidade or "-",
        "tipo": tipo,
        "removivel": tipo == "removivel",
        "classe": classe,
        "escrita_mbs": mbs,
        "leitura_mbs": medida["leitura_mbs"] if medida else None,
        "confirmacao_ms": medida["confirmacao_ms"] if medida else None,
        "livre_gb": livre_gb,
        "total_gb": total_gb,
        "usado_pct": usado_pct,
        "descricao": descricao,
        # Quantos save states de PlayStation cabem no espaco livre. Numero
        # concreto vale mais que "12,4 GB livres" para quem nunca pensou
        # em tamanho de arquivo.
        "cabem_states": int(livre_gb * 1024 / 1.2) if livre_gb else None,
    }


def shutil_disk_usage(pasta):
    import shutil
    return shutil.disk_usage(pasta).free


# ---------------------------------------------------------------------------
# Sistema operacional
# ---------------------------------------------------------------------------

def sistema():
    """Nome do sistema operacional, do jeito que o usuario reconhece."""
    if not sys.platform.startswith("win"):
        return "%s %s" % (platform.system(), platform.release())

    nome, build = "", ""
    try:
        import winreg
        chave = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        nome = winreg.QueryValueEx(chave, "ProductName")[0]
        try:
            build = winreg.QueryValueEx(chave, "CurrentBuildNumber")[0]
        except OSError:
            build = ""
        winreg.CloseKey(chave)
    except Exception:
        nome = "Windows %s" % platform.release()

    # O registro continua dizendo "Windows 10" no Windows 11. A build
    # 22000 em diante e Windows 11.
    try:
        if build and int(build) >= 22000 and "10" in nome:
            nome = nome.replace("10", "11")
    except ValueError:
        pass

    arquitetura = "64 bits" if sys.maxsize > 2 ** 32 else "32 bits"
    return "%s (%s)" % (" ".join(nome.split()), arquitetura)


# Marcas de placa de video integrada. Ela divide a memoria com o sistema e
# tem uma fracao do poder de uma placa dedicada - mesmo num processador bom.
INTEGRADAS = (
    "radeon(tm) graphics", "radeon graphics", "vega", "radeon(tm) vega",
    "intel(r) uhd", "intel(r) hd", "intel(r) iris", "intel uhd", "intel hd",
    "microsoft basic", "amd radeon(tm) r", "gpu integrada",
)


def identidade_da_maquina():
    """Um codigo que muda de computador para computador, sempre o mesmo
    no mesmo computador.

    Por que existe: quando o professor copia a pasta do ARENA para trinta
    pen drives, o config.json vai junto - e com ele o codigo do aparelho.
    Trinta ARENAs com o mesmo codigo quebram tudo: cada um acha que o
    outro e ele mesmo, a sincronizacao para e a partida a dois recusa a
    conexao.

    Aqui o codigo nasce do proprio computador: nome da maquina, usuario e
    endereco fisico da placa de rede. Copiou a pasta? O codigo continua
    diferente, porque a maquina e outra.
    """
    import hashlib
    import uuid as _uuid

    pedacos = []
    try:
        pedacos.append(socket.gethostname())
    except Exception:
        pass
    for variavel in ("USERNAME", "USER", "COMPUTERNAME"):
        valor = os.environ.get(variavel)
        if valor:
            pedacos.append(valor)
    try:
        # getnode devolve o endereco fisico da placa de rede. Quando nao
        # consegue ler, ele inventa um numero - e ai nao serve, entao o
        # bit 41 avisa que foi inventado.
        no = _uuid.getnode()
        if not (no >> 40) % 2:
            pedacos.append("%012x" % no)
    except Exception:
        pass

    if not pedacos:
        return None

    return hashlib.sha1("|".join(pedacos).encode("utf-8")).hexdigest()[:12]


def placa_video():
    """Descobre a placa de video e se ela e integrada ou dedicada.

    Por que isso importa, e por que a falta disso estragava tudo: um Ryzen
    5 5600G tem 12 nucleos e 11,8 GB de memoria, entao o ARENA dava nota 4
    e ligava resolucao quadruplicada no PSP. So que a placa dele e uma
    Radeon Vega INTEGRADA, que divide a memoria com o sistema. O resultado
    era jogo travando e som picotando - o processador dava conta, a placa
    nao.

    Le do registro do Windows, sem programa externo e sem administrador.
    """
    nome = ""
    if sys.platform.startswith("win"):
        try:
            import winreg
            base = (r"SYSTEM\CurrentControlSet\Control\Class"
                    r"\{4d36e968-e325-11ce-bfc1-08002be10318}")
            chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
            for indice in range(8):
                try:
                    sub = winreg.OpenKey(chave, "%04d" % indice)
                    candidato = winreg.QueryValueEx(sub, "DriverDesc")[0]
                    winreg.CloseKey(sub)
                except OSError:
                    continue
                # Fica com a primeira que nao seja adaptador generico.
                if candidato and "basic" not in candidato.lower():
                    nome = candidato
                    break
                nome = nome or candidato
            winreg.CloseKey(chave)
        except Exception:
            nome = ""

    limpo = " ".join((nome or "").split())
    minusculo = limpo.lower()
    integrada = any(marca in minusculo for marca in INTEGRADAS) if limpo else True

    return {
        "nome": limpo or "placa de video desconhecida",
        "integrada": integrada,
        # Sem saber qual e, o ARENA assume integrada. Errar para baixo faz
        # o jogo rodar liso; errar para cima faz ele travar.
        "conhecida": bool(limpo),
    }


def driver_video():
    """Melhor motor grafico realmente disponivel nesta maquina.

    Ordem: vulkan, d3d11, glcore. O teste e carregar a biblioteca do
    sistema: se 'vulkan-1.dll' carrega, existe driver Vulkan instalado.

    Placas Intel HD anteriores a 2015 nao tem Vulkan. Forcar Vulkan nelas
    faz o RetroArch abrir e fechar na hora, sem mensagem nenhuma.
    """
    for biblioteca, motor in (("vulkan-1.dll", "vulkan"), ("d3d11.dll", "d3d11")):
        try:
            ctypes.CDLL(biblioteca)
            return motor
        except OSError:
            continue
    return "glcore"


def runtime_visual_c():
    """Confere se o Visual C++ Runtime esta presente.

    O RetroArch e os nucleos sao compilados com ele. Sem essa biblioteca,
    o emulador nem abre - e a mensagem de erro do Windows nao ajuda nada.
    Melhor detectar aqui e avisar com clareza.
    """
    if not sys.platform.startswith("win"):
        return True
    for biblioteca in ("vcruntime140.dll", "msvcp140.dll"):
        try:
            ctypes.CDLL(biblioteca)
        except OSError:
            return False
    return True


# ---------------------------------------------------------------------------
# Resumo completo
# ---------------------------------------------------------------------------

def resumo(pasta_raiz):
    """Junta tudo num dicionario so, pronto para a tela."""
    ram = memoria()
    info_disco = disco(pasta_raiz)
    total_nucleos = nucleos()

    gpu = placa_video()
    return {
        "cpu": processador(),
        "gpu": gpu,
        "nucleos": total_nucleos,
        "ram_total_gb": ram["total_gb"],
        "ram_livre_gb": ram["livre_gb"],
        "disco": info_disco,
        "sistema": sistema(),
        "driver_video": driver_video(),
        "runtime_ok": runtime_visual_c(),
        "removivel": info_disco["removivel"],
        # Perfil: define quais plataformas aparecem na lista.
        "perfil_maquina": ("completo"
                           if (total_nucleos >= 4 and ram["total_gb"] >= 6)
                           else "leve"),
    }


# ---------------------------------------------------------------------------
# Capacidade da maquina
# ---------------------------------------------------------------------------
# Uma nota de 1 a 5 que resume o que este computador aguenta. E comparada
# com o 'custo' de cada plataforma (tambem de 1 a 5) para dizer quais
# consoles vao rodar bem aqui.

def capacidade(info=None, pasta_raiz=None):
    """Nota de 1 a 5 para o conjunto processador + memoria + video + disco."""
    if info is None:
        info = resumo(pasta_raiz or os.getcwd())

    pontos = 0

    # Processador: o que mais pesa na emulacao.
    n = info["nucleos"]
    pontos += 1 if n <= 2 else 2 if n == 3 else 3 if n <= 7 else 4

    # Memoria.
    ram = info["ram_total_gb"]
    pontos += 0 if ram < 4 else 1 if ram < 6 else 2 if ram < 8 else 3 if ram < 16 else 4

    # Motor grafico: Vulkan e D3D11 tiram trabalho do processador.
    pontos += 1 if info["driver_video"] in ("vulkan", "d3d11") else 0

    # Disco: pesa pouco no jogo em si, mas muito no save state e no
    # carregamento de jogo em CD.
    classe = info["disco"]["classe"]
    pontos += (1 if classe in ("muito_rapido", "rapido")
               else 0 if classe in ("medio", "nao medido") else -1)

    # 0..10 vira 1..5
    nota = max(1, min(5, round(pontos / 2.0)))

    # Nota separada para o que depende da PLACA DE VIDEO: resolucao
    # interna, filtro de textura, anti-serrilhado. Placa integrada nao
    # passa de 3, por melhor que seja o processador.
    gpu = info.get("gpu", {})
    if gpu.get("integrada", True):
        nota_gpu = min(nota, 3)
    else:
        nota_gpu = nota

    return {"nota": nota, "nota_gpu": nota_gpu, "pontos": pontos,
            "gpu_integrada": bool(gpu.get("integrada", True))}
