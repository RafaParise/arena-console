# -*- coding: utf-8 -*-
r"""
ARENA - o celular ligado no cabo, visto pelo computador.

ETAPA 1 do roteiro de 23/10/2026 (docs\PLANO-CELULAR.md). Pedido do Rafael:
"o arena deve mostrar o hardware completo do android para o aluno saber tudo
do celular dele, ate os miliamperes da bateria [...] e se um dia trocar a
bateria poder saber a capacidade dele".

O aluno liga o celular no computador pelo cabo USB (com a Depuracao USB
ligada) e o ARENA mostra, em Ajustes -> Maquina, o hardware dele: modelo,
Android, processador, placa de video, memoria, armazenamento, tela e bateria.
So LEITURA: nada e' instalado, nada muda no celular e nada do que se le vai
para arquivo (o numero de serie do celular so existe na memoria, durante o
pedido).

COMO: o ADB oficial do Google (Platform Tools). Ele NAO vai no pacote do ARENA
(e' do Google): o ARENA o procura nestes lugares, nesta ordem --
  1. a variavel ARENA_ADB (o caminho do adb);
  2. a pasta platform-tools dentro da pasta do ARENA (e' so descompactar la);
  3. o SDK de testes do ARENA (%LOCALAPPDATA%\ARENA-android\sdk);
  4. o Android SDK do computador (ANDROID_HOME / ANDROID_SDK_ROOT);
  5. o PATH.

O QUE O APARELHO ENTREGA (medido no Galaxy A12, Android 12): o shell do ADB
NAO le /sys/class/power_supply/battery/* ("Permission denied", sem root), entao
o charge_full_design quase nunca aparece. O que vale e' o "dumpsys battery"
(nivel, voltagem, temperatura, saude e o contador de carga, em uAh) e o
"dumpsys batterystats" (a capacidade que o perfil de energia do proprio
Android declara, em mAh). O painel diz de onde veio cada numero e escreve
"indisponivel neste aparelho" no que nao veio: nunca inventa valor.

Cada leitura e' independente: se uma falha, as outras aparecem e a que falhou
vai em "falhas". O programa tambem roda sozinho, para testar sem a tela:
    servidor\python\python.exe servidor\adb_aparelho.py [numero de serie]
"""
import contextlib
import os
import re
import shutil
import socket
import subprocess
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME_DO_ADB = "adb.exe" if os.name == "nt" else "adb"
TEMPO_DO_ADB = 15            # segundos: devices, kill-server
TEMPO_DA_LEITURA = 30        # segundos: a leitura inteira do celular
LIMITE_DA_SAIDA = 4 * 1024 * 1024   # o que vem do celular e' dado de fora: nunca confiar no tamanho

# Uma conversa com o adb por vez (duas ao mesmo tempo se atropelariam ao ligar
# e desligar o servidor do adb).
TRAVA_ADB = threading.Lock()

COMO_BAIXAR_O_ADB = (
    "O ARENA usa o ADB, a ferramenta oficial do Google para falar com o celular pelo cabo. Ela não vai "
    "junto com o ARENA (é do Google). Para pôr: baixe o \"SDK Platform-Tools\" do seu sistema em "
    "developer.android.com/tools/releases/platform-tools, descompacte e deixe a pasta \"platform-tools\" "
    "dentro da pasta do ARENA (ao lado da pasta \"servidor\"). Depois, clique em Procurar de novo.")

COMO_LIGAR_O_CELULAR = (
    "No celular: Configurações → Sobre o telefone → Informações do software, e toque 7 vezes em \"Número "
    "da versão\" (ou \"Número de compilação\"). Volte, abra \"Opções do desenvolvedor\" e ligue \"Depuração "
    "USB\". Ligue o cabo no computador e, na tela do celular, toque em Permitir na pergunta \"Permitir "
    "depuração USB?\" (marque \"Sempre permitir\"). Depois, clique em Procurar de novo.")

# estado do "adb devices" -> (pronto para ler?, o que dizer ao aluno)
ESTADOS = {
    "device": (True, "pronto"),
    "unauthorized": (False, "Olhe a tela do celular e toque em Permitir na pergunta \"Permitir depuração "
                            "USB?\" (marque \"Sempre permitir\"). Depois, clique em Procurar de novo."),
    "authorizing": (False, "Esperando você permitir no celular. Clique em Procurar de novo depois."),
    "offline": (False, "O celular não está respondendo. Tire o cabo, ponha de novo, destrave a tela do "
                       "celular e clique em Procurar de novo."),
    "connecting": (False, "Ainda conectando. Espere uns segundos e clique em Procurar de novo."),
    "no permissions": (False, "O computador não tem permissão para falar com o celular (no Linux, falta a "
                              "regra udev do Android). Peça ajuda ao professor."),
}
# Estados que o adb mostra e que o ARENA nao le (o celular nao esta ligado "normal").
ESTADOS_QUE_NAO_SE_LE = ("recovery", "sideload", "bootloader", "host", "rescue")

