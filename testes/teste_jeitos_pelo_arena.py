# -*- coding: utf-8 -*-
r"""Os jeitos de abrir pelo ARENA de verdade (pedido do Rafael, 15/10/2026):
com a BIOS original E a livre, o ARENA pergunta qual usar, lembra a
resposta e deixa trocar em Ajustes -> Emuladores.

Monta uma COPIA do ARENA numa pasta com "Pedagógicos" no nome
(testes\copia_do_arena.py) com o PlayStation: o SwanStation, a BIOS do
professor (a da Sony, copiada so para a copia) e um jogo dele. A OpenBIOS
(livre) o proprio ARENA da copia instala, de servidor\bios_livres.

  1. Sem escolha: a rota /api/jogar devolve a pergunta, com os dois jeitos.
     A OpenBIOS fica na pasta dela (retroarch\system\OpenBIOS), nunca
     solta na system: solta, o SwanStation a escolheria ate no original.
  2. O livre, lembrado: o jogo abre com a OpenBIOS (o registro do
     RetroArch diz qual BIOS o nucleo carregou) e a escolha fica na
     configuracao. A proxima abertura nao pergunta.
  3. O original, pela configuracao: o jogo abre com a BIOS da Sony.
  4. "Perguntar" de novo: a pergunta volta.
  5. Sem a BIOS da Sony (tirada da copia): o jogo abre pela OpenBIOS sem
     perguntar, com o aviso de que ela e' a livre.

Uso:
    servidor\python\python.exe testes\teste_jeitos_pelo_arena.py [jogo de PS1]
(sem jogo: o menor jogo de PS1 em jogos\pessoais\PS1)
"""
import glob
import os
import re
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
SISTEMA = os.path.join(RAIZ, "retroarch", "system")


def bios_da_sony():
    """A BIOS de PS1 do professor (reconhecida pelo conteudo), ou None."""
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    import bios
    for nome in sorted(os.listdir(SISTEMA)):
        caminho = os.path.join(SISTEMA, nome)
        achado = os.path.isfile(caminho) and bios.playstation(caminho)
        if achado and achado[0] == "ps1":
            return caminho
    return None


def menor_jogo():
    """O menor jogo de PS1 dos EUA (a BIOS do professor e' a americana: um
    jogo europeu abre com ela, mas demora mais), senao o menor de todos."""
    jogos = glob.glob(os.path.join(RAIZ, "jogos", "pessoais", "PS1", "*.chd"))
    americanos = [j for j in jogos if "(USA)" in os.path.basename(j)]
    return min(americanos or jogos, key=os.path.getsize) if jogos else None


def registro_novo(copia, vistos):
    """O registro do RetroArch da partida que acabou de rodar (dados\\retroarch__*.log)."""
    novos = [r for r in glob.glob(os.path.join(copia, "dados", "retroarch__*.log")) if r not in vistos]
    vistos.update(novos)
    return open(max(novos, key=os.path.getmtime), encoding="utf-8", errors="replace").read() if novos else ""


def linhas_da_bios(texto):
    """As linhas do registro que contam de onde veio a BIOS: a pasta que o
    RetroArch deu ao nucleo e a busca do SwanStation."""
    return [l.strip() for l in texto.splitlines()
            if re.search(r"GET_SYSTEM_DIRECTORY|Using BIOS|Using unknown BIOS|Falling back|Searching for", l)]


def pasta_do_nucleo(texto):
    """A pasta das BIOS que o RetroArch deu ao nucleo (GET_SYSTEM_DIRECTORY)."""
    achados = re.findall(r'GET_SYSTEM_DIRECTORY: "([^"]+)"', texto)
    return achados[-1] if achados else ""


def bios_carregada(texto):
    """O arquivo que o SwanStation achou na busca pela pasta ("Using BIOS",
    ou "Falling back..." com a BIOS de outra regiao), ou ''. Quando abre
    direto a BIOS das opcoes do nucleo (a openbios.bin no jeito livre), ele
    nao escreve nada: ai vale a pasta que ele recebeu (pasta_do_nucleo)."""
    achados = re.findall(r"(?:Using BIOS|Using unknown BIOS|Falling back to possibly-incompatible image) '([^']+)'",
                         texto)
    return os.path.basename(achados[-1]) if achados else ""


def so_a_openbios(pasta):
    """A pasta tem uma BIOS de PlayStation so (o tamanho dela, 512 KB), a openbios.bin?"""
    try:
        return [n for n in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, n))
                and os.path.getsize(os.path.join(pasta, n)) == 524288] == ["openbios.bin"]
    except OSError:
        return False


