# -*- coding: utf-8 -*-
"""O que esta deixando ESTE computador lento -- e o que fazer.

Pedido do Rafael (auditoria 2): o ARENA precisa identificar as barreiras
que deixam os notebooks da escola lentos -- programas que abrem sozinhos,
bloatware de fabrica, servicos pesados, telemetria, atualizacao do Windows
rodando, antivirus em dobro, efeitos visuais, gravacao em segundo plano,
disco cheio, bateria, pouca memoria -- e recomendar uma acao.

Como funciona (duas partes, de proposito separadas):

  1. coletar_fatos()  -- LE o Windows. Sem administrador: registro (so
     leitura), lista de processos, lista de servicos, Central de Seguranca.
     Uma chamada so ao PowerShell (que ja vem no Windows), ~3 s. O que der
     erro vira "nao deu para ler" e segue -- nunca trava.
  2. avaliar(fatos)   -- DECIDE, sem tocar em nada. Funcao pura: recebe os
     fatos e devolve a lista de barreiras. E' ela que os testes exercitam
     com fatos inventados, sem depender da maquina.

Cada barreira diz: o que foi achado, por que pesa, o que fazer, e QUEM
consegue fazer -- o aluno (sem senha de administrador) ou o professor/TI.
O ARENA nunca muda configuracao do Windows sozinho. A unica acao que ele
oferece e' fechar programas de uma lista curta e segura (OneDrive, Teams,
Discord...), e so quando o aluno clica.

Privacidade: nada de nome de usuario, nome da maquina ou caminho com o
nome da conta. Da lista de inicializacao guarda so o NOME do programa e se
e' "do usuario" ou "do computador". Dos programas instalados guarda so os
que batem com a lista de bloatware conhecido.
"""
import json
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Listas de conhecimento (curtas e conferiveis; crescem com o uso)
# ---------------------------------------------------------------------------

# Programas que o ARENA pode fechar quando o aluno clica: nenhum deles
# guarda trabalho do aluno sem salvar (sincronizam ou sao so mensageiros e
# lojas). Navegador, Word, etc. NUNCA entram aqui.
FECHAVEIS = {
    "onedrive": "OneDrive (sincroniza arquivos com a nuvem)",
    "teams": "Microsoft Teams", "ms-teams": "Microsoft Teams",
    "discord": "Discord", "spotify": "Spotify", "steam": "Steam",
    "steamwebhelper": "Steam", "epicgameslauncher": "Epic Games",
    "skype": "Skype", "zoom": "Zoom", "whatsapp": "WhatsApp",
    "telegram": "Telegram", "dropbox": "Dropbox", "googledrivefs": "Google Drive",
    "xboxpcapp": "App do Xbox", "gamebar": "Xbox Game Bar",
    "widgets": "Widgets do Windows", "phoneexperiencehost": "Vincular ao Celular",
    "yourphone": "Vincular ao Celular", "cortana": "Cortana",
}

# Nomes (parte do nome) de programas instalados que sao bloatware de
# fabrica ou "teste gratis" -- pesam e nao servem para a aula.
BLOATWARE = [
    "mcafee", "norton", "avast", "avg ", "avira", "wildtangent", "candy crush",
    "bubble witch", "farmville", "march of empires", "booking.com", "disney+",
    "tiktok", "cyberlink", "expressvpn", "dropbox promotion", "wps office",
    "segurazo", "reimage", "driver booster", "iobit", "ccleaner", "baidu",
    "opera gx", "hp support assistant", "hp jumpstart", "dell supportassist",
    "lenovo vantage", "asus giftbox", "acer care center", "ask toolbar",
    "king.com", "solitaire collection",
]

# Antivirus "de verdade" (um so ja basta; dois brigam e dobram o peso).
PROCESSOS_ANTIVIRUS = {"msmpeng", "mcshield", "avp", "avastsvc", "avgsvc", "nortonsecurity",
                       "ccsvchst", "bdagent", "vsserv", "ekrn", "savservice"}

# Processos do Windows Update trabalhando agora.
PROCESSOS_ATUALIZACAO = {"tiworker", "trustedinstaller", "mousocoreworker", "wuauclt",
                         "usoclient", "musnotification", "sihclient", "wsappx"}

# Servicos que costumam pesar em maquina fraca com disco mecanico.
SERVICOS_OBSERVADOS = ["DiagTrack", "dmwappushservice", "SysMain", "WSearch", "wuauserv",
                       "DoSvc", "BITS", "WerSvc", "XblAuthManager", "XblGameSave",
                       "XboxNetApiSvc", "MapsBroker", "RetailDemo", "Fax", "WMPNetworkSvc",
                       "PcaSvc", "OneSyncSvc", "CDPUserSvc"]

