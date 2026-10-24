# -*- coding: utf-8 -*-
"""Programas companheiros (o DreamPotato, VMU de verdade do Dreamcast): abrem junto com o jogo e fecham com ele, so o que o
ARENA abriu, so se estiverem em emuladores\\<pasta>."""
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import acessorios  # noqa: E402
import companheiros  # noqa: E402
import limpeza  # noqa: E402


class ProcessoDeMentira:
    def __init__(self, comando, **_):
        self.comando = comando
        self.encerrado = False
        self.morto = False

    def poll(self):
        return 0 if self.encerrado else None

    def terminate(self):
        self.encerrado = True

    def kill(self):
        self.morto = self.encerrado = True

    def wait(self, _tempo=None):
        return 0


class AbrirEFechar(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_companheiros_")
        self.exe = os.path.join(self.raiz, "emuladores", "DreamPotato", "DreamPotato.exe" if os.name == "nt" else "DreamPotato")
        companheiros._ABERTOS.clear()

    def tearDown(self):
        companheiros._ABERTOS.clear()
        limpeza.apagar_pasta(self.raiz)

    def instalar(self):
        os.makedirs(os.path.dirname(self.exe))
        open(self.exe, "wb").close()

    def test_sem_a_pasta_nada_acontece(self):
        self.assertIsNone(companheiros.achar("dreampotato", self.raiz))
        self.assertFalse(companheiros.abrir("dreampotato", self.raiz))
        self.assertEqual(companheiros.fechar_os_que_o_arena_abriu(), [])

    def test_id_que_nao_existe_nao_abre_nada(self):
        self.assertIsNone(companheiros.achar("../../windows/cmd", self.raiz))
        self.assertFalse(companheiros.abrir("programa_que_nao_existe", self.raiz))

    def test_abre_uma_vez_e_fecha_o_que_abriu(self):
        self.instalar()
        with mock.patch.object(companheiros.subprocess, "Popen", side_effect=ProcessoDeMentira) as popen:
            self.assertEqual(companheiros.abrir_todos(["dreampotato"], self.raiz), ["dreampotato"])
            self.assertEqual(companheiros.abrir_todos(["dreampotato"], self.raiz), [])      # ja aberto: nao abre outro
            self.assertEqual(popen.call_count, 1)
            processo = companheiros._ABERTOS["dreampotato"]
            self.assertEqual(processo.comando, [self.exe])
            self.assertEqual(companheiros.fechar_os_que_o_arena_abriu(), ["dreampotato"])
            self.assertTrue(processo.encerrado)
            self.assertFalse(processo.morto)                                                # saiu ao ser pedido: sem forca
            self.assertEqual(companheiros.fechar_os_que_o_arena_abriu(), [])

    def test_falha_ao_abrir_nao_derruba_o_jogo(self):
        self.instalar()
        with mock.patch.object(companheiros.subprocess, "Popen", side_effect=OSError("sem permissao")):
            self.assertFalse(companheiros.abrir("dreampotato", self.raiz))


class QuemChamaQuem(unittest.TestCase):
    def test_o_encaixe_dreampotato_chama_o_programa(self):
        estado = {"dc_encaixes_1": {"encaixe1": "DreamPotato"}}
        self.assertEqual(acessorios.companheiros(estado, "dreamcast"), ["dreampotato"])

    def test_o_padrao_e_os_outros_valores_nao_chamam_ninguem(self):
        self.assertEqual(acessorios.companheiros({}, "dreamcast"), [])
        self.assertEqual(acessorios.companheiros({"dc_encaixes_1": {"encaixe1": "VMU"}}, "dreamcast"), [])
        self.assertEqual(acessorios.companheiros({"dc_encaixes_1": {"encaixe1": "DreamPotato"}}, "n64"), [])

    def test_a_memoria_compartilhada_liga_a_opcao_do_flycast(self):
        estado = {"dc_vmu_memoria_compartilhada": {"compartilhar": True}, "dc_encaixes_1": {"encaixe1": "DreamPotato"}}
        opcoes = acessorios.opcoes_do_nucleo(estado, "dreamcast", "flycast")
        self.assertEqual(opcoes["reicast_linked_vmu_storage"], "enabled")
        self.assertEqual(opcoes["reicast_device_port1_slot1"], "DreamPotato")


if __name__ == "__main__":
    unittest.main()
