# -*- coding: utf-8 -*-
r"""Medidor da escala da tela (item 10 dos pedidos de 15/10/2026).

Pergunta que ele responde: quanto custa, NESTA maquina, cada jeito de
desenhar o jogo e de esticar a imagem ate a tela, e como fica a imagem.

Para cada CENA (um jogo e um trecho com 3D na tela, achado de antemao):
  1. PREPARO: abre o jogo com as opcoes reais do ARENA, espera chegar ao
     trecho (a abertura ou a demonstracao do proprio jogo; ninguem aperta
     botao) e salva um estado, numa pasta temporaria. Uma vez por cena.
  2. Para cada JEITO (o de hoje e as alternativas): abre o jogo ja no
     estado salvo (-e 0), espera ASSENTAR segundos e mede por MEDINDO
     segundos, no ritmo de jogo (com vsync, como o aluno joga):
       - quadros por segundo (o contador do titulo da janela: fps_show e
         framecount_show). Abaixo da tela (60) = a maquina nao deu conta;
       - % da placa de video: o motor 3D do RetroArch, pelo contador "GPU
         Engine" do Windows (o mesmo do Gerenciador de Tarefas), pedido em
         ingles (PdhAddEnglishCounterW) para valer em Windows de qualquer
         lingua, sem administrador;
       - % do processador, de UM nucleo (GetProcessTimes);
     e tira a foto da imagem final, ja com o filtro e do tamanho da tela
     (video_gpu_screenshot).

Por que no ritmo de jogo, e nao "sem trava" (quantos quadros a maquina
faria sem esperar a tela): o driver pode forcar o vsync. Achado de
16/10/2026: na Radeon do professor, "Aguardar atualizacao vertical" esta em
"Sempre ligado" (VSyncControl = 3 no registro; o padrao da AMD e' 1) e
nenhum programa passa de 60 quadros. A % da placa vale em qualquer
maquina: com 60 quadros garantidos, ela diz quanto sobra.

Cuidado ao ler a % da placa: a placa baixa o proprio relogio quando o
trabalho e' pouco, e o mesmo trabalho aparece com % maior. Compare jeitos
da mesma cena, na mesma maquina, e nao um numero solto.

As opcoes sao as REAIS do ARENA: a mesma preparacao da matriz de consoles
(testes\teste_matriz_consoles.py -> preparar_sessao). Tudo numa pasta
temporaria (saves, estados, fotos, opcoes), com o retroarch.cfg de verdade
protegido (testes\protege_cfg). O jogo roda em tela cheia sem borda, como o
aluno joga, e mudo.

Uso:
    servidor\python\python.exe ferramentas\medir_escala.py [--cenas=ps1,psp]
        [--jeitos=hoje,fsr] [--saida=arquivo.json] [--fotos=pasta] [--alvo]
  --alvo: dentro da caixa do modo alvo (ferramentas\modo_alvo.py): o
          processador fica como o do Celeron N5100; a placa nao.
"""
import ctypes
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import teste_matriz_consoles as matriz  # noqa: E402

arena = matriz.arena
hardware = arena.hardware
PASTA_SHADERS = os.path.join(RAIZ, "retroarch", "shaders", "shaders_slang")
ASSENTAR = 3        # segundos depois do estado carregado, antes de medir
MEDINDO = 10        # segundos de medicao
# A foto sai no MESMO quadro em todo jeito (--max-frames a partir do estado
# salvo): o RetroArch roda este numero de quadros, tira a foto e fecha.
# Com a foto por comando, cada jeito saia num instante diferente da corrida.
QUADROS_ATE_A_FOTO = 60 * (ASSENTAR + MEDINDO + 5)
ESPERA_PREPARO = 300

# O trecho de cada jogo, olhado foto a foto em 16/10/2026 (o jogo sozinho,
# sem ninguem apertar botao): a partir deste quadro, ha 3D na tela por mais
# tempo do que a medicao dura.
CENAS = {
    "ps1": {"titulo": "CTR", "quadro": 6300,
            "o_que": "a abertura em 3D (a nave do Nitros Oxide)"},
    "psp": {"titulo": "Burnout Legends", "quadro": 3000,
            "o_que": "a tela-titulo, com corrida em 3D atras"},
    "n64": {"titulo": "Mario Kart 64", "quadro": 2100,
            "o_que": "a corrida de demonstracao"},
    "dreamcast": {"titulo": "Gauntlet Legends", "quadro": 7000,
                  "o_que": "a abertura em 3D"},
    "snes": {"titulo": "Super Bomberman 4", "quadro": 1500,
             "o_que": "desenho 2D (pixel)"},
}

