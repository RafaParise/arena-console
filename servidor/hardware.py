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


# Instrucoes do processador que decidem se um emulador ABRE. Codigos da
# funcao IsProcessorFeaturePresent, da documentacao da Microsoft (os mesmos
# do ferramentas\coletar_maquina.py). Sem AVX o Xenia (Xbox 360) fecha na
# hora -- a mensagem esta dentro do proprio xenia_canary.exe.
CODIGOS_INSTRUCOES = {"avx": 39, "avx2": 40}


def instrucoes():
    """{'avx': bool, 'avx2': bool}; None se nao der para perguntar."""
    if not sys.platform.startswith("win"):
        return {"avx": None, "avx2": None}
    resultado = {}
    for nome, codigo in CODIGOS_INSTRUCOES.items():
        try:
            resultado[nome] = bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(codigo))
        except Exception:
            resultado[nome] = None
    return resultado


# Velocidade de UM nucleo, MEDIDA -- nao adivinhada pela quantidade de
# nucleos. Achado de 30/09/2026: a nota antiga dava o mesmo 4 ao Celeron
# N5100 da escola e ao Ryzen 5 5600G do professor, e por isso chamava o PS2
# de "Capenga" nos dois (no Celeron otimizado ele roda com 4 jogadores).
#
# Unidade: quantas vezes o notebook-alvo (docs\MAQUINA-ALVO.md). 1,0 = a
# mesma velocidade dele; 2,0 = duas vezes mais rapido.
#
# PROVISORIO: o numero do alvo foi tirado do Ryzen (7,5 milhoes) vezes a
# proporcao do PassMark por nucleo (1.361 / 3.178 = 0,43). O COLETAR.bat
# passa a medir o valor de verdade no Celeron; ai este numero e' trocado.
OPERACOES_DO_NOTEBOOK_ALVO = 3_200_000
REFERENCIA_PROVISORIA = True


def _carga_de_medicao(tamanho):
    """Conta, tabela e texto: o que um programa Python faz o tempo todo.
    O resultado e' devolvido so para o trabalho nao ser jogado fora."""
    total = 0
    tabela = {}
    texto = ""
    for i in range(tamanho):
        total += (i * 7) ^ (i >> 3)
        tabela[i & 255] = total
        if i % 50 == 0:
            texto = str(total)[-6:]
    return total, len(tabela), texto


def velocidade_de_um_nucleo(rodadas=7, tamanho=60000):
    """Mede a velocidade de um nucleo (operacoes por segundo).

    Roda a mesma carga varias vezes e fica com a MAIS RAPIDA: as outras
    perderam tempo com o Windows atendendo outra coisa no meio. Assim o
    numero diz do que o processador e' capaz -- quanto o Windows esta
    pesando hoje e' outra pergunta, respondida pelas barreiras.
    No Ryzen leva uns 0,06 s; no Celeron, uns 0,15 s."""
    melhor = None
    for _ in range(rodadas):
        inicio = time.perf_counter()
        _carga_de_medicao(tamanho)
        gasto = time.perf_counter() - inicio
        if melhor is None or gasto < melhor:
            melhor = gasto
    operacoes = tamanho / max(melhor, 1e-6)
    return {"operacoes_por_segundo": int(operacoes),
            "relativa_ao_alvo": round(operacoes / OPERACOES_DO_NOTEBOOK_ALVO, 2),
            "referencia_provisoria": REFERENCIA_PROVISORIA}


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


# Divisas das classes de disco (MB/s de gravacao), as mesmas de disco().
DIVISAS_DISCO = (15.0, 45.0, 150.0)


