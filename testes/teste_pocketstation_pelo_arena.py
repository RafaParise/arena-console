# -*- coding: utf-8 -*-
r"""O console PocketStation pelo ARENA de verdade (10/11/2026), com um minijogo de verdade: o nucleo Pokket abre o jogo,
a tela mostra imagem e o jogo fecha pela janela, como o aluno fecha.

Monta uma COPIA do ARENA (testes\copia_do_arena.py, numa pasta com "o" acentuado no nome, como a do Rafael) com o
nucleo Pokket, a BIOS do professor (pocketstation.bin, que o ARENA nao distribui: e' da Sony) e o primeiro minijogo de
jogos\pessoais\PocketStation. O Pokket abre a BIOS com fopen em ANSI: com acento na pasta, quem resolve e' a ponte sem
acento (servidor\ponte_sem_acento.py), e este teste prova que ela funciona.

Uso:
    servidor\python\python.exe testes\teste_pocketstation_pelo_arena.py [minijogo .gme/.mcr/.bin]
"""
import os
import shutil
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402

RAIZ = c.RAIZ
NUCLEO = "pokket_libretro.dll"
BIOS = os.path.join(RAIZ, "retroarch", "system", "pocketstation.bin")


def minijogo():
    pasta = os.path.join(RAIZ, "jogos", "pessoais", "PocketStation")
    if not os.path.isdir(pasta):
        return None
    itens = sorted(os.path.join(pasta, n) for n in os.listdir(pasta) if not n.lower().endswith(".txt"))
    return itens[0] if itens else None


def main():
    caminhos = [a for a in sys.argv[1:] if not a.startswith("--")]
    jogo = os.path.abspath(caminhos[0]) if caminhos else minijogo()
    if not jogo or not os.path.isfile(jogo) or not os.path.isfile(BIOS):
        print("Faltam: um minijogo em jogos\\pessoais\\PocketStation e a BIOS em retroarch\\system\\pocketstation.bin.")
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    def retroarchs():
        return c.processos("retroarch", retroarch)

    try:
        print("Copiando o ARENA (com %s) para %s ..." % (os.path.basename(jogo), copia), flush=True)
        c.montar(copia, [NUCLEO], {"PocketStation": [jogo]}, sistema=[BIOS])
        servidor = c.subir_servidor(copia, os.path.join(trabalho, "servidor.log"))
        c.pedir("/api/indexar", {}, espera=90)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "pocketstation"), 60)
        confere("o minijogo aparece no PocketStation", bool(achados))
        if not achados:
            return 1
        resposta = c.pedir("/api/jogar", {"jogo_id": achados[0]["id"]}, espera=30)
        confere("o jogo abriu", bool(resposta.get("ok")), None if resposta.get("ok") else resposta)
        programa = c.esperar(retroarchs, 30)
        confere("o RetroArch abriu", bool(programa))
        time.sleep(10)
        confere("o RetroArch continua aberto depois de 10 s", bool(retroarchs()))
        foto = os.path.join(trabalho, "foto_pocketstation.png")
        ok, detalhe = False, "o RetroArch nao abriu"
        for _ in range(3 if programa else 0):
            c.foto_da_janela(programa[0], foto)
            ok, detalhe = imagem_de_verdade(foto)
            if ok:
                break
            time.sleep(4)
        confere("a tela mostra imagem", ok, detalhe)
        if os.path.isfile(foto):
            shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_pocketstation.png"))
        c.fechar_pela_janela(retroarch, 30)
        confere("o jogo fechou pela janela", bool(c.esperar(lambda: not retroarchs(), 20)))
    finally:
        for pid in retroarchs():
            c.subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        if servidor is not None:
            c.derrubar(copia)
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        print("FALHOU: %d de %s" % (len(falhas), ", ".join(falhas)))
        return 1
    print("PocketStation pelo ARENA: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
