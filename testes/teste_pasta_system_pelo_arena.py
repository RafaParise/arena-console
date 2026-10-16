# -*- coding: utf-8 -*-
r"""O N64 e o VICE numa pasta com acento, pelo ARENA de verdade (achado da
rodada final de 15/10/2026).

Os dois nucleos abrem o jogo com acento, mas gravam na pasta system pelo
caminho em ANSI, o jeito antigo do Windows: o "ó" de "Pedagógicos" virava
"Ã³", e o cache do N64 (shaders, texturas e o mupen64plus.ini) ia parar numa
pasta de nome estragado, fora do ARENA. Agora o ARENA diz a pasta system a
eles pelo caminho relativo ("system", a partir da pasta do RetroArch:
servidor\ponte_sem_acento.py).

Monta uma COPIA do ARENA numa pasta com "Pedagógicos" no nome
(testes\copia_do_arena.py) com o N64 (o menor jogo do professor, se houver)
e o VIC-20 (o Baguel, livre, de testes\jogos_livres). Para cada um:
  1. o jogo abre pela rota /api/jogar e aparece na janela;
  2. o nucleo recebeu "system" (o registro do RetroArch diz qual pasta);
  3. o que ele gravou esta na retroarch\system da copia (a Mupen64plus,
     a vice), e a pasta de nome estragado nao apareceu. O N64 tambem passa
     a ler o banco de jogos dele (o mupen64plus.ini, com o jeito certo de
     cada jogo): antes, ele o gravava na pasta estragada e o procurava na
     certa ("Unable to open rom database file", "unknown rom");
  4. o retroarch.cfg volta, depois do jogo, com a pasta system de antes
     (":\system", a forma do RetroArch para a pasta dele mesmo): a
     relativa vale so na partida.

Uso:
    servidor\python\python.exe testes\teste_pasta_system_pelo_arena.py
"""
import glob
import json
import os
import re
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402
from teste_jeitos_pelo_arena import pasta_do_nucleo, registro_novo  # noqa: E402

RAIZ = c.RAIZ


def menor_jogo_de_n64():
    jogos = [j for extensao in ("*.z64", "*.n64", "*.v64")
             for j in glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "Nintendo 64", extensao))]
    return min(jogos, key=os.path.getsize) if jogos else None


def estragado(caminho):
    """O nome que o nucleo em ANSI cria: os bytes do UTF-8 lidos como cp1252."""
    return caminho.encode("utf-8").decode("cp1252", "replace")


def system_no_cfg(retroarch):
    with open(os.path.join(retroarch, "retroarch.cfg"), encoding="utf-8", errors="replace") as arquivo:
        achado = re.search(r'^system_directory\s*=\s*"([^"]*)"', arquivo.read(), re.M)
    return achado.group(1) if achado else ""


def main():
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    n64 = menor_jogo_de_n64()
    casos = [("vic20", "Commodore VIC-20", "vice_xvic_libretro.dll",
              os.path.join(RAIZ, "testes", "jogos_livres", "VIC-20", "baguel.d64"), "vice")]
    if n64:
        casos.insert(0, ("n64", "Nintendo 64", "mupen64plus_next_libretro.dll", n64,
                         os.path.join("Mupen64plus", "mupen64plus.ini")))
    else:
        print("Sem jogo de N64 em jogos\\pessoais\\Nintendo 64: so o VIC-20.")
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    sistema = os.path.join(retroarch, "system")
    torto = estragado(trabalho)
    registro = os.path.join(trabalho, "servidor.log")
    falhas, vistos = [], set()
    servidor = None

    def confere(nome, ok, detalhe=""):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    try:
        print("Copiando o ARENA para %s ..." % copia, flush=True)
        c.montar(copia, [caso[2] for caso in casos], {caso[1]: [caso[3]] for caso in casos})
        # O jogo numa janela, nao em tela cheia: em tela cheia, a foto da
        # janela do N64 (OpenGL) sai preta mesmo com o jogo rodando, com e
        # sem o conserto (visto em 16/10/2026; a foto da tela inteira tambem).
        with open(os.path.join(copia, "dados", "config.json"), "w", encoding="utf-8") as arquivo:
            json.dump({"avancado": {"video_fullscreen": "false"}}, arquivo)
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=60)
        catalogo = c.esperar(lambda: c.pedir("/api/catalogo", espera=30), 60)
        antes = system_no_cfg(retroarch)
        for console, _pasta, _nucleo, jogo, gravado in casos:
            print("== %s (%s)" % (console, os.path.basename(jogo)), flush=True)
            achados = c.jogos_do_console(catalogo, console)
            confere("o jogo aparece no console", bool(achados))
            if not achados:
                continue
            resposta = c.pedir("/api/jogar", {"jogo_id": achados[0]["id"]})
            confere("abriu sem perguntar", not resposta.get("escolher_jeito"), resposta.get("erro", ""))
            ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
            time.sleep(20)
            foto = os.path.join(trabalho, "foto_%s.png" % console)
            ok, detalhe = False, "o RetroArch nao abriu"
            for _vez in range(3 if ra else 0):
                c.foto_da_janela(ra[0], foto)
                ok, detalhe = imagem_de_verdade(foto)
                if ok:
                    break
                time.sleep(10)
            confere("a janela mostra o jogo", ok, detalhe)
            confere("fechou pela janela", c.fechar_pela_janela(retroarch))
            time.sleep(2)
            texto = registro_novo(copia, vistos)
            confere("o nucleo recebeu a pasta system relativa", pasta_do_nucleo(texto) == "system",
                    pasta_do_nucleo(texto))
            confere("gravou dentro do ARENA (retroarch\\system\\%s)" % gravado,
                    os.path.exists(os.path.join(sistema, gravado)))
            confere("nada na pasta de nome estragado", not os.path.exists(torto), torto)
            if console == "n64":
                confere("o N64 leu o banco de jogos (mupen64plus.ini)", "unknown rom" not in texto)
            depois = system_no_cfg(retroarch)
            confere("o retroarch.cfg voltou com a pasta system de antes", depois == antes and depois != "system",
                    "%s, antes %s" % (depois, antes))
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
        if os.path.isdir(torto):
            limpeza.apagar_pasta(torto)
    if falhas:
        print("\nFALHAS: %d" % len(falhas))
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