ACOES_ALUNO = "aluno"          # da para fazer sem senha de administrador
ACOES_TI = "professor/TI"      # precisa da senha de administrador

# ---------------------------------------------------------------------------
# 1. Coletar fatos (le o Windows, sem administrador)
# ---------------------------------------------------------------------------

_SCRIPT = r"""
# Escrito para funcionar tambem no PowerShell em "modo de linguagem
# restrita" (Constrained Language Mode), que muita escola liga para aluno:
# nada de [pscustomobject], [math], [Environment], [Convert] nem metodos de
# objetos que nao sejam texto/numero. Objetos saem de Select-Object com
# propriedades calculadas (permitido); as contas finas sao feitas no Python.
$ErrorActionPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
function Reg($caminho, $nome) { (Get-ItemProperty -Path $caminho -Name $nome -ErrorAction SilentlyContinue).$nome }
$r = @{}

# Processos: duas fotos com 2 s de intervalo, para o uso de CPU de cada um.
$p1 = @{}; Get-Process | ForEach-Object { $p1[$_.Id] = $_.CPU }
$t1 = Get-Date
Start-Sleep -Milliseconds 2000
$seg = ((Get-Date) - $t1).TotalSeconds
$nucleos = [int]$env:NUMBER_OF_PROCESSORS
if ($nucleos -lt 1) { $nucleos = 1 }
$r.processos = @(Get-Process | Select-Object @{n='nome';e={$_.ProcessName.ToLower()}},
    @{n='mb';e={[int]($_.WorkingSet64 / 1MB)}},
    @{n='cpu';e={ if ($p1[$_.Id] -ne $null -and $_.CPU -ne $null) { ($_.CPU - $p1[$_.Id]) / $seg / $nucleos * 100 } else { 0 } }} |
  Group-Object nome | Select-Object @{n='nome';e={$_.Name}}, @{n='instancias';e={$_.Count}},
    @{n='mb';e={($_.Group | Measure-Object mb -Sum).Sum}}, @{n='cpu';e={($_.Group | Measure-Object cpu -Sum).Sum}})

# Inicializacao: so o NOME e o lugar. Nada de usuario ou SID.
$ini = @()
foreach ($par in @(@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','usuario'),
                   @('HKLM:\Software\Microsoft\Windows\CurrentVersion\Run','computador'),
                   @('HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run','computador'))) {
  $onde = $par[1]
  foreach ($n in @((Get-Item -Path $par[0]).Property)) {
    if ($n) { $ini += ('' | Select-Object @{n='nome';e={$n}}, @{n='onde';e={$onde}}) } }
}
# O que o aluno desligou no Gerenciador de Tarefas fica marcado aqui (byte 0 impar = desligado).
$desligados = @{}
foreach ($c in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run',
                 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run',
                 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32',
                 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder')) {
  $valores = Get-ItemProperty -Path $c
  foreach ($n in @((Get-Item -Path $c).Property)) { $v = $valores.$n; if ($v -and ($v[0] % 2) -eq 1) { $desligados[$n] = $true } }
}
foreach ($pasta in @(($env:APPDATA + '\Microsoft\Windows\Start Menu\Programs\Startup'),
                     ($env:ProgramData + '\Microsoft\Windows\Start Menu\Programs\StartUp'))) {
  if (Test-Path $pasta) {
    Get-ChildItem -Path $pasta -File | Where-Object Name -ne 'desktop.ini' | ForEach-Object {
      $ini += ($_ | Select-Object @{n='nome';e={$_.BaseName}}, @{n='onde';e={'pasta Inicializar'}}) } }
}
$r.inicializacao = @($ini | Select-Object nome, onde, @{n='desligado';e={[bool]$desligados[$_.nome]}})

# Servicos (so os observados; os protegidos que negam leitura sao pulados).
$r.servicos = @(Get-Service -Name @(%SERVICOS%) -ErrorAction SilentlyContinue |
  Select-Object @{n='nome';e={$_.Name}}, @{n='rodando';e={[string]$_.Status -eq 'Running'}}, @{n='inicio';e={[string]$_.StartType}})

# Antivirus pela Central de Seguranca (qualquer usuario pode ler).
$r.antivirus = @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct |
  Select-Object @{n='nome';e={$_.displayName}}, @{n='ligado';e={((($_.productState -shr 12) -band 15) -eq 1)}})

# Programas instalados: so a lista de NOMES, filtrada no Python.
$r.instalados = @(Get-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' | Where-Object DisplayName |
  ForEach-Object { $_.DisplayName }) + @(Get-AppxPackage | ForEach-Object { $_.Name })

$r.telemetria_politica = Reg 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' 'AllowTelemetry'
$r.telemetria_sistema = Reg 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection' 'AllowTelemetry'
$r.game_dvr = Reg 'HKCU:\System\GameConfigStore' 'GameDVR_Enabled'
$r.captura_de_jogo = Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' 'AppCaptureEnabled'
$r.modo_de_jogo = Reg 'HKCU:\Software\Microsoft\GameBar' 'AutoGameModeEnabled'
$r.efeitos_visuais = Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects' 'VisualFXSetting'
$r.transparencia = Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize' 'EnableTransparency'
$r.apps_segundo_plano_desligados = Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications' 'GlobalUserDisabled'
$r.arquivo_de_paginacao = Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' 'PagingFiles'
$r.reinicio_pendente = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
                       (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
# Tipo do disco do Windows (HDD/SSD), dito pelo proprio Windows.
$letra = $env:SystemDrive.TrimEnd(':')
$dw = Get-Partition -DriveLetter $letra | Get-Disk | ForEach-Object { $num = $_.Number; Get-PhysicalDisk | Where-Object DeviceId -eq $num } | Select-Object -First 1
$r.disco_windows_tipo = if ($dw) { [string]$dw.MediaType } else { $null }
$v = Get-CimInstance Win32_VideoController | Select-Object -First 1
$r.video = if ($v) { [string]$v.Name } else { $null }

# Limite de uso do processador no plano de energia atual (0x64 = 100%). Vai
# o texto bruto; a conversao e' feita no Python.
$q = powercfg /query SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 2>$null
$hex = @($q | Select-String '0x[0-9a-fA-F]{8}' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
if ($hex.Count -ge 2) { $r.processador_maximo_hex = @($hex[-2], $hex[-1]) }
$r.plano_de_energia = ((powercfg /getactivescheme) -replace '^.*\((.*)\).*$', '$1')

$r | ConvertTo-Json -Depth 4 -Compress
"""