# Os códigos do "CPU part" que o Linux conhece (arch/arm64/include/asm/cputype.h,
# conferido em 23/10/2026) e, nos celulares de 32 bits, do arch/arm. Nucleo que
# nao esta aqui aparece pelo codigo, nunca com um nome chutado.
NUCLEOS_ARM = {
    "0xd03": "Cortex-A53", "0xd04": "Cortex-A35", "0xd05": "Cortex-A55", "0xd07": "Cortex-A57",
    "0xd08": "Cortex-A72", "0xd09": "Cortex-A73", "0xd0a": "Cortex-A75", "0xd0b": "Cortex-A76",
    "0xd0d": "Cortex-A77", "0xd41": "Cortex-A78", "0xd44": "Cortex-X1", "0xd46": "Cortex-A510",
    "0xd47": "Cortex-A710", "0xd48": "Cortex-X2", "0xd4d": "Cortex-A715", "0xd4e": "Cortex-X3",
    "0xd80": "Cortex-A520", "0xd81": "Cortex-A720", "0xd82": "Cortex-X4", "0xd85": "Cortex-X925",
    "0xd87": "Cortex-A725",
    "0xc05": "Cortex-A5", "0xc07": "Cortex-A7", "0xc08": "Cortex-A8", "0xc09": "Cortex-A9",
    "0xc0d": "Cortex-A12", "0xc0e": "Cortex-A17", "0xc0f": "Cortex-A15",
}
FABRICANTES_DE_NUCLEO = {"0x41": "Arm", "0x42": "Broadcom", "0x43": "Cavium", "0x46": "Fujitsu",
                         "0x48": "HiSilicon", "0x4e": "NVIDIA", "0x50": "APM", "0x51": "Qualcomm",
                         "0x61": "Apple", "0x6d": "Microsoft", "0xc0": "Ampere"}

# battery health do Android (BatteryManager.BATTERY_HEALTH_*)
SAUDE_DA_BATERIA = {1: "desconhecida", 2: "boa", 3: "esquentando demais", 4: "gasta (já não segura carga)",
                    5: "voltagem alta demais", 6: "com defeito", 7: "fria demais"}

# O que o celular recebe para ler (um unico "adb shell", uma ida so). Cada bloco
# comeca com @@nome e o programa separa por ele. </dev/null: o comando nao pode
# engolir o resto do roteiro, que chega pela mesma entrada.
SCRIPT_DE_LEITURA = r"""
echo @@props
getprop </dev/null
echo @@meminfo
cat /proc/meminfo
echo @@cpuinfo
cat /proc/cpuinfo
echo @@freq
for f in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/cpuinfo_max_freq; do echo "$f $(cat $f 2>/dev/null)"; done
echo @@bateria
dumpsys battery </dev/null
echo @@capacidade
timeout 10 dumpsys batterystats </dev/null 2>/dev/null | grep -iE "capacity" | head -n 8
echo @@sys
for n in $(ls /sys/class/power_supply 2>/dev/null | head -n 12); do
  for f in charge_counter charge_full_design charge_full energy_full_design capacity cycle_count; do
    p=/sys/class/power_supply/$n/$f
    echo "$p|$(cat $p 2>&1 </dev/null | head -n 1)"
  done
done
echo @@tela
wm size </dev/null
wm density </dev/null
dumpsys display </dev/null 2>/dev/null | grep -m1 -oE "fps=[0-9.]+"
echo @@disco
df -k /data </dev/null
echo @@kernel
uname -r
cat /proc/uptime
echo @@gpu
dumpsys SurfaceFlinger </dev/null 2>/dev/null | grep -m1 "GLES:"
echo @@recursos
pm list features </dev/null 2>/dev/null | grep -E "gyroscope|accelerometer|usb.host|bluetooth|vulkan|opengles|multitouch"
echo @@fim
"""

PROPRIEDADES = (
    "ro.product.model", "ro.product.manufacturer", "ro.product.device", "ro.build.version.release",
    "ro.build.version.sdk", "ro.build.version.security_patch", "ro.build.display.id", "ro.hardware",
    "ro.board.platform", "ro.soc.model", "ro.soc.manufacturer", "ro.product.cpu.abilist",
    "ro.product.cpu.abilist64", "ro.opengles.version",
)

PADRAO_DE_SERIAL = re.compile(r"^[A-Za-z0-9\[][A-Za-z0-9._:\-\[\]]{0,127}$")


class FalhaDoAdb(Exception):
    """Algo que o aluno precisa saber, ja em portugues."""


# ---------------------------------------------------------------------------
# O adb: achar, rodar, e nao deixar o servidor dele de pe sem ter sido chamado
# ---------------------------------------------------------------------------

def candidatos():
    """[(de onde vem, caminho)] na ordem em que o ARENA procura o adb."""
    lista = []
    do_ambiente = os.environ.get("ARENA_ADB", "").strip()
    if do_ambiente:
        lista.append(("a variável ARENA_ADB", do_ambiente))
    lista.append(("a pasta platform-tools do ARENA", os.path.join(RAIZ, "platform-tools", NOME_DO_ADB)))
    local = os.environ.get("LOCALAPPDATA", "").strip()
    if local:
        lista.append(("o SDK de testes do ARENA", os.path.join(local, "ARENA-android", "sdk", "platform-tools",
                                                                NOME_DO_ADB)))
    for variavel in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        sdk = os.environ.get(variavel, "").strip()
        if sdk:
            lista.append(("o Android SDK deste computador", os.path.join(sdk, "platform-tools", NOME_DO_ADB)))
    no_path = shutil.which("adb")
    if no_path:
        lista.append(("o adb deste computador (PATH)", no_path))
    return lista


def achar_adb():
    """(caminho, de onde veio) do primeiro adb que existe, ou (None, None)."""
    for origem, caminho in candidatos():
        if os.path.isfile(caminho):
            return caminho, origem
    return None, None


