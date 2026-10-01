# -*- coding: utf-8 -*-
r"""A correcao do retroarch.cfg nao acrescenta linha repetida a cada abertura.

Achado de 01/10/2026: o retroarch.cfg deste PC tinha "cache_directory" CINCO
vezes. Ao fechar, o RetroArch regrava a chave na forma dele, ":\cache" (a
pasta do proprio RetroArch, ja dentro do ARENA); a correcao automatica
(graficos.corrigir_caminhos_retroarch_cfg) so reconhecia caminho C:\..., achava
que a chave "nao existia" e acrescentava outra linha a cada abertura.

Numa copia isolada do servidor (o retroarch.cfg de verdade nao e' tocado):
  1. ":\cache" fica como esta e nao ganha linha nova; a 2a correcao nao muda nada;
  2. cinco linhas iguais viram uma;
  3. sem a chave: ganha UMA, dentro do ARENA, e a 2a correcao nao repete;
  4. vazia ou apontando para fora: vai para retroarch\cache, uma linha so.

Uso: servidor\python\python.exe testes\teste_cfg_sem_linha_repetida.py
"""
import importlib.util
import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_cfg_repetido_")
    destino = os.path.join(pasta, "ARENA")
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        os.makedirs(os.path.join(destino, "retroarch"))
        cfg = os.path.join(destino, "retroarch", "retroarch.cfg")
        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location(
            "graficos_cfg_repetido", os.path.join(destino, "servidor", "graficos.py"))
        graficos = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(graficos)

        def rodar(conteudo):
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(conteudo)
            primeira = graficos.corrigir_caminhos_retroarch_cfg()
            texto = open(cfg, encoding="utf-8").read()
            segunda = graficos.corrigir_caminhos_retroarch_cfg()
            depois = open(cfg, encoding="utf-8").read()
            linhas = [l for l in depois.splitlines() if l.split("=", 1)[0].strip() == "cache_directory"]
            return primeira, segunda, texto == depois, linhas

        base = 'video_driver = "gl"\nnetwork_cmd_enable = "false"\n'
        certo = 'cache_directory = "%s"' % os.path.join(destino, "retroarch", "cache")

        _p, segunda, igual, linhas = rodar('cache_directory = ":\\cache"\n' + base)
        confere("forma do RetroArch (:\\cache): fica, sem linha nova", linhas == ['cache_directory = ":\\cache"'],
                linhas)
        confere("... e a 2a correcao nao muda nada", segunda == 0 and igual, (segunda, igual))

        _p, segunda, igual, linhas = rodar('cache_directory = ":\\cache"\n' * 5 + base)
        confere("cinco linhas iguais viram uma", len(linhas) == 1, linhas)
        confere("... e a 2a correcao nao muda nada", segunda == 0 and igual, (segunda, igual))

        _p, segunda, igual, linhas = rodar(base)
        confere("sem a chave: ganha uma, dentro do ARENA", linhas == [certo], linhas)
        confere("... e a 2a correcao nao repete", segunda == 0 and igual, (segunda, igual))

        for nome, valor in (("vazia", ""), ("fora do ARENA", r"C:\Users\alguem\AppData\Local\Temp\x")):
            _p, segunda, igual, linhas = rodar('cache_directory = "%s"\n' % valor + base)
            confere("%s: vai para retroarch\\cache, uma linha so" % nome, linhas == [certo], linhas)
        texto = open(cfg, encoding="utf-8").read()
        confere("as outras linhas continuam", 'video_driver = "gl"' in texto
                and 'network_cmd_enable = "false"' in texto)
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("retroarch.cfg sem linha repetida: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
