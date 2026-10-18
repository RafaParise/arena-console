# -*- coding: utf-8 -*-
r"""Escreve a libjack.so.0 "vazia" que o RetroArch do Linux pede (item 13).

Por que existe (17/10/2026, item 13 do plano de 15/10): o RetroArch 1.22.2
para Linux (o AppImage oficial do libretro) foi montado ligado a biblioteca
do JACK, um servidor de som de estudio. O Linux so abre o programa se achar
a libjack.so.0 -- e o Ubuntu 24.04 de desktop nao traz o JACK (conferido na
lista de pacotes oficial dele). O ARENA nunca usa o JACK: o som vai pelo
PulseAudio ou pelo ALSA (servidor\plataforma.py). Entao basta uma biblioteca
com o MESMO nome e as MESMAS funcoes, em que cada funcao so devolve 0 ("nao
deu"): o RetroArch abre, tenta o JACK so se alguem pedir, recebe "nao deu" e
segue com o som de verdade.

Esta ferramenta escreve essa biblioteca byte a byte, no formato ELF dos
programas do Linux (x86-64), sem compilador: o resultado e' sempre o mesmo
arquivo, e o codigo abaixo e' todo o "codigo-fonte" dela. Cada funcao tem 3
instrucoes de maquina: xor eax,eax (zera a resposta), ret (volta) e um nop
para completar 4 bytes. Nenhuma funcao escreve na memoria de quem chamou.

O ARENA so poe esta biblioteca ao lado do RetroArch quando o Linux nao tem a
de verdade (plataforma._completar_bibliotecas): quem tem o JACK (ou o do
PipeWire) continua com o dele.

Uso (o preparar_linux.py ja chama):
    servidor\python\python.exe ferramentas\jack_vazio.py [arquivo de saida]
"""
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "retroarch", "bibliotecas-linux", "libjack.so.0")
NOME = b"libjack.so.0"

# As 21 que o RetroArch 1.22.2 pede (nm -D --undefined-only, no conteiner),
# e as vizinhas delas na API do JACK, para um RetroArch mais novo que peca
# uma a mais nao parar de abrir.
FUNCOES = sorted({
    "jack_activate", "jack_client_close", "jack_client_open", "jack_connect", "jack_deactivate",
    "jack_free", "jack_get_buffer_size", "jack_get_ports", "jack_get_sample_rate", "jack_on_shutdown",
    "jack_port_get_buffer", "jack_port_get_latency_range", "jack_port_name", "jack_port_register",
    "jack_ringbuffer_create", "jack_ringbuffer_free", "jack_ringbuffer_get_read_vector",
    "jack_ringbuffer_read_advance", "jack_ringbuffer_write", "jack_ringbuffer_write_space",
    "jack_set_process_callback",
    # vizinhas
    "jack_client_new", "jack_disconnect", "jack_get_client_name", "jack_port_by_name",
    "jack_port_connected", "jack_port_unregister", "jack_port_type", "jack_port_flags",
    "jack_set_xrun_callback", "jack_set_buffer_size_callback", "jack_set_sample_rate_callback",
    "jack_on_info_shutdown", "jack_frame_time", "jack_frames_since_cycle_start", "jack_get_time",
    "jack_ringbuffer_read", "jack_ringbuffer_read_space", "jack_ringbuffer_get_write_vector",
    "jack_ringbuffer_write_advance", "jack_ringbuffer_reset", "jack_ringbuffer_mlock",
    "jack_set_error_function", "jack_set_info_function", "jack_get_version_string",
})
CORPO = b"\x31\xc0\xc3\x90"          # xor eax,eax ; ret ; nop

# Numeros do formato ELF (elf.h).
PT_LOAD, PT_DYNAMIC, PT_GNU_STACK = 1, 2, 0x6474E551
DT_NULL, DT_HASH, DT_STRTAB, DT_SYMTAB, DT_STRSZ, DT_SYMENT, DT_SONAME = 0, 4, 5, 6, 10, 11, 14
SHT_PROGBITS, SHT_STRTAB, SHT_HASH, SHT_DYNAMIC, SHT_DYNSYM = 1, 3, 5, 6, 11
PAGINA = 0x1000


def hash_elf(nome):
    """A soma do formato ELF (a do DT_HASH), que o Linux usa para achar a
    funcao pelo nome."""
    h = 0
    for c in nome:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h


def alinhar(n, a):
    return (n + a - 1) // a * a


