# -*- coding: utf-8 -*-
r"""As medidas do item 15, iguais em todo sistema (o Windows de verdade, o
Linux do conteiner, o Android do aparelho virtual).

Pedido do Rafael (15/10/2026, item 15): "testes nos sistemas virtuais
(Docker e WSL), com numeros e descontando a perda de rodar dentro de outro
sistema". Aqui fica o que se mede, do mesmo jeito em cada lugar; quem junta
e faz as contas e' o testes\teste_sistemas_virtuais.py.

  1. O processador: a mesma conta do hardware.velocidade_de_um_nucleo (a
     que da a nota do ARENA), com mais rodadas. A razao entre a de dentro e
     a do Windows e' a "perda" de rodar dentro do outro sistema.
  2. O RetroArch sem freio: o video e o som "null" (nada de placa nem de
     caixa de som: so o trabalho do emulador), sem esperar a tela nem o som,
     com um jogo livre de cada nucleo (testes\jogos_livres) e as BIOS
     livres. Pelo metodo das duas rodadas do ferramentas\medir_arena.py: 60
     quadros e uma rodada longa (3000, ou mais, ate durar uns 8 s);
     quadros por segundo = (quadros da longa - 60) / (tempo da longa -
     tempo da curta), o que tira o tempo de abrir e fechar o RetroArch. So
     com a configuracao da medida (--config), nunca por cima da do ARENA.
  3. A gravacao em disco (hardware.medir_velocidade), na pasta de trabalho.

Uso (cada sistema roda com o proprio Python do ARENA):
    python testes\medidas_virtuais.py <programa do RetroArch> <pasta dos nucleos> <extensao> [saida.json]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _pasta in (AQUI, os.path.join(RAIZ, "servidor")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

QUADROS = (60, 3000)
# Os nucleos medidos: os de computador antigo que abrem com jogo livre e BIOS
# livre (o processador faz todo o trabalho; nenhum usa a placa). O CHIP-8
# ficou de fora: e' leve demais, e 3000 quadros passam no tempo de abrir e
# fechar o RetroArch (a conta dava zero ou negativo, 21/10/2026).
CONSOLES = ("msx", "vic20", "zx81")


def jogos_da_medida():
    """[(console, nucleo, jogo de testes\\jogos_livres)] dos CONSOLES."""
    with open(os.path.join(AQUI, "jogos_livres", "lista.json"), encoding="utf-8") as arquivo:
        lista = json.load(arquivo)["arquivos"]
    with open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        consoles = {p["id"]: p for p in json.load(arquivo)["plataformas"]}
    saida = []
    for console in CONSOLES:
        item = next((j for j in lista if j["console"] == console), None)
        if item and consoles.get(console, {}).get("core"):
            saida.append((console, os.path.splitext(consoles[console]["core"])[0],
                          os.path.join(AQUI, "jogos_livres", *item["origem"].split("/"))))
    return saida


def cfg_sem_freio(pasta, sistema, controle="null"):
    """O retroarch.cfg da medida: sem video nem som de verdade, sem esperar
    a tela nem o som (o RetroArch corre o mais rapido que puder), sem nada
    que pese a mais (rebobinar, adiantar quadro), as pastas na de trabalho.
    'controle': o driver de controle. A medida nao precisa de controle, e
    sem video o RetroArch do Linux tentava o do X11 ("x") e fechava na hora
    ("Cannot initialize input driver", 21/10/2026). None deixa o do sistema
    (o Android, medido assim em 21/10)."""
    opcoes = {
        "video_driver": "null", "audio_driver": "null", "audio_enable": "false", "video_vsync": "false",
        "audio_sync": "false", "video_threaded": "false", "rewind_enable": "false", "run_ahead_enabled": "false",
        # O retroarch.cfg do ARENA liga a sincronia com a taxa exata do jogo:
        # com ela, o laco do RetroArch dorme ate o proximo quadro (runloop.c,
        # "if there's a fast forward limit, inject sleeps").
        "vrr_runloop_enable": "false",
        "pause_nonactive": "false", "config_save_on_exit": "false", "input_autodetect_enable": "false",
        "fps_show": "false", "notification_show_autoconfig": "false", "menu_driver": "rgui",
        "savefile_directory": os.path.join(pasta, "saves"), "savestate_directory": os.path.join(pasta, "states"),
        "screenshot_directory": os.path.join(pasta, "fotos"), "cache_directory": os.path.join(pasta, "cache"),
        "system_directory": sistema, "libretro_info_path": os.path.join(RAIZ, "retroarch", "info"),
        "log_to_file": "false", "network_cmd_enable": "false", "global_core_options": "true",
        "core_options_path": os.path.join(pasta, "opcoes.opt"),
    }
    if controle:
        opcoes["input_driver"] = controle
    for chave in ("savefile_directory", "savestate_directory", "screenshot_directory", "cache_directory"):
        os.makedirs(opcoes[chave], exist_ok=True)
    caminho = os.path.join(pasta, "medida.cfg")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("".join('%s = "%s"\n' % par for par in sorted(opcoes.items())))
    return caminho


def segundos_de(comando, limite=300):
    """O tempo de parede de um comando (o RetroArch fecha sozinho no fim, com
    o codigo 0). Saiu com erro: None. Antes o tempo de quem caiu na hora
    (0,03 s) virava bilhoes de quadros por segundo (o Linux, 21/10/2026)."""
    inicio = time.perf_counter()
    try:
        processo = subprocess.run(comando, timeout=limite, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
    except (subprocess.TimeoutExpired, OSError):    # travou, ou o programa nem abriu
        return None
    if processo.returncode != 0:
        return None
    return time.perf_counter() - inicio


# A rodada longa precisa durar uns segundos: com 3000 quadros, o MSX do
# Windows acabava em 0,1 s, e o ruido de abrir e fechar o RetroArch engolia a
# conta (21/10/2026). A de 3000 vira a rodada de prova, que diz quantos
# quadros dao uns SEGUNDOS_DA_LONGA.
SEGUNDOS_DA_LONGA = 8.0
QUADROS_NO_MAXIMO = 400000


REPETICOES = 2      # cada medida sai duas vezes: a diferenca entre elas mostra o ruido


def _uma_medida(montar_comando, medir):
    curta = medir(montar_comando(QUADROS[0]))
    if curta is None:
        return {"fps": None, "curta_s": None}
    quadros, longa = QUADROS[1], medir(montar_comando(QUADROS[1]))
    # Ate a longa durar uns segundos, em degraus (de 4 a 20 vezes mais
    # quadros por vez): a estimativa tirada de uma rodada curta demais e'
    # quase so ruido, e o salto direto passava muito do ponto.
    for _ in range(3):
        if longa is None or longa - curta >= SEGUNDOS_DA_LONGA / 2:
            break
        rapidez = (quadros - QUADROS[0]) / max(longa - curta, 0.05)
        proximos = int(min(QUADROS_NO_MAXIMO, max(quadros * 4, min(rapidez * SEGUNDOS_DA_LONGA, quadros * 20))))
        if proximos <= quadros:
            break
        quadros, longa = proximos, medir(montar_comando(proximos))
    # A longa tem de durar de verdade: com o maximo de quadros e menos de um
    # segundo a mais que a curta, o jogo nem rodou (a conta seria ruido).
    if longa is None or longa - curta < SEGUNDOS_DA_LONGA / 8:
        return {"fps": None, "curta_s": round(curta, 2), "longa_s": longa, "quadros": quadros}
    return {"fps": round((quadros - QUADROS[0]) / (longa - curta), 1), "curta_s": round(curta, 2),
            "longa_s": round(longa, 2), "quadros": quadros}


def fps_sem_freio(montar_comando, medir=segundos_de):
    """Quadros por segundo pelo metodo das duas rodadas. 'montar_comando'
    recebe o numero de quadros e devolve a linha de comando; 'medir' diz
    quantos segundos ela levou (no Android, pelo adb). A curta (60 quadros)
    e' o tempo de abrir e fechar; a longa tem quadros bastantes para durar
    uns SEGUNDOS_DA_LONGA. Sai a media das rodadas que deram certo (quantas,
    em "rodadas_boas"), com cada uma ao lado."""
    rodadas = [_uma_medida(montar_comando, medir) for _ in range(REPETICOES)]
    boas = [r["fps"] for r in rodadas if r.get("fps")]
    return {"fps": round(sum(boas) / len(boas), 1) if boas else None, "rodadas_boas": len(boas),
            "rodadas": rodadas}


def velocidade_do_processador():
    import hardware
    return hardware.velocidade_de_um_nucleo(rodadas=21)


def gravacao_em_disco(pasta):
    import hardware
    try:
        return hardware.medir_velocidade(pasta)
    except Exception as falha:          # a medida nao derruba as outras
        return {"erro": str(falha)}


def medir_aqui(programa, pasta_nucleos, extensao):
    """Todas as medidas neste sistema. 'programa' e' o RetroArch daqui
    (retroarch.exe; no Linux, o AppRun do AppImage tirado para o cache). O
    RetroArch roda so com a configuracao da medida (--config): por cima da
    do ARENA (--appendconfig), algum ajuste de jogo o prendia em uns 90
    quadros por segundo em qualquer nucleo (visto no Windows em 21/10/2026),
    e a medida deixava de medir o processador."""
    import bios
    import limpeza
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "sistema": sys.platform,
                 "processador": velocidade_do_processador(), "nucleos": {}}
    trabalho = tempfile.mkdtemp(prefix="arena_medida_")
    try:
        sistema = os.path.join(trabalho, "system")
        os.makedirs(sistema)
        bios.instalar_livres(sistema)
        cfg = cfg_sem_freio(trabalho, sistema)
        for console, nucleo, jogo in jogos_da_medida():
            arquivo_nucleo = os.path.join(pasta_nucleos, nucleo + extensao)
            if not os.path.isfile(arquivo_nucleo):
                resultado["nucleos"][console] = {"erro": "sem o nucleo %s" % os.path.basename(arquivo_nucleo)}
                continue
            copia = os.path.join(trabalho, os.path.basename(jogo))
            shutil.copyfile(jogo, copia)
            medida = fps_sem_freio(lambda quadros: [
                programa, "--config", cfg, "-L", arquivo_nucleo, "--max-frames=%d" % quadros, copia])
            resultado["nucleos"][console] = dict(medida, nucleo=nucleo)
        resultado["disco"] = gravacao_em_disco(trabalho)
    finally:
        limpeza.apagar_pasta(trabalho)
    return resultado


def principal():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    resultado = medir_aqui(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3])
    texto = json.dumps(resultado, ensure_ascii=False, indent=1)
    if len(sys.argv) > 4:
        with open(sys.argv[4], "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
