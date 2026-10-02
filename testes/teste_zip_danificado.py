# -*- coding: utf-8 -*-
r"""Zip de fliperama danificado: o ARENA descobre e avisa.

Achado de 02/10/2026 (tarefa 7, "Metal Slug X com cores erradas"): o
mslugx.zip da pasta tinha a parte MSX_C3.rom (grafico dos personagens)
danificada -- nao confere com a assinatura (CRC) do proprio zip. O FBNeo
carregava a parte estragada e os personagens saiam com cor estranha; o
MAME recusava. servidor\integridade.py confere cada zip uma vez.

Numa pasta temporaria (o arquivo de conferencias tambem e' temporario):
  1. zip inteiro -> "" ; zip com uma parte estragada -> o nome dela;
     arquivo que nem e' zip -> "(o zip inteiro)"; nao-.zip -> None;
  2. o resultado fica guardado: a 2a vez nao descompacta (conferir=False
     devolve o guardado); copiou de novo (mudou tamanho/data) -> confere de novo;
  3. o cartao do jogo avisa (indexador), so com o resultado guardado;
  4. o mslugx.zip DE VERDADE, se estiver na pasta: so leitura, sem guardar.

Uso: servidor\python\python.exe testes\teste_zip_danificado.py
"""
import os
import sys
import tempfile
import time
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import limpeza  # noqa: E402
import integridade  # noqa: E402
import indexador  # noqa: E402


def estragar(caminho, nome_da_parte):
    """Troca bytes no MEIO dos dados comprimidos de uma parte (o diretorio do
    zip continua certo -- como no mslugx.zip de verdade)."""
    with zipfile.ZipFile(caminho) as pacote:
        info = pacote.getinfo(nome_da_parte)
    with open(caminho, "r+b") as arquivo:
        arquivo.seek(info.header_offset + 26)
        n_nome = int.from_bytes(arquivo.read(2), "little")
        n_extra = int.from_bytes(arquivo.read(2), "little")
        inicio_dados = info.header_offset + 30 + n_nome + n_extra
        arquivo.seek(inicio_dados + info.compress_size // 2)
        bytes_lidos = bytearray(arquivo.read(16))
        arquivo.seek(inicio_dados + info.compress_size // 2)
        arquivo.write(bytes(b ^ 0x5A for b in bytes_lidos))


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe))
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_zip_danificado_")
    guardado = integridade.ARQUIVO
    try:
        integridade.ARQUIVO = os.path.join(pasta, "zips_conferidos.json")
        bom = os.path.join(pasta, "bom.zip")
        ruim = os.path.join(pasta, "ruim.zip")
        for caminho in (bom, ruim):
            with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as pacote:
                pacote.writestr("250-p1.p1", os.urandom(20000) + b"x" * 200000)
                pacote.writestr("MSX_C3.rom", os.urandom(50000) + b"y" * 300000)
        estragar(ruim, "MSX_C3.rom")
        lixo = os.path.join(pasta, "lixo.zip")
        open(lixo, "wb").write(b"isto nao e zip")
        outro = os.path.join(pasta, "jogo.7z")
        open(outro, "wb").write(b"7z")

        confere("zip inteiro: nenhuma parte ruim", integridade.parte_danificada(bom) == "")
        confere("zip com uma parte estragada: diz qual", integridade.parte_danificada(ruim) == "MSX_C3.rom",
                integridade.parte_danificada(ruim))
        confere("arquivo que nem e' zip", integridade.parte_danificada(lixo) == "(o zip inteiro)")
        confere(".7z nao e' conferido (None)", integridade.parte_danificada(outro) is None)
        confere("resultado guardado: a 2a vez nao descompacta",
                integridade.parte_danificada(ruim, conferir=False) == "MSX_C3.rom")
        # "Copiou de novo": o arquivo muda (tamanho e data) e volta a ser conferido.
        with zipfile.ZipFile(ruim, "w", zipfile.ZIP_DEFLATED) as pacote:
            pacote.writestr("MSX_C3.rom", b"bom" * 1000)
        os.utime(ruim, (time.time() + 5, time.time() + 5))
        confere("copiou de novo: o guardado nao vale mais (None sem conferir)",
                integridade.parte_danificada(ruim, conferir=False) is None)
        confere("... e a conferencia nova diz que esta inteiro", integridade.parte_danificada(ruim) == "")
        confere("a frase para o aluno diz a parte e o que fazer",
                "MSX_C3.rom" in integridade.texto_do_aviso("MSX_C3.rom")
                and "Copie o jogo de novo" in integridade.texto_do_aviso("MSX_C3.rom"))

        # 3. O cartao do jogo, pelo indexador (so le o guardado).
        por_id, por_extensao = indexador.carregar_plataformas()
        jogos_pasta = os.path.join(pasta, "jogos")
        neo = os.path.join(jogos_pasta, por_id["neogeo"]["pasta"])
        os.makedirs(neo)
        estragado = os.path.join(neo, "mslugx.zip")
        with zipfile.ZipFile(estragado, "w", zipfile.ZIP_DEFLATED) as pacote:
            pacote.writestr("MSX_C3.rom", os.urandom(40000) + b"z" * 200000)
        estragar(estragado, "MSX_C3.rom")
        cartao = lambda: [j for j in indexador.varrer_pasta(jogos_pasta, "pessoais", por_extensao, por_id)
                          if j["arquivo"].lower().endswith("mslugx.zip")][0]
        confere("antes de conferir: a lista nao descompacta nem avisa",
                not any("danificado" in a["texto"] for a in cartao()["avisos"]))
        integridade.parte_danificada(estragado)
        confere("depois de conferido: o cartao avisa",
                any("danificado" in a["texto"] and "MSX_C3.rom" in a["texto"] for a in cartao()["avisos"]),
                cartao()["avisos"])
    finally:
        integridade.ARQUIVO = guardado
        limpeza.apagar_pasta(pasta)

    # 4. O mslugx.zip de verdade (so leitura, sem guardar nada).
    real = os.path.join(RAIZ, "jogos", "pessoais", "Neo Geo", "mslugx.zip")
    if os.path.isfile(real):
        parte = integridade.descompactar_tudo(real)
        print("  (mslugx.zip da pasta: %s)" % ("DANIFICADO em %s" % parte if parte else "inteiro"))

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Zip danificado: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