def executar(adb, argumentos, entrada=None, tempo=TEMPO_DO_ADB):
    """Roda o adb. Devolve (codigo, texto) com a saida e os erros juntos, em
    UTF-8. OSError se o adb nao abre; TimeoutError se passa de 'tempo' segundos."""
    try:
        feito = subprocess.run([adb] + list(argumentos), input=entrada,
                               stdin=subprocess.DEVNULL if entrada is None else None,
                               capture_output=True, timeout=tempo,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise TimeoutError("o adb passou de %d segundos sem responder" % tempo) from None
    texto = ((feito.stdout or b"") + (feito.stderr or b"")).decode("utf-8", errors="replace")
    return feito.returncode, texto.replace("\r\n", "\n")


def servidor_do_adb_de_pe():
    """O servidor do adb (um programa que fica de fundo, na porta 5037) ja esta
    ligado? Quem o liga e' o primeiro comando do adb."""
    try:
        porta = int(os.environ.get("ANDROID_ADB_SERVER_PORT", "5037"))
    except ValueError:
        porta = 5037
    try:
        with socket.create_connection(("127.0.0.1", porta), timeout=0.5):
            return True
    except OSError:
        return False


@contextlib.contextmanager
def sessao(adb):
    """Uma conversa com o adb. So uma por vez. Se o servidor do adb nao estava
    ligado quando ela comecou, ela o desliga no fim: o ADB no pen drive deixaria
    um programa de fundo segurando a pasta, e o pen drive nao sairia limpo. Se
    ja estava ligado (o aluno usa o adb por conta propria), ninguem mexe nele."""
    with TRAVA_ADB:
        estava_de_pe = servidor_do_adb_de_pe()
        try:
            yield
        finally:
            if not estava_de_pe and servidor_do_adb_de_pe():
                try:
                    executar(adb, ["kill-server"], tempo=TEMPO_DO_ADB)
                except (OSError, TimeoutError):
                    pass


def interpretar_lista(texto):
    """Os celulares da saida de "adb devices -l". Cada um: serial, estado,
    pronto (pode ler?), estado_texto, modelo, por_wifi."""
    aparelhos = []
    for linha in str(texto)[:LIMITE_DA_SAIDA].splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("*") or linha.lower().startswith("list of devices"):
            continue
        partes = linha.split()
        if len(partes) < 2 or not PADRAO_DE_SERIAL.match(partes[0]):
            continue
        serial, estado = partes[0], partes[1]
        if estado == "no" and len(partes) > 2 and partes[2].startswith("permissions"):
            estado = "no permissions"
        # A saida do adb mistura a lista com recados e erros ("error: ...", "adb server version
        # ... doesn't match"): so vale linha cujo estado e' um dos que o adb usa de verdade.
        if estado not in ESTADOS and estado not in ESTADOS_QUE_NAO_SE_LE:
            continue
        extras = dict(p.split(":", 1) for p in partes[2:] if ":" in p and not p.startswith("("))
        pronto, dizer = ESTADOS.get(estado, (False, "O celular está num modo que o ARENA não lê (%s). Ligue-o "
                                                    "normalmente e clique em Procurar de novo." % estado))
        aparelhos.append({
            "serial": serial,
            "serial_curto": ("…" + serial[-4:]) if len(serial) > 6 else serial,
            "estado": estado,
            "pronto": pronto,
            "estado_texto": dizer,
            "modelo": extras.get("model", "").replace("_", " "),
            "por_wifi": ":" in serial or "_adb-tls" in serial,
        })
    return aparelhos


# ---------------------------------------------------------------------------
# Ler o que o celular respondeu: cada pedaco no seu canto (isolamento de falhas)
# ---------------------------------------------------------------------------

def inteiro(texto, padrao=None):
    try:
        return int(str(texto).strip())
    except (TypeError, ValueError):
        return padrao


def decimal(texto, padrao=None):
    try:
        return float(str(texto).strip())
    except (TypeError, ValueError):
        return padrao


def dividir_em_secoes(texto):
    """{nome: texto} a partir dos marcadores @@nome do SCRIPT_DE_LEITURA."""
    secoes, atual = {}, None
    for linha in str(texto)[:LIMITE_DA_SAIDA].splitlines():
        if linha.startswith("@@"):
            atual = linha[2:].strip()
            secoes[atual] = []
        elif atual is not None:
            secoes[atual].append(linha)
    return {nome: "\n".join(linhas) for nome, linhas in secoes.items()}


def ler_props(texto):
    """So as propriedades que o painel usa (o getprop inteiro tem coisa do
    aparelho que nao interessa e nunca e' guardado)."""
    props = {}
    for linha in texto.splitlines():
        achou = re.match(r"^\[([^\]]+)\]: \[(.*)\]$", linha.strip())
        if achou and achou.group(1) in PROPRIEDADES:
            props[achou.group(1)] = achou.group(2).strip()
    return props


def ler_meminfo(texto):
    kb = {}
    for linha in texto.splitlines():
        achou = re.match(r"^(\w+):\s+(\d+)\s*kB", linha.strip())
        if achou:
            kb[achou.group(1)] = int(achou.group(2))
    if not kb.get("MemTotal"):
        raise ValueError("sem MemTotal")
    return {"total_mb": round(kb["MemTotal"] / 1024), "disponivel_mb": round(kb.get("MemAvailable", 0) / 1024),
            "troca_mb": round(kb.get("SwapTotal", 0) / 1024)}


def ler_cpuinfo(texto):
    """([nucleo], hardware): cada nucleo com implementador, parte e modelo."""
    nucleos, atual, hardware = [], None, ""
    for linha in texto.splitlines():
        if ":" not in linha:
            continue
        chave, valor = (p.strip() for p in linha.split(":", 1))
        chave = chave.lower()
        if chave == "processor" and valor.isdigit():
            atual = {"implementador": "", "parte": "", "modelo": ""}
            nucleos.append(atual)
        elif atual is not None and chave == "cpu implementer":
            atual["implementador"] = valor.lower()
        elif atual is not None and chave == "cpu part":
            atual["parte"] = valor.lower()
        elif atual is not None and chave == "model name":
            atual["modelo"] = valor
        elif chave == "hardware":
            hardware = valor
    return nucleos, hardware


def nome_do_nucleo(nucleo):
    implementador, parte = nucleo.get("implementador", ""), nucleo.get("parte", "")
    if implementador == "0x41" and parte in NUCLEOS_ARM:
        return NUCLEOS_ARM[parte]
    if nucleo.get("modelo"):
        return nucleo["modelo"]
    if implementador or parte:
        return "núcleo %s (%s)" % (FABRICANTES_DE_NUCLEO.get(implementador, implementador or "?"), parte or "?")
    return None


def ler_frequencias(texto):
    """{indice do nucleo: kHz maximo}."""
    frequencias = {}
    for linha in texto.splitlines():
        achou = re.search(r"/cpu(\d+)/cpufreq/cpuinfo_max_freq\s+(\d+)\s*$", linha)
        if achou:
            frequencias[int(achou.group(1))] = int(achou.group(2))
    return frequencias


def agrupar_nucleos(nucleos, frequencias):
    """[{nome, quantidade, mhz_max}] dos nucleos iguais juntos, do mais rapido ao mais lento."""
    grupos = {}
    for indice, nucleo in enumerate(nucleos):
        khz = frequencias.get(indice)
        chave = (nome_do_nucleo(nucleo), round(khz / 1000) if khz else None)
        grupos[chave] = grupos.get(chave, 0) + 1
    ordem = sorted(grupos.items(), key=lambda item: (-(item[0][1] or 0), item[0][0] or ""))
    return [{"nome": nome, "quantidade": quantidade, "mhz_max": mhz} for (nome, mhz), quantidade in ordem]


def ler_pares(texto):
    """"chave: valor" de varias linhas, com a chave em minuscula (a primeira vale)."""
    pares = {}
    for linha in texto.splitlines():
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            pares.setdefault(chave.strip().lower(), valor.strip())
    return pares


def para_mah(valor):
    """O arquivo da bateria diz uAh na maioria dos aparelhos (5000000 = 5000 mAh)
    e mAh em alguns (5000). Bateria de celular tem de 500 a 20000 mAh, entao
    de 100000 para cima so pode ser uAh."""
    if valor is None:
        return None
    return round(valor / 1000.0, 1) if valor >= 100000 else float(valor)


def ler_caminhos_da_bateria(texto):
    """[{caminho, estado, valor}] de cada arquivo de /sys/class/power_supply que
    o roteiro tentou ler: ok (com o valor), negado (o Android nao deixa ler sem
    root), inexistente ou vazio."""
    caminhos = []
    for linha in texto.splitlines()[:120]:
        if "|" not in linha:
            continue
        caminho, resposta = linha.split("|", 1)
        caminho, resposta = caminho.strip(), resposta.strip()
        if not caminho.startswith("/sys/class/power_supply/"):
            continue
        valor = None
        if "permission denied" in resposta.lower():
            estado = "negado"
        elif "no such file" in resposta.lower() or "not found" in resposta.lower():
            estado = "inexistente"
        elif not resposta:
            estado = "vazio"
        else:
            valor = inteiro(resposta)
            estado = "ok" if valor is not None else "vazio"
        caminhos.append({"caminho": caminho, "estado": estado, "valor": valor})
    return caminhos


def ler_bateria(texto_bateria, texto_capacidade, texto_sys):
    pares = ler_pares(texto_bateria)
    bateria = {"presente": pares.get("present", "true") != "false"}
    nivel, escala = inteiro(pares.get("level")), inteiro(pares.get("scale"), 100) or 100
    if nivel is not None:
        bateria["nivel_pct"] = max(0, min(100, round(100.0 * nivel / escala)))
    if inteiro(pares.get("voltage")):
        bateria["voltagem_mv"] = inteiro(pares["voltage"])
    temperatura = inteiro(pares.get("temperature"))
    if temperatura is not None:
        bateria["temperatura_c"] = temperatura / 10.0
    saude = inteiro(pares.get("health"))
    if saude is not None:
        bateria["saude_codigo"] = saude
        bateria["saude"] = SAUDE_DA_BATERIA.get(saude, "desconhecida")
    if pares.get("technology"):
        bateria["tecnologia"] = pares["technology"][:20]
    fonte = [nome for chave, nome in (("usb powered", "USB"), ("ac powered", "tomada"),
                                      ("wireless powered", "sem fio")) if pares.get(chave) == "true"]
    bateria["fonte"] = fonte[0] if fonte else None
    status = inteiro(pares.get("status"))
    bateria["carregando"] = status == 2
    bateria["cheia"] = status == 5
    # carga de agora (uAh), pelo contador do Android; sem ele, pelo arquivo da bateria
    caminhos = ler_caminhos_da_bateria(texto_sys)
    bateria["caminhos"] = caminhos
    do_arquivo = {c["caminho"].rsplit("/", 1)[1]: c["valor"] for c in caminhos if c["estado"] == "ok"}
    contador = inteiro(pares.get("charge counter"))
    if contador is None:
        contador = do_arquivo.get("charge_counter")
    if contador:
        bateria["carga_agora_mah"] = para_mah(contador)
    if inteiro(pares.get("msavedbatteryasoc")) is not None:
        bateria["saude_samsung_pct"] = inteiro(pares["msavedbatteryasoc"])
    ciclos = inteiro(pares.get("cycle count"), inteiro(pares.get("cyclecount")))
    if ciclos is None:
        ciclos = do_arquivo.get("cycle_count")
    if ciclos:
        bateria["ciclos"] = ciclos
    # capacidade em mAh: o que o fabricante declarou ao Android e o que o Android aprendeu
    projeto = next((c["valor"] for c in caminhos
                    if c["estado"] == "ok" and c["caminho"].endswith("/charge_full_design") and c["valor"]), None)
    if projeto:
        bateria["capacidade_de_projeto_mah"] = para_mah(projeto)
        bateria["capacidade_de_projeto_arquivo"] = next(
            c["caminho"] for c in caminhos if c["estado"] == "ok" and c["caminho"].endswith("/charge_full_design"))
    perfil = re.search(r"^\s*capacity:\s*([\d.]+)", texto_capacidade, re.I | re.M)
    if perfil and decimal(perfil.group(1)):
        bateria["capacidade_do_perfil_mah"] = decimal(perfil.group(1))
    aprendida = re.search(r"last learned battery capacity:\s*([\d.]+)\s*mah", texto_capacidade, re.I)
    if aprendida and decimal(aprendida.group(1)):
        bateria["capacidade_aprendida_mah"] = decimal(aprendida.group(1))
    de_fabrica = bateria.get("capacidade_de_projeto_mah") or bateria.get("capacidade_do_perfil_mah")
    if de_fabrica:
        bateria["capacidade_de_fabrica_mah"] = de_fabrica
        bateria["capacidade_de_fabrica_fonte"] = ("o arquivo charge_full_design do celular"
                                                  if bateria.get("capacidade_de_projeto_mah")
                                                  else "o perfil de energia do próprio Android")
    pct, carga = bateria.get("nivel_pct"), bateria.get("carga_agora_mah")
    if pct and pct >= 15 and carga:
        # o nivel e' inteiro (24% pode ser de 23,5 a 24,5): a conta vai com a faixa
        # que isso deixa, e fica mais justa quanto mais carregada a bateria
        bateria["capacidade_pela_conta_mah"] = round(carga / (pct / 100.0))
        bateria["capacidade_pela_conta_faixa_mah"] = [round(carga / ((pct + 0.5) / 100.0)),
                                                      round(carga / ((pct - 0.5) / 100.0))]
    # porque o charge_full_design nao veio (so quando nao veio)
    if not projeto:
        do_projeto = [c for c in caminhos if c["caminho"].endswith("/charge_full_design")]
        negados = [c for c in do_projeto if c["estado"] == "negado"]
        bateria["capacidade_de_projeto_motivo"] = (
            "o Android não deixa o computador ler esse arquivo sem permissão de administrador (root)"
            if negados else "este celular não tem esse arquivo")
    return bateria


def ler_tela(texto):
    tela = {}
    for linha in texto.splitlines():
        achou = re.match(r"^\s*(Physical|Override) size:\s*(\d+)x(\d+)", linha)
        if achou:
            # o tamanho que o aluno escolheu (Override) vale mais que o de fabrica
            if achou.group(1) == "Override" or "largura" not in tela:
                tela["largura"], tela["altura"] = int(achou.group(2)), int(achou.group(3))
        achou = re.match(r"^\s*(Physical|Override) density:\s*(\d+)", linha)
        if achou and (achou.group(1) == "Override" or "dpi" not in tela):
            tela["dpi"] = int(achou.group(2))
        achou = re.search(r"fps=([0-9.]+)", linha)
        if achou and "hz" not in tela:
            tela["hz"] = round(float(achou.group(1)), 1)
    if "largura" not in tela:
        raise ValueError("sem tamanho de tela")
    return tela


def ler_disco(texto):
    for linha in texto.splitlines():
        partes = linha.split()
        if len(partes) >= 5 and partes[1].isdigit() and partes[2].isdigit() and partes[3].isdigit():
            total, usado, livre = (int(p) / 1024.0 for p in partes[1:4])
            return {"total_mb": round(total), "usado_mb": round(usado), "livre_mb": round(livre),
                    "usado_pct": round(100.0 * usado / total) if total else 0}
    raise ValueError("sem linha do df")


def ler_kernel(texto):
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    kernel = {"versao": linhas[0] if linhas else ""}
    if len(linhas) > 1:
        ligado = decimal(linhas[1].split()[0])
        if ligado is not None:
            kernel["ligado_ha_segundos"] = int(ligado)
    return kernel


def ler_gpu(texto):
    # "GLES: Imagination Technologies, PowerVR Rogue GE8320, OpenGL ES 3.2 build 1.13@5776728"
    achou = re.search(r"GLES:\s*([^,]+),\s*(.+?),\s*OpenGL ES\s*([\d.]+)", texto)
    if not achou:
        raise ValueError("sem linha GLES")
    return {"fabricante": achou.group(1).strip(), "placa": achou.group(2).strip(), "opengl_es": achou.group(3)}


def ler_recursos(texto):
    """O que o celular tem para controle e jogo (pm list features)."""
    nomes = {}
    for linha in texto.splitlines():
        linha = linha.strip()
        if linha.startswith("feature:"):
            nome, _, valor = linha[len("feature:"):].partition("=")
            nomes[nome] = valor
    recursos = {
        "usb_host": "android.hardware.usb.host" in nomes,
        "bluetooth": "android.hardware.bluetooth" in nomes,
        "bluetooth_le": "android.hardware.bluetooth_le" in nomes,
        "giroscopio": "android.hardware.sensor.gyroscope" in nomes,
        "acelerometro": "android.hardware.sensor.accelerometer" in nomes,
        "multitoque": any(n.startswith("android.hardware.touchscreen.multitouch") for n in nomes),
        "vulkan": None,
    }
    versao = inteiro(nomes.get("android.hardware.vulkan.version"))
    if versao:
        # a versao do Vulkan vem como (maior << 22) | (menor << 12) | correcao
        recursos["vulkan"] = "%d.%d" % (versao >> 22, (versao >> 12) & 0x3FF)
    elif nomes:
        recursos["vulkan"] = ""      # a lista veio, e nao tem Vulkan
    return recursos


def interpretar(texto):
    """A leitura do celular: dicionario com aparelho, processador, memoria,
    armazenamento, tela, grafico, recursos e bateria. Cada pedaco e' lido
    sozinho: o que falhar fica de fora e vai em "falhas"."""
    secoes = dividir_em_secoes(texto)
    leitura, falhas = {}, []

    def tentar(nome, funcao):
        try:
            leitura[nome] = funcao()
        except Exception as falha:   # noqa: BLE001 -- dado do celular: o que nao deu certo vira aviso, nunca queda
            falhas.append("%s (%s)" % (nome, str(falha)[:60] or type(falha).__name__))

    props = ler_props(secoes.get("props", ""))

    def aparelho():
        if not props.get("ro.product.model") and not props.get("ro.product.manufacturer"):
            raise ValueError("o celular não respondeu o modelo")
        fabricante = props.get("ro.product.manufacturer", "")
        sdk = inteiro(props.get("ro.build.version.sdk"))
        resultado = {"fabricante": fabricante.capitalize() if fabricante.islower() else fabricante,
                     "modelo": props.get("ro.product.model", ""), "codinome": props.get("ro.product.device", ""),
                     "android": props.get("ro.build.version.release", ""), "sdk": sdk,
                     "seguranca": props.get("ro.build.version.security_patch", ""),
                     "versao_do_sistema": props.get("ro.build.display.id", "")}
        resultado.update(ler_kernel(secoes.get("kernel", "")))
        return resultado

    def processador():
        nucleos, hardware = ler_cpuinfo(secoes.get("cpuinfo", ""))
        grupos = agrupar_nucleos(nucleos, ler_frequencias(secoes.get("freq", "")))
        soc = props.get("ro.soc.model") or hardware or props.get("ro.board.platform") or props.get("ro.hardware", "")
        if not soc and not nucleos:
            raise ValueError("sem processador")
        abis = [a for a in props.get("ro.product.cpu.abilist", "").split(",") if a]
        abis64 = [a for a in props.get("ro.product.cpu.abilist64", "").split(",") if a]
        return {"soc": soc, "fabricante_do_soc": props.get("ro.soc.manufacturer", ""),
                "plataforma": props.get("ro.board.platform", "") or props.get("ro.hardware", ""),
                "nucleos": len(nucleos) or None, "grupos": grupos, "arquiteturas": abis,
                "de_64_bits": bool(abis64) or any("64" in a for a in abis)}

    tentar("aparelho", aparelho)
    tentar("processador", processador)
    tentar("memoria", lambda: ler_meminfo(secoes.get("meminfo", "")))
    tentar("armazenamento", lambda: ler_disco(secoes.get("disco", "")))
    tentar("tela", lambda: ler_tela(secoes.get("tela", "")))
    tentar("bateria", lambda: ler_bateria(secoes.get("bateria", ""), secoes.get("capacidade", ""),
                                          secoes.get("sys", "")))
    tentar("recursos", lambda: ler_recursos(secoes.get("recursos", "")))

    def grafico():
        resultado = ler_gpu(secoes.get("gpu", ""))
        versao = inteiro(props.get("ro.opengles.version"))
        if versao:
            resultado["opengl_es"] = "%d.%d" % (versao >> 16, versao & 0xFFFF)
        return resultado
    tentar("grafico", grafico)
    if not leitura.get("bateria", {}).get("presente", True):
        leitura["bateria"] = {"presente": False}
    # A bateria e os recursos "dao certo" mesmo sem dado nenhum: so conta como
    # resposta do celular o que tem a ver com o aparelho em si.
    if not any(parte in leitura for parte in ("aparelho", "processador", "memoria", "tela")):
        raise FalhaDoAdb("O celular não respondeu à leitura. Destrave a tela, confira o cabo e tente de novo.")
    leitura["falhas"] = falhas
    return leitura


# ---------------------------------------------------------------------------
# Texto para o aluno: o painel inteiro sai daqui (a tela so desenha as linhas)
# ---------------------------------------------------------------------------

def br(numero, casas=0):
    """1234.5 -> "1.234,5" (a tela e' em portugues)."""
    texto = "{:,.{c}f}".format(numero, c=casas)
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def tamanho(mb):
    return "%s GB" % br(mb / 1024.0, 1) if mb >= 1024 else "%s MB" % br(mb)


def duracao(segundos):
    horas, resto = divmod(int(segundos), 3600)
    minutos = resto // 60
    dias, horas = divmod(horas, 24)
    return ("%d d " % dias if dias else "") + ("%d h " % horas if horas or dias else "") + "%d min" % minutos


def data_br(iso):
    achou = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    return "%s/%s/%s" % (achou.group(3), achou.group(2), achou.group(1)) if achou else (iso or "")


def linhas_do_painel(leitura):
    """[{titulo, linhas: [[rotulo, valor]]}] do que foi lido. Só entra o que o
    celular respondeu; o que nao veio e' dito, nunca inventado."""
    grupos = []

    def grupo(titulo, linhas):
        linhas = [[rotulo, valor] for rotulo, valor in linhas if valor not in (None, "")]
        if linhas:
            grupos.append({"titulo": titulo, "linhas": linhas})

    a = leitura.get("aparelho")
    if a:
        seguranca = data_br(a.get("seguranca"))
        grupo("O aparelho", [
            ["Modelo", " ".join(p for p in (a.get("fabricante"), a.get("modelo")) if p)],
            ["Android", ("%s (API %s)" % (a.get("android"), a["sdk"]) if a.get("sdk") else a.get("android"))
             + (" · atualização de segurança de %s" % seguranca if seguranca else "")],
            ["Versão do sistema", a.get("versao_do_sistema")],
            ["Kernel (Linux)", a.get("versao")],
            ["Ligado há", duracao(a["ligado_ha_segundos"]) if a.get("ligado_ha_segundos") is not None else None],
        ])
    p = leitura.get("processador")
    if p:
        partes = []
        for g in p.get("grupos", []):
            nome = g["nome"] or "núcleo"
            partes.append("%d × %s%s" % (g["quantidade"], nome,
                                         " até %s GHz" % br(g["mhz_max"] / 1000.0, 1) if g.get("mhz_max") else ""))
        g = leitura.get("grafico") or {}
        r = leitura.get("recursos") or {}
        vulkan = r.get("vulkan")
        grupo("Processador e vídeo", [
            ["Processador (SoC)", (p.get("soc") or "") + (" (%s)" % p["fabricante_do_soc"] if p.get("fabricante_do_soc") else "")],
            ["Núcleos", ("%d núcleos: " % p["nucleos"] if p.get("nucleos") else "") + " + ".join(partes) if partes else None],
            ["Arquitetura", ", ".join(p.get("arquiteturas", [])) + (" · 64 bits" if p.get("de_64_bits") else " · só 32 bits")],
            ["Placa de vídeo", ((g.get("placa") or "") + (" (%s)" % g["fabricante"] if g.get("fabricante") else "")) or None],
            ["OpenGL ES", g.get("opengl_es")],
            ["Vulkan", None if vulkan is None else (vulkan if vulkan else "este celular não tem")],
        ])
    m, d, t = leitura.get("memoria"), leitura.get("armazenamento"), leitura.get("tela")
    if m or d or t:
        grupo("Memória, armazenamento e tela", [
            ["Memória RAM", "%s (%s livres agora)" % (tamanho(m["total_mb"]), tamanho(m["disponivel_mb"])) if m else None],
            ["Armazenamento", "%s (%s livres, %d%% usado)" % (tamanho(d["total_mb"]), tamanho(d["livre_mb"]), d["usado_pct"]) if d else None],
            ["Tela", ("%d × %d pontos" % (t["largura"], t["altura"]) + (" · %d dpi" % t["dpi"] if t.get("dpi") else "")
                      + (" · %s Hz" % br(t["hz"], 0 if t["hz"] == int(t["hz"]) else 1) if t.get("hz") else "")) if t else None],
        ])
    r = leitura.get("recursos")
    if r:
        def tem(valor):
            return "tem" if valor else "não tem"
        grupo("Para jogar com controle", [
            ["Controle por cabo ou adaptador (USB-C/OTG)", tem(r.get("usb_host"))],
            ["Controle por Bluetooth", tem(r.get("bluetooth")) + (" (e Bluetooth LE)" if r.get("bluetooth_le") else "")],
            ["Giroscópio", tem(r.get("giroscopio"))],
            ["Acelerômetro (inclinar o celular)", tem(r.get("acelerometro"))],
            ["Toque com vários dedos", tem(r.get("multitoque"))],
        ])
    b = leitura.get("bateria")
    if b and b.get("presente") is False:
        grupo("Bateria", [["Bateria", "este aparelho não tem bateria"]])
    elif b:
        linhas = []
        if b.get("nivel_pct") is not None:
            estado = ("cheia" if b.get("cheia") else
                      ("carregando" + (" pelo %s" % b["fonte"] if b.get("fonte") else "") if b.get("carregando")
                       else ("ligado na %s, sem carregar" % b["fonte"] if b.get("fonte") else "usando a bateria")))
            linhas.append(["Nível da bateria", "%d%% · %s" % (b["nivel_pct"], estado)])
        if b.get("carga_agora_mah"):
            linhas.append(["Carga guardada agora", "%s mAh" % br(b["carga_agora_mah"])])
        if b.get("capacidade_de_fabrica_mah"):
            linhas.append(["Capacidade de fábrica", "%s mAh (segundo %s)"
                           % (br(b["capacidade_de_fabrica_mah"]), b["capacidade_de_fabrica_fonte"])])
        if not b.get("capacidade_de_projeto_mah"):
            linhas.append(["Capacidade de projeto (charge_full_design)",
                           "indisponível neste aparelho: %s" % b.get("capacidade_de_projeto_motivo", "")])
        if b.get("capacidade_aprendida_mah"):
            linhas.append(["Capacidade que o Android aprendeu", "%s mAh" % br(b["capacidade_aprendida_mah"])])
        if b.get("capacidade_pela_conta_mah"):
            conta = b["capacidade_pela_conta_mah"]
            faixa = b.get("capacidade_pela_conta_faixa_mah")
            fabrica = b.get("capacidade_de_fabrica_mah")
            linhas.append(["Conta: carga ÷ nível",
                           "uns %s mAh%s%s. É só uma pista, não uma medida: o nível é um número inteiro, e alguns "
                           "aparelhos usam a capacidade de fábrica como base do contador e não mostram o desgaste. "
                           "Com a bateria mais cheia, a conta fica mais justa."
                           % (br(conta), " (entre %s e %s)" % (br(faixa[0]), br(faixa[1])) if faixa else "",
                              ", ou %d%% da de fábrica" % round(100.0 * conta / fabrica) if fabrica else "")])
        if b.get("saude"):
            linhas.append(["Saúde, pelo Android", b["saude"]])
        if b.get("saude_samsung_pct") is not None:
            linhas.append(["Índice de saúde da Samsung (ASOC)",
                           "%d%% · aproximado: a Samsung só atualiza depois de várias cargas completas" % b["saude_samsung_pct"]])
        if b.get("ciclos"):
            linhas.append(["Ciclos de carga", str(b["ciclos"])])
        if b.get("voltagem_mv"):
            linhas.append(["Voltagem", "%s V" % br(b["voltagem_mv"] / 1000.0, 3)])
        if b.get("temperatura_c") is not None:
            linhas.append(["Temperatura da bateria", "%s °C" % br(b["temperatura_c"], 1)])
        linhas.append(["Tipo da bateria", b.get("tecnologia")])
        grupo("Bateria", linhas)
    return grupos


def texto_dos_caminhos(leitura):
    """Os arquivos da bateria que o ARENA tentou ler e o que cada um respondeu:
    os do "battery" e dos medidores de carga (o que interessa) e qualquer um que
    tenha respondido. Carregador, USB e tomada ficam de fora da lista, e o
    resumo conta quantos eram. -> (resumo, [{caminho, resultado, ok}])"""
    nomes = {"ok": "leu", "negado": "o Android não deixa ler (sem root)", "inexistente": "não existe neste aparelho",
             "vazio": "veio vazio"}
    caminhos = (leitura.get("bateria") or {}).get("caminhos", [])
    if not caminhos:
        return "", []

    def interessa(c):
        no = c["caminho"].split("/")[4] if c["caminho"].count("/") >= 5 else ""
        return c["estado"] == "ok" or any(parte in no for parte in ("batt", "gauge", "bms", "fuel", "cell"))
    mostrados = [{"caminho": c["caminho"], "resultado": nomes.get(c["estado"], c["estado"]), "ok": c["estado"] == "ok"}
                 for c in caminhos if interessa(c)]
    funcionaram = [c for c in caminhos if c["estado"] == "ok"]
    resumo = ("%d de %d arquivos responderam." % (len(funcionaram), len(caminhos)) if funcionaram
              else "Nenhum dos %d arquivos testados respondeu: é o normal sem root." % len(caminhos))
    return resumo, mostrados


# ---------------------------------------------------------------------------
# O que a tela chama
# ---------------------------------------------------------------------------

def procurar(serial=None):
    """Procura o celular no cabo e le o hardware dele. 'serial' (de um pedido
    anterior) escolhe um; sem ele, le o unico celular pronto. Nunca levanta
    erro: o que o aluno precisa saber vai em "erro" ou "dica"."""
    resposta = {"adb": None, "como_baixar": None, "aparelhos": [], "escolhido": None, "leitura": None,
                "painel": [], "resumo_dos_caminhos": "", "caminhos": [], "dica": None, "erro": None}
    if serial is not None and not (isinstance(serial, str) and PADRAO_DE_SERIAL.match(serial)):
        resposta["erro"] = "Celular inválido. Clique em Procurar de novo."
        return resposta
    adb, origem = achar_adb()
    if not adb:
        resposta["como_baixar"] = COMO_BAIXAR_O_ADB
        return resposta
    resposta["adb"] = origem
    try:
        with sessao(adb):
            aparelhos = interpretar_lista(executar(adb, ["devices", "-l"], tempo=TEMPO_DO_ADB)[1])
            resposta["aparelhos"] = aparelhos
            prontos = [a for a in aparelhos if a["pronto"]]
            alvo = None
            if serial is not None:
                alvo = next((a for a in aparelhos if a["serial"] == serial), None)
                if alvo is None:
                    resposta["erro"] = "Esse celular saiu do cabo. Clique em Procurar de novo."
            elif len(prontos) == 1:
                alvo = prontos[0]
            elif len(prontos) > 1:
                resposta["dica"] = "Há %d celulares no cabo. Escolha qual ler." % len(prontos)
            elif aparelhos:
                resposta["dica"] = aparelhos[0]["estado_texto"]
            else:
                resposta["dica"] = "Nenhum celular encontrado no cabo. " + COMO_LIGAR_O_CELULAR
            if alvo is not None and not alvo["pronto"]:
                resposta["dica"] = alvo["estado_texto"]
            elif alvo is not None:
                resposta["escolhido"] = alvo["serial"]
                codigo, saida = executar(adb, ["-s", alvo["serial"], "shell"],
                                         entrada=SCRIPT_DE_LEITURA.encode("utf-8"), tempo=TEMPO_DA_LEITURA)
                if codigo != 0 and "@@props" not in saida:
                    # o celular saiu do cabo no meio, ou travou: o adb diz o motivo na primeira linha
                    motivo = (saida.strip().splitlines() or ["sem resposta"])[0][:100]
                    raise FalhaDoAdb("O celular parou de responder durante a leitura (%s). Confira o cabo, "
                                     "destrave a tela e clique em Procurar de novo." % motivo)
                leitura = interpretar(saida)
                resposta["leitura"] = leitura
                resposta["painel"] = linhas_do_painel(leitura)
                resposta["resumo_dos_caminhos"], resposta["caminhos"] = texto_dos_caminhos(leitura)
    except FalhaDoAdb as falha:
        resposta["erro"] = str(falha)
    except TimeoutError:
        resposta["erro"] = ("O celular demorou demais para responder. Destrave a tela, confira o cabo e "
                            "clique em Procurar de novo.")
    except OSError as falha:
        resposta["erro"] = "Não consegui abrir o adb (%s). Confira se o arquivo está inteiro." % (falha.strerror or falha)
    return resposta


def principal(argumentos):
    """Roda sozinho (sem a tela): mostra o painel do celular no terminal."""
    reconfigurar = getattr(sys.stdout, "reconfigure", None)
    if reconfigurar:
        reconfigurar(encoding="utf-8", errors="replace")     # o terminal do Windows nao e' UTF-8
    resposta = procurar(argumentos[0] if argumentos else None)
    if resposta["como_baixar"]:
        print(resposta["como_baixar"])
        return 2
    print("ADB: %s" % resposta["adb"])
    for aparelho in resposta["aparelhos"]:
        print("Celular %s (%s): %s" % (aparelho["serial_curto"], aparelho["modelo"] or "?", aparelho["estado"]))
    if resposta["dica"]:
        print(resposta["dica"])
    for grupo in resposta["painel"]:
        print("\n== %s" % grupo["titulo"])
        for rotulo, valor in grupo["linhas"]:
            print("  %-44s %s" % (rotulo, valor))
    if resposta["caminhos"]:
        print("\n== Arquivos da bateria que o ARENA tentou ler: %s" % resposta["resumo_dos_caminhos"])
        for c in resposta["caminhos"]:
            print("  %-62s %s" % (c["caminho"], c["resultado"]))
    if resposta["leitura"] and resposta["leitura"].get("falhas"):
        print("\nNão deu para ler: %s" % "; ".join(resposta["leitura"]["falhas"]))
    if resposta["erro"]:
        print(resposta["erro"])
        return 1
    return 0 if resposta["leitura"] else 3


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
