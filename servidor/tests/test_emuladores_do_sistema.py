# -*- coding: utf-8 -*-
"""O emulador de fora instalado no sistema do Linux (14/11/2026).

No Linux, quando a pasta emuladores\\ do ARENA nao tem o PCSX2, o Dolphin
ou o RPCS3, mas a distribuicao tem (o pacote no PATH), o ARENA usa esse,
com a configuracao e a BIOS na pasta do ARENA (graficos.achar_externo_detalhado
e plataforma.dados_do_externo). O Linux e' imitado trocando as constantes
de sistema e o shutil.which, numa pasta temporaria: roda em qualquer
computador e nao precisa de emulador nenhum instalado."""
import contextlib
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import graficos  # noqa: E402
import plataforma  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))
import limpeza  # noqa: E402


def _ler_cadastro(id_da_plataforma):
    """A plataforma de verdade do servidor\\consoles.json (ps2, gamecube, ps3...)."""
    import json
    with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
        return next(p for p in json.load(arquivo)["plataformas"] if p["id"] == id_da_plataforma)


def _criar(caminho, conteudo=b"x"):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)
    return caminho


class EmuladorDoSistema(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_sistema_")
        self.emuladores = os.path.join(self.pasta, "emuladores")
        self.sistema = os.path.join(self.pasta, "usr", "bin")
        self.retroarch = os.path.join(self.pasta, "retroarch")
        os.makedirs(os.path.join(self.retroarch, "system"))
        os.makedirs(self.emuladores)
        # O que o "sistema" tem instalado: nome -> caminho (o shutil.which de mentira).
        self.instalados = {}
        self.perguntados = []

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def _which(self, nome, *_args, **_kwargs):
        self.perguntados.append(nome)
        return self.instalados.get(nome)

    def _instalar_no_sistema(self, nome):
        self.instalados[nome] = _criar(os.path.join(self.sistema, nome))
        return self.instalados[nome]

    @contextlib.contextmanager
    def _sistema(self, windows=False, android=False):
        """Imita o Linux (ou o Windows, ou o Android) com a pasta temporaria."""
        with contextlib.ExitStack() as pilha:
            pilha.enter_context(mock.patch.object(graficos, "NO_WINDOWS", windows))
            pilha.enter_context(mock.patch.object(plataforma, "WINDOWS", windows))
            pilha.enter_context(mock.patch.object(plataforma, "ANDROID", android))
            pilha.enter_context(mock.patch.object(graficos, "PASTA_EMULADORES", self.emuladores))
            pilha.enter_context(mock.patch.object(plataforma, "PASTA_DOS_EMULADORES", self.emuladores))
            pilha.enter_context(mock.patch.object(graficos, "PASTA_RETROARCH", self.retroarch))
            pilha.enter_context(mock.patch("shutil.which", self._which))
            yield

    # --- quem vence -------------------------------------------------------

    def test_a_pasta_do_arena_vence_o_sistema(self):
        do_arena = _criar(os.path.join(self.emuladores, "PCSX2", "PCSX2", "pcsx2-qt"))
        self._instalar_no_sistema("pcsx2-qt")
        with self._sistema():
            caminho, compactado, _ = graficos.achar_externo_detalhado(_ler_cadastro("ps2"))
            self.assertEqual(caminho, do_arena)
            self.assertIsNone(compactado)
            self.assertEqual(graficos.de_onde_vem_o_externo(caminho), "arena")
            # O da pasta do ARENA continua com a configuracao do lado dele.
            dados = plataforma.dados_do_externo("PCSX2", caminho)
        self.assertEqual(dados[1], {"XDG_CONFIG_HOME": os.path.join(self.emuladores, "PCSX2")})

    def test_so_o_sistema_tem_o_pcsx2(self):
        programa = self._instalar_no_sistema("pcsx2-qt")
        with self._sistema():
            caminho, compactado, _ = graficos.achar_externo_detalhado(_ler_cadastro("ps2"))
            self.assertEqual(caminho, programa)
            self.assertIsNone(compactado)
            config, ambiente, argumentos = plataforma.dados_do_externo("PCSX2", caminho)
            # A configuracao vai para a pasta do ARENA, nunca para a do programa (/usr/bin).
            pasta_do_pcsx2 = os.path.join(self.emuladores, "PCSX2", "PCSX2")
            self.assertEqual(config, os.path.join(pasta_do_pcsx2, "pcsx2-qt"))
            self.assertEqual(ambiente, {"XDG_CONFIG_HOME": os.path.join(self.emuladores, "PCSX2")})
            self.assertEqual(argumentos, [])
            self.assertTrue(os.path.isdir(pasta_do_pcsx2), "o ARENA cria a pasta de dados que falta")
            # A BIOS: sem ela, a tela avisa; com ela na pasta bios do ARENA, nada falta.
            self.assertIn("BIOS", graficos.falta_para_o_externo("PCSX2", caminho))
            _criar(os.path.join(pasta_do_pcsx2, "bios", "scph.bin"))
            self.assertEqual(graficos.falta_para_o_externo("PCSX2", caminho), "")
            situacao = next(s for s in graficos.situacao_dos_externos([_ler_cadastro("ps2")])
                            if s["nome"] == "PCSX2")
        self.assertTrue(situacao["instalado"])
        self.assertEqual(situacao["origem"], "sistema")
        self.assertIn("instalado no sistema", situacao["de_onde"])

    def test_so_o_sistema_tem_o_rpcs3(self):
        programa = self._instalar_no_sistema("rpcs3")
        with self._sistema():
            caminho, _, _ = graficos.achar_externo_detalhado(_ler_cadastro("ps3"))
            self.assertEqual(caminho, programa)
            config, ambiente, _ = plataforma.dados_do_externo("RPCS3", caminho)
            # O firmware e' procurado na mesma pasta de dados que o RPCS3 vai usar.
            self.assertIn("firmware", graficos.falta_para_o_externo("RPCS3", caminho))
        self.assertEqual(ambiente, {"XDG_CONFIG_HOME": os.path.join(self.emuladores, "RPCS3")})
        self.assertEqual(config, os.path.join(self.emuladores, "RPCS3", "rpcs3", "rpcs3"))

    def test_dolphin_do_sistema_usa_a_pasta_do_dolphin_do_windows(self):
        # O pen drive tem o Dolphin do Windows: o do sistema usa a mesma pasta User (mesmos saves).
        _criar(os.path.join(self.emuladores, "Dolphin", "Dolphin-x64", "Dolphin.exe"))
        programa = self._instalar_no_sistema("dolphin-emu")
        with self._sistema():
            caminho, _, _ = graficos.achar_externo_detalhado(_ler_cadastro("gamecube"))
            self.assertEqual(caminho, programa)
            config, ambiente, argumentos = plataforma.dados_do_externo("Dolphin", caminho)
        pasta = os.path.join(self.emuladores, "Dolphin", "Dolphin-x64")
        self.assertEqual(config, os.path.join(pasta, "dolphin-emu"))
        self.assertEqual(ambiente, {})
        self.assertEqual(argumentos, ["-u", os.path.join(pasta, "User")])

    def test_nenhum_dos_dois_falta_como_antes(self):
        with self._sistema():
            self.assertEqual(graficos.achar_externo_detalhado(_ler_cadastro("ps2"))[:2], (None, None))
            # O compactado esquecido na pasta continua sendo avisado.
            zipado = _criar(os.path.join(self.emuladores, "PCSX2", "pcsx2.zip"))
            self.assertEqual(graficos.achar_externo_detalhado(_ler_cadastro("ps2"))[:2], (None, zipado))
            situacao = graficos.situacao_dos_externos([_ler_cadastro("ps2")])[0]
        self.assertFalse(situacao["instalado"])
        self.assertEqual(situacao["origem"], "")

    def test_nome_com_curinga_nao_vai_ao_path(self):
        with self._sistema():
            graficos.achar_externo_detalhado(_ler_cadastro("ps2"))
        self.assertIn("pcsx2-qt", self.perguntados)
        self.assertFalse(any("*" in nome for nome in self.perguntados))

    def test_outro_processador_fica_de_fora(self):
        self._instalar_no_sistema("pcsx2-qt")
        with self._sistema(), mock.patch.object(plataforma, "roda_neste_processador", lambda _c: False):
            self.assertIsNone(graficos.achar_externo_detalhado(_ler_cadastro("ps2"))[0])

    # --- os outros sistemas nao mudam -------------------------------------

    def test_no_windows_nada_muda(self):
        self._instalar_no_sistema("pcsx2-qt")
        self._instalar_no_sistema("pcsx2-qt.exe")
        with self._sistema(windows=True):
            self.assertIsNone(graficos.achar_externo_detalhado(_ler_cadastro("ps2"))[0])
            self.assertIsNone(plataforma.programa_do_sistema(["pcsx2-qt"]))
            programa = self.instalados["pcsx2-qt"]
            self.assertEqual(plataforma.dados_do_externo("PCSX2", programa), (programa, {}, []))
            self.assertFalse(plataforma.e_do_sistema(programa))

    def test_no_android_nada_muda(self):
        self._instalar_no_sistema("pcsx2-qt")
        with self._sistema(android=True):
            self.assertIsNone(graficos.achar_externo_detalhado(_ler_cadastro("ps2"))[0])
            self.assertIsNone(plataforma.programa_do_sistema(["pcsx2-qt"]))
            self.assertFalse(plataforma.e_do_sistema(self.instalados["pcsx2-qt"]))


if __name__ == "__main__":
    unittest.main()