# Degraus de resolucao interna de cada nucleo: a chave e os valores, do 1x
# (o tamanho do console) para cima. Conferidos nas opcoes de cada nucleo.
DEGRAUS = {
    "swanstation": ("swanstation_GPU_ResolutionScale",
                    {"1x": "1", "2x": "2", "3x": "3", "4x": "4", "6x": "6", "9x": "9"}),
    "ppsspp": ("ppsspp_internal_resolution",
               {"1x": "480x272", "2x": "960x544", "3x": "1440x816", "4x": "1920x1088",
                "6x": "2880x1632"}),
    "mupen64plus_next": ("mupen64plus-EnableNativeResFactor",
                         {"1x": "1", "2x": "2", "3x": "3", "4x": "4", "6x": "6"}),
    "flycast": ("reicast_internal_resolution",
                {"1x": "640x480", "2x": "1280x960", "3x": "1920x1440", "4x": "2560x1920",
                 "6x": "3840x2880"}),
}

# Filtros que o medidor escreve na pasta dele (a referencia aponta para os
# shaders que vem com o RetroArch do ARENA).
FILTROS = {
    # FSR 1 da AMD (licenca MIT): EASU estica, RCAS devolve a nitidez. O
    # preset do RetroArch liga um grao de filme (0,3): aqui, sem grao.
    "fsr": ("edge-smoothing/fsr/fsr.slangp", {"FSR_SHARPENING": "0.2", "FSR_FILMGRAIN": "0.0"}),
    # So o primeiro passo do FSR (o EASU, que estica), sem o RCAS.
    "easu": ("edge-smoothing/fsr/fsr-easu.slangp", {}),
    # Os classicos de esticar foto, em dois passos simples (vertical e
    # horizontal): mais nitidos que o bilinear, mais baratos que o EASU.
    "catmull": ("interpolation/catmull-rom-fast.slangp", {}),
    "lanczos": ("interpolation/lanczos2-fast.slangp", {}),
    # So o RCAS (a nitidez do FSR) no quadro ainda pequeno; o RetroArch
    # estica depois com o bilinear.
    "rcas": ("sharpen/rca_sharpen.slangp", {}),
    "pixel": ("pixel-art-scaling/sharp-bilinear-simple.slangp", {}),
    "xbr": ("edge-smoothing/xbr/xbr-lv2.slangp", {}),
    "scalefx": ("edge-smoothing/scalefx/scalefx.slangp", {}),
    "anime4k": ("sharpen/Anime4k.slangp", {}),
}


def jeitos_da_cena(nucleo):
    """Os jeitos a comparar para este nucleo: o de hoje e as alternativas.

    Cada jeito: (nome, rotulo, opcoes do nucleo, filtro, opcoes do RetroArch).
    filtro None = o que o ARENA escolheu hoje; "" = nenhum.
    """
    jeitos = [("hoje", "o ARENA de hoje", {}, None, {})]
    sem_filtro_borrado = {"video_shader_enable": "false", "video_smooth": "true"}
    sem_filtro_cru = {"video_shader_enable": "false", "video_smooth": "false"}
    com_filtro = {"video_shader_enable": "true"}
    if nucleo in DEGRAUS:
        chave, degraus = DEGRAUS[nucleo]
        for degrau in ("1x", "2x", "4x", "6x"):
            if degrau not in degraus:
                continue
            opcao = {chave: degraus[degrau]}
            jeitos.append((degrau, "%s, esticado pelo bilinear" % degrau, opcao, "", sem_filtro_borrado))
            jeitos.append((degrau + "+fsr", "%s, esticado pelo FSR" % degrau, opcao, "fsr", com_filtro))
        # Na resolucao de hoje, os outros jeitos de esticar.
        if nucleo == "mupen64plus_next":
            # O parallel-rdp (Vulkan): desenha como o N64 de verdade (o HUD
            # do Mario Kart sai certo); o ARENA o liga da nota 4 da placa.
            for degrau in ("1x", "2x"):
                jeitos.append(("parallel_" + degrau, "parallel-rdp %s" % degrau,
                               {"mupen64plus-rdp-plugin": "parallel",
                                "mupen64plus-parallel-rdp-synchronous": "True",
                                "mupen64plus-parallel-rdp-upscaling": degrau}, "", sem_filtro_borrado))
        for filtro, rotulo in (("easu", "so o EASU do FSR"), ("catmull", "Catmull-Rom"),
                               ("lanczos", "Lanczos 2"), ("rcas", "so a nitidez (RCAS)"),
                               ("pixel", "pixel nitido")):
            extra = dict(com_filtro, video_smooth="true") if filtro == "rcas" else com_filtro
            jeitos.append(("hoje+" + filtro, "hoje, esticado: %s" % rotulo, {}, filtro, extra))
    else:
        jeitos += [
            ("cru", "pixel cru (vizinho mais proximo)", {}, "", sem_filtro_cru),
            ("bilinear", "bilinear (borrado)", {}, "", sem_filtro_borrado),
            ("pixel", "pixel nitido (sharp-bilinear)", {}, "pixel", com_filtro),
            ("fsr", "FSR", {}, "fsr", com_filtro),
            ("catmull", "Catmull-Rom", {}, "catmull", com_filtro),
            ("xbr", "xBR nivel 2", {}, "xbr", com_filtro),
            ("scalefx", "ScaleFX", {}, "scalefx", com_filtro),
            ("anime4k", "Anime4K", {}, "anime4k", com_filtro),
        ]
    return jeitos


