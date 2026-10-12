# -*- coding: utf-8 -*-
r"""Fase 5 da auditoria 3: o PS2 com os jogos que estao na pasta e o seletor
de qualidade do ARENA ("Mais leve", "Automatico", "Mais bonito", em Ajustes
-> Emuladores).

Abre o PCSX2 de verdade numa COPIA isolada (sem os cartoes de memoria, os
saves e o cache do aluno; o PCSX2.ini de verdade nao e' tocado), com a
configuracao que o ARENA grava (graficos.escrever_config_pcsx2), e confere
no registro do PCSX2 que o jogo COMECOU ("is executing", com o banco de jogos
lido -- "games on record"), sem aviso de configuracao que "pode quebrar a
renderizacao". Antes (10/10/2026) o teste exigia "GameDB: Enabled", que so
aparece em jogo com correcao no banco: o Half-Life e o Hitman 2 nao tem
nenhuma e o Marvel Ultimate Alliance imprime "GameDB: Changing", e os tres
"nao comecavam" -- comecavam (o jogo rodando aos 15-18 s, vivo aos 35 s):
  1. cada jogo de PS2 da pasta, no Automatico (o padrao);
  2. os tres niveis de qualidade, em 3 jogos (o mais leve, um medio e o
     mais pesado da pasta, pelo tamanho).
Jogo que nao comeca em 60 s conta como falha, com o fim do registro.

O PCSX2 abre minimizado (nao rouba o foco). Na maquina-alvo (Celeron, sem
placa dedicada) o PS2 e' "Pode travar": este teste diz se ABRE, nao se roda
liso -- isso so o notebook da escola mostra (roteiro de sala).

Uso: servidor\python\python.exe testes\teste_ps2_todos_os_jogos.py [pedaco do nome]
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, AQUI)
import graficos  # noqa: E402
import limpeza  # noqa: E402
import teste_pcsx2_seguro as seguro  # noqa: E402

PASTA_PCSX2 = os.path.join(RAIZ, "emuladores", "PCSX2", "PCSX2")
PASTA_JOGOS = os.path.join(RAIZ, "jogos", "pessoais", "PS2")
EXTENSOES = (".iso", ".chd", ".cso", ".bin", ".gz", ".zso")
ESPERA = 60


def jogos_de_ps2(filtro=""):
    achados = []
    for atual, _sub, nomes in os.walk(PASTA_JOGOS):
        for nome in sorted(nomes):
            if nome.lower().endswith(EXTENSOES) and filtro in nome.lower():
                caminho = os.path.join(atual, nome)
                achados.append((os.path.getsize(caminho), caminho))
    return [c for _t, c in sorted(achados, key=lambda par: os.path.basename(par[1]).lower())]


def abrir(copia, jogo, preset):
    """Grava a configuracao do ARENA na copia, abre o jogo e espera ele
    comecar. Devolve (comecou, segundos, avisos, fim do registro)."""
    exe = os.path.join(copia, "pcsx2-qt.exe")
    graficos.escrever_config_pcsx2(exe, nota=4, nota_gpu=3, modesto=False, preset=preset,
                                   integrada=True, motor="automatico", jogadores=2, controles_xinput=[])
    ini = os.path.join(copia, "inis", "PCSX2.ini")
    with open(ini, encoding="utf-8") as arquivo:
        texto = graficos._trocar_chaves_ini(arquivo.read(), "Logging", {"EnableFileLogging": "true"})
    with open(ini, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    registro = os.path.join(copia, "logs", "emulog.txt")
    if os.path.exists(registro):
        os.remove(registro)
    janela = subprocess.STARTUPINFO()
    janela.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    janela.wShowWindow = 7                       # minimizada, sem roubar o foco
    inicio = time.monotonic()
    processo = subprocess.Popen([exe, jogo], cwd=copia, startupinfo=janela)
    lido, comecou = "", False
    try:
        while time.monotonic() - inicio < ESPERA and processo.poll() is None:
            time.sleep(1)
            try:
                with open(registro, encoding="utf-8", errors="replace") as arquivo:
                    lido = arquivo.read()
            except OSError:
                continue
            if "is executing" in lido and "games on record" in lido:
                comecou = True
                time.sleep(4)
                with open(registro, encoding="utf-8", errors="replace") as arquivo:
                    lido = arquivo.read()
                break
        segundos = round(time.monotonic() - inicio, 1)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)], capture_output=True)
        try:
            processo.wait(15)
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2)
    return comecou, segundos, seguro.avisos_perigosos(lido), lido[-400:]


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    jogos = jogos_de_ps2(filtro)
    if not os.path.isfile(os.path.join(PASTA_PCSX2, "pcsx2-qt.exe")):
        print("FALHOU: sem o PCSX2 em emuladores\\PCSX2 (o teste precisa dele).")
        return 1
    if not jogos:
        print("FALHOU: nenhum jogo de PS2 em jogos\\pessoais\\PS2 (o teste precisa de pelo menos um).")
        return 1
    falhas, linhas = [], []
    base = tempfile.mkdtemp(prefix="arena_ps2_todos_")
    try:
        copia = os.path.join(base, "PCSX2")
        shutil.copytree(PASTA_PCSX2, copia, ignore=shutil.ignore_patterns(
            "memcards", "cache", "logs", "snaps", "sstates", "covers", "videos"))
        os.makedirs(os.path.join(copia, "memcards"), exist_ok=True)

        print("1. Cada jogo de PS2 da pasta, no Automatico (%d jogos)" % len(jogos))
        for jogo in jogos:
            comecou, segundos, avisos, fim = abrir(copia, jogo, None)
            nome = os.path.basename(jogo)
            ok = comecou and not avisos
            print("  [%s] %-70s %5.1f s%s" % ("OK" if ok else "FALHOU", nome[:70], segundos,
                                             "" if ok else ("  avisos: %s" % avisos if comecou else "  nao comecou")),
                  flush=True)
            linhas.append({"jogo": nome, "nivel": "automatico", "comecou": comecou, "segundos": segundos,
                           "avisos": avisos})
            if not ok:
                falhas.append("%s (automatico)" % nome)
                if not comecou:
                    print("        fim do registro: %s" % fim.replace("\n", " | ")[-300:])

        por_tamanho = sorted(jogos, key=os.path.getsize)
        tres = list(dict.fromkeys([por_tamanho[0], por_tamanho[len(por_tamanho) // 2], por_tamanho[-1]]))
        print("\n2. Os tres niveis de qualidade em %d jogo(s)" % len(tres))
        for jogo in tres:
            for preset in ("leve", "bonito"):
                comecou, segundos, avisos, fim = abrir(copia, jogo, preset)
                nome = os.path.basename(jogo)
                ok = comecou and not avisos
                print("  [%s] %-60s %-7s %5.1f s%s" % ("OK" if ok else "FALHOU", nome[:60], preset, segundos,
                                                      "" if ok else "  %s" % (avisos or "nao comecou")),
                      flush=True)
                linhas.append({"jogo": nome, "nivel": preset, "comecou": comecou, "segundos": segundos,
                               "avisos": avisos})
                if not ok:
                    falhas.append("%s (%s)" % (nome, preset))
    finally:
        limpeza.apagar_pasta(base)

    destino = os.path.join(RAIZ, "docs", "auditoria3", "ps2_todos_os_jogos.json")
    import json
    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(linhas, arquivo, ensure_ascii=False, indent=1)
    print()
    if falhas:
        print("FALHOU: %d de %d (%s)" % (len(falhas), len(linhas), "; ".join(falhas)))
        return 1
    print("PS2, todos os jogos: %d de %d certos." % (len(linhas), len(linhas)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