def _powershell_fatos(limite=40):
    script = _SCRIPT.replace("%SERVICOS%", ",".join("'%s'" % s for s in SERVICOS_OBSERVADOS))
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-Command", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=limite,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    texto = r.stdout.strip()
    inicio = texto.find("{")
    return json.loads(texto[inicio:]) if inicio >= 0 else {}


def _memoria_e_energia(rapido=False):
    """Memoria, bateria e tempo ligado (instantaneo, ctypes) e, fora do modo
    rapido, disco do Windows e pasta temporaria (a pasta pode levar ate 3 s)."""
    import ctypes
    import shutil

    class MEM(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ("total", "livre", "pag_total", "pag_livre",
                                               "virt_total", "virt_livre", "ext")]

    class ENERGIA(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]

    fatos = {}
    k = ctypes.windll.kernel32
    m = MEM()
    m.dwLength = ctypes.sizeof(m)
    if k.GlobalMemoryStatusEx(ctypes.byref(m)):
        fatos["memoria_total_mb"] = round(m.total / 1024 ** 2)
        fatos["memoria_livre_mb"] = round(m.livre / 1024 ** 2)
        fatos["memoria_em_uso_pct"] = int(m.dwMemoryLoad)
    e = ENERGIA()
    if k.GetSystemPowerStatus(ctypes.byref(e)):
        fatos["na_tomada"] = {0: False, 1: True}.get(e.ACLineStatus)
        fatos["tem_bateria"] = e.BatteryFlag != 128 and e.BatteryLifePercent != 255
        fatos["bateria_pct"] = e.BatteryLifePercent if fatos["tem_bateria"] else None
        fatos["economia_de_bateria"] = bool(e.SystemStatusFlag & 1)
    k.GetTickCount64.restype = ctypes.c_ulonglong
    fatos["ligado_ha_horas"] = round(k.GetTickCount64() / 3600000.0, 1)
    if rapido:
        return fatos
    raiz = os.environ.get("SystemDrive", "C:") + "\\"
    try:
        uso = shutil.disk_usage(raiz)
        fatos["disco_windows_livre_gb"] = round(uso.free / 1024 ** 3, 1)
        fatos["disco_windows_livre_pct"] = round(100.0 * uso.free / uso.total, 1)
    except OSError:
        pass
    temp = os.environ.get("TEMP")
    if temp and os.path.isdir(temp):
        total, inicio = 0, time.time()
        for atual, _s, arquivos in os.walk(temp):
            for n in arquivos:
                try:
                    total += os.path.getsize(os.path.join(atual, n))
                except OSError:
                    pass
            if time.time() - inicio > 3:        # pasta enorme: para de contar
                fatos["temp_contagem_parcial"] = True
                break
        fatos["temp_mb"] = round(total / 1024 ** 2)
    fatos["processadores_logicos"] = os.cpu_count()
    return fatos


