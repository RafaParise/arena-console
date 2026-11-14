# -*- coding: utf-8 -*-
"""Linux ARM64 (14/11/2026): TV Box com Armbian, Raspberry Pi 4 e 5 e Chromebook ARM com Linux.

O RetroArch, os nucleos e o Python do ARM ficam em pastas proprias (retroarch/linux-aarch64,
retroarch/cores-aarch64, servidor/python-linux-aarch64), o mesmo pen drive serve aos dois processadores, e o
programa x86-64 do mesmo pen drive (o AppImage do PCSX2, por exemplo) conta como ausente no ARM, em vez de abrir e
falhar. Aqui o ARM e' simulado (servidor/plataforma.py, ARM64 = True); o teste no aparelho fica no
docs/PLANO-DE-ACAO-RUST.md."""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import graficos  # noqa: E402
import plataforma  # noqa: E402

PASTA_TESTES = os.path.join(RAIZ, "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


def cabecalho_elf(numero):
    """Os 20 primeiros bytes de um programa do Linux de 64 bits, ordem little-endian, processador 'numero'."""
    return b"\x7fELF" + bytes([2, 1, 1, 0]) + bytes(8) + (2).to_bytes(2, "little") + numero.to_bytes(2, "little")


def como_arm64(ligado=True):
    """O ARENA como se rodasse num Linux (ARM64 ou x86-64)."""
    return mock.patch.multiple(plataforma, LINUX=True, ANDROID=False, WINDOWS=False, ARM64=ligado)


class Processador(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_arm64_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def arquivo(self, nome, conteudo):
        caminho = os.path.join(self.pasta, nome)
        with open(caminho, "wb") as saida:
            saida.write(conteudo + bytes(64))
        return caminho

    def test_le_o_processador_do_cabecalho(self):
        self.assertEqual(plataforma.processador_do_programa(self.arquivo("x86", cabecalho_elf(62))), "x86_64")
        self.assertEqual(plataforma.processador_do_programa(self.arquivo("arm", cabecalho_elf(183))), "aarch64")
        self.assertEqual(plataforma.processador_do_programa(self.arquivo("risc", cabecalho_elf(243))), "243")
        self.assertIsNone(plataforma.processador_do_programa(self.arquivo("texto", b"#!/bin/sh\n")))
        self.assertIsNone(plataforma.processador_do_programa(os.path.join(self.pasta, "nao-existe")))

    def test_programa_de_outro_processador_nao_roda(self):
        x86 = self.arquivo("x86", cabecalho_elf(62))
        arm = self.arquivo("arm", cabecalho_elf(183))
        script = self.arquivo("script", b"#!/bin/sh\n")
        with como_arm64(True):
            self.assertFalse(plataforma.roda_neste_processador(x86))
            self.assertTrue(plataforma.roda_neste_processador(arm))
            self.assertTrue(plataforma.roda_neste_processador(script))
        with como_arm64(False):
            self.assertTrue(plataforma.roda_neste_processador(x86))
            self.assertFalse(plataforma.roda_neste_processador(arm))
        with mock.patch.multiple(plataforma, LINUX=False, WINDOWS=True, ANDROID=False, ARM64=False):
            self.assertTrue(plataforma.roda_neste_processador(arm))     # fora do Linux, nao julga


class Pastas(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_arm64_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def test_nucleos_e_python_em_pastas_proprias(self):
        with como_arm64(True):
            self.assertEqual(plataforma.pasta_dos_nucleos("ra"), os.path.join("ra", "cores-aarch64"))
            self.assertEqual(plataforma.python_que_veio_junto("srv"),
                             os.path.join("srv", "python-linux-aarch64", "bin", "python3.13"))
        with como_arm64(False):
            self.assertEqual(plataforma.pasta_dos_nucleos("ra"), os.path.join("ra", "cores"))
            self.assertEqual(plataforma.python_que_veio_junto("srv"),
                             os.path.join("srv", "python-linux", "bin", "python3.13"))

    def test_retroarch_do_pacote_ou_do_sistema(self):
        do_pacote = os.path.join(self.pasta, "linux-aarch64", "retroarch")
        with como_arm64(True):
            with mock.patch.object(plataforma.shutil, "which", return_value="/usr/bin/retroarch"):
                self.assertEqual(plataforma.executavel_do_retroarch(self.pasta), "/usr/bin/retroarch")
            with mock.patch.object(plataforma.shutil, "which", return_value=None):
                self.assertEqual(plataforma.executavel_do_retroarch(self.pasta), do_pacote)
            os.makedirs(os.path.dirname(do_pacote))
            with open(do_pacote, "wb") as saida:
                saida.write(cabecalho_elf(183))
            with mock.patch.object(plataforma.shutil, "which", return_value="/usr/bin/retroarch"):
                self.assertEqual(plataforma.executavel_do_retroarch(self.pasta), do_pacote)   # o do pacote vence

    def test_retroarch_solto_vai_pelo_cache(self):
        with como_arm64(True), mock.patch.object(plataforma, "programa_que_roda", return_value="/cache/ra") as pr:
            self.assertEqual(plataforma.retroarch_que_roda("/pen/retroarch/linux-aarch64/retroarch"), "/cache/ra")
            pr.assert_called_once_with("/pen/retroarch/linux-aarch64/retroarch", "retroarch-aarch64")


class EmuladorDeFora(unittest.TestCase):
    """O AppImage x86-64 do PCSX2 no mesmo pen drive: no ARM conta como ausente; no PC, como sempre."""
    PLATAFORMA = {"id": "ps2", "externo": {"nome": "PCSX2", "pasta": "PCSX2", "executaveis": ["pcsx2-qt.exe"],
                                           "executaveis_linux": ["pcsx2*.appimage"]}}

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_arm64_")
        os.makedirs(os.path.join(self.pasta, "PCSX2"))
        self.programa = os.path.join(self.pasta, "PCSX2", "pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def achar(self, numero, arm):
        with open(self.programa, "wb") as saida:
            saida.write(cabecalho_elf(numero) + bytes(64))
        with como_arm64(arm), mock.patch.object(graficos, "NO_WINDOWS", False), \
                mock.patch.object(graficos, "PASTA_EMULADORES", self.pasta):
            return graficos.achar_externo_detalhado(self.PLATAFORMA)[0]

    def test_appimage_x86_no_arm_fica_de_fora(self):
        self.assertIsNone(self.achar(62, arm=True))
        self.assertEqual(self.achar(183, arm=True), self.programa)   # um AppImage do ARM serve
        self.assertEqual(self.achar(62, arm=False), self.programa)   # no PC, como sempre


class Arquivos(unittest.TestCase):
    def ler(self, *partes):
        with open(os.path.join(RAIZ, *partes), encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_arena_sh_aceita_arm64_com_retroarch(self):
        texto = self.ler("ARENA.sh")
        self.assertIn("aarch64|arm64)", texto)
        self.assertIn("retroarch/linux-aarch64/retroarch", texto)
        self.assertIn("command -v retroarch", texto)          # o do sistema tambem serve
        self.assertIn("sudo apt install retroarch", texto)    # e o erro diz o que fazer
        self.assertIn("python-linux-aarch64", self.ler("servidor", "achar_python.sh"))

    def test_lista_do_nightly_conferida(self):
        caminho = os.path.join(RAIZ, "ferramentas", "linux_aarch64.json")
        if not os.path.isfile(caminho):
            self.skipTest("a lista do nightly ARM64 ainda nao foi registrada")
        with open(caminho, encoding="utf-8") as arquivo:
            lista = json.load(arquivo)
        self.assertRegex(lista["conferido"], r"^\d{4}-\d{2}-\d{2}$")
        itens = [lista["retroarch"]] + lista["nucleos"]
        for item in itens:
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(item["tamanho"], 1000)
            self.assertTrue(item["endereco"].startswith("https://buildbot.libretro.com/nightly/linux/aarch64/"))
        sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
        import preparar_linux
        usados = set(preparar_linux.nucleos_usados())
        listados = {n["nome"] for n in lista["nucleos"]} | set(lista["sem_versao_arm64"])
        self.assertEqual(listados, usados)       # nenhum nucleo esquecido nem a mais
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", preparar_linux.PYTHON_ARM64["sha256"]))
        self.assertIn("aarch64-unknown-linux-gnu", preparar_linux.PYTHON_ARM64["endereco"])


if __name__ == "__main__":
    unittest.main()
