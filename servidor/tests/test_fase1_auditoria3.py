# -*- coding: utf-8 -*-
"""Auditoria 3, Fase 1: as correcoes C1, C2, C4 e C5 (docs\\RELATORIO-QUALIDADE.md).

  C1 -- abrir o ARENA nao faz copia de seguranca (so a volta de verdade da
        internet faz);
  C2 -- importar o pacote de progresso pelo temporario (nada de save cortado);
  C4 -- opcao avancada acima da nota desta maquina nao vale (o pen drive
        vindo de um PC forte);
  C5 -- descoberta de colegas: pacote torto nao levanta erro, e a lista tem
        teto (por endereco e no total) e poda.
Tudo em pasta temporaria; o arena.py e' importado, nao sobe servidor.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import arena  # noqa: E402


class _EncerraDepois:
    """Imita o VIGIA["encerrar"]: deixa o laco dar 'voltas' voltas e para."""

    def __init__(self, voltas):
        self.voltas = voltas

    def wait(self, _segundos=None):
        self.voltas -= 1
        return self.voltas < 0

    def is_set(self):
        return self.voltas < 0


class TestCopiaAoAbrir(unittest.TestCase):
    """C1: a primeira checagem do vigia nao conta como "a internet voltou"."""

    def setUp(self):
        self.guardado = dict(arena.VIGIA)
        self.copias = []

    def tearDown(self):
        arena.VIGIA.clear()
        arena.VIGIA.update(self.guardado)

    def rodar_uma_volta(self, tem_internet):
        arena.VIGIA["encerrar"] = _EncerraDepois(1)
        with mock.patch.object(arena, "quem_esta_online", return_value=([], [])), \
                mock.patch.object(arena, "internet_disponivel", return_value=tem_internet), \
                mock.patch.object(arena, "enderecos_locais", return_value=[]), \
                mock.patch.object(arena, "contar_pendentes", return_value=0), \
                mock.patch.object(arena, "fazer_backup", side_effect=lambda: self.copias.append(1) or "x"):
            arena.rodar_vigia()

    def test_o_vigia_comeca_sem_saber(self):
        self.assertIsNone(self.guardado["internet_estava_fora"])

    def test_abrir_com_internet_nao_faz_copia(self):
        arena.VIGIA["internet_estava_fora"] = self.guardado["internet_estava_fora"]
        arena.VIGIA["ultimo_backup"] = 0.0
        self.rodar_uma_volta(tem_internet=True)
        self.assertEqual(self.copias, [])

    def test_a_internet_que_voltou_de_verdade_ainda_faz_copia(self):
        arena.VIGIA["internet_estava_fora"] = True          # ficou fora numa volta antes
        arena.VIGIA["ultimo_backup"] = 0.0
        self.rodar_uma_volta(tem_internet=True)
        self.assertEqual(self.copias, [1])


class TestImportarPeloTemporario(unittest.TestCase):
    """C2: o save importado so aparece inteiro."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="arena_importar_teste_")
        self.backup = os.path.join(self.dir, "backup")
        self.retroarch = os.path.join(self.dir, "retroarch")
        os.makedirs(self.backup)
        self.troca = mock.patch.multiple(
            arena, PASTA_BACKUP=self.backup, PASTA_RETROARCH=self.retroarch,
            PASTA_SAVES=os.path.join(self.retroarch, "saves"), PASTA_STATES=os.path.join(self.retroarch, "states"),
            PASTA_CHEATS=os.path.join(self.retroarch, "cheats"), PASTA_REMAPS=os.path.join(self.retroarch, "remaps"),
            PASTA_CONTROLES=os.path.join(self.retroarch, "controles"),
            PASTA_SISTEMA=os.path.join(self.retroarch, "system"))
        self.troca.start()
        with zipfile.ZipFile(os.path.join(self.backup, "meu-progresso.zip"), "w") as z:
            z.writestr("saves/Snes9x/Jogo.srm", b"S" * 8192)

    def tearDown(self):
        self.troca.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def sobras(self):
        return [n for _a, _s, nomes in os.walk(self.retroarch) for n in nomes if n.endswith(".importando")]

    def test_importa_inteiro_e_sem_sobra(self):
        resultado, erro = arena.importar_saves("meu-progresso.zip")
        self.assertIsNone(erro)
        self.assertEqual(resultado["trazidos"], 1)
        with open(os.path.join(self.retroarch, "saves", "Snes9x", "Jogo.srm"), "rb") as f:
            self.assertEqual(f.read(), b"S" * 8192)
        self.assertEqual(self.sobras(), [])

    def test_caiu_no_meio_nao_deixa_save_cortado(self):
        def corta(origem, saida, *_resto):
            saida.write(origem.read(100))
            raise OSError("o pen drive saiu")
        with mock.patch.object(shutil, "copyfileobj", side_effect=corta):
            resultado, erro = arena.importar_saves("meu-progresso.zip")
        self.assertIsNone(resultado)
        self.assertTrue(erro)
        self.assertFalse(os.path.exists(os.path.join(self.retroarch, "saves", "Snes9x", "Jogo.srm")))
        self.assertEqual(self.sobras(), [])
        # E a proxima importacao traz o save (nao o pula por "ja existir").
        resultado, erro = arena.importar_saves("meu-progresso.zip")
        self.assertEqual((resultado or {}).get("trazidos"), 1, erro)