def perto_da_divisa(mbs, margem=0.3):
    """A velocidade medida esta a menos de 30% de uma divisa de classe?"""
    return any(divisa * (1 - margem) <= mbs <= divisa * (1 + margem)
               for divisa in DIVISAS_DISCO)


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

    Agora: grava ate 8 MB em blocos de 1 MB, com o fsync na conta, e fica
    com a MELHOR amostra - a pior sempre e ruido de outro programa mexendo
    no disco. Disco lento para cedo (2 MB bastam), e so se repete a amostra
    quando ela cai perto de uma divisa de classe (perto_da_divisa).
    """
    caminho = os.path.join(pasta, ".arena_teste_velocidade")
    bloco = os.urandom(1024 * 1024)
    blocos = 8                       # ate 8 MB por amostra
    um_mb = 1024.0 * 1024.0

    melhor = None                    # (MB/s, segundos, MB) da melhor amostra
    melhor_leitura = None            # MB/s
    latencia = None

    try:
        for _tentativa in range(max(1, amostras)):
            # ---- escrita ----
            # O fsync ENTRA na conta de proposito. Sem ele mediriamos a
            # memoria do Windows, nao o disco: 8 MB cabem no cache e
            # qualquer pen drive pareceria rapidissimo. Com 8 MB o custo
            # fixo do fsync se dilui e sobra a velocidade de verdade.
            with open(caminho, "wb", buffering=0) as arquivo:
                inicio = time.perf_counter()
                escritos = 0
                for _ in range(blocos):
                    arquivo.write(bloco)
                    escritos += 1
                    # Disco lento: 2 MB em mais de 0,25 s ja dizem que e'
                    # lento. Gravar os 8 MB custava 1,6 s (e 8 MB do pen
                    # drive) a cada abertura num pen drive de 5 MB/s.
                    if escritos >= 2 and time.perf_counter() - inicio > 0.25:
                        break
                so_escrita = time.perf_counter() - inicio
                os.fsync(arquivo.fileno())
                escrita = time.perf_counter() - inicio
                espera = (escrita - so_escrita) * 1000
            megabytes = escritos * len(bloco) / um_mb
            mbs = megabytes / max(escrita, 1e-6)

            # ---- leitura ----
            inicio = time.perf_counter()
            with open(caminho, "rb", buffering=0) as arquivo:
                while arquivo.read(len(bloco)):
                    pass
            leitura = megabytes / max(time.perf_counter() - inicio, 1e-6)

            if melhor is None or mbs > melhor[0]:
                melhor, latencia = (mbs, escrita, megabytes), espera
            if melhor_leitura is None or leitura > melhor_leitura:
                melhor_leitura = leitura

            # Achado de 01/10/2026: aqui havia um "continue" onde o
            # comentario dizia "nao precisa insistir" -- o disco rapido
            # fazia as 3 amostras, e o pen drive comum (15 a 40 MB/s)
            # tambem: ate 24 MB gravados e mais de 1 s a cada abertura do
            # ARENA, so para medir. Agora a segunda e a terceira amostra so
            # acontecem quando a primeira cai PERTO de uma divisa de classe
            # (15, 45 ou 150 MB/s), onde o ruido poderia trocar a classe.
            if not perto_da_divisa(mbs):
                break
    except OSError:
        return None
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass

    return {
        "escrita_mbs": round(melhor[0], 1),
        "leitura_mbs": round(melhor_leitura, 1),
        "escrita_ms": round(melhor[1] * 1000, 1),
        "amostra_mb": round(melhor[2], 1),
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


def sistema_de_arquivos(pasta):
    """Nome do sistema de arquivos do disco onde 'pasta' esta (FAT32,
    exFAT, NTFS...), via GetVolumeInformationW -- so leitura, sem admin.

    Importa porque FAT32 nao aceita arquivo maior que 4 GB. Achado real
    na auditoria: este projeto tem jogos de PS2 reais passando disso
    (Gran Turismo 4, 4,95 GB) -- copiar um arquivo assim para um pen
    drive em FAT32 falha ou trunca no meio, sem o ARENA saber por que o
    jogo "nao abre". So funciona no Windows; None nos outros.
    """
    if not sys.platform.startswith("win"):
        return None
    try:
        raiz = os.path.splitdrive(os.path.abspath(pasta))[0] + "\\"
        nome_buffer = ctypes.create_unicode_buffer(256)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(raiz), None, 0, None, None, None,
            nome_buffer, ctypes.sizeof(nome_buffer))
        return nome_buffer.value if ok else None
    except Exception:
        return None


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


def placa_da_tela_principal():
    """Nome da placa de video que desenha a tela principal (ou "" se nao
    der para saber). Usa EnumDisplayDevicesW, da propria API do Windows."""
    try:
        import ctypes
        from ctypes import wintypes

        class DISPLAY_DEVICEW(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("DeviceName", wintypes.WCHAR * 32),
                        ("DeviceString", wintypes.WCHAR * 128),
                        ("StateFlags", wintypes.DWORD),
                        ("DeviceID", wintypes.WCHAR * 128),
                        ("DeviceKey", wintypes.WCHAR * 128)]

        LIGADA_NA_TELA, PRINCIPAL = 0x1, 0x4
        ligada = ""
        for indice in range(16):
            placa = DISPLAY_DEVICEW()
            placa.cb = ctypes.sizeof(placa)
            if not ctypes.windll.user32.EnumDisplayDevicesW(None, indice, ctypes.byref(placa), 0):
                break
            if placa.StateFlags & PRINCIPAL:
                return placa.DeviceString
            if placa.StateFlags & LIGADA_NA_TELA and not ligada:
                ligada = placa.DeviceString
        return ligada
    except (AttributeError, OSError, ValueError):
        return ""


def placa_video():
    """Descobre a placa de video e se ela e integrada ou dedicada.

    Por que isso importa, e por que a falta disso estragava tudo: um Ryzen
    5 5600G tem 12 nucleos e 11,8 GB de memoria, entao o ARENA dava nota 4
    e ligava resolucao quadruplicada no PSP. So que a placa dele e uma
    Radeon Vega INTEGRADA, que divide a memoria com o sistema. O resultado
    era jogo travando e som picotando - o processador dava conta, a placa
    nao.

    Pergunta primeiro ao Windows qual placa esta LIGADA NA TELA PRINCIPAL.
    O registro sozinho engana: ele guarda placas que ja sairam da maquina.
    Achado real (25/09/2026): o registro desta maquina de desenvolvimento
    lista primeiro uma "NVIDIA GeForce 210" antiga; a tela esta na Radeon
    integrada. O ARENA achava que era placa dedicada, dava nota 4 e o PS1
    ia para 6x -- o texto do CTR saia quebrado. Sem administrador.
    """
    nome = placa_da_tela_principal() if sys.platform.startswith("win") else ""
    if not nome and sys.platform.startswith("win"):
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


# Pergunta ao Vulkan, num processo SEPARADO, quantas placas ele enxerga.
# Por que (achado de 01/10/2026): driver_video() escolhe Vulkan so porque o
# vulkan-1.dll CARREGA -- e esse arquivo pode ter sobrado de outra placa (o
# registro do PC do Rafael ainda lembra de uma GeForce 210 que ja saiu).
# Vulkan sem placa = jogo que abre e fecha na hora. Processo separado porque
# driver de video velho pode derrubar quem pergunta: cai o ajudante, nao o
# ARENA. Custa ~0,2 s (Ryzen, frio), por isso roda depois que a tela abriu.
_PERGUNTA_VULKAN = r"""
import ctypes
class Info(ctypes.Structure):
    _fields_ = [("sType", ctypes.c_int), ("pNext", ctypes.c_void_p), ("flags", ctypes.c_uint32),
                ("pApplicationInfo", ctypes.c_void_p), ("enabledLayerCount", ctypes.c_uint32),
                ("ppEnabledLayerNames", ctypes.c_void_p), ("enabledExtensionCount", ctypes.c_uint32),
                ("ppEnabledExtensionNames", ctypes.c_void_p)]