def coletar_fatos():
    """Tudo o que avaliar() precisa. Nunca levanta erro: o que falhar fica
    registrado em fatos['nao_deu_para_ler']."""
    fatos = {"nao_deu_para_ler": []}
    if not sys.platform.startswith("win"):
        fatos["nao_deu_para_ler"].append("este diagnóstico é só para Windows")
        return fatos
    try:
        fatos.update(_memoria_e_energia())
    except Exception as falha:           # nunca trava
        fatos["nao_deu_para_ler"].append("memoria/energia: %s" % falha)
    try:
        fatos.update(_powershell_fatos())
    except Exception as falha:
        fatos["nao_deu_para_ler"].append("Windows (PowerShell): %s" % str(falha)[:120])
    # Arredondamento aqui (no PowerShell em modo restrito o [math] e' recusado).
    for p in _processos(fatos):
        try:
            p["cpu"] = round(float(p.get("cpu") or 0), 1)
            p["mb"] = int(p.get("mb") or 0)
        except (TypeError, ValueError):
            p["cpu"], p["mb"] = 0.0, 0
    brutos = fatos.pop("processador_maximo_hex", None)
    if isinstance(brutos, list) and len(brutos) == 2:
        try:
            fatos["processador_maximo_tomada"] = int(str(brutos[0]), 16)
            fatos["processador_maximo_bateria"] = int(str(brutos[1]), 16)
        except ValueError:
            pass
    # Da lista de instalados, fica SO o que e' bloatware conhecido.
    instalados = fatos.pop("instalados", None) or []
    fatos["bloatware_instalado"] = sorted({n for n in instalados if isinstance(n, str)
                                           and any(b in n.lower() for b in BLOATWARE)})
    fatos["programas_instalados"] = len(instalados)
    return fatos


# ---------------------------------------------------------------------------
# 2. Avaliar (funcao pura: fatos -> barreiras)
# ---------------------------------------------------------------------------

GRAVIDADE = {"alta": 0, "media": 1, "baixa": 2}


def _b(id_, gravidade, titulo, achado, por_que, acao, quem, fechar=None):
    item = {"id": id_, "gravidade": gravidade, "titulo": titulo, "achado": achado,
            "por_que": por_que, "acao": acao, "quem": quem}
    if fechar:
        item["fechar"] = fechar          # processos que o ARENA pode fechar num clique
    return item


def _processos(fatos):
    return [p for p in (fatos.get("processos") or []) if isinstance(p, dict) and p.get("nome")]


