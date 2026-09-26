# -*- coding: utf-8 -*-
r"""Confere se o neogeo.zip tem os arquivos que o FBNeo exige, com o CRC certo.

O registro do RetroArch disse (auditoria 2): "ROM ... sm1.sm1 and CRC
0x94416d67 is required". Os outros tres que faltavam antes: sp-s3.sp1
(91b64be3), sfix.sfix (c2ea0cfd) e 000-lo.lo (5a86cff2).

Uso: servidor\python\python.exe ferramentas\conferir_bios_neogeo.py
"""
import os
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXIGIDOS = {"sm1.sm1": 0x94416D67, "sp-s3.sp1": 0x91B64BE3,
            "sfix.sfix": 0xC2EA0CFD, "000-lo.lo": 0x5A86CFF2}
LUGARES = [os.path.join(RAIZ, "retroarch", "system", "neogeo.zip"),
           os.path.join(RAIZ, "jogos", "pessoais", "Neo Geo", "neogeo.zip")]


def main():
    for caminho in LUGARES:
        print("\n==", os.path.relpath(caminho, RAIZ))
        if not os.path.isfile(caminho):
            print("   nao existe")
            continue
        try:
            with zipfile.ZipFile(caminho) as pacote:
                por_crc = {i.CRC: i.filename for i in pacote.infolist()}
                por_nome = {i.filename.lower(): i.CRC for i in pacote.infolist()}
                print("   %d arquivos dentro" % len(por_nome))
        except zipfile.BadZipFile:
            print("   zip quebrado")
            continue
        for nome, crc in EXIGIDOS.items():
            if por_nome.get(nome) == crc:
                situacao = "OK (nome e CRC certos)"
            elif crc in por_crc:
                situacao = "conteudo certo, mas com o nome '%s'" % por_crc[crc]
            elif nome in por_nome:
                situacao = "nome certo, CRC ERRADO (%08x)" % por_nome[nome]
            else:
                situacao = "FALTA"
            print("   %-10s %s" % (nome, situacao))


if __name__ == "__main__":
    main()