def main():
    jogo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else menor_jogo()
    sony = bios_da_sony()
    if not jogo or not sony:
        print("Falta um jogo de PS1 em jogos\\pessoais\\PS1 ou a BIOS do PS1 em retroarch\\system.")
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
        print("  %-4s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    def jogar_e_fechar(corpo, rotulo):
        """Abre pela rota, espera, fotografa e fecha pela janela. Devolve a
        resposta da rota e o registro do RetroArch dessa partida."""
        resposta = c.pedir("/api/jogar", corpo)
        confere("%s: o jogo abriu sem perguntar" % rotulo, not resposta.get("escolher_jeito"))
        ra = c.esperar(lambda: c.processos("retroarch", retroarch), 30)
        time.sleep(25)
        foto = os.path.join(trabalho, "foto_%s.png" % rotulo)
        ok, detalhe = False, "o RetroArch nao abriu"
        # Ate 3 fotos, 10 s entre elas: entre a abertura da BIOS e o jogo, a
        # tela fica preta por um instante.
        for _vez in range(3 if ra else 0):
            c.foto_da_janela(ra[0], foto)
            ok, detalhe = imagem_de_verdade(foto)
            if ok:
                break
            time.sleep(10)
        confere("%s: a janela mostra o jogo" % rotulo, ok, detalhe)
        if os.path.isfile(foto):
            shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_jeito_%s.png" % rotulo))
        confere("%s: fechou pela janela" % rotulo, c.fechar_pela_janela(retroarch))
        time.sleep(2)
        texto = registro_novo(copia, vistos)
        for linha in linhas_da_bios(texto)[:4]:
            print("       registro: %s" % linha[:150])
        return resposta, texto

    try:
        print("Copiando o ARENA (com %s) para %s ..." % (os.path.basename(jogo), copia), flush=True)
        c.montar(copia, ["swanstation_libretro.dll", "pcsx_rearmed_libretro.dll"], {"PS1": [jogo]},
                 sistema=[sony])
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=60)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "ps1"), 60)
        confere("o jogo aparece no PlayStation", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]
        sistema_copia = os.path.join(retroarch, "system")
        sony_copia = os.path.join(sistema_copia, os.path.basename(sony))

        print("1. Sem escolha: a pergunta", flush=True)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id})
        ids = [j["id"] for j in resposta.get("jeitos", [])]
        confere("a rota pergunta, com o original e o livre", ids == ["original", "livre"], ids)
        confere("nenhum RetroArch abriu com a pergunta", not c.processos("retroarch", retroarch))
        confere("a OpenBIOS esta na pasta dela (system\\OpenBIOS)",
                os.path.isfile(os.path.join(sistema_copia, "OpenBIOS", "openbios.bin")))
        confere("e nao solta na system", not os.path.exists(os.path.join(sistema_copia, "openbios.bin")))

        pasta_openbios = os.path.join(sistema_copia, "OpenBIOS")

        def confere_livre(rotulo, texto):
            """No jeito livre, o nucleo recebe a pasta da OpenBIOS como a pasta
            das BIOS, e nela a unica BIOS e' a openbios.bin."""
            pasta = pasta_do_nucleo(texto)
            confere("%s: o nucleo recebeu a pasta da OpenBIOS" % rotulo,
                    os.path.normcase(pasta) == os.path.normcase(pasta_openbios), pasta or "nada no registro")
            confere("%s: e nela so ha a openbios.bin" % rotulo,
                    so_a_openbios(pasta_openbios) and bios_carregada(texto).lower() in ("", "openbios.bin"),
                    bios_carregada(texto))

        print("2. O livre, lembrado", flush=True)
        _resposta, texto = jogar_e_fechar({"jogo_id": jogo_id, "jeito": "livre", "lembrar": True}, "livre")
        confere_livre("livre", texto)
        lembrado = c.pedir("/api/estado").get("config", {}).get("jeito_de_abrir", {})
        confere("a escolha ficou lembrada", lembrado.get("ps1") == "livre", lembrado)
        _resposta, texto = jogar_e_fechar({"jogo_id": jogo_id}, "livre-lembrado")
        confere_livre("livre-lembrado", texto)

        print("3. O original, pela configuracao", flush=True)
        c.pedir("/api/config", {"jeito_de_abrir": {"ps1": "original"}})
        _resposta, texto = jogar_e_fechar({"jogo_id": jogo_id}, "original")
        confere("original: o nucleo recebeu a system",
                os.path.normcase(pasta_do_nucleo(texto)) == os.path.normcase(sistema_copia), pasta_do_nucleo(texto))
        confere("original: o SwanStation achou a BIOS da Sony, nao a OpenBIOS da pasta dela",
                bios_carregada(texto) == os.path.basename(sony), bios_carregada(texto) or "nada no registro")

        print("4. Perguntar de novo", flush=True)
        c.pedir("/api/config", {"jeito_de_abrir": {"ps1": ""}})
        confere("a pergunta voltou", bool(c.pedir("/api/jogar", {"jogo_id": jogo_id}).get("escolher_jeito")))

        print("5. Sem a BIOS da Sony (tirada da copia)", flush=True)
        os.replace(sony_copia, os.path.join(trabalho, os.path.basename(sony)))
        resposta, texto = jogar_e_fechar({"jogo_id": jogo_id}, "so-a-livre")
        confere_livre("so-a-livre", texto)
        confere("com o aviso da BIOS livre", "OpenBIOS" in resposta.get("aviso", ""), resposta.get("aviso"))
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
