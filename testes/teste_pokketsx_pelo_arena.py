# -*- coding: utf-8 -*-
r"""O PokketSX pelo ARENA de verdade (24/10/2026): o PlayStation 1 com o PocketStation ligado, como UM JEITO A MAIS de
abrir o console (consoles.json -> ps1 -> externo_extra).

Monta uma COPIA do ARENA numa pasta com "Pedagógicos" no nome (testes\copia_do_arena.py), com o PlayStation pelo
RetroArch (SwanStation), a BIOS do PlayStation e a do PocketStation do professor (copiadas so para a copia), o PokketSX
SEM settings.ini, BIOS nem cartoes (o ARENA os prepara) e um jogo dele.

  1. Sem escolha: a rota /api/jogar pergunta, com o PokketSX por ultimo, e nada abre.
  2. O PokketSX, escolhido: abre em tela cheia; o ARENA levou as BIOS, criou o cartao do PocketStation e escreveu o
     settings.ini (sem o assistente, PocketStation na entrada 2); o registro dele diz que o PocketStation ligou.
  3. Lembrado: a proxima abertura nao pergunta e abre pelo PokketSX de novo.
  4. Jogar Junto com o PokketSX lembrado: nao da erro e abre pelo RetroArch (o emulador a mais nao vale no Jogar Junto).
  5. "Perguntar" de novo: a pergunta volta.

Uso:
    servidor\python\python.exe testes\teste_pokketsx_pelo_arena.py [jogo de PS1]
(sem jogo: o menor jogo de PS1 dos EUA em jogos\pessoais\PS1; precisa do PokketSX em emuladores\PokketSX)
"""
import os
import shutil
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402
from teste_jeitos_pelo_arena import bios_da_sony, menor_jogo  # noqa: E402

RAIZ = c.RAIZ
NOME_DO_PROGRAMA = "pokketsx-qt-x64-Release-MSVC"
# O que o ARENA tem que preparar sozinho: nada disto vai para a copia.
NAO_LEVAR = shutil.ignore_patterns("bios", "memcards", "savestates", "cache", "settings.ini", "*.log", "screenshots",
                                   "dump", "covers", "gameicons", "cheats", "gamesettings", "inputprofiles")