vk = ctypes.WinDLL("vulkan-1.dll")
vk.vkCreateInstance.argtypes = [ctypes.POINTER(Info), ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
vk.vkEnumeratePhysicalDevices.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
vk.vkDestroyInstance.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
inst = ctypes.c_void_p()
n = ctypes.c_uint32(0)
if vk.vkCreateInstance(ctypes.byref(Info(sType=1)), None, ctypes.byref(inst)) == 0:
    vk.vkEnumeratePhysicalDevices(inst, ctypes.byref(n), None)
    vk.vkDestroyInstance(inst, None)
print("placas=%d" % n.value)
"""


def vulkan_tem_placa(limite=10):
    """True/False: o Vulkan enxerga alguma placa de video? None = nao deu
    para saber (sem Windows, demorou demais) -- quem chama nao muda nada."""
    if not sys.platform.startswith("win"):
        return None
    try:
        import subprocess
        r = subprocess.run([sys.executable, "-c", _PERGUNTA_VULKAN], capture_output=True,
                           text=True, timeout=limite,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:          # nao abriu, demorou demais (TimeoutExpired)...
        return None
    saida = (r.stdout or "").strip()
    if saida.startswith("placas="):
        try:
            return int(saida.split("=", 1)[1]) > 0
        except ValueError:
            return None
    # Sem resposta: o ajudante caiu dentro do driver (codigo de erro do
    # Windows) -- Vulkan nao serve nesta maquina.
    return False if r.returncode != 0 else None


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

def altura_da_tela():
    """Linhas da tela principal em pixels de verdade -- 768, 1080, 2160 --,
    sem a escala de 150% ou 200% do Windows. 0 se nao der para saber.

    Serve para o degrau "tela 4K" das opcoes de imagem (graficos.json ->
    tela_4k). DESKTOPVERTRES (117) do GetDeviceCaps nao depende da escala
    do Windows. Os tipos vao declarados (a alca de 64 bits cortada pela
    metade ja foi bug aqui: SetPriorityClass sem tipos), numa copia propria
    da user32 para nao mexer em quem mais usa a mesma funcao."""
    if os.name != "nt":
        return 0
    try:
        usuario, gdi = ctypes.WinDLL("user32"), ctypes.WinDLL("gdi32")
        usuario.GetDC.restype = ctypes.c_void_p
        usuario.GetDC.argtypes = [ctypes.c_void_p]
        usuario.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
        dc = usuario.GetDC(None)
        if not dc:
            return 0
        try:
            return max(0, int(gdi.GetDeviceCaps(dc, 117)))
        finally:
            usuario.ReleaseDC(None, dc)
    except (OSError, AttributeError, ValueError):
        return 0


def resumo(pasta_raiz):
    """Junta tudo num dicionario so, pronto para a tela."""
    ram = memoria()
    info_disco = disco(pasta_raiz)
    total_nucleos = nucleos()

    gpu = placa_video()
    return {
        "cpu": processador(),
        "gpu": gpu,
        "instrucoes": instrucoes(),
        "velocidade": velocidade_de_um_nucleo(),
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