class TestAvancadoDestaMaquina(unittest.TestCase):
    """C4: a configuracao vinda de um PC forte nao liga o pesado no fraco."""

    def setUp(self):
        self.nota = arena.CAPACIDADE["nota"]

    def tearDown(self):
        arena.CAPACIDADE["nota"] = self.nota

    def test_maquina_fraca_tira_o_pesado_e_mantem_o_resto(self):
        arena.CAPACIDADE["nota"] = 3
        config = dict(arena.config_padrao())
        config["avancado"] = dict(config["avancado"], run_ahead_enabled="true", audio_volume="-5")
        desta = arena.avancado_desta_maquina(config)
        self.assertNotIn("run_ahead_enabled", desta)
        self.assertEqual(desta["audio_volume"], "-5")
        self.assertEqual(arena.opcoes_efetivas(config)["run_ahead_enabled"], "false")

    def test_fora_da_nota_vai_o_padrao_desligado(self):
        # O que o perfil de imagem nao escreve vai com o padrao do ARENA:
        # so tirar deixaria valer o que o RetroArch guardou no PC forte.
        arena.CAPACIDADE["nota"] = 4
        config = dict(arena.config_padrao())
        config["avancado"] = dict(config["avancado"], run_ahead_secondary_instance="true",
                                  run_ahead_frames="3")
        desta = arena.avancado_desta_maquina(config)
        self.assertEqual(desta["run_ahead_secondary_instance"], "false")   # nota minima 5
        self.assertEqual(desta["run_ahead_frames"], "3")                    # nota minima 4: vale
        efetivas = arena.opcoes_efetivas(config)
        self.assertEqual(efetivas["run_ahead_secondary_instance"], "false")

    def test_maquina_forte_respeita_a_escolha(self):
        arena.CAPACIDADE["nota"] = 5
        config = dict(arena.config_padrao())
        config["avancado"] = dict(config["avancado"], run_ahead_enabled="true")
        self.assertEqual(arena.avancado_desta_maquina(config)["run_ahead_enabled"], "true")


class TestReceberGrito(unittest.TestCase):
    """C5: o que chega na porta da descoberta e' conferido, e a lista tem teto."""

    MEUS = {"127.0.0.1", "192.168.0.10"}

    def setUp(self):
        with arena.TRAVA_VIZINHOS:
            self.guardados = dict(arena.VIZINHOS)
            arena.VIZINHOS.clear()
        arena._PODA_DOS_VIZINHOS["ultima"] = 0.0

    def tearDown(self):
        with arena.TRAVA_VIZINHOS:
            arena.VIZINHOS.clear()
            arena.VIZINHOS.update(self.guardados)

    def grito(self, dados, ip="192.168.0.50", agora=1000.0):
        corpo = dados if isinstance(dados, bytes) else json.dumps(dados).encode("utf-8")
        return arena.receber_grito(arena.MARCA_DESCOBERTA + corpo, (ip, 55436), meus=self.MEUS, agora=agora)

    def test_pacotes_tortos_sao_ignorados_sem_erro(self):
        for torto in (b"[1, 2]", b'"texto"', b"42", b"\xff\xfe", b"{",
                      {"id": "a", "porta": "abc"}, {"id": "b", "porta": [1]}, {"id": "c", "porta": 999999},
                      {"id": "d", "porta": 0}, {"apelido": "sem id"}, {"id": ""}):
            self.assertFalse(self.grito(torto), torto)
        self.assertFalse(arena.receber_grito(b"OUTRA-MARCA{}", ("1.2.3.4", 1), meus=self.MEUS))
        self.assertEqual(arena.VIZINHOS, {})

    def test_grito_bom_entra_limpo(self):
        self.assertTrue(self.grito({"id": "lucas-1", "apelido": 'Lucas "o brabo"', "porta": 8777,
                                    "partida": {"jogo": "Super Bomberman 4", "jogo_id": "x"}}))
        visto = arena.VIZINHOS["lucas-1"]
        self.assertEqual((visto["ip"], visto["porta"]), ("192.168.0.50", 8777))
        self.assertNotIn('"', visto["apelido"])
        self.assertEqual(visto["partida"]["jogo"], "Super Bomberman 4")

    def test_o_proprio_eco_nao_entra(self):
        self.assertFalse(self.grito({"id": "eu", "porta": arena.PORTA}, ip="192.168.0.10"))

    def test_um_computador_inventando_codigos_nao_enche_a_lista(self):
        self.grito({"id": "colega-de-verdade", "porta": 8777}, ip="192.168.0.77")
        for n in range(500):
            self.grito({"id": "inventado-%d" % n, "porta": 8777}, ip="192.168.0.66", agora=1000.0 + n / 1000)
        do_invasor = [v for v in arena.VIZINHOS.values() if v["ip"] == "192.168.0.66"]
        self.assertLessEqual(len(do_invasor), arena.LIMITE_POR_ENDERECO)
        self.assertIn("colega-de-verdade", arena.VIZINHOS)

    def test_a_lista_tem_teto(self):
        for n in range(arena.LIMITE_VIZINHOS + 50):
            self.grito({"id": "c%d" % n, "porta": 8777}, ip="10.0.%d.%d" % (n // 250, n % 250 + 1),
                       agora=1000.0 + n / 1000)
        self.assertLessEqual(len(arena.VIZINHOS), arena.LIMITE_VIZINHOS)

    def test_quem_sumiu_ha_mais_de_um_minuto_sai(self):
        self.grito({"id": "velho", "porta": 8777}, agora=100.0)
        self.grito({"id": "novo", "porta": 8777}, ip="192.168.0.51", agora=200.0)
        self.assertNotIn("velho", arena.VIZINHOS)
        self.assertIn("novo", arena.VIZINHOS)


if __name__ == "__main__":
    unittest.main()
