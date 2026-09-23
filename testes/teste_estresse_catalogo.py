"""Fase 2 da auditoria: teste de estresse do catalogo (5.000 jogos falsos).

Gera 5.000 arquivos de jogo falsos (0 bytes, extensao valida), espalhados
em 3 consoles reais, dentro de uma subpasta propria (facil de apagar depois
e nao se mistura com jogo de verdade). Mede o tempo de indexacao chamando
indexador.indexar(forcar=True) diretamente -- sem precisar subir o servidor
HTTP inteiro -- e confere que o catalogo responde com os 5.000 (mais o que
ja existia). Apaga tudo no final, mesmo se der erro no meio.
"""
import importlib.util
import os
import shutil
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_JOGOS_PESSOAIS = os.path.join(RAIZ, "jogos", "pessoais")

# pasta real (consoles.json -> "pasta") + extensao valida daquele console
CONSOLES_DO_TESTE = [
    ("NES", ".nes"),
    ("Super Nintendo", ".sfc"),
    ("Game Boy", ".gb"),
]
TOTAL_ARQUIVOS = 5000
SUBPASTA_TESTE = "_teste_estresse_auditoria"


def carregar_indexador():
    caminho = os.path.join(RAIZ, "servidor", "indexador.py")
    spec = importlib.util.spec_from_file_location("indexador_teste", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    spec.loader.exec_module(modulo)
    return modulo


def criar_arquivos_falsos():
    por_console = TOTAL_ARQUIVOS // len(CONSOLES_DO_TESTE)
    pastas_criadas = []
    criados = 0
    for pasta_console, extensao in CONSOLES_DO_TESTE:
        destino = os.path.join(PASTA_JOGOS_PESSOAIS, pasta_console, SUBPASTA_TESTE)
        os.makedirs(destino, exist_ok=True)
        pastas_criadas.append(destino)
        for i in range(por_console):
            nome = "Jogo Falso de Estresse %04d%s" % (i, extensao)
            with open(os.path.join(destino, nome), "w") as f:
                pass
            criados += 1
    return pastas_criadas, criados


def apagar_arquivos_falsos(pastas):
    for pasta in pastas:
        shutil.rmtree(pasta, ignore_errors=True)


def main():
    indexador = carregar_indexador()

    print("Indexando o catalogo real ANTES do teste (linha de base)...")
    inicio = time.monotonic()
    catalogo_antes = indexador.indexar(forcar=True)
    tempo_antes = time.monotonic() - inicio
    total_antes = catalogo_antes["total"]
    print("  %d jogo(s) reais, indexado em %.3fs" % (total_antes, tempo_antes))

    print("\nCriando %d arquivos de jogo falsos em %s..." % (TOTAL_ARQUIVOS, SUBPASTA_TESTE))
    pastas, criados = criar_arquivos_falsos()
    print("  %d arquivo(s) criado(s)" % criados)

    try:
        print("\nIndexando com os %d jogos falsos somados aos reais..." % TOTAL_ARQUIVOS)
        inicio = time.monotonic()
        catalogo_depois = indexador.indexar(forcar=True)
        tempo_depois = time.monotonic() - inicio
        total_depois = catalogo_depois["total"]
        print("  %d jogo(s) no total, indexado em %.3fs" % (total_depois, tempo_depois))

        print("\nSegunda chamada (deveria reaproveitar o cache, sem varrer de novo)...")
        inicio = time.monotonic()
        catalogo_cache = indexador.indexar(forcar=False)
        tempo_cache = time.monotonic() - inicio
        print("  %d jogo(s), %.3fs, reaproveitado=%s"
              % (catalogo_cache["total"], tempo_cache, catalogo_cache.get("reaproveitado")))

        ok = (total_depois >= total_antes + criados
              and catalogo_cache.get("reaproveitado") is True
              and tempo_cache < tempo_depois)

        print("\n--- RESULTADO ---")
        print("Antes:  %d jogos, %.3fs" % (total_antes, tempo_antes))
        print("Depois: %d jogos (+%d falsos), %.3fs" % (total_depois, criados, tempo_depois))
        print("Cache:  %.3fs (reaproveitado)" % tempo_cache)
        print("RESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        print("\nApagando os arquivos falsos...")
        apagar_arquivos_falsos(pastas)
        print("Reindexando para tirar o catalogo do estado de teste...")
        indexador.indexar(forcar=True)
        print("Limpeza concluida.")


if __name__ == "__main__":
    sys.exit(main())