def main():
    jogo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else menor_jogo()
    sony = bios_da_sony()
    pocketstation = os.path.join(RAIZ, "retroarch", "system", "pocketstation.bin")
    original = os.path.join(RAIZ, "emuladores", "PokketSX")
    if not jogo or not sony or not os.path.isfile(pocketstation) or not os.path.isdir(original):
        print("Faltam: um jogo de PS1 em jogos\\pessoais\\PS1, as BIOS do PS1 e do PocketStation em retroarch\\system "
              "e o PokketSX em emuladores\\PokketSX.")
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    pasta_do_pokketsx = os.path.join(copia, "emuladores", "PokketSX")
    registro = os.path.join(trabalho, "servidor.log")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    def abertos():
        return c.processos(NOME_DO_PROGRAMA, pasta_do_pokketsx)

    def fechar_o_pokketsx():
        for pid in abertos():
            subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True)
        if not c.esperar(lambda: not abertos(), 20):
            for pid in abertos():
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            return False
        return True

    try:
        print("Copiando o ARENA (com %s) para %s ..." % (os.path.basename(jogo), copia), flush=True)
        c.montar(copia, ["swanstation_libretro.dll", "pcsx_rearmed_libretro.dll"], {"PS1": [jogo]},
                 sistema=[sony, pocketstation])
        shutil.copytree(original, pasta_do_pokketsx, ignore=NAO_LEVAR)
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=60)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "ps1"), 60)
        confere("o jogo aparece no PlayStation", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]

        print("1. Sem escolha: a pergunta", flush=True)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id})
        ids = [j["id"] for j in resposta.get("jeitos", [])]
        confere("a rota pergunta, com o PokketSX por ultimo", ids == ["original", "livre", "externo"], ids)
        titulos = [j["titulo"] for j in resposta.get("jeitos", [])]
        confere("o ultimo se chama PokketSX", bool(titulos) and "PokketSX" in titulos[-1], titulos)
        confere("nada abriu com a pergunta", not abertos() and not c.processos("retroarch", retroarch))
        ps1 = next(p for p in c.pedir("/api/catalogo", espera=30)["plataformas"] if p["id"] == "ps1")
        confere("o PlayStation segue sendo do RetroArch (nao do emulador de fora)",
                ps1["emulador"] == "RetroArch" and ps1["aceita_partida"], (ps1["emulador"], ps1["aceita_partida"]))
        externos = [e for e in c.pedir("/api/estado").get("externos", []) if e["nome"] == "PokketSX"]
        confere("Ajustes -> Emuladores lista o PokketSX como opcional e instalado",
                bool(externos) and externos[0]["extra"] and externos[0]["instalado"], externos)
        confere("e nao falta nada a ele", bool(externos) and not externos[0]["falta"], externos and externos[0]["falta"])

        print("2. O PokketSX, escolhido", flush=True)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id, "jeito": "externo", "lembrar": True})
        confere("o jogo abriu sem perguntar", not resposta.get("escolher_jeito") and resposta.get("ok"), resposta)
        confere("o aviso fala do PocketStation", "PocketStation" in resposta.get("aviso", ""), resposta.get("aviso"))
        programa = c.esperar(abertos, 30)
        confere("o PokketSX abriu (o RetroArch, nao)", bool(programa) and not c.processos("retroarch", retroarch))
        time.sleep(14)
        foto = os.path.join(trabalho, "foto_pokketsx.png")
        ok, detalhe = False, "o PokketSX nao abriu"
        for _ in range(3 if programa else 0):
            c.foto_da_janela(programa[0], foto)
            ok, detalhe = imagem_de_verdade(foto)
            if ok:
                break
            time.sleep(8)
        confere("a janela mostra imagem", ok, detalhe)
        if os.path.isfile(foto):
            shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_pokketsx.png"))
        ini = open(os.path.join(pasta_do_pokketsx, "settings.ini"), encoding="utf-8", errors="replace").read()
        for linha in ("SetupWizardIncomplete = false", "Card2Type = Shared", "Card2PocketStation = true",
                      "Card2Path = PocketStation.mcd", "PocketStationBiosPath = pocketstation.bin",
                      "PowerOff = Keyboard/F10", "ConfirmPowerOff = false"):
            confere("settings.ini: %s" % linha, linha in ini)
        bios = os.listdir(os.path.join(pasta_do_pokketsx, "bios"))
        confere("as BIOS foram levadas (a do PS1 e a do PocketStation)",
                os.path.basename(sony) in bios and "pocketstation.bin" in bios, bios)
        cartao = os.path.join(pasta_do_pokketsx, "memcards", "PocketStation.mcd")
        confere("o cartao do PocketStation nasceu (128 KB, formatado)",
                os.path.isfile(cartao) and os.path.getsize(cartao) == 131072
                and open(cartao, "rb").read(2) == b"MC")
        confere("fechou pela janela", fechar_o_pokketsx())
        time.sleep(2)

        print("3. Lembrado: nao pergunta", flush=True)
        lembrado = c.pedir("/api/estado").get("config", {}).get("jeito_de_abrir", {})
        confere("a escolha ficou lembrada", lembrado.get("ps1") == "externo", lembrado)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id})
        confere("abriu sem perguntar", not resposta.get("escolher_jeito") and resposta.get("ok"), resposta)
        confere("pelo PokketSX de novo", bool(c.esperar(abertos, 30)))
        confere("fechou pela janela", fechar_o_pokketsx())
        time.sleep(2)
        ja = open(cartao, "rb").read()
        confere("o cartao que ja existia nao foi trocado", ja[:2] == b"MC" and len(ja) == 131072)

        print("4. Jogar Junto com o PokketSX lembrado", flush=True)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id, "partida": "hospedar"})
        confere("a rota nao reclama (o emulador a mais nao vale no Jogar Junto)",
                resposta.get("ok") and not resposta.get("escolher_jeito"), resposta)
        ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
        confere("abriu pelo RetroArch", bool(ra) and not abertos())
        c.fechar_pela_janela(retroarch)
        time.sleep(2)

        print("5. Perguntar de novo", flush=True)
        c.pedir("/api/config", {"jeito_de_abrir": {"ps1": ""}})
        confere("a pergunta voltou", bool(c.pedir("/api/jogar", {"jogo_id": jogo_id}).get("escolher_jeito")))
    finally:
        if servidor and servidor.poll() is None:
            servidor.kill()
            servidor.wait()
        for pid in c.processos(NOME_DO_PROGRAMA, pasta_do_pokketsx):
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        c.derrubar(copia)
        time.sleep(1)
        if falhas and os.path.isfile(registro):
            print("--- registro do servidor (fim) ---")
            for linha in open(registro, encoding="utf-8", errors="replace").read().splitlines()[-25:]:
                print("   ", linha[:200])
        limpeza.apagar_pasta(trabalho)
    if falhas:
        print("
FALHAS: %d" % len(falhas))
        return 1
    print("
Tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
