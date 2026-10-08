r"""Quantas gravacoes em disco o ARENA faz parado (cartao SD e pen drive se gastam).

Pendencia da Fase 0 da auditoria 1 (a amostra de 15 s era curta demais para
pegar um ciclo do vigia); criado na Fase 8. Ampliado na auditoria 3
(07/10/2026): a hora inteira, a TELA aberta (como o aluno deixa o ARENA na
mesa), e a pasta INTEIRA conferida, nao so dados\ e backup\.

Sobe o ARENA (sem abrir a janela dele: ARENA_SEM_JANELA=1), espera assentar e
observa por N segundos:

- contador de gravacoes do proprio processo (Win32_Process.WriteOperationCount
  e WriteTransferCount, que o Windows ja entrega sem instalar nada);
- quais arquivos da pasta do ARENA (menos jogos\ e .git\) mudaram, nasceram
  ou sumiram nesse tempo -- pega gravacao de qualquer programa ali dentro.

Com --com-tela, a tela fica aberta num Edge sem janela (perfil temporario,
fora da pasta do ARENA; o Edge do usuario nao e' tocado): os temporizadores
e os pedidos dela ao servidor rodam como na janela de verdade.

A saida do servidor vai para o "nada" (DEVNULL), para que escrever na
janela preta nao conte como gravacao.

Com --abertura (auditoria 3), mede a ABERTURA em vez da hora parada: as
gravacoes desde o processo nascer ate a resposta do servidor, e ate N
segundos depois (o vigia da a primeira volta aos 20 s) -- com os arquivos
que mudaram nesse tempo.

Uso:
    servidor\python\python.exe testes\medir_gravacoes_parado.py [segundos] [--com-tela] [--saida=<arquivo.json>]
    servidor\python\python.exe testes\medir_gravacoes_parado.py 60 --abertura [--saida=<arquivo.json>]
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
NUMEROS = [a for a in sys.argv[1:] if a.isdigit()]
JANELA_S = int(NUMEROS[0]) if NUMEROS else 600
FORA = {"jogos", ".git"}


def contadores(pid):
    saida = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "Get-CimInstance Win32_Process -Filter 'ProcessId=%d' | "
         "Select-Object WriteOperationCount, WriteTransferCount | ConvertTo-Json" % pid],
        capture_output=True, text=True, timeout=60).stdout
    dados = json.loads(saida)
    return int(dados["WriteOperationCount"]), int(dados["WriteTransferCount"])


def retrato_da_pasta():
    """Data e tamanho de cada arquivo da pasta do ARENA (menos jogos e .git)."""
    datas = {}
    for atual, subs, arquivos in os.walk(RAIZ):
        rel = os.path.relpath(atual, RAIZ)
        if rel != "." and rel.split(os.sep)[0] in FORA:
            subs[:] = []
            continue
        for nome in arquivos:
            caminho = os.path.join(atual, nome)
            try:
                info = os.stat(caminho)
            except OSError:
                continue
            datas[os.path.relpath(caminho, RAIZ)] = (info.st_mtime, info.st_size)
    return datas


def porta_ocupada():
    try:
        with socket.create_connection(("127.0.0.1", 8777), timeout=0.5):
            return True
    except OSError:
        return False


def medir_abertura(destino):
    """As gravacoes da abertura: o retrato da pasta antes de nascer o
    processo, os contadores dele quando o servidor responde e N s depois."""
    pasta_antes = retrato_da_pasta()
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1")
    processo = subprocess.Popen([PYTHON, os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ, env=ambiente,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(300):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/", timeout=0.5)
                break
            except OSError:
                time.sleep(0.1)
        ops_pronto, bytes_pronto = contadores(processo.pid)
        print("Servidor no ar. Observando a abertura por %d s..." % JANELA_S, flush=True)
        time.sleep(JANELA_S)
        ops_fim, bytes_fim = contadores(processo.pid)
        pasta_depois = retrato_da_pasta()
    finally:
        subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True)
    de_desenvolvimento = ("docs" + os.sep, "testes" + os.sep, "ferramentas" + os.sep,
                          os.path.join("servidor", "tests") + os.sep)
    mudou = sorted(c for c, d in pasta_depois.items() if pasta_antes.get(c) != d
                   and not c.startswith(de_desenvolvimento))
    resultado = {
        "janela_s": JANELA_S,
        "ate_o_servidor_responder": {"operacoes": ops_pronto, "kb": round(bytes_pronto / 1024.0, 1)},
        "ate_o_fim": {"operacoes": ops_fim, "kb": round(bytes_fim / 1024.0, 1)},
        "arquivos_que_mudaram_ou_nasceram": mudou,
        "kb_dos_arquivos": round(sum(pasta_depois[c][1] for c in mudou if c in pasta_depois) / 1024.0, 1),
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return 0


def principal():
    destino = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--saida=")),
                   os.path.join(RAIZ, "docs", "gravacoes_parado_bruto.json"))
    if not os.path.isabs(destino):
        destino = os.path.join(RAIZ, destino)
    if porta_ocupada():
        print("Ja ha um ARENA aberto na porta 8777. Feche-o e rode de novo.")
        return 2
    com_tela = "--com-tela" in sys.argv
    if "--abertura" in sys.argv:
        return medir_abertura(destino)
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1")
    processo = subprocess.Popen([PYTHON, os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ, env=ambiente,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    navegador = None
    try:
        for _ in range(300):
            try:
                urllib.request.urlopen("http://127.0.0.1:8777/", timeout=0.5)
                break
            except OSError:
                time.sleep(0.1)
        if com_tela:
            import tela_sem_janela
            navegador = tela_sem_janela.Navegador().__enter__()
            navegador.abrir("http://127.0.0.1:8777/", largura=1180, altura=760, espera=5)
        print("Servidor no ar%s. Esperando 30 s para assentar..." % (" com a tela" if com_tela else ""), flush=True)
        time.sleep(30)
        ops_antes, bytes_antes = contadores(processo.pid)
        pasta_antes = retrato_da_pasta()
        inicio = time.monotonic()
        print("Observando por %d s sem ninguem usar..." % JANELA_S, flush=True)
        time.sleep(JANELA_S)
        janela = time.monotonic() - inicio
        ops_depois, bytes_depois = contadores(processo.pid)
        pasta_depois = retrato_da_pasta()
    finally:
        if navegador is not None:
            navegador.__exit__(None, None, None)
        subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True)

    fator = 3600.0 / janela
    ops = ops_depois - ops_antes
    kb = (bytes_depois - bytes_antes) / 1024.0
    mudaram = sorted(c for c, d in pasta_depois.items() if c in pasta_antes and pasta_antes[c] != d)
    nasceram = sorted(c for c in pasta_depois if c not in pasta_antes)
    sumiram = sorted(c for c in pasta_antes if c not in pasta_depois)
    resultado = {
        "janela_s": round(janela),
        "com_tela": com_tela,
        "operacoes_de_gravacao": ops,
        "kb_gravados": round(kb, 1),
        "operacoes_por_hora": round(ops * fator),
        "kb_por_hora": round(kb * fator, 1),
        "arquivos_que_mudaram": mudaram,
        "arquivos_que_nasceram": nasceram,
        "arquivos_que_sumiram": sumiram,
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
