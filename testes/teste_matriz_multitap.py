# -*- coding: utf-8 -*-
r"""Multitap, Fase E: matriz por console com os jogos da pasta.

Para cada jogo (RetroArch, com o nucleo que o ARENA usa):
  1. ABRE: roda ~10 s sozinho (--max-frames) e tira uma foto da tela
     (--max-frames-ss). Foto com mais de 2 KB = mostrou imagem. Guarda do
     registro os erros (BIOS/arquivo que falta).
  2. JOGAR JUNTO: abre um hospedeiro e um convidado de verdade no mesmo
     computador (127.0.0.1), com as opcoes de partida do ARENA (o mesmo
     nucleo que o /api/jogar escolhe: PS1 = PCSX ReARMed). Confere no
     registro do hospedeiro "se juntou como o jogador 2", ou a recusa do
     nucleo.

O que so uma pessoa confirma (o controle mexe o boneco, 3+ no mesmo
computador) fica para a parte com o professor.

Protege o retroarch.cfg real. Resultado bruto em
docs\matriz_multitap_bruto.json.

Uso:
    servidor\python\python.exe testes\teste_matriz_multitap.py
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import protege_cfg  # noqa: E402
import jogos_de_teste  # noqa: E402  (acha o jogo tambem em subpasta)

spec = importlib.util.spec_from_file_location("arena_matriz_mt", os.path.join(RAIZ, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arena)
graficos = arena.graficos

RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
P = os.path.join(RAIZ, "jogos", "pessoais")

# (console, pasta do jogo, arquivo, nucleo sozinho, nucleo do Jogar Junto)
JOGOS = [
    ("Super Nintendo", "Super Nintendo", "Super Bomberman 4 (Japan) [T-En by Svambo v1.0].sfc", "snes9x", "snes9x"),
    ("Super Nintendo", "Super Nintendo", "Super Mario Kart (USA).sfc", "snes9x", "snes9x"),
    ("NES", "NES", "Contra (USA).nes", "fceumm", "fceumm"),
    ("Mega Drive", "Mega Drive", "Mega Bomberman (USA).md", "genesis_plus_gx", "genesis_plus_gx"),
    ("Mega Drive", "Mega Drive", "Micro Machines 2 - Turbo Tournament (Europe).md", "genesis_plus_gx", "genesis_plus_gx"),
    ("Nintendo 64", "Nintendo 64", "GoldenEye 007 (USA).z64", "mupen64plus_next", "mupen64plus_next"),
    ("PlayStation", "PS1", "CTR - Crash Team Racing (USA).cue", "swanstation", "pcsx_rearmed"),
    ("Sega Saturn", "Sega Saturn", "Saturn Bomberman (USA) (1S) (Track 01).bin", "mednafen_saturn", "mednafen_saturn"),
    ("Dreamcast", "Dreamcast", "Marvel vs. Capcom 2 - New Age of Heroes (Europe).cue", "flycast", "flycast"),
    ("PSP", "PSP", "Killzone - Liberation (USA) (En,Fr,De,Es,It,Nl,Pl,Ru).iso", "ppsspp", "ppsspp"),
    ("Neo Geo", "Neo Geo", "kof97.zip", "fbneo", "fbneo"),
]


def config_base(pasta, extras):
    opcoes = arena.opcoes_efetivas(arena.config_padrao())
    opcoes.update(extras)
    for chave in ("savefile_directory", "savestate_directory", "screenshot_directory",
                  "cache_directory", "playlist_directory", "log_dir"):
        opcoes[chave] = pasta
    # Opcoes de nucleo geradas NA HORA, como o ARENA faz a cada partida
    # (gravar_opcoes_dos_nucleos), numa copia -- o arquivo de verdade guarda
    # o que sobrou da ultima sessao e nao e' o que o ARENA usaria.
    opcoes_nucleo = os.path.join(pasta, "retroarch-core-options.cfg")
    original = graficos.ARQUIVO_OPCOES_CORE
    graficos.ARQUIVO_OPCOES_CORE = opcoes_nucleo
    try:
        graficos.gravar_opcoes_dos_nucleos(
            arena.CAPACIDADE["nota"], graficos.opcoes_de_memory_card("", "ps1"),
            arena.CAPACIDADE.get("nota_gpu"), False)
    finally:
        graficos.ARQUIVO_OPCOES_CORE = original
    opcoes.update({"system_directory": os.path.join(RAIZ, "retroarch", "system"),
                   "core_options_path": opcoes_nucleo,
                   "global_core_options": "true", "config_save_on_exit": "false",
                   "network_cmd_enable": "false", "video_fullscreen": "false",
                   "log_to_file": "true", "log_verbosity": "true", "frontend_log_level": "0"})
    cfg = os.path.join(pasta, "partida.cfg")
    open(cfg, "w", encoding="utf-8").write("\n".join('%s = "%s"' % kv for kv in sorted(opcoes.items())) + "\n")
    return cfg


def registro(pasta):
    nomes = sorted(n for n in os.listdir(pasta) if n.endswith(".log"))
    return "".join(open(os.path.join(pasta, n), encoding="utf-8", errors="ignore").read() for n in nomes)


def erros_importantes(texto):
    # "GET_VARIABLE: ... - Invalid value." e' o nucleo perguntando por uma
    # opcao que ele mesmo nao declarou (o Flycast, reicast_dump_unique_textures,
    # 16/10/2026): nao diz nada do jogo.
    return [l.strip()[:150] for l in texto.splitlines()
            if re.search(r"\[ERROR\]|required|não tem suporte|not support", l)
            and not re.search(r"(?i)midi|áudio|audio|autoconf|mmdevice|GET_VARIABLE: .* - Invalid value", l)][:6]


def abrir(console, jogo, nucleo, pasta, quadros=600):
    os.makedirs(pasta)
    cfg = config_base(pasta, {})
    foto = os.path.join(pasta, "foto.png")
    log = os.path.join(pasta, "sozinho.log")
    inicio = time.monotonic()
    try:
        subprocess.run([RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll"),
                        "--appendconfig", cfg, "--verbose", "--log-file", log, "--max-frames=%d" % quadros,
                        "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                       cwd=os.path.dirname(RETROARCH), timeout=90 + quadros // 30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        travou = False
    except subprocess.TimeoutExpired:
        travou = True
    tamanho = os.path.getsize(foto) if os.path.exists(foto) else 0
    texto = open(log, encoding="utf-8", errors="ignore").read() if os.path.exists(log) else ""
    return {"abre_e_mostra_imagem": tamanho > 2000 and not travou, "foto_bytes": tamanho,
            "segundos": round(time.monotonic() - inicio, 1), "travou": travou,
            "erros": erros_importantes(texto)}


def jogar_junto(jogo, nucleo, pasta):
    processos = []
    resultado = {}
    try:
        for papel, hospedar in (("hospedeiro", True), ("convidado", False)):
            sub = os.path.join(pasta, papel)
            os.makedirs(sub)
            opcoes = graficos.opcoes_de_partida("Anfitriao" if hospedar else "Colega", hospedar, jogador=2)
            cfg = config_base(sub, opcoes)
            args = graficos.argumentos_de_partida(hospedar, "127.0.0.1")
            log = os.path.join(sub, "ra.log")
            processos.append(subprocess.Popen(
                [RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", nucleo + "_libretro.dll"),
                 "--appendconfig", cfg, "--verbose", "--log-file", log] + args + [jogo],
                cwd=os.path.dirname(RETROARCH), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            if hospedar:
                time.sleep(10)
        fim = time.monotonic() + 25
        while time.monotonic() < fim:
            host = registro(os.path.join(pasta, "hospedeiro"))
            if re.search(r"se juntou como o jogador 2", host) or re.search(r"(?i)não tem suporte|not support", host):
                break
            time.sleep(0.5)
        host = registro(os.path.join(pasta, "hospedeiro"))
        convidado = registro(os.path.join(pasta, "convidado"))
        recusa = re.search(r"[^\n]*(?:não tem suporte|not support)[^\n]*", host + convidado, re.I)
        # O hospedeiro as vezes nao grava a linha a tempo; o convidado dizer
        # que entrou como jogador 2+ tambem prova a conexao (25/09/2026:
        # SNES dava "NAO conectou" com o convidado dentro).
        resultado = {"conectou": bool(re.search(r"se juntou como o jogador 2", host)
                                      or re.search(r"Você se juntou como jogador [2-9]", convidado)),
                     "convidado_diz": (re.search(r"Você se juntou como jogador \d+", convidado) or [None])[0],
                     "recusa_do_nucleo": recusa.group(0).strip()[:150] if recusa else "",
                     "hospedeiro_vivo": processos[0].poll() is None,
                     "erros": erros_importantes(host)}
    finally:
        for p in processos:
            try:
                p.terminate()
            except OSError:
                pass
        time.sleep(2)
        for p in processos:
            if p.poll() is None:
                p.kill()
    return resultado


def main():
    raiz_teste = tempfile.mkdtemp(prefix="arena_matriz_mt_")
    resultados = []
    try:
        for i, (console, pasta, arquivo, sozinho, junto) in enumerate(JOGOS):
            jogo = jogos_de_teste.achar(pasta, arquivo) or os.path.join(P, pasta, arquivo)
            linha = {"console": console, "jogo": arquivo}
            if not os.path.isfile(jogo):
                linha["erro"] = "arquivo nao esta na pasta"
                resultados.append(linha)
                print("[--] %-14s %s: arquivo nao esta na pasta" % (console, arquivo[:40]))
                continue
            linha["abre"] = abrir(console, jogo, sozinho, os.path.join(raiz_teste, "%02d_sozinho" % i))
            linha["jogar_junto"] = jogar_junto(jogo, junto, os.path.join(raiz_teste, "%02d_junto" % i))
            resultados.append(linha)
            a, j = linha["abre"], linha["jogar_junto"]
            print("[%s] %-14s %-42s abre=%s (%d B)  junto=%s %s" % (
                "OK" if a["abre_e_mostra_imagem"] else "!!", console, arquivo[:42],
                a["abre_e_mostra_imagem"], a["foto_bytes"],
                "conectou" if j.get("conectou") else ("NUCLEO RECUSA" if j.get("recusa_do_nucleo") else "nao conectou"),
                ("| " + "; ".join(a["erros"][:2])) if a["erros"] else ""))
        destino = os.path.join(RAIZ, "docs", "matriz_multitap_bruto.json")
        json.dump(resultados, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("\nBruto em", destino)
        return 0
    finally:
        shutil.rmtree(raiz_teste, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
