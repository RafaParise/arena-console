# -*- coding: utf-8 -*-
"""Testa se o memory card do host chega ao convidado numa partida de PS1.

Nao da pra "jogar" de verdade (sem tela, sem como reagir ao jogo), entao o
teste confere o que da pra confirmar sem interacao: se o cartao de memoria
que o host cria ao abrir o jogo e enviado ao convidado quando ele conecta.

Descoberta ao rodar a primeira versao deste teste: o PCSX ReARMed NAO usa o
mecanismo padrao de SRAM do RetroArch pro memory card (o log mostra
"[SRAM] Ignorando carregamento da SRAM"). Ele gerencia o cartao sozinho, num
arquivo de nome fixo tipo "pcsx-card2.mcd" (nao um .srm com o nome do jogo).
Por isso o teste procura por *.mcd na pasta de saves, em vez de supor o nome.
A comunidade RetroArch confirma que esse nucleo sincroniza o cartao do host
pro convidado ao conectar - e' exatamente o que este teste verifica de fato.

O convidado roda com uma pasta de saves PROPRIA (fora do ARENA), simulando
uma segunda maquina de verdade - em vez de ler/escrever no mesmo arquivo do
host, que e' o que aconteceria numa maquina so.

Passos:
 1. Hospeda pelo /api/jogar de verdade (Crash Team Racing, tem memory card
    de verdade: fantasmas e pistas destravadas, nao so pontuacao).
 2. Espera o host criar o cartao (acontece ao carregar o jogo).
 3. Sobe o convidado com savefile_directory isolado, conecta.
 4. Espera a sincronizacao inicial e confere se o cartao apareceu na pasta
    do convidado e bate com o do host (prova que foi enviado na conexao).

Roda: servidor\\python\\python.exe ferramentas\\teste_memory_card_ps1.py
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_SAVES_HOST = os.path.join(RAIZ, "retroarch", "saves", "PCSX-ReARMed")
PORTA_ARENA = 8777
PORTA_PARTIDA = 55435


def pedir(caminho, corpo=None):
    url = "http://127.0.0.1:%d%s" % (PORTA_ARENA, caminho)
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sha256_de(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def cartoes_em(pasta):
    achados = glob.glob(os.path.join(pasta, "**", "*.mcd"), recursive=True)
    return sorted(set(os.path.normpath(c) for c in achados))


def main():
    cartoes_originais = {}
    for caminho in cartoes_em(PASTA_SAVES_HOST):
        backup = caminho + ".backup_teste"
        shutil.copy2(caminho, backup)
        cartoes_originais[caminho] = backup
        os.remove(caminho)

    pasta_convidado = os.path.join(RAIZ, "ferramentas", "_saves_convidado_teste")
    if os.path.isdir(pasta_convidado):
        shutil.rmtree(pasta_convidado)
    os.makedirs(pasta_convidado, exist_ok=True)

    servidor_proc = subprocess.Popen(
        [os.path.join(RAIZ, "servidor", "python", "python.exe"),
         os.path.join(RAIZ, "servidor", "arena.py")],
        cwd=os.path.join(RAIZ, "servidor"))
    print("Servidor ARENA rodando, PID", servidor_proc.pid)
    time.sleep(3)

    convidado_proc = None
    try:
        catalogo = pedir("/api/catalogo")
        jogo = next((j for j in catalogo["jogos"]
                    if "Crash Team Racing" in j["titulo"] and j["id"].endswith(".cue")),
                   None)
        if not jogo:
            print("FALHOU: Crash Team Racing nao esta no catalogo.")
            return 1

        resp = pedir("/api/jogar", {
            "jogo_id": jogo["id"], "apelido": "hospedeiro", "partida": "hospedar"})
        print("Resposta do host:", resp)
        if not resp.get("ok"):
            print("FALHOU ao hospedar.")
            return 1

        print("Esperando 10s o host criar o cartao de memoria...")
        time.sleep(10)

        cartoes_host = cartoes_em(PASTA_SAVES_HOST)
        if not cartoes_host:
            print("FALHOU: o host nao criou nenhum cartao (*.mcd) em", PASTA_SAVES_HOST)
            return 1
        caminho_cartao_host = cartoes_host[0]
        hash_host = sha256_de(caminho_cartao_host)
        tam_host = os.path.getsize(caminho_cartao_host)
        print("Host criou cartao: %s (%d bytes, sha256=%s)" %
              (os.path.basename(caminho_cartao_host), tam_host, hash_host[:16]))

        core = os.path.join(RAIZ, "retroarch", "cores", "pcsx_rearmed_libretro.dll")
        rom = os.path.join(RAIZ, jogo["arquivo"].replace("/", os.sep))
        exe = os.path.join(RAIZ, "retroarch", "retroarch.exe")
        opcoes = graficos.opcoes_de_partida("convidado", hospedar=False, jogador=2)
        # Pasta de saves propria, simulando o disco de uma segunda maquina -
        # numa unica maquina os dois processos nao podem escrever no mesmo
        # arquivo, senao o teste nao prova nada sobre sincronizacao.
        opcoes["savefile_directory"] = pasta_convidado
        override_convidado = os.path.join(RAIZ, "ferramentas", "_join_memcard.cfg")
        with open(override_convidado, "w", encoding="utf-8") as f:
            for k, v in opcoes.items():
                f.write('%s = "%s"\n' % (k, v))

        comando = [exe, "-L", core, "--appendconfig", override_convidado,
                  "--connect", "127.0.0.1", "--port", str(PORTA_PARTIDA), rom]
        convidado_proc = subprocess.Popen(comando, cwd=os.path.join(RAIZ, "retroarch"))
        print("Convidado rodando, PID", convidado_proc.pid)

        print("Esperando 10s a sincronizacao inicial (cartao do host -> convidado)...")
        time.sleep(10)

        if convidado_proc.poll() is not None:
            print("FALHOU: o convidado morreu antes da sincronizacao.")
            return 1

        cartoes_convidado = cartoes_em(pasta_convidado)
        if not cartoes_convidado:
            print("FALHOU: o convidado nao recebeu cartao nenhum.")
            print("Conteudo de", pasta_convidado, ":", os.listdir(pasta_convidado))
            return 1

        caminho_cartao_convidado = cartoes_convidado[0]
        hash_convidado = sha256_de(caminho_cartao_convidado)
        tam_convidado = os.path.getsize(caminho_cartao_convidado)
        print("Convidado tem em disco (ainda conectado): %s (%d bytes, sha256=%s)" %
              (os.path.basename(caminho_cartao_convidado), tam_convidado, hash_convidado[:16]))
        print("Bate com o host neste momento:", hash_convidado == hash_host,
              "(pode nao bater ainda e mesmo assim estar sincronizado em memoria -")
        print(" so fechando de forma normal pra saber se o nucleo grava o estado em disco)")

        # Fecha de forma NORMAL (nao forcada) pra dar chance do nucleo gravar
        # em disco o estado sincronizado, do jeito que fecharia um jogo de
        # verdade pela tela do ARENA (nao com "matar o processo").
        pid_convidado = convidado_proc.pid
        subprocess.run(["taskkill", "/IM", "retroarch.exe", "/PID", str(pid_convidado)],
                       capture_output=True)
        try:
            convidado_proc.wait(timeout=10)
            print("Convidado fechou sozinho depois do taskkill normal.")
        except subprocess.TimeoutExpired:
            print("Convidado nao fechou sozinho em 10s - forcando.")
            convidado_proc.kill()
            convidado_proc.wait(timeout=5)

        cartoes_convidado_final = cartoes_em(pasta_convidado)
        if not cartoes_convidado_final:
            print("FALHOU: depois de fechar, o convidado nao tem cartao nenhum.")
            return 1
        caminho_final = cartoes_convidado_final[0]
        hash_final = sha256_de(caminho_final)
        tam_final = os.path.getsize(caminho_final)
        print("Cartao do convidado depois de fechar: %d bytes, sha256=%s" %
              (tam_final, hash_final[:16]))

        sincronizou = hash_final == hash_host
        print("Cartao do convidado bate com o do host depois de fechar:", sincronizou)

        if not sincronizou:
            print("FALHOU: o cartao do host nao chegou ao convidado nem depois de fechar.")
            return 1

        print("OK: o memory card do host e enviado ao convidado ao conectar,")
        print("    confirmando na pratica que os dois jogadores usam o memory")
        print("    card de quem hospeda, como o CLAUDE.md ja documentava.")
        return 0
    finally:
        if convidado_proc is not None and convidado_proc.poll() is None:
            convidado_proc.terminate()
            try:
                convidado_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                convidado_proc.kill()
        subprocess.run(["taskkill", "/F", "/IM", "retroarch.exe"],
                       capture_output=True)
        servidor_proc.terminate()
        try:
            servidor_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor_proc.kill()

        override_convidado = os.path.join(RAIZ, "ferramentas", "_join_memcard.cfg")
        if os.path.isfile(override_convidado):
            os.remove(override_convidado)
        # _saves_convidado_teste NAO e apagada aqui de proposito, pra dar
        # pra inspecionar o resultado depois. Apague na mao quando terminar.
        for caminho in cartoes_em(PASTA_SAVES_HOST):
            os.remove(caminho)
        for caminho, backup in cartoes_originais.items():
            shutil.move(backup, caminho)


if __name__ == "__main__":
    sys.exit(main())