def montar():
    nomes = [f.encode("ascii") for f in FUNCOES]
    quantos = len(nomes) + 1                     # o simbolo 0 e' o vazio

    # Os textos (o nome da biblioteca e o de cada funcao), um atras do outro.
    dynstr = b"\0" + NOME + b"\0"
    posicao_do_nome = {}
    for nome in nomes:
        posicao_do_nome[nome] = len(dynstr)
        dynstr += nome + b"\0"

    # A tabela de soma (DT_HASH): cada balde aponta a primeira funcao com
    # aquela soma, e a corrente, a proxima.
    baldes = [0] * quantos
    corrente = [0] * quantos
    for indice, nome in enumerate(nomes, start=1):
        b = hash_elf(nome) % quantos
        corrente[indice] = baldes[b]
        baldes[b] = indice
    tabela_hash = struct.pack("<%dI" % (2 + 2 * quantos), quantos, quantos, *(baldes + corrente))

    # Onde cada pedaco fica (no primeiro trecho, o endereco e' a posicao).
    cabecalhos = 64 + 4 * 56
    pos_hash = cabecalhos
    pos_dynsym = alinhar(pos_hash + len(tabela_hash), 8)
    pos_dynstr = pos_dynsym + 24 * quantos
    pos_texto = alinhar(pos_dynstr + len(dynstr), 16)
    fim_do_texto = pos_texto + len(CORPO) * len(nomes)
    pos_dynamic = alinhar(fim_do_texto, 16)
    end_dynamic = pos_dynamic + PAGINA           # outra pagina: esta pode ser gravada
    dynamic = b"".join(struct.pack("<qQ", tag, valor) for tag, valor in (
        (DT_HASH, pos_hash), (DT_STRTAB, pos_dynstr), (DT_SYMTAB, pos_dynsym), (DT_STRSZ, len(dynstr)),
        (DT_SYMENT, 24), (DT_SONAME, 1), (DT_NULL, 0)))

    # Os simbolos: cada funcao, global, no trecho de codigo (secao 4).
    dynsym = b"\0" * 24
    for i, nome in enumerate(nomes):
        dynsym += struct.pack("<IBBHQQ", posicao_do_nome[nome], 0x12, 0, 4, pos_texto + i * len(CORPO),
                              len(CORPO))
    texto = CORPO * len(nomes)

    # As secoes (so para as ferramentas, como o nm e o readelf, lerem; o
    # Linux, para abrir, usa os trechos dos cabecalhos de programa).
    shstrtab = b"\0.hash\0.dynsym\0.dynstr\0.text\0.dynamic\0.shstrtab\0"

    def nome_secao(nome):
        return shstrtab.index(b"\0" + nome + b"\0") + 1

    pos_shstrtab = pos_dynamic + len(dynamic)
    pos_secoes = alinhar(pos_shstrtab + len(shstrtab), 8)

    def secao(nome, tipo, flags, endereco, posicao, tamanho, link=0, info=0, alinhamento=1, entrada=0):
        return struct.pack("<IIQQQQIIQQ", nome_secao(nome) if nome else 0, tipo, flags, endereco, posicao,
                           tamanho, link, info, alinhamento, entrada)
    A, X, W = 0x2, 0x4, 0x1
    secoes = b"".join([
        b"\0" * 64,
        secao(b".hash", SHT_HASH, A, pos_hash, pos_hash, len(tabela_hash), link=2, alinhamento=8, entrada=4),
        secao(b".dynsym", SHT_DYNSYM, A, pos_dynsym, pos_dynsym, len(dynsym), link=3, info=1, alinhamento=8,
              entrada=24),
        secao(b".dynstr", SHT_STRTAB, A, pos_dynstr, pos_dynstr, len(dynstr)),
        secao(b".text", SHT_PROGBITS, A | X, pos_texto, pos_texto, len(texto), alinhamento=16),
        secao(b".dynamic", SHT_DYNAMIC, A | W, end_dynamic, pos_dynamic, len(dynamic), link=3, alinhamento=8,
              entrada=16),
        secao(b".shstrtab", SHT_STRTAB, 0, 0, pos_shstrtab, len(shstrtab)),
    ])

    # Os trechos que o Linux carrega: o codigo (ler e executar), o dynamic
    # (ler e gravar: o Linux ajusta os enderecos dele), e a pilha sem
    # execucao (GNU_STACK: sem ela, o Linux novo recusa a biblioteca).
    def trecho(tipo, flags, posicao, endereco, tamanho, alinhamento):
        return struct.pack("<IIQQQQQQ", tipo, flags, posicao, endereco, endereco, tamanho, tamanho, alinhamento)
    programas = b"".join([
        trecho(PT_LOAD, 5, 0, 0, fim_do_texto, PAGINA),
        trecho(PT_LOAD, 6, pos_dynamic, end_dynamic, len(dynamic), PAGINA),
        trecho(PT_DYNAMIC, 6, pos_dynamic, end_dynamic, len(dynamic), 8),
        trecho(PT_GNU_STACK, 6, 0, 0, 0, 16),
    ])

    identificacao = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\0" * 8   # 64 bits, little-endian, versao 1, System V
    cabecalho = identificacao + struct.pack("<HHIQQQIHHHHHH", 3, 62, 1, 0, 64, pos_secoes, 0, 64, 56, 4, 64, 7, 6)

    arquivo = bytearray(pos_secoes + len(secoes))
    for posicao, pedaco in ((0, cabecalho), (64, programas), (pos_hash, tabela_hash), (pos_dynsym, dynsym),
                            (pos_dynstr, dynstr), (pos_texto, texto), (pos_dynamic, dynamic),
                            (pos_shstrtab, shstrtab), (pos_secoes, secoes)):
        arquivo[posicao:posicao + len(pedaco)] = pedaco
    return bytes(arquivo)


def escrever(destino=SAIDA):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    dados = montar()
    with open(destino, "wb") as arquivo:
        arquivo.write(dados)
    return destino, len(dados)


if __name__ == "__main__":
    caminho, tamanho = escrever(sys.argv[1] if len(sys.argv) > 1 else SAIDA)
    print("%s (%d bytes, %d funcoes)" % (caminho, tamanho, len(FUNCOES)))
