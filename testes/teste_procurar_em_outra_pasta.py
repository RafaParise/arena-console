# -*- coding: utf-8 -*-
r"""Procurar jogos e BIOS numa pasta escolhida, pelo ARENA de verdade (10/11/2026).

Numa COPIA do ARENA (testes\copia_do_arena.py): cria uma pasta "de fora" com um jogo livre de MSX tres pastas abaixo
e um neogeo.zip de mentira; acrescenta a pasta pela rota da tela; confere que a busca acha o jogo e a BIOS; leva os
dois; confere que o jogo entrou na lista e que a BIOS foi para a pasta BIOS. Nada da pasta do Rafael muda.

Uso:
    servidor\python\python.exe testes\teste_procurar_em_outra_pasta.py
"""
import os
import shutil
import urllib.error
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402

JOGO = os.path.join(AQUI, "jogos_livres", "MSX", "noborunoca.rom")


def main():
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    fora = os.path.join(trabalho, "Pasta de fora")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    try:
        c.montar(copia, ["bluemsx_libretro.dll"], {})
        fundo = os.path.join(fora, "jogos antigos", "msx", "cartuchos")
        os.makedirs(fundo)
        shutil.copyfile(JOGO, os.path.join(fundo, "noborunoca.rom"))
        with open(os.path.join(fora, "neogeo.zip"), "wb") as arquivo:
            arquivo.write(b"\0" * 4096)          # so o nome importa aqui (com tamanho de arquivo de verdade)
        servidor = c.subir_servidor(copia, os.path.join(trabalho, "servidor.log"))
        c.pedir("/api/indexar", {}, espera=90)

        resposta = c.pedir("/api/baixados/pasta", {"pasta": fora}, espera=15)
        confere("a pasta foi aceita", fora in [os.path.normcase(p) for p in resposta.get("escolhidas", [])]
                or os.path.realpath(fora) in resposta.get("escolhidas", []), resposta)
        try:
            recusa = c.pedir("/api/baixados/pasta", {"pasta": copia}, espera=15)
            confere("a pasta do proprio ARENA e' recusada", not recusa.get("ok"), recusa)
        except urllib.error.HTTPError as falha:
            confere("a pasta do proprio ARENA e' recusada", falha.code == 400, falha.code)

        achados = c.pedir("/api/baixados", espera=60)
        jogo = next((j for j in achados.get("jogos", []) if j["nome"] == "noborunoca.rom"), None)
        confere("achou o jogo tres pastas abaixo", bool(jogo))
        confere("sugeriu o MSX", bool(jogo) and jogo.get("sugestao") == "msx", jogo and jogo.get("sugestao"))
        bios_neogeo = next((b for b in achados.get("bios", []) if b["nome"] == "neogeo.zip"), None)
        confere("achou a BIOS do Neo Geo a parte", bool(bios_neogeo))

        if jogo:
            levado = c.pedir("/api/baixados/levar", {"arquivo": jogo["arquivo"], "console": "msx"}, espera=30)
            confere("levou o jogo", bool(levado.get("ok")), levado.get("erro"))
            lista = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "msx"), 30)
            confere("o jogo esta na lista do MSX", bool(lista))
        if bios_neogeo:
            levada = c.pedir("/api/baixados/levar-bios", {"arquivo": bios_neogeo["arquivo"]}, espera=60)
            confere("levou a BIOS", bool(levada.get("ok")), levada.get("erro"))
            confere("a BIOS esta na pasta BIOS do ARENA",
                    os.path.isfile(os.path.join(copia, "BIOS", "neogeo.zip")), levada.get("destino"))
        confere("nada sobrou na pasta de fora (foi movido, nao copiado)",
                not os.path.exists(os.path.join(fora, "neogeo.zip")))
    finally:
        if servidor is not None:
            c.derrubar(copia)
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        print("FALHOU: %d de %s" % (len(falhas), ", ".join(falhas)))
        return 1
    print("Procurar em outra pasta: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
