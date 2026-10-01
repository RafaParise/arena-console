# -*- coding: utf-8 -*-
r"""Arquivos de dados\ com JSON valido mas de FORMATO errado nao derrubam nada.

O testes\teste_arquivos_corrompidos.py cobre lixo binario (JSON invalido).
Faltava o outro jeito de quebrar: JSON certinho no formato errado -- [] no
lugar de {...}, numero no lugar de lista -- que acontece com arquivo mexido
a mao ou copiado de outra versao. Achados de 01/10/2026 (fuzz):
  - config.json com "servidores": 5 derrubava a leitura da configuracao e,
    com ela, a ABERTURA do ARENA;
  - config.json, manifesto.json e controles.json com [] ou "texto"
    derrubavam a leitura (config, lista de jogos, mapa de controles);
  - acervo_autorizado.json com itens que nao sao objeto quebravam a aba.

Tudo em arquivos temporarios: nenhum arquivo de dados\ de verdade e' tocado.

Uso: servidor\python\python.exe testes\teste_dados_tortos.py
"""
import json
import os
import random
import shutil
import sys
import tempfile
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import acervo  # noqa: E402
import arena  # noqa: E402
import controles  # noqa: E402
import indexador  # noqa: E402
import jogadores  # noqa: E402

TORTOS = ["[]", '"texto"', "123", "null", "true", "[1, \"x\", null]", '{"jogos": 5}', '{"jogos": [1, 2]}',
          '{"1": [], "2": 7}', '[{"a": 1}, 5, "x"]', "{}"]


def ruim(profundidade=0):
    escolhas = [None, True, False, 0, -1, 10 ** 30, 1.5, "", "x" * 5000, "\U0001F3AE\x00\n", [], {},
                [1, "a", None], {"a": 1}, {"apelido": [], "url": {}}, [{"apelido": 5, "url": None, "id": []}],
                ["x"] * 50]
    if profundidade < 2 and random.random() < 0.3:
        return {random.choice(["a", "url", "apelido", "video_smooth", "ps1", "1", "id"]): ruim(profundidade + 1)}
    return random.choice(escolhas)


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_dados_tortos_")
    guardados = (arena.ARQUIVO_CONFIG, arena.ARQUIVO_OVERRIDE, controles.ARQUIVO, acervo.ARQUIVO,
                 indexador.ARQUIVO_MANIFESTO, indexador.ARQUIVO_MANUAIS, arena.ARQUIVO_QUEDAS)
    try:
        arena.ARQUIVO_CONFIG = os.path.join(pasta, "config.json")
        arena.ARQUIVO_OVERRIDE = os.path.join(pasta, "override.cfg")
        controles.ARQUIVO = os.path.join(pasta, "controles.json")
        acervo.ARQUIVO = os.path.join(pasta, "acervo_autorizado.json")
        indexador.ARQUIVO_MANIFESTO = os.path.join(pasta, "manifesto.json")
        indexador.ARQUIVO_MANUAIS = os.path.join(pasta, "consoles_manuais.json")
        arena.ARQUIVO_QUEDAS = os.path.join(pasta, "fechamentos.json")

        # 1. config.json: 3.000 combinacoes aleatorias (sempre as mesmas: semente fixa).
        random.seed(20261001)
        chaves = list(arena.config_padrao()) + ["servidores", "servidor_url", "perfil_controle"]
        erros = []
        for i in range(3000):
            dados = {c: ruim() for c in random.sample(chaves, k=random.randint(1, len(chaves)))}
            with open(arena.ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(dados, f)
            arena._config_cache.update({"quando": 0.0, "valor": None})
            try:
                config = arena.carregar_config()
                arena.salvar_config(config)
                arena.opcoes_efetivas(config, 2)
                if i % 100 == 0:
                    arena.gravar_override(config, 2)
            except Exception:
                erros.append(traceback.format_exc().strip().splitlines()[-1][:120])
        confere("config.json: 3.000 combinacoes tortas, nenhuma derruba a leitura",
                not erros, "; ".join(sorted(set(erros))[:3]))

        # 2. Cada arquivo, cada formato torto.
        leitores = [
            ("config.json", arena.ARQUIVO_CONFIG, lambda: (arena._config_cache.update({"quando": 0.0, "valor": None}),
                                                           arena.carregar_config())),
            ("controles.json", controles.ARQUIVO, controles.ler),
            ("acervo_autorizado.json", acervo.ARQUIVO, acervo.ler_itens),
            ("manifesto.json", indexador.ARQUIVO_MANIFESTO, indexador.ler_manifesto_salvo),
            ("consoles_manuais.json", indexador.ARQUIVO_MANUAIS, indexador.ler_manuais),
            ("fechamentos.json", arena.ARQUIVO_QUEDAS, arena.ler_fechamentos),
        ]
        for nome, caminho, ler in leitores:
            quebras = []
            for torto in TORTOS:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(torto)
                try:
                    ler()
                except Exception:
                    quebras.append("%s -> %s" % (torto, traceback.format_exc().strip().splitlines()[-1][:80]))
            confere("%s com %d formatos tortos: nenhum derruba" % (nome, len(TORTOS)), not quebras,
                    "; ".join(quebras[:2]))
        confere("manifesto.json torto nao e' reaproveitado (a lista e' refeita)",
                all((open(indexador.ARQUIVO_MANIFESTO, "w").write(t), indexador.ler_manifesto_salvo())[1] is None
                    for t in ("[]", '{"jogos": 5}', '{"jogos": [1]}')))

        # 3. jogadores.txt: binario, linhas tortas, numeros absurdos.
        caminho = os.path.join(pasta, "jogadores.txt")
        with open(caminho, "wb") as f:
            f.write(os.urandom(2000) + b"\nSuper Bomberman = 5\n= 3\nx = -9\ny = 999999\nz == 2\n")
        try:
            regras = jogadores.ler(caminho)
            ok = isinstance(regras, list) and all(1 <= n <= jogadores.MAXIMO for _nome, n in regras)
        except Exception as falha:
            ok, regras = False, falha
        confere("jogadores.txt com lixo e numeros absurdos: le o que da, limita 1..16", ok, str(regras)[:120])
    finally:
        (arena.ARQUIVO_CONFIG, arena.ARQUIVO_OVERRIDE, controles.ARQUIVO, acervo.ARQUIVO,
         indexador.ARQUIVO_MANIFESTO, indexador.ARQUIVO_MANUAIS, arena.ARQUIVO_QUEDAS) = guardados
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Dados tortos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
