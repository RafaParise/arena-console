# -*- coding: utf-8 -*-
"""Os 60 quadros de verdade do PS2 (servidor\\quadros_ps2.py): serial, CRC, patches e o gamesettings."""
import json
import os
import struct
import sys
import tempfile
import unittest
import zipfile

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import quadros_ps2  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

PNACH = "gametitle=Teste\n\n[Widescreen 16:9]\npatch=1,EE,0,word,0\n\n[60 FPS]\npatch=1,EE,1,word,1\n"


def registro_iso(nome, setor, tamanho):
    """Um registro de diretorio do ISO 9660 (so o que o identificador le)."""
    nome = nome.encode("ascii")
    corpo = bytearray(33 + len(nome) + (0 if len(nome) % 2 else 1))
    corpo[0] = len(corpo)
    corpo[2:6] = struct.pack("<I", setor)
    corpo[10:14] = struct.pack("<I", tamanho)
    corpo[32] = len(nome)
    corpo[33:33 + len(nome)] = nome
    return bytes(corpo)


def montar_iso(caminho, elf):
    """Um ISO minimo: SYSTEM.CNF e o ELF na raiz, como num disco de PS2."""
    cnf = b"BOOT2 = cdrom0:\\SLUS_123.45;1\r\nVER = 1.00\r\n"
    raiz = registro_iso("\x00", 18, 2048) + registro_iso("SYSTEM.CNF;1", 19, len(cnf)) + \
        registro_iso("SLUS_123.45;1", 20, len(elf))
    descritor = bytearray(2048)
    descritor[0] = 1
    descritor[1:6] = b"CD001"
    descritor[156:190] = registro_iso("\x00", 18, 2048)[:34]
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x00" * 2048 * 16 + bytes(descritor) + b"\x00" * 2048)
        arquivo.write(raiz.ljust(2048, b"\x00"))
        arquivo.write(cnf.ljust(2048, b"\x00"))
        arquivo.write(elf.ljust(2048 * ((len(elf) + 2047) // 2048), b"\x00"))


class SerialECrc(unittest.TestCase):
    def test_crc_e_o_ou_exclusivo_das_palavras(self):
        dados = struct.pack("<3I", 0x11111111, 0x22222222, 0x0F0F0F0F) + b"\x01"
        self.assertEqual(quadros_ps2.crc_do_elf(dados), 0x11111111 ^ 0x22222222 ^ 0x0F0F0F0F)

    def test_serial(self):
        self.assertEqual(quadros_ps2.serial_do_elf("SLUS_213.76;1"), "SLUS-21376")
        self.assertEqual(quadros_ps2.serial_do_elf("qualquer.elf"), "")

    def test_registro_do_pcsx2(self):
        texto = ("[    2,8697]   Serial: SLUS-21376\n[    2,8697]   CRC: 5C891FF1\n"
                 "[    4,2321] ELF Loading: , Game CRC = 00000000\n")
        self.assertEqual(quadros_ps2.ler_do_registro(texto), ("SLUS-21376", "5C891FF1"))
        self.assertIsNone(quadros_ps2.ler_do_registro("nada aqui"))


class Patches(unittest.TestCase):
    def test_escolhe_o_de_60(self):
        self.assertEqual(quadros_ps2.patch_de_60(["Widescreen 16:9", "60 FPS"]), "60 FPS")
        self.assertEqual(quadros_ps2.patch_de_60(["60 fps & No Interlacing", "60 fps"]), "60 fps")
        self.assertEqual(quadros_ps2.patch_de_60(["50/60 FPS"]), "50/60 FPS")
        self.assertEqual(quadros_ps2.patch_de_60(["60 fps & No Interlacing"]), "60 fps & No Interlacing")
        self.assertEqual(quadros_ps2.patch_de_60(["Widescreen 16:9", "No-Interlacing"]), "")

    def test_decidir(self):
        self.assertFalse(quadros_ps2.decidir("desligado", 5, 5, 0)[0])
        self.assertTrue(quadros_ps2.decidir("sempre", 1, 1, 3)[0])
        self.assertTrue(quadros_ps2.decidir("automatico", 4, 4, 0)[0])
        # O Celeron N5100: nota 2 ou 3.
        self.assertFalse(quadros_ps2.decidir("automatico", 3, 3, 0)[0])
        # O PS2 ficou no limite antes.
        self.assertFalse(quadros_ps2.decidir("automatico", 5, 5, 1)[0])


class Aplicar(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps2_60_")
        self.pcsx2 = os.path.join(self.pasta, "PCSX2")
        self.dados = os.path.join(self.pasta, "dados")
        os.makedirs(os.path.join(self.pcsx2, "resources"))
        with zipfile.ZipFile(os.path.join(self.pcsx2, "resources", "patches.zip"), "w") as pacote:
            pacote.writestr("SLUS-12345_0000ABCD.pnach", PNACH)
        self.ini = os.path.join(self.pcsx2, "gamesettings", "SLUS-12345_0000ABCD.ini")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _ler(self):
        with open(self.ini, encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_liga_e_tira_criando_o_arquivo(self):
        self.assertEqual(quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", True, self.dados), "60 FPS")
        self.assertIn("[Patches]\nEnable = 60 FPS\n", self._ler())
        # De novo: nada repete.
        quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", True, self.dados)
        self.assertEqual(self._ler().count("Enable = 60 FPS"), 1)
        self.assertEqual(quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", False, self.dados), "")
        self.assertFalse(os.path.exists(self.ini))

    def test_o_ajuste_da_pessoa_fica(self):
        os.makedirs(os.path.dirname(self.ini))
        with open(self.ini, "w", encoding="utf-8") as arquivo:
            arquivo.write("[EmuCore/GS]\nupscale_multiplier = 3\n\n[Patches]\nEnable = Widescreen 16:9\n")
        quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", True, self.dados)
        texto = self._ler()
        self.assertIn("Enable = 60 FPS", texto)
        self.assertIn("Enable = Widescreen 16:9", texto)
        quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", False, self.dados)
        texto = self._ler()
        self.assertNotIn("60 FPS", texto)
        self.assertIn("Enable = Widescreen 16:9", texto)
        self.assertIn("upscale_multiplier = 3", texto)

    def test_nao_tira_o_que_a_pessoa_ligou(self):
        os.makedirs(os.path.dirname(self.ini))
        with open(self.ini, "w", encoding="utf-8") as arquivo:
            arquivo.write("[Patches]\nEnable = 60 FPS\n")
        quadros_ps2.aplicar(self.pcsx2, "SLUS-12345", "0000ABCD", False, self.dados)
        self.assertIn("Enable = 60 FPS", self._ler())

    def test_jogo_sem_patch(self):
        self.assertEqual(quadros_ps2.aplicar(self.pcsx2, "SLUS-99999", "00000001", True, self.dados), "")
        self.assertFalse(os.path.isdir(os.path.join(self.pcsx2, "gamesettings")))


class Identificar(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ps2_iso_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_le_o_iso(self):
        elf = struct.pack("<4I", 0x7F454C46, 1, 2, 3)
        iso = os.path.join(self.pasta, "jogo.iso")
        montar_iso(iso, elf)
        self.assertEqual(quadros_ps2.identificar(iso, self.pasta),
                         ("SLUS-12345", "%08X" % (0x7F454C46 ^ 1 ^ 2 ^ 3)))

    def test_o_iso_lido_uma_vez_fica_guardado(self):
        # Revisao de 11/11/2026: o CRC do ELF e' lento na maquina fraca; o ARENA guarda e, da segunda vez, nem abre
        # o ISO (aqui, o arquivo some e o jogo continua identificado).
        iso = os.path.join(self.pasta, "jogo.iso")
        montar_iso(iso, struct.pack("<2I", 7, 9))
        primeiro = quadros_ps2.identificar(iso, self.pasta)
        self.assertEqual(primeiro, ("SLUS-12345", "%08X" % (7 ^ 9)))
        tamanho = os.path.getsize(iso)
        os.remove(iso)
        with open(iso, "wb") as arquivo:
            arquivo.write(b"\x00" * tamanho)          # mesmo nome e tamanho, conteudo nenhum
        self.assertEqual(quadros_ps2.identificar(iso, self.pasta), primeiro)

    def test_lista_de_patches_na_pasta_do_programa(self):
        # Linux: a configuracao numa pasta, o programa (AppImage desmontado) em outra.
        config = os.path.join(self.pasta, "config")
        programa = os.path.join(self.pasta, "squashfs-root")
        os.makedirs(config)
        os.makedirs(os.path.join(programa, "usr", "share", "PCSX2", "resources"))
        self.assertFalse(quadros_ps2.tem_lista_de_patches(config))
        with zipfile.ZipFile(os.path.join(programa, "usr", "share", "PCSX2", "resources", "patches.zip"), "w") as pacote:
            pacote.writestr("SLUS-12345_0000ABCD.pnach", PNACH)
        self.assertFalse(quadros_ps2.tem_lista_de_patches(config))
        self.assertTrue(quadros_ps2.tem_lista_de_patches(config, [programa]))
        self.assertEqual(quadros_ps2.patches_do_jogo(config, "SLUS-12345", "0000ABCD", [programa]),
                         ["Widescreen 16:9", "60 FPS"])

    def test_aprende_o_disco_comprimido(self):
        chd = os.path.join(self.pasta, "jogo.chd")
        with open(chd, "wb") as arquivo:
            arquivo.write(b"MComprHD" + b"\x00" * 100)
        self.assertIsNone(quadros_ps2.identificar(chd, self.pasta))
        os.makedirs(os.path.join(self.pasta, "PCSX2", "logs"))
        with open(os.path.join(self.pasta, "PCSX2", "logs", "emulog.txt"), "w", encoding="utf-8") as arquivo:
            arquivo.write("[    1,0]   Serial: SLES-52325\n[    1,0]   CRC: 75d86958\n")
        quadros_ps2.aprender_do_registro(os.path.join(self.pasta, "PCSX2"), chd, self.pasta)
        self.assertEqual(quadros_ps2.identificar(chd, self.pasta), ("SLES-52325", "75D86958"))
        with open(os.path.join(self.pasta, quadros_ps2.ARQUIVO_DOS_JOGOS), encoding="utf-8") as arquivo:
            guardado = json.load(arquivo)
        # Sem caminho absoluto: o pen drive troca de letra.
        self.assertTrue(all(":" not in chave and "\\" not in chave for chave in guardado))


if __name__ == "__main__":
    unittest.main()
