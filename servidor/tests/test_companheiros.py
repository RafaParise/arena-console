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
        with mock.patch.object(companheiros.subprocess, "Popen", side_effect=ProcessoDeMentira) as popen, \
                mock.patch.object(companheiros, "_pedir_para_fechar", side_effect=lambda p: p.terminate()):
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

    def test_o_dreampotato_que_pergunta_ao_fechar_nao_e_derrubado(self):
        # 10/11/2026: com mudanca no VMU ainda nao gravada, o DreamPotato pergunta antes de fechar. Derrubar perderia o
        # save: o ARENA pede, espera e, se ele continuar aberto, deixa aberto.
        self.instalar()
        with mock.patch.object(companheiros.subprocess, "Popen", side_effect=ProcessoDeMentira), \
                mock.patch.object(companheiros, "_pedir_para_fechar") as pedir:
            companheiros.abrir("dreampotato", self.raiz)
            processo = companheiros._ABERTOS["dreampotato"]
            self.assertEqual(companheiros.fechar_os_que_o_arena_abriu(espera=0.3), [])
            pedir.assert_called_once_with(processo)
            self.assertFalse(processo.morto)


class VmuDoDreamPotato(unittest.TestCase):
    """Memoria compartilhada (10/11/2026): o DreamPotato abre saves\\DreamPotato\\VMU-A1.bin e grava nele. Na primeira vez
    ele nasce do VMU comum do Flycast; depois, nunca e' trocado."""

    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_vmu_dp_")
        self.saves = os.path.join(self.raiz, "saves")
        self.sistema = os.path.join(self.raiz, "system")
        self.flycast = os.path.join(self.sistema, "dc", "vmu_save_A1.bin")

    def tearDown(self):
        limpeza.apagar_pasta(self.raiz)

    def gravar(self, caminho, conteudo):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as saida:
            saida.write(conteudo)

    def test_sem_o_vmu_do_flycast_nao_inventa_um(self):
        self.assertIsNone(companheiros.vmu_do_dreampotato(self.saves, self.sistema))
        self.assertFalse(os.path.exists(os.path.join(self.saves, "DreamPotato")))

    def test_primeira_vez_copia_o_do_flycast(self):
        self.gravar(self.flycast, b"\x07" * companheiros.TAMANHO_DO_VMU)
        vmu = companheiros.vmu_do_dreampotato(self.saves, self.sistema)
        self.assertEqual(vmu, os.path.join(self.saves, "DreamPotato", "VMU-A1.bin"))
        with open(vmu, "rb") as entrada:
            self.assertEqual(entrada.read(), b"\x07" * companheiros.TAMANHO_DO_VMU)

    def test_o_que_ja_existe_nunca_e_trocado(self):
        self.gravar(self.flycast, b"\x07" * companheiros.TAMANHO_DO_VMU)
        meu = os.path.join(self.saves, "DreamPotato", "VMU-A1.bin")
        self.gravar(meu, b"\x01" * companheiros.TAMANHO_DO_VMU)
        self.assertEqual(companheiros.vmu_do_dreampotato(self.saves, self.sistema), meu)
        with open(meu, "rb") as entrada:
            self.assertEqual(entrada.read(1), b"\x01")

    def test_tamanho_errado_nao_vai_para_o_dreampotato(self):
        # O DreamPotato so aceita exatamente 128 KB; um arquivo errado nao e' passado (nem apagado).
        meu = os.path.join(self.saves, "DreamPotato", "VMU-A1.bin")
        self.gravar(meu, b"\x01" * 10)
        self.assertIsNone(companheiros.vmu_do_dreampotato(self.saves, self.sistema))
        self.assertTrue(os.path.isfile(meu))
        self.gravar(self.flycast, b"\x07" * 100)
        limpeza.apagar_pasta(os.path.join(self.saves, "DreamPotato"))
        self.assertIsNone(companheiros.vmu_do_dreampotato(self.saves, self.sistema))

    def test_abrir_passa_o_arquivo_ao_programa(self):
        exe = os.path.join(self.raiz, "emuladores", "DreamPotato", "DreamPotato.exe" if os.name == "nt" else "DreamPotato")
        self.gravar(exe, b"")
        companheiros._ABERTOS.clear()
        try:
            with mock.patch.object(companheiros.subprocess, "Popen", side_effect=ProcessoDeMentira):
                companheiros.abrir_todos(["dreampotato"], self.raiz, {"dreampotato": ["C:\\vmu.bin"]})
                self.assertEqual(companheiros._ABERTOS["dreampotato"].comando, [exe, "C:\\vmu.bin"])
        finally:
            companheiros._ABERTOS.clear()


class EncaixadoAntesDoJogo(unittest.TestCase):
    """10/11/2026: o Flycast pergunta "quem e' voce?" assim que se liga; desencaixado, o DreamPotato responde "reiniciar" e
    a ligacao cai. O ARENA grava o VMU ja encaixado e sem o encaixe automatico, sem mexer no resto dos ajustes."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_dreampotato_")
        self.arquivo = os.path.join(self.pasta, "Data", "configuration.json")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def ler(self):
        import json
        with open(self.arquivo, encoding="utf-8") as entrada:
            return json.load(entrada)

    def test_primeira_vez_cria_o_arquivo(self):
        self.assertTrue(companheiros.preparar_dreampotato(self.pasta))
        self.assertEqual(self.ler(), companheiros.AJUSTES_DO_DREAMPOTATO)
        with open(self.arquivo, "rb") as entrada:
            self.assertFalse(entrada.read(3) == b"\xef\xbb\xbf")          # sem BOM

    def test_guarda_os_outros_ajustes_da_pessoa(self):
        os.makedirs(os.path.dirname(self.arquivo))
        with open(self.arquivo, "w", encoding="utf-8") as saida:
            saida.write('{"Volume": 3, "AutoDockEject": true, "VmuConnectionState": "None", "ColorPaletteName": "Azul"}')
        self.assertTrue(companheiros.preparar_dreampotato(self.pasta))
        lido = self.ler()
        self.assertEqual((lido["Volume"], lido["ColorPaletteName"]), (3, "Azul"))
        self.assertIs(lido["AutoDockEject"], False)
        self.assertEqual((lido["VmuConnectionState"], lido["DreamcastPort"]), ("PrimaryDocked", "A"))
        self.assertEqual([n for n in os.listdir(os.path.dirname(self.arquivo)) if n.endswith(".tmp")], [])

    def test_arquivo_estragado_comeca_do_zero(self):
        os.makedirs(os.path.dirname(self.arquivo))
        with open(self.arquivo, "w", encoding="utf-8") as saida:
            saida.write("{ isto nao e json")
        self.assertTrue(companheiros.preparar_dreampotato(self.pasta))
        self.assertEqual(self.ler(), companheiros.AJUSTES_DO_DREAMPOTATO)

    def test_abrir_prepara_antes(self):
        exe = os.path.join(self.pasta, "emuladores", "DreamPotato", "DreamPotato.exe" if os.name == "nt" else "DreamPotato")
        os.makedirs(os.path.dirname(exe))
        open(exe, "wb").close()
        companheiros._ABERTOS.clear()
        try:
            with mock.patch.object(companheiros.subprocess, "Popen", side_effect=ProcessoDeMentira):
                self.assertTrue(companheiros.abrir("dreampotato", self.pasta))
        finally:
            companheiros._ABERTOS.clear()
        self.arquivo = os.path.join(os.path.dirname(exe), "Data", "configuration.json")
        self.assertEqual(self.ler()["VmuConnectionState"], "PrimaryDocked")


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
