# -*- coding: utf-8 -*-
r"""Os jeitos de abrir do Dreamcast pelo ARENA de verdade (16/10/2026): com a
BIOS do professor (dc_boot.bin) e a imitacao do Flycast (a BIOS livre que vem
dentro do emulador), o ARENA pergunta qual usar.

Numa COPIA do ARENA (testes\copia_do_arena.py), com a dc_boot.bin do
professor copiada para a system dela (os saves de VMU e a memoria do console
do professor, em retroarch\system\dc, nao sao tocados) e um jogo dele:

  1. Sem escolha: a rota /api/jogar devolve a pergunta, com os dois jeitos.
  2. O livre, lembrado: o registro do RetroArch diz "Did not load BIOS,
     using reios" (a BIOS imitada do Flycast).
  3. O original, pela configuracao: o registro nao fala do reios, e a opcao
     da imitacao saiu do arquivo de opcoes de nucleo da copia.

Uso:
    servidor\python\python.exe testes\teste_jeito_dreamcast.py [pasta do jogo]
(sem pasta: o GigaWing 2, se estiver em jogos\pessoais\Dreamcast)
"""
import glob
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
from teste_jeitos_pelo_arena import registro_novo  # noqa: E402

RAIZ = c.RAIZ
BIOS = os.path.join(RAIZ, "retroarch", "system", "dc", "dc_boot.bin")


def main():
    padrao = glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Dreamcast", "GigaWing 2*"))
    jogo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else (padrao[0] if padrao else "")
    if not os.path.isdir(jogo) or not os.path.isfile(BIOS):
        print("Falta um jogo de Dreamcast (pasta) em jogos\\pessoais\\Dreamcast ou a dc_boot.bin em "
              "retroarch\\system\\dc.")
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    registro = os.path.join(trabalho, "servidor.log")
    falhas, vistos = [], set()
    servidor = None

    def confere(nome, ok, detalhe=""):
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    def jogar_e_fechar(corpo, rotulo):
        resposta = c.pedir("/api/jogar", corpo)
        confere("%s: o jogo abriu sem perguntar" % rotulo, not resposta.get("escolher_jeito"))
        ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
        time.sleep(30)
        foto = os.path.join(trabalho, "foto_%s.png" % rotulo)
        ok, detalhe = False, "o RetroArch nao abriu"
        for _vez in range(3 if ra else 0):
            c.foto_da_janela(ra[0], foto)
            ok, detalhe = imagem_de_verdade(foto)
            if ok:
                break
            time.sleep(10)
        confere("%s: a janela mostra o jogo" % rotulo, ok, detalhe)
        if os.path.isfile(foto):
            shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_dc_%s.png" % rotulo))
        confere("%s: fechou pela janela" % rotulo, c.fechar_pela_janela(retroarch, limite=40))
        time.sleep(2)
        return registro_novo(copia, vistos)

    try:
        print("Copiando o ARENA (com %s) para %s ..." % (os.path.basename(jogo), copia), flush=True)
        c.montar(copia, ["flycast_libretro.dll"], {"Dreamcast": [jogo]})
        os.makedirs(os.path.join(retroarch, "system", "dc"), exist_ok=True)
        shutil.copyfile(BIOS, os.path.join(retroarch, "system", "dc", "dc_boot.bin"))
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=60)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "dreamcast"), 60)
        confere("o jogo aparece no Dreamcast", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]

        print("1. Sem escolha: a pergunta", flush=True)
        ids = [j["id"] for j in c.pedir("/api/jogar", {"jogo_id": jogo_id}).get("jeitos", [])]
        confere("a rota pergunta, com o original e o livre", ids == ["original", "livre"], ids)

        print("2. O livre, lembrado", flush=True)
        texto = jogar_e_fechar({"jogo_id": jogo_id, "jeito": "livre", "lembrar": True}, "livre")
        confere("o Flycast ligou com a BIOS imitada (reios)", "using reios" in texto)

        print("3. O original, pela configuracao", flush=True)
        c.pedir("/api/config", {"jeito_de_abrir": {"dreamcast": "original"}})
        texto = jogar_e_fechar({"jogo_id": jogo_id}, "original")
        confere("o Flycast ligou com a dc_boot.bin (sem o reios)", "using reios" not in texto and bool(texto))
        opcoes = os.path.join(retroarch, "retroarch-core-options.cfg")
        conteudo = open(opcoes, encoding="utf-8", errors="replace").read() if os.path.isfile(opcoes) else ""
        confere("a opcao da imitacao nao ficou ligada no arquivo", 'reicast_hle_bios = "enabled"' not in conteudo)
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