# ---------------------------------------------------------------------------
# A % da placa de video, por processo (PDH, sem administrador)
# ---------------------------------------------------------------------------
class _VALOR(ctypes.Structure):
    _fields_ = [("CStatus", wintypes.DWORD), ("doubleValue", ctypes.c_double)]


class _ITEM(ctypes.Structure):
    _fields_ = [("szName", wintypes.LPWSTR), ("FmtValue", _VALOR)]


class UsoDaPlaca:
    """Soma o "Utilization Percentage" do motor 3D de um processo.

    O contador e' uma taxa: cada leitura vale para o tempo desde a anterior.
    """
    def __init__(self):
        self.pdh = ctypes.WinDLL("pdh")
        p = self.pdh
        p.PdhOpenQueryW.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        p.PdhAddEnglishCounterW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p)]
        p.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
        p.PdhGetFormattedCounterArrayW.argtypes = [ctypes.c_void_p, wintypes.DWORD,
                                                   ctypes.POINTER(wintypes.DWORD),
                                                   ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        p.PdhCloseQuery.argtypes = [ctypes.c_void_p]
        for nome in ("PdhOpenQueryW", "PdhAddEnglishCounterW", "PdhCollectQueryData",
                     "PdhGetFormattedCounterArrayW", "PdhCloseQuery"):
            getattr(p, nome).restype = wintypes.LONG
        self.consulta, self.contador = ctypes.c_void_p(), ctypes.c_void_p()
        if p.PdhOpenQueryW(None, None, ctypes.byref(self.consulta)) != 0:
            raise OSError("PdhOpenQueryW falhou")
        if p.PdhAddEnglishCounterW(self.consulta, r"\GPU Engine(*)\Utilization Percentage", None,
                                   ctypes.byref(self.contador)) != 0:
            raise OSError("o Windows nao tem o contador GPU Engine")
        p.PdhCollectQueryData(self.consulta)

    def ler(self, pid):
        """% do motor 3D do processo desde a leitura anterior (soma dos motores)."""
        p = self.pdh
        p.PdhCollectQueryData(self.consulta)
        tamanho, quantos = wintypes.DWORD(0), wintypes.DWORD(0)
        p.PdhGetFormattedCounterArrayW(self.contador, 0x200, ctypes.byref(tamanho), ctypes.byref(quantos), None)
        if not tamanho.value:
            return 0.0
        memoria = ctypes.create_string_buffer(tamanho.value)
        if p.PdhGetFormattedCounterArrayW(self.contador, 0x200, ctypes.byref(tamanho), ctypes.byref(quantos),
                                          memoria) != 0:
            return 0.0
        itens = ctypes.cast(memoria, ctypes.POINTER(_ITEM))
        prefixo = "pid_%d_" % pid
        return sum(itens[i].FmtValue.doubleValue for i in range(quantos.value)
                   if itens[i].szName.startswith(prefixo) and itens[i].szName.endswith("engtype_3D"))

    def fechar(self):
        self.pdh.PdhCloseQuery(self.consulta)


# ---------------------------------------------------------------------------
# A maquina
# ---------------------------------------------------------------------------
def vsync_forcado_pela_amd():
    """O driver da AMD forca o vsync? (so leitura do registro, sem administrador).

    VSyncControl: "0"/"1" = o programa decide; "2" = ligado, a menos que o
    programa peca o contrario; "3" = sempre ligado. None = nao e' AMD, ou nao
    deu para ler."""
    if os.name != "nt":
        return None
    import winreg
    base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    for i in range(10):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base + "\\%04d\\UMD" % i) as chave:
                valor, _tipo = winreg.QueryValueEx(chave, "VSyncControl")
        except OSError:
            continue
        texto = valor.decode("ascii", "replace").strip("\x00") if isinstance(valor, bytes) else str(valor)
        return texto
    return None