def avaliar(fatos, proprios=("python", "retroarch")):
    """Devolve as barreiras, da mais grave para a mais leve. Nao toca em nada."""
    barreiras = []
    procs = _processos(fatos)
    por_nome = {p["nome"]: p for p in procs}
    total_mb = fatos.get("memoria_total_mb") or 0

    # --- Memoria --------------------------------------------------------
    livre = fatos.get("memoria_livre_mb")
    if isinstance(livre, (int, float)) and total_mb:
        if livre < 800 or fatos.get("memoria_em_uso_pct", 0) >= 85:
            barreiras.append(_b("memoria", "alta", "Memória quase cheia",
                                "Só %d MB livres de %d MB (%d%% em uso)." % (
                                    livre, total_mb, fatos.get("memoria_em_uso_pct", 0)),
                                "Sem memória livre o Windows passa a usar o disco no lugar dela, e tudo trava.",
                                "Feche programas que não está usando (veja a lista abaixo). No ARENA, ligue o modo modesto.",
                                ACOES_ALUNO))
        elif livre < 1500 and total_mb <= 4500:
            barreiras.append(_b("memoria", "media", "Pouca memória livre",
                                "%d MB livres de %d MB." % (livre, total_mb),
                                "Numa máquina de 4 GB, abaixo de 1,5 GB livre os jogos começam a engasgar.",
                                "Feche o que não estiver usando antes de jogar.", ACOES_ALUNO))

    # --- Programas pesados rodando agora ---------------------------------
    pesados = [p for p in procs if p["nome"] not in proprios
               and (p.get("cpu", 0) >= 10 or p.get("mb", 0) >= 400)
               and p["nome"] not in ("system", "idle", "memory compression", "registry", "dwm",
                                     "explorer", "csrss", "svchost", "msmpeng", "searchhost",
                                     "startmenuexperiencehost", "textinputhost", "shellexperiencehost")]
    fechaveis = sorted({p["nome"] for p in procs if p["nome"] in FECHAVEIS})
    if fechaveis:
        barreiras.append(_b("fechaveis", "media", "Programas em segundo plano que dá para fechar",
                            ", ".join(sorted({FECHAVEIS[n] for n in fechaveis})) + ".",
                            "Ficam gastando memória e internet mesmo sem ninguém usar.",
                            "Clique em Fechar. O ARENA fecha só estes, e só quando você manda.",
                            ACOES_ALUNO,
                            # processo (para fechar) + nome que o aluno reconhece (para o botao)
                            fechar=[{"processo": n, "nome": FECHAVEIS[n].split(" (")[0]} for n in fechaveis]))
    navegador = sum(p.get("mb", 0) for p in procs if p["nome"] in ("msedge", "chrome", "firefox", "opera", "brave"))
    if navegador >= 1200:
        barreiras.append(_b("navegador", "media", "Navegador com muitas abas",
                            "O navegador está usando %d MB." % navegador,
                            "Cada aba aberta come memória, mesmo escondida.",
                            "Feche as abas que não precisa (a janela do ARENA pode ficar).", ACOES_ALUNO))
    outros = [p for p in pesados if p["nome"] not in FECHAVEIS
              and p["nome"] not in ("msedge", "chrome", "firefox", "opera", "brave")
              and p["nome"] not in PROCESSOS_ATUALIZACAO and p["nome"] not in PROCESSOS_ANTIVIRUS
              and p["nome"] not in ("searchindexer", "searchprotocolhost", "searchfilterhost")]
    if outros:
        outros.sort(key=lambda p: (-p.get("cpu", 0), -p.get("mb", 0)))
        barreiras.append(_b("pesados", "media", "Programas pesados abertos",
                            "; ".join("%s (%d MB, %s%% do processador)" % (p["nome"], p.get("mb", 0), p.get("cpu", 0))
                                      for p in outros[:5]) + ".",
                            "Disputam o processador e a memória com o jogo.",
                            "Se não estiver usando, feche pelo próprio programa ou pelo Gerenciador de Tarefas (Ctrl+Shift+Esc).",
                            ACOES_ALUNO))

    # --- Processador ocupado com a maquina "parada" ----------------------
    cpu_total = sum(p.get("cpu", 0) for p in procs if p["nome"] not in proprios and p["nome"] != "idle")
    if cpu_total >= 40:
        barreiras.append(_b("cpu_ocupada", "alta", "Processador ocupado sem ninguém jogando",
                            "Os outros programas estão usando %d%% do processador." % cpu_total,
                            "Sobra pouco para o jogo, e ele fica lento.",
                            "Espere terminar o que está rodando (atualização, antivírus) ou feche os programas da lista.",
                            ACOES_ALUNO))

    # --- Windows Update trabalhando ---------------------------------------
    atualizando = [p for p in procs if p["nome"] in PROCESSOS_ATUALIZACAO and p.get("cpu", 0) >= 3]
    if atualizando:
        barreiras.append(_b("atualizando", "media", "O Windows está se atualizando agora",
                            "Trabalhando: " + ", ".join(p["nome"] for p in atualizando) + ".",
                            "A atualização usa disco e processador por um bom tempo.",
                            "Se der, deixe terminar antes da aula. Não desligue no meio.", ACOES_ALUNO))
    if fatos.get("reinicio_pendente"):
        barreiras.append(_b("reiniciar", "media", "Falta reiniciar para terminar uma atualização",
                            "O Windows está esperando um reinício.",
                            "Até reiniciar, a atualização fica pela metade e pesando.",
                            "Salve tudo e use Reiniciar (não Desligar).", ACOES_ALUNO))
    horas = fatos.get("ligado_ha_horas")
    if isinstance(horas, (int, float)) and horas >= 72:
        barreiras.append(_b("ligado", "baixa", "Computador ligado há muito tempo",
                            "Ligado direto há %d dias." % int(horas // 24),
                            "Com o tempo, programas vão deixando memória presa.",
                            "Use Reiniciar de vez em quando. (\"Desligar\" no Windows 10/11 nem sempre zera tudo.)",
                            ACOES_ALUNO))

    # --- Antivirus --------------------------------------------------------
    ligados = [a["nome"] for a in (fatos.get("antivirus") or []) if isinstance(a, dict) and a.get("ligado")]
    if len(ligados) >= 2:
        barreiras.append(_b("antivirus_duplo", "alta", "Dois antivírus ligados ao mesmo tempo",
                            ", ".join(ligados) + ".",
                            "Os dois examinam cada arquivo aberto: o dobro de trabalho, e às vezes brigam.",
                            "Deixar só um (o Windows Defender já basta).", ACOES_TI))
    av = [p for p in procs if p["nome"] in PROCESSOS_ANTIVIRUS and p.get("cpu", 0) >= 15]
    if av:
        barreiras.append(_b("antivirus_agora", "media", "O antivírus está examinando o computador agora",
                            "%s usando %s%% do processador." % (av[0]["nome"], av[0].get("cpu")),
                            "Enquanto examina, o disco e o processador ficam ocupados.",
                            "Espere terminar. Para o ARENA não ser examinado toda hora, o professor pode "
                            "colocar a pasta do ARENA nas exclusões do antivírus (guia 1).", ACOES_TI))

    # --- Bloatware --------------------------------------------------------
    bloat = fatos.get("bloatware_instalado") or []
    if bloat:
        barreiras.append(_b("bloatware", "media" if len(bloat) >= 3 else "baixa",
                            "Programas de fábrica ou de teste instalados",
                            ", ".join(bloat[:8]) + ("..." if len(bloat) > 8 else "") + ".",
                            "Vêm com o computador, rodam sozinhos e não servem para a aula.",
                            "Desinstalar em Configurações > Aplicativos (pede senha de administrador).", ACOES_TI))

    # --- Inicializacao ----------------------------------------------------
    ligados_ini = [i for i in (fatos.get("inicializacao") or []) if isinstance(i, dict) and not i.get("desligado")]
    if len(ligados_ini) >= 6:
        do_usuario = [i["nome"] for i in ligados_ini if i.get("onde") in ("usuario", "pasta Inicializar")]
        barreiras.append(_b("inicializacao", "media" if len(ligados_ini) >= 10 else "baixa",
                            "Muitos programas abrem junto com o Windows",
                            "%d programas: %s." % (len(ligados_ini), ", ".join(i["nome"] for i in ligados_ini[:10])),
                            "Cada um come memória e atrasa o computador a ficar pronto.",
                            "Gerenciador de Tarefas (Ctrl+Shift+Esc) > Aplicativos de inicialização > Desabilitar. "
                            + ("Os do usuário (%s) o próprio aluno desliga; " % ", ".join(do_usuario[:5]) if do_usuario else "")
                            + "os do computador pedem administrador.",
                            ACOES_ALUNO if do_usuario else ACOES_TI))

    # --- Servicos ---------------------------------------------------------
    servicos = {s["nome"]: s for s in (fatos.get("servicos") or []) if isinstance(s, dict)}
    rodando = lambda n: bool(servicos.get(n, {}).get("rodando"))
    # HD mecanico: o coletor mede de verdade (disco_mecanico); o ARENA usa o
    # que o proprio Windows diz do disco C: (disco_windows_tipo).
    disco_lento = (fatos.get("disco_mecanico") is True
                   or str(fatos.get("disco_windows_tipo") or "").upper() == "HDD")
    if disco_lento and (rodando("SysMain") or rodando("WSearch")):
        quais = [n for n, texto in (("SysMain", "SysMain (pré-carregamento)"), ("WSearch", "Windows Search (indexação)"))
                 if rodando(n)]
        barreiras.append(_b("servicos_disco", "media", "Serviços que ocupam o disco mecânico",
                            ", ".join(quais) + " ligados num HD mecânico.",
                            "Num HD, esses serviços ficam lendo o disco o tempo todo, e o jogo espera.",
                            "O TI pode desativar esses serviços (services.msc) nas máquinas com HD.", ACOES_TI))
    # Servicos que nao servem para nada numa sala de aula (fax, loja de
    # demonstracao, mapas offline, Xbox, compartilhar musica do Media Player,
    # mensagens push de telemetria) e mesmo assim rodam.
    inuteis = {"Fax": "Fax", "RetailDemo": "Demonstração de loja", "MapsBroker": "Mapas baixados",
               "WMPNetworkSvc": "Compartilhamento do Windows Media Player",
               "XblAuthManager": "Xbox (conta)", "XblGameSave": "Xbox (salvar jogo na nuvem)",
               "XboxNetApiSvc": "Xbox (rede)", "dmwappushservice": "Mensagens push de telemetria"}
    ligados = [texto for nome, texto in inuteis.items() if rodando(nome)]
    if ligados:
        barreiras.append(_b("servicos_inuteis", "baixa", "Serviços que a escola não usa rodando",
                            ", ".join(ligados) + ".",
                            "Cada serviço ligado ocupa um pouco de memória e acorda de vez em quando.",
                            "O TI pode deixá-los em \"Manual\" ou \"Desativado\" (services.msc).", ACOES_TI))
    indexando = por_nome.get("searchindexer") or por_nome.get("searchprotocolhost")
    if indexando and indexando.get("cpu", 0) >= 10:
        barreiras.append(_b("indexando", "media", "O Windows está indexando os arquivos agora",
                            "A busca do Windows (%s) está usando %s%% do processador." % (
                                indexando["nome"], indexando.get("cpu")),
                            "Enquanto indexa, o Windows lê o disco sem parar -- num HD, tudo trava.",
                            "Espere terminar. Se acontecer toda aula, o TI pode desligar a indexação "
                            "da pasta do ARENA ou do disco (Opções de Indexação).", ACOES_TI))
    if rodando("DiagTrack") and fatos.get("telemetria_politica") not in (0, 1):
        barreiras.append(_b("telemetria", "baixa", "Telemetria do Windows no máximo",
                            "O serviço de telemetria (DiagTrack) está ligado, sem limite de política.",
                            "Envia dados de uso para a Microsoft em segundo plano. O peso é pequeno, mas existe.",
                            "O TI pode limitar por política: Configuração do Computador > Modelos Administrativos > "
                            "Componentes do Windows > Coleta de Dados > Permitir Telemetria = Básico.", ACOES_TI))
    if rodando("DoSvc") and disco_lento:
        barreiras.append(_b("otimizacao_entrega", "baixa", "Otimização de Entrega ligada",
                            "O Windows compartilha atualizações com outros computadores da rede.",
                            "Usa disco e internet da escola em segundo plano.",
                            "Configurações > Windows Update > Opções avançadas > Otimização de Entrega > desligar "
                            "\"Permitir downloads de outros computadores\".", ACOES_ALUNO))

    # --- Recursos visuais e de jogo do Windows ----------------------------
    if fatos.get("game_dvr") == 1 or fatos.get("captura_de_jogo") == 1:
        barreiras.append(_b("gravacao_fundo", "media", "Gravação de jogo em segundo plano ligada",
                            "O Xbox Game Bar está gravando o jogo o tempo todo (para \"gravar o que aconteceu\").",
                            "Gravar vídeo o tempo todo pesa na placa de vídeo e no processador.",
                            "Configurações > Jogos > Capturas > desligar \"Gravar o que aconteceu\".", ACOES_ALUNO))
    if fatos.get("modo_de_jogo") == 0:
        barreiras.append(_b("modo_de_jogo", "baixa", "Modo de Jogo do Windows desligado",
                            "O Modo de Jogo está desligado.",
                            "Com ele ligado, o Windows segura atualizações e dá prioridade ao jogo.",
                            "Configurações > Jogos > Modo de Jogo > ligar.", ACOES_ALUNO))
    if fatos.get("efeitos_visuais") not in (2, None) or fatos.get("transparencia") == 1:
        barreiras.append(_b("efeitos", "baixa", "Efeitos visuais do Windows ligados",
                            "Transparência e animações do Windows estão ligadas.",
                            "Em computador fraco, o próprio Windows gasta a placa de vídeo desenhando enfeites.",
                            "Configurações > Acessibilidade > Efeitos visuais > desligar transparência e animações.",
                            ACOES_ALUNO))
    if fatos.get("apps_segundo_plano_desligados") == 0:
        barreiras.append(_b("apps_fundo", "baixa", "Aplicativos rodando em segundo plano",
                            "Os aplicativos da loja podem rodar escondidos.",
                            "Mesmo fechados, continuam acordando e gastando.",
                            "Configurações > Privacidade > Aplicativos em segundo plano > desligar.", ACOES_ALUNO))

    # --- Energia ----------------------------------------------------------
    if fatos.get("tem_bateria") and fatos.get("na_tomada") is False:
        barreiras.append(_b("bateria", "alta", "Notebook na bateria",
                            "Fora da tomada (%s%%)." % fatos.get("bateria_pct"),
                            "Na bateria, o Windows segura o processador para economizar.",
                            "Ligue na tomada antes de jogar.", ACOES_ALUNO))
    if fatos.get("economia_de_bateria"):
        barreiras.append(_b("economia_bateria", "alta", "Economia de bateria ligada",
                            "O modo de economia de bateria está ativo.",
                            "Ele corta o desempenho de propósito.",
                            "Clique no ícone da bateria e desligue a Economia de bateria.", ACOES_ALUNO))
    plano = str(fatos.get("plano_de_energia") or "").lower()
    if "econom" in plano or "power saver" in plano:
        barreiras.append(_b("plano_energia", "media", "Plano de energia em Economia",
                            "Plano ativo: %s." % fatos.get("plano_de_energia"),
                            "Esse plano deixa o processador devagar de propósito.",
                            "Painel de Controle > Opções de Energia > Equilibrado (ou Alto desempenho).", ACOES_ALUNO))
    for chave, onde in (("processador_maximo_tomada", "na tomada"), ("processador_maximo_bateria", "na bateria")):
        valor = fatos.get(chave)
        if isinstance(valor, int) and valor < 100:
            barreiras.append(_b("processador_limitado_" + chave.split("_")[-1], "media",
                                "Processador limitado pelo plano de energia (%s)" % onde,
                                "O plano deixa o processador usar só %d%% %s." % (valor, onde),
                                "O jogo nunca recebe o processador inteiro.",
                                "Opções de Energia > Alterar configurações do plano > avançadas > Gerenciamento de "
                                "energia do processador > Estado máximo = 100%.", ACOES_ALUNO))

    # --- Disco e memoria virtual ------------------------------------------
    livre_pct = fatos.get("disco_windows_livre_pct")
    livre_gb = fatos.get("disco_windows_livre_gb")
    if isinstance(livre_pct, (int, float)) and (livre_pct < 10 or (livre_gb or 99) < 5):
        barreiras.append(_b("disco_cheio", "alta", "Disco do Windows quase cheio",
                            "Só %s GB livres (%s%%)." % (livre_gb, livre_pct),
                            "Com o disco cheio, o Windows não tem onde pôr a memória virtual e fica lento.",
                            "Configurações > Sistema > Armazenamento > Arquivos temporários > Remover.", ACOES_ALUNO))
    temp = fatos.get("temp_mb")
    if isinstance(temp, (int, float)) and temp >= 2048:
        barreiras.append(_b("temp", "baixa", "Pasta de arquivos temporários grande",
                            "%d MB em arquivos temporários." % temp,
                            "Ocupa disco à toa.",
                            "Configurações > Sistema > Armazenamento > Arquivos temporários > Remover.", ACOES_ALUNO))
    paginacao = fatos.get("arquivo_de_paginacao")
    if paginacao is not None and not any(str(x).strip() for x in (paginacao if isinstance(paginacao, list) else [paginacao])):
        barreiras.append(_b("sem_paginacao", "alta", "Memória virtual desligada",
                            "O Windows está sem arquivo de paginação.",
                            "Com 4 GB e sem memória virtual, programas fecham sozinhos quando a memória acaba.",
                            "O TI deve religar: Sistema > Configurações avançadas > Desempenho > Memória virtual > "
                            "Tamanho gerenciado pelo sistema.", ACOES_TI))

    # --- Video ------------------------------------------------------------
    video = str(fatos.get("video") or "").lower()
    if "basic display" in video or "básico" in video or "basico" in video:
        barreiras.append(_b("driver_video", "alta", "Sem driver de vídeo de verdade",
                            "O Windows está usando o \"Adaptador de Vídeo Básico\".",
                            "Sem o driver da placa, os jogos 3D ficam lentíssimos ou nem abrem.",
                            "O TI instala o driver da placa de vídeo (site do fabricante).", ACOES_TI))

    barreiras.sort(key=lambda b: GRAVIDADE[b["gravidade"]])
    return barreiras


def diagnosticar(disco_mecanico=None):
    """Coleta + avaliacao. 'disco_mecanico' vem do coletor (que mede o disco);
    o ARENA nao mede disco aqui (seria caro)."""
    inicio = time.time()
    fatos = coletar_fatos()
    if disco_mecanico is not None:
        fatos["disco_mecanico"] = disco_mecanico
    barreiras = avaliar(fatos)
    # Da lista de processos guarda so os 15 mais pesados: a lista inteira
    # diria demais sobre o que o aluno usa, e nao ajuda a decidir nada.
    procs = _processos(fatos)
    procs.sort(key=lambda p: (-p.get("cpu", 0), -p.get("mb", 0)))
    fatos["processos"] = procs[:15]
    fatos["processos_total"] = len(procs)
    return {"barreiras": barreiras, "fatos": fatos,
            "nao_deu_para_ler": fatos.get("nao_deu_para_ler", []),
            "segundos": round(time.time() - inicio, 1)}


# O que a checagem rapida (na hora de jogar) pode acusar: so o grave e o
# que da para medir num instante, sem PowerShell.
IDS_RAPIDOS = ("memoria", "bateria", "economia_bateria")


def avaliar_rapido(fatos):
    return [b for b in avaliar(fatos) if b["id"] in IDS_RAPIDOS and b["gravidade"] == "alta"]


def checagem_rapida():
    """Chamada ao abrir um jogo: memoria quase cheia, notebook na bateria,
    economia de bateria ligada. Leva milissegundos. Nunca levanta erro."""
    if not sys.platform.startswith("win"):
        return []
    try:
        return avaliar_rapido(_memoria_e_energia(rapido=True))
    except Exception:
        return []


def fechar_programa(nome):
    """Fecha um programa da lista FECHAVEIS (so os do proprio usuario: o
    taskkill sem administrador nao consegue fechar os do sistema). Devolve
    (ok, mensagem)."""
    nome = str(nome or "").strip().lower()
    if nome not in FECHAVEIS:
        return False, "Esse programa não está na lista dos que o ARENA pode fechar."
    r = subprocess.run(["taskkill", "/IM", nome + ".exe", "/F"], capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode == 0:
        return True, "%s fechado." % FECHAVEIS[nome]
    return False, "Não consegui fechar %s (talvez já estivesse fechado)." % FECHAVEIS[nome]


if __name__ == "__main__":
    resultado = diagnosticar()
    for b in resultado["barreiras"]:
        print("[%s] %s -- %s" % (b["gravidade"].upper(), b["titulo"], b["achado"]))
        print("      O que fazer (%s): %s" % (b["quem"], b["acao"]))
    print("(%s s; nao deu para ler: %s)" % (resultado["segundos"], resultado["nao_deu_para_ler"] or "nada"))
