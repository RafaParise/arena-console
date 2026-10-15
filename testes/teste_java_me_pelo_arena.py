# -*- coding: utf-8 -*-
r"""Java ME pelo ARENA de verdade (15/10/2026): o caminho inteiro, como o aluno
usa -- o servidor do ARENA, a rota /api/jogar, o RetroArch, o Java que vem
no ARENA e a ponte sem acento.

Monta uma COPIA do ARENA numa pasta com "Pedagógicos" no nome
(testes\copia_do_arena.py): o servidor, a tela, o RetroArch com o nucleo do
Java ME, o Java (emuladores\Java) e um jogo. Nada do ARENA de verdade e'
tocado: nem os dados, nem os saves.

  1. JOGO NORMAL: abre pela rota /api/jogar, fotografa a janela, fecha como
     o aluno fecha (a janela recebe o "fechar"). Confere: a imagem, o Java
     que fechou junto, a ponte sem acento no registro do ARENA, os dados do
     jogo gravados na pasta certa (retroarch\saves da copia) e nenhuma
     pasta com o nome estragado ("PedagÃ³gicos") criada.
  2. QUEDA: abre de novo e derruba o RetroArch a forca. O Java do jogo tem
     que fechar junto (a caixa do Windows, servidor\processos.py).

Uso:
    servidor\python\python.exe testes\teste_java_me_pelo_arena.py [jogo.jar]
(sem jogo: o Shooter, livre, de testes\jogos_livres)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402


def main():
    jogo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
        os.path.join(AQUI, "jogos_livres", "J2ME", "shooter.jar")
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    temporaria = tempfile.gettempdir()
    antes_temp = set(os.listdir(temporaria))
    trabalho, copia = c.nova_pasta()
    falhas = []
    servidor = None
    registro = os.path.join(trabalho, "servidor.log")

    def confere(nome, ok, detalhe=""):
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    try:
        print("Copiando o ARENA para %s ..." % copia, flush=True)
        c.montar(copia, ["freej2me_libretro.dll"], {"J2ME": [jogo]}, java=True)
        servidor = c.subir_servidor(copia, registro)
        confere("o servidor da copia abriu", c.responde())
        c.pedir("/api/indexar", {}, espera=60)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "j2me"), 60)
        confere("o jogo aparece no console Java ME", bool(achados))
        if not achados:
            return 1
        jar_na_system = os.path.join(copia, "retroarch", "system", "freej2me-lr.jar")
        java = os.path.join(copia, "emuladores", "Java")
        retroarch = os.path.join(copia, "retroarch")

        # 1. Jogo normal.
        print("1. Jogo normal (fecha pela janela)", flush=True)
        c.pedir("/api/jogar", {"jogo_id": achados[0]["id"]})
        ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
        confere("o RetroArch da copia abriu", bool(ra))
        # A metade Java vai para a system antes do jogo, mesmo com a arrumacao
        # das BIOS da abertura ainda rodando (o primeiro jogo abria sem ela).
        confere("o ARENA pos a metade Java do emulador na system", os.path.isfile(jar_na_system))
        javaw = c.esperar(lambda: c.processos("javaw", java), 40)
        confere("o Java do ARENA abriu o jogo (sem Java instalado no caminho)", bool(javaw))
        time.sleep(20)                 # aberturas do jogo (logo da empresa, menu)
        foto = os.path.join(trabalho, "java_me.png")
        if ra:
            c.foto_da_janela(ra[0], foto)
        ok, detalhe = imagem_de_verdade(foto)
        confere("a janela mostra o jogo", ok, detalhe)
        if os.path.isfile(foto):
            guardada = os.path.join(temporaria, "arena_java_me_foto.png")
            shutil.copyfile(foto, guardada)
            print("     foto: %s" % guardada)
        confere("o RetroArch fechou pela janela", c.fechar_pela_janela(retroarch))
        confere("o Java fechou junto", c.esperar(lambda: not c.processos("javaw", java), 10))
        time.sleep(2)
        texto = open(registro, encoding="utf-8", errors="replace").read()
        confere("o jogo abriu pela ponte sem acento", "Pasta com acento: o jogo abre por" in texto)
        confs = [os.path.join(atual, nome) for atual, _pastas, nomes in os.walk(os.path.join(retroarch, "saves"))
                 for nome in nomes if nome == "game.conf"]
        confere("os dados do jogo ficaram em retroarch\\saves da copia", bool(confs),
                os.path.relpath(confs[0], copia) if confs else "nenhum game.conf")
        estragadas = [n for n in set(os.listdir(temporaria)) - antes_temp if "Ã" in n]
        confere("nenhuma pasta com o nome estragado (PedagÃ³gicos)", not estragadas, estragadas)

        # 2. Queda.
        print("2. Queda (o RetroArch derrubado a forca)", flush=True)
        c.pedir("/api/jogar", {"jogo_id": achados[0]["id"]})
        ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
        javaw = c.esperar(lambda: c.processos("javaw", java), 40)
        confere("abriu de novo (RetroArch e Java)", bool(ra and javaw))
        time.sleep(5)
        for pid in ra:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        sobrou = c.esperar(lambda: not c.processos("javaw", java), 10)
        confere("o Java do jogo fechou junto com a queda (a caixa do Windows)", sobrou)
    finally:
        if servidor and servidor.poll() is None:
            servidor.kill()
            servidor.wait()
        c.derrubar(copia)
        time.sleep(1)
        if falhas and os.path.isfile(registro):
            print("--- registro do servidor (fim) ---")
            for linha in open(registro, encoding="utf-8", errors="replace").read().splitlines()[-25:]:
                print("   ", linha[:200])
        limpeza.apagar_pasta(trabalho)
    if falhas:
        print("\nFALHAS: %d" % len(falhas))
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