def a_maquina():
    usuario = ctypes.WinDLL("user32")
    gdi = ctypes.WinDLL("gdi32")
    usuario.GetDC.restype = ctypes.c_void_p
    usuario.GetDC.argtypes = [ctypes.c_void_p]
    usuario.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
    dc = usuario.GetDC(None)
    try:
        largura, altura, hz = (gdi.GetDeviceCaps(dc, 118), gdi.GetDeviceCaps(dc, 117),
                               gdi.GetDeviceCaps(dc, 116))
    finally:
        usuario.ReleaseDC(None, dc)
    return {
        "processador": str(hardware.processador()),
        "placa": hardware.placa_video(),
        "motor_de_video": hardware.driver_video(),
        "tela": "%dx%d" % (largura, altura), "hz": hz,
        "nota": arena.CAPACIDADE.get("nota"), "nota_gpu": arena.CAPACIDADE.get("nota_gpu"),
        "vsync_da_amd": vsync_forcado_pela_amd(),
    }


# ---------------------------------------------------------------------------
# Cada jeito
# ---------------------------------------------------------------------------
def escrever_filtro(nome, pasta):
    """Preset do filtro na pasta do medidor; None se o shader nao veio."""
    relativo, parametros = FILTROS[nome]
    base = os.path.join(PASTA_SHADERS, relativo.replace("/", os.sep))
    if not os.path.isfile(base):
        return None
    caminho = os.path.join(pasta, "filtro_%s.slangp" % nome)
    linhas = ['#reference "%s"' % base.replace("\\", "/")]
    linhas += ['%s = "%s"' % item for item in sorted(parametros.items())]
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")
    return caminho


def trocar_linhas(caminho, novas):
    """Troca (ou acrescenta) chave = "valor" num arquivo de opcoes."""
    with open(caminho, encoding="utf-8") as arquivo:
        linhas = [l for l in arquivo.read().splitlines()
                  if not any(l.startswith(c + " = ") for c in novas)]
    linhas += ['%s = "%s"' % item for item in sorted(novas.items())]
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")


def ler_opcao(caminho, chave):
    with open(caminho, encoding="utf-8") as arquivo:
        achado = re.findall(r'^%s = "([^"]*)"' % re.escape(chave), arquivo.read(), re.M)
    return achado[-1] if achado else None


SO_DO_MEDIDOR = {
    "video_fullscreen": "true", "video_windowed_fullscreen": "true",
    "video_gpu_screenshot": "true", "audio_mute_enable": "true",
    "video_font_enable": "false", "fps_update_interval": "15",
    "savestate_thumbnail_enable": "false", "savestate_auto_load": "false",
    "savestate_auto_save": "false",
}


def abrir(pasta_sessao, jogo, plataforma, nucleo_curto, opcoes_nucleo, filtro_jeito, opcoes_ra,
          pasta_filtros, estado, foto=None):
    """Grava as opcoes do jeito e abre o RetroArch. Devolve (processo, linha, filtro)."""
    override, filtro_hoje, pastas = matriz.preparar_sessao(jogo, plataforma, False, pasta_sessao)
    trocar_linhas(override, dict(SO_DO_MEDIDOR, **opcoes_ra))
    nucleo_cfg = os.path.join(pasta_sessao, "retroarch-core-options.cfg")
    if opcoes_nucleo:
        trocar_linhas(nucleo_cfg, opcoes_nucleo)
    if filtro_jeito is None:
        filtro = filtro_hoje
    elif filtro_jeito == "":
        filtro = ""
    else:
        filtro = escrever_filtro(filtro_jeito, pasta_filtros) or ""
    linha = [matriz.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", plataforma["core"]),
             "--appendconfig", override]
    if filtro:
        linha += ["--set-shader", filtro]
    if estado:
        linha += ["-e", "0"]
    if foto:
        linha += ["--max-frames=%d" % QUADROS_ATE_A_FOTO, "--max-frames-ss",
                  "--max-frames-ss-path=" + foto]
    linha.append(os.path.join(RAIZ, jogo["arquivo"]))
    saida = open(os.path.join(pasta_sessao, "stdout.log"), "w")
    processo = subprocess.Popen(linha, cwd=os.path.join(RAIZ, "retroarch"), stdout=saida,
                                stderr=subprocess.STDOUT)
    processo._saida_medidor = saida
    return processo, override, nucleo_cfg, filtro, pastas


