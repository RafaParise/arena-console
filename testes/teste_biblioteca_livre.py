# -*- coding: utf-8 -*-
r"""A biblioteca de jogos livres pelo ARENA de verdade (15/10/2026): numa COPIA
do ARENA (testes\copia_do_arena.py), baixa jogos da internet pela rota, como
o aluno faz pela tela, e abre cada um.

  1. A lista: a rota /api/biblioteca-livre mostra os jogos, nenhum instalado.
  2. O aceite: jogo do mamedev.org sem a caixinha marcada nao baixa.
  3. Baixar: cada jogo vem do site de quem publicou, com a marca conferida,
     e cai em jogos\livres\<pasta do console>.
  4. A lista de jogos do ARENA mostra cada um no console certo.
  5. Jogar: cada um abre no nucleo do ARENA (foto da janela) e fecha.

Precisa de internet. Uso:
    servidor\python\python.exe testes\teste_biblioteca_livre.py [id ...]
(sem id: um de cada fonte -- mamedev-robby, homebrew-thwaite,
homebrew-kleleatoms-md-121 e homebrew-space_raid_8k)
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

PADRAO = ["mamedev-robby", "homebrew-thwaite", "homebrew-kleleatoms-md-121", "homebrew-space_raid_8k"]
NUCLEOS = ["mame_libretro.dll", "fceumm_libretro.dll", "genesis_plus_gx_libretro.dll", "stella_libretro.dll"]


def main():
    escolhidos = sys.argv[1:] or PADRAO
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    registro = os.path.join(trabalho, "servidor.log")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=""):
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    try:
        print("Copiando o ARENA para %s ..." % copia, flush=True)
        c.montar(copia, NUCLEOS, {})
        servidor = c.subir_servidor(copia, registro)

        print("1. A lista", flush=True)
        lista = {j["id"]: j for j in c.pedir("/api/biblioteca-livre", espera=30)["jogos"]}
        confere("a rota lista os jogos livres", len(lista) >= 30, len(lista))
        confere("nenhum instalado ainda", not any(j["instalado"] for j in lista.values()))
        confere("os jogos escolhidos estao na lista", all(i in lista for i in escolhidos), escolhidos)

        print("2. O aceite", flush=True)
        com_aceite = next((i for i in escolhidos if lista.get(i, {}).get("aceite")), None)
        if com_aceite:
            try:
                c.pedir("/api/biblioteca-livre/instalar", {"id": com_aceite}, espera=60)
                confere("sem a caixinha, nao baixa", False, "baixou")
            except c.urllib.error.HTTPError as falha:
                texto = falha.read().decode("utf-8", "replace")
                confere("sem a caixinha, nao baixa", falha.code == 400 and "caixinha" in texto, texto[:120])

        print("3. Baixar", flush=True)
        for ident in escolhidos:
            inicio = time.time()
            feito = c.pedir("/api/biblioteca-livre/instalar", {"id": ident, "aceite": True}, espera=240)
            arquivo = os.path.join(copia, feito.get("arquivo", ""))
            confere("%s baixado em %s (%.0f s)" % (ident, feito.get("arquivo"), time.time() - inicio),
                    os.path.isfile(arquivo) and not feito.get("ja_tinha"))

        print("4. Na lista de jogos do ARENA", flush=True)
        c.pedir("/api/indexar", {}, espera=60)
        catalogo = c.pedir("/api/catalogo", espera=30)
        no_catalogo = {}
        for ident in escolhidos:
            console = lista[ident]["console"]
            achados = c.jogos_do_console(catalogo, console)
            confere("%s aparece em %s" % (lista[ident]["titulo"], lista[ident]["console_nome"]), bool(achados),
                    [a.get("titulo") for a in achados])
            if achados:
                no_catalogo[ident] = next((a for a in achados if a.get("titulo", "").lower()[:4]
                                           in lista[ident]["titulo"].lower()), achados[0])
        depois = {j["id"]: j["instalado"] for j in c.pedir("/api/biblioteca-livre", espera=30)["jogos"]}
        confere("a lista marca os baixados como instalados", all(depois.get(i) for i in escolhidos))

        print("5. Jogar", flush=True)
        for ident, jogo in no_catalogo.items():
            resposta = c.pedir("/api/jogar", {"jogo_id": jogo["id"]})
            ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
            confere("%s: o RetroArch abriu" % ident, bool(ra) and not resposta.get("escolher_jeito"))
            time.sleep(15)
            foto = os.path.join(trabalho, "foto_%s.png" % ident)
            ok, detalhe = False, "sem RetroArch"
            for _vez in range(3 if ra else 0):
                c.foto_da_janela(ra[0], foto)
                ok, detalhe = imagem_de_verdade(foto)
                if ok:
                    break
                time.sleep(8)
            confere("%s: a janela mostra o jogo" % ident, ok, detalhe)
            if os.path.isfile(foto):
                shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_livre_%s.png" % ident))
            confere("%s: fechou pela janela" % ident, c.fechar_pela_janela(retroarch))
            time.sleep(2)
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
