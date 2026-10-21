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
     quadros e 3000; quadros por segundo = (3000 - 60) / (tempo da longa -
     tempo da curta), o que tira o tempo de abrir e fechar o RetroArch.
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
# Os nucleos medidos: os de computador antigo e de console que abrem com jogo
# livre e BIOS livre (o processador faz todo o trabalho; nenhum usa a placa).
CONSOLES = ("msx", "vic20", "zx81", "chip8")


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


def cfg_sem_freio(pasta, sistema):
    """O retroarch.cfg da medida: sem video nem som de verdade, sem esperar
    a tela nem o som (o RetroArch corre o mais rapido que puder), sem nada
    que pese a mais (rebobinar, adiantar quadro), as pastas na de trabalho."""
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
    for chave in ("savefile_directory", "savestate_directory", "screenshot_directory", "cache_directory"):
        os.makedirs(opcoes[chave], exist_ok=True)
    caminho = os.path.join(pasta, "medida.cfg")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("".join('%s = "%s"\n' % par for par in sorted(opcoes.items())))
    return caminho


def segundos_de(comando, limite=300):
    """O tempo de parede de um comando (o RetroArch fecha sozinho no fim)."""
    inicio = time.perf_counter()
    try:
        subprocess.run(comando, timeout=limite, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.TimeoutExpired, OSError):    # travou, ou o programa nem abriu
        return None
    return time.perf_counter() - inicio


def fps_sem_freio(montar_comando):
    """Quadros por segundo pelo metodo das duas rodadas. 'montar_comando'
    recebe o numero de quadros e devolve a linha de comando."""
    curta = segundos_de(montar_comando(QUADROS[0]))
    longa = segundos_de(montar_comando(QUADROS[1]))
    if curta is None or longa is None or longa <= curta:
        return {"fps": None, "curta_s": curta, "longa_s": longa}
    return {"fps": round((QUADROS[1] - QUADROS[0]) / (longa - curta), 1), "curta_s": round(curta, 2),
            "longa_s": round(longa, 2)}


def velocidade_do_processador():
    import hardware
    return hardware.velocidade_de_um_nucleo(rodadas=21)


def gravacao_em_disco(pasta):
    import hardware
    try:
        return hardware.medir_velocidade(pasta)
    except Exception as falha:          # a medida nao derruba as outras
        return {"erro": str(falha)}


def medir_aqui(programa, pasta_nucleos, extensao, antes_do_comando=()):
    """Todas as medidas neste sistema. 'programa' e' o RetroArch daqui
    (retroarch.exe; no Linux, o AppRun do AppImage tirado para o cache), e
    'antes_do_comando', o que vai entre ele e o -L (no Linux, o --config)."""
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
            medida = fps_sem_freio(lambda quadros: [programa] + list(antes_do_comando) + [
                "-L", arquivo_nucleo, "--appendconfig", cfg, "--max-frames=%d" % quadros, copia])
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