def fechar(processo):
    matriz.comando("QUIT")
    try:
        processo.wait(20)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait(10)
    processo._saida_medidor.close()


def esperar_quadros(processo, alvo, limite):
    inicio = time.monotonic()
    while time.monotonic() - inicio < limite and processo.poll() is None:
        lido = matriz.fps_e_quadros(processo.pid)
        if lido and lido[1] >= alvo:
            return lido
        time.sleep(0.1)
    return None


def preparar_cena(chave, cena, jogo, plataforma, pasta_sessao, pasta_filtros):
    """Chega ao trecho e salva o estado (slot 0) na pasta temporaria."""
    nucleo_curto = arena.nome_curto_do_core(plataforma["core"])
    processo, *_resto, pastas = abrir(pasta_sessao, jogo, plataforma, nucleo_curto, {}, None, {},
                                      pasta_filtros, estado=False)
    try:
        if not esperar_quadros(processo, cena["quadro"], ESPERA_PREPARO):
            return None, "nao chegou ao quadro %d" % cena["quadro"]
        antes = matriz.arquivos(pastas["PASTA_STATES"])
        matriz.comando("SAVE_STATE")
        for _ in range(40):
            time.sleep(0.5)
            depois = matriz.arquivos(pastas["PASTA_STATES"])
            novos = [c for c in depois if depois[c] > antes.get(c, -1) and depois[c] > 0]
            if novos:
                time.sleep(2)     # o arquivo grande ainda pode estar sendo escrito
                return novos, None
        return None, "o estado nao foi salvo"
    finally:
        fechar(processo)


def medir_jeito(cena, jogo, plataforma, pasta_sessao, pasta_filtros, jeito, placa, pasta_fotos, chave):
    nome, rotulo, opcoes_nucleo, filtro_jeito, opcoes_ra = jeito
    nucleo_curto = arena.nome_curto_do_core(plataforma["core"])
    resultado = {"cena": chave, "jogo": jogo["titulo"], "nucleo": nucleo_curto, "jeito": nome,
                 "rotulo": rotulo}
    foto = os.path.join(pasta_fotos, "%s_%s.png" % (chave, nome.replace("+", "_")))
    if os.path.exists(foto):
        os.remove(foto)
    processo, override, nucleo_cfg, filtro, pastas = abrir(
        pasta_sessao, jogo, plataforma, nucleo_curto, opcoes_nucleo, filtro_jeito, opcoes_ra,
        pasta_filtros, estado=True, foto=foto)
    try:
        if nucleo_curto in DEGRAUS:
            resultado["resolucao_interna"] = ler_opcao(nucleo_cfg, DEGRAUS[nucleo_curto][0])
        resultado["filtro"] = os.path.basename(filtro) if filtro else ""
        resultado["suavizar"] = ler_opcao(override, "video_smooth")
        if not esperar_quadros(processo, 1, 60):
            resultado["erro"] = "nao abriu"
            return resultado
        time.sleep(ASSENTAR)
        placa.ler(processo.pid)
        t0, cpu0, q0 = time.monotonic(), matriz.tempo_de_processador(processo.pid), matriz.fps_e_quadros(processo.pid)
        amostras = []
        while time.monotonic() - t0 < MEDINDO:
            time.sleep(1.0)
            amostras.append(placa.ler(processo.pid))
        t1, cpu1, q1 = time.monotonic(), matriz.tempo_de_processador(processo.pid), matriz.fps_e_quadros(processo.pid)
        if q0 and q1:
            resultado["quadros_por_segundo"] = round((q1[1] - q0[1]) / (t1 - t0), 1)
        if cpu0 is not None and cpu1 is not None:
            resultado["processador_pct_de_um_nucleo"] = round(100 * (cpu1 - cpu0) / (t1 - t0), 1)
        if amostras:
            resultado["placa_pct"] = round(sum(amostras) / len(amostras), 1)
            resultado["placa_pct_maior"] = round(max(amostras), 1)
        # A foto: o RetroArch tira sozinho no quadro QUADROS_ATE_A_FOTO e fecha.
        limite = time.monotonic() + 90
        while processo.poll() is None and time.monotonic() < limite:
            time.sleep(0.25)
        if os.path.isfile(foto) and os.path.getsize(foto) > 2000:
            resultado["foto"] = foto
        else:
            resultado["foto_erro"] = "o RetroArch nao gravou a foto no quadro %d" % QUADROS_ATE_A_FOTO
    finally:
        fechar(processo)
    return resultado


