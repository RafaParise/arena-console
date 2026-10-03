# -*- coding: utf-8 -*-
r"""A versao dos alunos em uso: montar recusa, --atualizar troca so o programa.

Achado de 02/10/2026: o Rafael estava jogando na ARENA-alunos (3,7 GB de
jogos dele, configuracao, recordes, saves) quando a versao precisou de
conserto -- e montar de novo APAGA a pasta inteira. Agora:
  - montar recusa pasta em uso e nao mexe em nada;
  - --atualizar troca so o programa (servidor, tela, guias, .bat e as
    ferramentas do COLETAR), tira o que saiu do programa e nao encosta no
    resto (jogos, dados, saves, estados, cartoes de memoria, emuladores).

Tudo numa "ARENA-alunos" de mentira, numa pasta temporaria: a de verdade
nao e' tocada. A ultima parte (o comando inteiro, que abre o servidor da
versao atualizada numa copia) so roda com a porta 8777 livre.

Uso: servidor\python\python.exe testes\teste_atualizar_versao_alunos.py
"""
import filecmp
import hashlib
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import montar_versao_alunos as montador  # noqa: E402

# O que e' de quem usou: tem que ficar igualzinho.
DE_QUEM_USOU = {
    os.path.join("dados", "config.json"): b'{"apelido": "Rafa"}',
    os.path.join("dados", "jogadores.txt"): "Mario Kart 64 = 4\n".encode("utf-8"),
    os.path.join("dados", "arena.db"): b"SQLite format 3\x00" + b"\x00" * 100,
    os.path.join("jogos", "pessoais", "PS2", "Crash Nitro Kart (USA).iso"): b"\x01" * 4096,
    os.path.join("jogos", "pessoais", "Arcade", "kof2002.zip"): b"PK\x05\x06" + b"\x00" * 18,
    os.path.join("retroarch", "saves", "Contra (USA).srm"): b"\x02" * 512,
    os.path.join("retroarch", "states", "Contra (USA).state1"): b"\x03" * 512,
    os.path.join("emuladores", "PCSX2", "PCSX2", "memcards", "Mcd001.ps2"): b"\x04" * 1024,
    os.path.join("backup", "copia.zip"): b"PK\x05\x06" + b"\x00" * 18,
    # A correcao do som do KOF 2002 convertido (03/10/2026) e o original guardado.
    os.path.join("retroarch", "system", "fbneo", "patched", "kof2k2fd.zip"): b"PK\x05\x06" + b"\x00" * 18,
    os.path.join("backup", "originais", "kof2002.zip"): b"PK\x05\x06" + b"\x00" * 18,
}
# Nem do programa nem das pastas de quem usou (emulador, nucleo, a
# configuracao do RetroArch): o --atualizar tambem nao encosta.
DE_FORA = {
    os.path.join("retroarch", "retroarch.cfg"): b'video_driver = "gl"\n',
    os.path.join("retroarch", "cores", "fceumm_libretro.dll"): b"MZ" + b"\x00" * 64,
}
# A versao "velha" do programa: arquivos trocados e arquivos que sairam.
VELHOS = {
    os.path.join("servidor", "arena.py"): b"# versao velha\n",
    os.path.join("launcher", "app.js"): b"// versao velha\n",
    "2-JOGOS.md": b"guia velho\n",
    os.path.join("ferramentas", "medir_arena.py"): b"# velho\n",
}
SAIRAM = [os.path.join("servidor", "sobra_velha.py"),
          os.path.join("servidor", "__pycache__", "arena.cpython-313.pyc"),
          os.path.join("launcher", "velho.js")]


def gravar(raiz, rel, conteudo):
    caminho = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)


def marcas(raiz, arquivos):
    """Conteudo (hash), tamanho e data de cada arquivo."""
    saida = {}
    for rel in arquivos:
        caminho = os.path.join(raiz, rel)
        with open(caminho, "rb") as arquivo:
            saida[rel] = (hashlib.sha1(arquivo.read()).hexdigest(), os.stat(caminho).st_mtime_ns)
    return saida