def achar_jogo(titulo):
    plataformas, _ = matriz.indexador.carregar_plataformas()
    resultado = matriz.indexador.indexar(forcar=True)
    jogos = resultado["jogos"] if isinstance(resultado, dict) else resultado
    for jogo in jogos:
        if jogo["titulo"].lower().startswith(titulo.lower()):
            return jogo, plataformas[jogo["plataforma"]]
    return None, None


def argumento(nome, padrao=None):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    if "--alvo" in sys.argv:
        import modo_alvo
        modo_alvo.entrar()
    # --nota-placa=N: o "hoje" como se a placa tirasse a nota N (para saber
    # se ela aguenta o degrau de cima antes de mudar a nota de verdade).
    if argumento("nota-placa"):
        arena.CAPACIDADE["nota_gpu"] = int(argumento("nota-placa"))
        arena.CAPACIDADE["nota"] = max(arena.CAPACIDADE["nota"], int(argumento("nota-placa")))
    agora = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    saida = argumento("saida", os.path.join(tempfile.gettempdir(), "medir_escala_%s.json" % agora))
    pasta_fotos = argumento("fotos", os.path.splitext(saida)[0] + "_fotos")
    os.makedirs(pasta_fotos, exist_ok=True)
    cenas = [c for c in argumento("cenas", ",".join(CENAS)).split(",") if c in CENAS]
    so_jeitos = argumento("jeitos")
    relatorio = {"data": agora, "modo_alvo": "--alvo" in sys.argv,
                 "nota_placa_simulada": argumento("nota-placa"), "maquina": a_maquina(),
                 "assentar_s": ASSENTAR, "medindo_s": MEDINDO, "resultados": [], "cenas": {}}
    print("Maquina:", json.dumps(relatorio["maquina"], ensure_ascii=False))
    placa = UsoDaPlaca()
    temporaria = tempfile.mkdtemp(prefix="arena_medir_escala_")
    try:
        for chave in cenas:
            cena = CENAS[chave]
            jogo, plataforma = achar_jogo(cena["titulo"])
            if not jogo:
                print("[%s] jogo nao esta nesta maquina: %s" % (chave, cena["titulo"]))
                relatorio["cenas"][chave] = {"erro": "jogo nao esta nesta maquina"}
                continue
            pasta_sessao = os.path.join(temporaria, chave)
            os.makedirs(pasta_sessao)
            print("[%s] %s: preparando o trecho (quadro %d)..." % (chave, jogo["titulo"], cena["quadro"]))
            estados, erro = preparar_cena(chave, cena, jogo, plataforma, pasta_sessao, temporaria)
            relatorio["cenas"][chave] = {"jogo": jogo["titulo"], "quadro": cena["quadro"],
                                         "o_que": cena["o_que"], "erro": erro}
            if erro:
                print("   ", erro)
                continue
            nucleo_curto = arena.nome_curto_do_core(plataforma["core"])
            for jeito in jeitos_da_cena(nucleo_curto):
                if so_jeitos and jeito[0] not in so_jeitos.split(","):
                    continue
                r = medir_jeito(cena, jogo, plataforma, pasta_sessao, temporaria, jeito, placa,
                                pasta_fotos, chave)
                relatorio["resultados"].append(r)
                print("   %-10s %-34s quadros/s %5s | placa %5s%% | processador %5s%% | %s %s" % (
                    jeito[0], jeito[1][:34], r.get("quadros_por_segundo"), r.get("placa_pct"),
                    r.get("processador_pct_de_um_nucleo"), r.get("resolucao_interna") or "",
                    r.get("erro") or ""))
                with open(saida, "w", encoding="utf-8") as arquivo:
                    json.dump(relatorio, arquivo, ensure_ascii=False, indent=1)
    finally:
        placa.fechar()
        limpeza.apagar_pasta(temporaria)
    print("Resultado:", saida)
    print("Fotos:", pasta_fotos)
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