def tudo(raiz):
    """Todos os arquivos da pasta, com hash e data (para "nada mudou")."""
    arquivos = [os.path.relpath(os.path.join(atual, n), raiz)
                for atual, _sub, nomes in os.walk(raiz) for n in nomes]
    return marcas(raiz, arquivos)


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_atualizar_alunos_")
    try:
        destino = os.path.join(pasta, "isolado", montador.NOME_DESTINO)
        # Uma versao montada antes (o programa de agora, com lixo e arquivos
        # velhos por cima) e depois usada.
        for nome in montador.ARQUIVOS_DA_RAIZ:
            montador.copiar_arquivo(os.path.join(RAIZ, nome), os.path.join(destino, nome))
        montador.copiar_arvore(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"), extra=["tests"])
        montador.copiar_arvore(os.path.join(RAIZ, "launcher"), os.path.join(destino, "launcher"))
        for nome in montador.FERRAMENTAS:
            montador.copiar_arquivo(os.path.join(RAIZ, "ferramentas", nome),
                                    os.path.join(destino, "ferramentas", nome))
        for rel, conteudo in list(VELHOS.items()) + [(r, b"velho\n") for r in SAIRAM]:
            gravar(destino, rel, conteudo)
        for rel, conteudo in list(DE_QUEM_USOU.items()) + list(DE_FORA.items()):
            gravar(destino, rel, conteudo)
        gravar(destino, os.path.join("dados", "LEIA.txt"), b"leia\n")
        gravar(destino, os.path.join("jogos", "pessoais", "Arcade", "neogeo.zip"), b"bios\n")

        print("1. Montar de novo recusa a pasta em uso")
        antes = tudo(destino)
        try:
            montador.montar(destino)
            recusou, recado = False, ""
        except SystemExit as saida:
            recusou, recado = True, str(saida)
        confere("recusou, dizendo que esta em uso e mandando usar --atualizar",
                recusou and "ja esta em uso" in recado and "--atualizar" in recado, recado[:300])
        confere("e nao mexeu em nada (nenhum arquivo apagado ou mudado)", tudo(destino) == antes)
        confere("o que a montagem poe (LEIA.txt, neogeo.zip) nao conta como 'em uso'",
                sorted(montador.coisas_de_quem_usou(destino)) == sorted(DE_QUEM_USOU),
                montador.coisas_de_quem_usou(destino))

        print("2. --atualizar troca so o programa")
        guardados = marcas(destino, list(DE_QUEM_USOU) + list(DE_FORA))
        copiados, tirados, quantos, problemas = montador.atualizar(destino)
        confere("sem problema relatado", not problemas, problemas)
        confere("contou os %d arquivos de quem usou" % len(DE_QUEM_USOU), quantos == len(DE_QUEM_USOU), quantos)
        confere("jogos, dados, saves, estados, cartao de memoria, backup, retroarch.cfg e nucleo: iguais "
                "(conteudo e data)", marcas(destino, list(DE_QUEM_USOU) + list(DE_FORA)) == guardados)
        trocados = [rel for rel in VELHOS
                    if filecmp.cmp(os.path.join(RAIZ, rel), os.path.join(destino, rel), shallow=False)]
        confere("os 4 arquivos velhos do programa foram trocados pelos de agora", len(trocados) == len(VELHOS),
                sorted(set(VELHOS) - set(trocados)))
        confere("o que saiu do programa saiu da versao", not any(os.path.exists(os.path.join(destino, r))
                                                                 for r in SAIRAM),
                [r for r in SAIRAM if os.path.exists(os.path.join(destino, r))])
        confere("a lista do que saiu cita os 3", all(r in tirados for r in SAIRAM), tirados)
        confere("o modulo novo (motivo_do_erro.py) chegou",
                os.path.isfile(os.path.join(destino, "servidor", "motivo_do_erro.py")))
        confere("nenhuma pasta de desenvolvimento entrou (servidor\\tests)",
                not os.path.exists(os.path.join(destino, "servidor", "tests")))

        print("3. De novo: nada a trocar")
        copiados, tirados, _quantos, problemas = montador.atualizar(destino)
        confere("segunda vez nao troca nem tira nada", not copiados and not tirados and not problemas,
                (copiados[:5], tirados[:5], problemas))

        print("4. O comando inteiro (abre o servidor da versao numa copia)")
        if not montador.porta_livre():
            print("     (pulado: a porta 8777 esta ocupada -- o ARENA esta aberto)")
        else:
            saida = subprocess.run([sys.executable, os.path.join(RAIZ, "ferramentas", "montar_versao_alunos.py"),
                                    "--atualizar", "--destino", destino], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300)
            texto = saida.stdout + saida.stderr
            confere("o comando termina sem problema", saida.returncode == 0, texto[-600:])
            confere("e o servidor da versao atualizada abriu com a versao certa",
                    "servidor atualizado abriu" in texto, texto[-600:])
            confere("e os dados continuam iguais",
                    marcas(destino, list(DE_QUEM_USOU) + list(DE_FORA)) == guardados)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Atualizar a versao dos alunos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
