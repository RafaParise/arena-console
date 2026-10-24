# -*- coding: utf-8 -*-
"""Acessorios dos consoles (pedido do Rafael, 24/10/2026): VMU na tela, Rumble Pak, multitap, pistola de luz...

Confere o catalogo (servidor\\acessorios.json), a limpeza do que a pessoa escolhe, o que cada escolha vira para o
emulador (opcao do nucleo, tipo de controle da porta, cartao do PS2) e a conferencia com o que o nucleo declara."""
import json
import os
import sys
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))

import acessorios  # noqa: E402
import conferir_acessorios  # noqa: E402
import graficos  # noqa: E402


def consoles_do_arena():
    with open(os.path.join(PASTA_SERVIDOR, "consoles.json"), encoding="utf-8") as arquivo:
        return {p["id"]: p["nome"] for p in json.load(arquivo)["plataformas"]}


class CatalogoDeAcessorios(unittest.TestCase):
    def todos(self):
        return [(g, a) for g in acessorios.carregar() for a in g["acessorios"]]

    def test_tem_acessorio_para_os_consoles_principais(self):
        ids = {a["id"] for _, a in self.todos()}
        for esperado in ("dc_vmu_tela_1", "dc_vmu_tela_4", "n64_acessorio_1", "n64_acessorio_4", "snes_porta2",
                         "md_porta2", "sat_cartucho", "ps2_cartoes", "nes_porta2"):
            self.assertIn(esperado, ids)

    def test_todo_console_do_catalogo_existe_no_arena(self):
        existentes = consoles_do_arena()
        for grupo in acessorios.carregar():
            for console in grupo["consoles"]:
                self.assertIn(console, existentes, "console %r nao existe em consoles.json" % console)

    def test_ids_unicos_e_bem_formados(self):
        vistos = set()
        for _, acessorio in self.todos():
            self.assertRegex(acessorio["id"], r"^[a-z0-9_]{1,60}$")
            self.assertNotIn(acessorio["id"], vistos, "id repetido: %s" % acessorio["id"])
            vistos.add(acessorio["id"])
            self.assertTrue(acessorio.get("nome") and acessorio.get("texto"), acessorio["id"])

    def test_nenhum_modelo_ficou_sem_trocar(self):
        texto = json.dumps(acessorios.carregar(), ensure_ascii=False)
        self.assertNotRegex(texto, r"\{(n|letra)\}")

    def test_jogadores_repetem_com_numero_e_letra(self):
        ids = acessorios.todos_os_acessorios()
        self.assertIn("dc_vmu_tela_3", ids)
        encaixes = ids["dc_encaixes_2"]
        rotulos = [c["rotulo"] for c in encaixes["controles"]]
        self.assertEqual(rotulos, ["Encaixe B1", "Encaixe B2"])
        self.assertEqual(encaixes["controles"][0]["alvo"], {"opcao": "reicast_device_port2_slot1"})
        self.assertEqual(ids["dc_controle_4"]["controles"][0]["alvo"], {"porta": "4"})

    def test_cada_controle_tem_um_so_alvo_e_valores_certos(self):
        for _, acessorio in self.todos():
            self.assertTrue(acessorio.get("controles"), acessorio["id"])
            identificadores = set()
            for controle in acessorio["controles"]:
                onde = "%s/%s" % (acessorio["id"], controle.get("id"))
                self.assertNotIn(controle["id"], identificadores, onde)
                identificadores.add(controle["id"])
                self.assertIn(controle["tipo"], ("chave", "escolha"), onde)
                self.assertEqual(len(controle["alvo"]), 1, onde)
                self.assertIn(next(iter(controle["alvo"])), ("opcao", "porta", "cartao_ps2"), onde)
                if controle["tipo"] == "chave":
                    self.assertTrue(controle["ligado"] and controle["desligado"] and controle["ligado"] != controle["desligado"], onde)
                    self.assertIsInstance(controle["padrao"], bool, onde)
                else:
                    valores = [str(par[0]) for par in controle["escolhas"]]
                    self.assertEqual(len(valores), len(set(valores)), "valor repetido em " + onde)
                    self.assertIn(str(controle["padrao"]), valores, "o padrao tem que ser uma das escolhas: " + onde)
                    for par in controle["escolhas"]:
                        self.assertEqual(len(par), 2, onde)
                        self.assertTrue(par[1], onde)


class EscolhaDaPessoa(unittest.TestCase):
    def test_limpar_descarta_o_que_nao_existe_ou_nao_serve(self):
        sujo = {
            "dc_vmu_tela_1": {"tela": True, "lugar": "Lower Right", "tamanho": "99x", "inventado": True},
            "n64_acessorio_1": {"pak": "rumble"},
            "n64_acessorio_2": {"pak": 5},
            "nao_existe": {"x": True},
            "dc_vmu_som": {"som": "sim"},
            "ps2_cartoes": "texto",
        }
        self.assertEqual(acessorios.limpar_estado(sujo), {
            "dc_vmu_tela_1": {"tela": True, "lugar": "Lower Right"},
            "n64_acessorio_1": {"pak": "rumble"}})
        self.assertEqual(acessorios.limpar_estado(None), {})
        self.assertEqual(acessorios.limpar_estado([1, 2]), {})

    def test_numero_de_porta_aceito_como_numero_ou_texto(self):
        limpo = acessorios.limpar_estado({"snes_porta2": {"tipo": 260}})
        self.assertEqual(limpo, {"snes_porta2": {"tipo": "260"}})

    def test_o_vmu_na_tela_vira_opcoes_do_flycast(self):
        estado = {"dc_vmu_tela_1": {"tela": True, "lugar": "Lower Right", "tamanho": "3x"},
                  "dc_vmu_som": {"som": True}}
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "dreamcast", "flycast"), {
            "reicast_vmu1_screen_display": "enabled",
            "reicast_vmu1_screen_position": "Lower Right",
            "reicast_vmu1_screen_size_mult": "3x",
            "reicast_vmu_sound": "enabled"})

    def test_desligar_grava_o_valor_de_desligado(self):
        estado = {"dc_vmu_tela_2": {"tela": False}, "n64_expansion": {"memoria": False}}
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "dreamcast", "flycast"),
                         {"reicast_vmu2_screen_display": "disabled"})
        # A chave do Expansion Pak e' invertida no nucleo: desligar o acessorio e' "True" em Disable Expansion Pak.
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "n64", "mupen64plus_next"),
                         {"mupen64plus-ForceDisableExtraMem": "True"})

    def test_controle_que_a_pessoa_nao_mexeu_nao_e_gravado(self):
        self.assertEqual(acessorios.opcoes_do_nucleo({}, "dreamcast", "flycast"), {})
        estado = {"dc_vmu_tela_1": {"tela": True}}
        self.assertNotIn("reicast_vmu1_screen_position", acessorios.opcoes_do_nucleo(estado, "dreamcast", "flycast"))

    def test_como_o_emulador_escolhe_nao_grava_nada(self):
        estado = {"dc_encaixes_1": {"encaixe1": "", "encaixe2": "Purupuru"}}
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "dreamcast", "flycast"),
                         {"reicast_device_port1_slot2": "Purupuru"})

    def test_so_vale_para_o_console_e_o_nucleo_certos(self):
        estado = {"dc_vmu_tela_1": {"tela": True}}
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "n64", "mupen64plus_next"), {})
        self.assertEqual(acessorios.opcoes_do_nucleo(estado, "dreamcast", "outro_nucleo"), {})
        # O PS1 do catalogo e' o do SwanStation: no PCSX ReARMed (outros codigos de controle) nao entra nada.
        ps1 = {"ps1_controle_1": {"tipo": "260"}}
        self.assertEqual(acessorios.opcoes_de_porta(ps1, "ps1", "swanstation"), {"input_libretro_device_p1": "260"})
        self.assertEqual(acessorios.opcoes_de_porta(ps1, "ps1", "pcsx_rearmed"), {})

    def test_pistola_de_luz_na_porta_certa(self):
        estado = {"snes_porta2": {"tipo": "260"}, "nes_porta1": {"tipo": "258"}, "nes_expansao": {"tipo": "769"}}
        self.assertEqual(acessorios.opcoes_de_porta(estado, "snes", "snes9x"), {"input_libretro_device_p2": "260"})
        self.assertEqual(acessorios.opcoes_de_porta(estado, "nes", "fceumm"),
                         {"input_libretro_device_p1": "258", "input_libretro_device_p5": "769"})

    def test_dreamcast_tipo_de_controle_por_jogador(self):
        estado = {"dc_controle_3": {"tipo": "1281"}}
        self.assertEqual(acessorios.opcoes_de_porta(estado, "dreamcast", "flycast"), {"input_libretro_device_p3": "1281"})

    def test_o_mega_drive_e_o_sega_cd_dividem_os_acessorios(self):
        estado = {"md_porta2": {"tipo": "516"}}
        for console in ("megadrive", "segacd"):
            self.assertEqual(acessorios.opcoes_de_porta(estado, console, "genesis_plus_gx"), {"input_libretro_device_p2": "516"})


class CartoesDoPs2PeloAcessorio(unittest.TestCase):
    def test_sem_escolha_vale_o_maior_cartao_na_entrada_1_e_o_pocketstation_na_2(self):
        # Decisao do Rafael (24/10/2026): igual ao ARENA do computador.
        esperado = {"slot1_tipo": "ps2", "slot1_mb": 64, "slot2_tipo": "ps1", "slot2_mb": 8}
        self.assertEqual(acessorios.cartoes_ps2({}), esperado)

    def test_a_pessoa_troca_os_cartoes(self):
        estado = {"ps2_cartoes": {"entrada1": "8", "entrada2": "32"}}
        self.assertEqual(acessorios.cartoes_ps2(estado), {"slot1_tipo": "ps2", "slot1_mb": 8, "slot2_tipo": "ps2", "slot2_mb": 32})

    def test_o_pocketstation_pode_ir_na_entrada_1(self):
        estado = {"ps2_cartoes": {"entrada1": "pocketstation", "entrada2": "64"}}
        self.assertEqual(acessorios.cartoes_ps2(estado), {"slot1_tipo": "ps1", "slot1_mb": 64, "slot2_tipo": "ps2", "slot2_mb": 64})

    def test_valor_estranho_volta_ao_padrao(self):
        estado = {"ps2_cartoes": {"entrada1": "1000", "entrada2": "abc"}}
        self.assertEqual(acessorios.cartoes_ps2(estado), acessorios.cartoes_ps2({}))


class ParaATela(unittest.TestCase):
    def test_so_os_consoles_que_o_arena_tem(self):
        nomes = {"dreamcast": "Sega Dreamcast"}
        lista = acessorios.para_a_tela({}, "windows", nomes)
        self.assertEqual([c["console"] for c in lista], ["dreamcast"])
        self.assertEqual(lista[0]["nome"], "Sega Dreamcast")

    def test_grupo_so_do_android_nao_aparece_no_windows(self):
        nomes = {"ps2": "PlayStation 2"}
        self.assertEqual(acessorios.para_a_tela({}, "windows", nomes), [])
        self.assertEqual([c["console"] for c in acessorios.para_a_tela({}, "android", nomes)], ["ps2"])

    def test_o_valor_mostrado_e_o_da_pessoa_ou_o_padrao(self):
        nomes = {"dreamcast": "Sega Dreamcast"}
        estado = {"dc_vmu_tela_1": {"tela": True, "tamanho": "4x"}}
        lista = acessorios.para_a_tela(estado, "windows", nomes)
        vmu = next(a for a in lista[0]["acessorios"] if a["id"] == "dc_vmu_tela_1")
        valores = {c["id"]: c["valor"] for c in vmu["controles"]}
        self.assertEqual(valores, {"tela": True, "lugar": "", "tamanho": "4x", "opacidade": "100%"})
        self.assertTrue(vmu["so_alguns_jogos"])
        escolha = next(c for c in vmu["controles"] if c["id"] == "tamanho")
        self.assertIn(["4x", "4×"], escolha["escolhas"])


class ConferenciaComONucleo(unittest.TestCase):
    """ferramentas\\conferir_acessorios.py com um 'nucleo de mentira': pega chave, valor e tipo de controle que nao existem."""

    def grupo(self, controle, console="dreamcast"):
        return [{"consoles": [console], "nucleo": "flycast", "plataformas": [],
                 "acessorios": [{"id": "x", "controles": [controle]}]}]

    def dump(self, opcoes=None, portas=None):
        return {"nucleos": {"flycast_libretro.dll": {"opcoes": opcoes or {}, "controles": portas or []}}}

    def opcao(self, *valores):
        return {"valores": [{"valor": v, "rotulo": v} for v in valores]}

    def test_tudo_certo(self):
        controle = {"id": "c", "tipo": "chave", "alvo": {"opcao": "k"}, "ligado": "enabled", "desligado": "disabled", "padrao": False}
        problemas, avisos = conferir_acessorios.conferir(self.dump({"k": self.opcao("enabled", "disabled")}), self.grupo(controle))
        self.assertEqual((problemas, avisos), ([], []))

    def test_chave_que_o_nucleo_nao_tem(self):
        controle = {"id": "c", "tipo": "chave", "alvo": {"opcao": "k"}, "ligado": "a", "desligado": "b", "padrao": False}
        problemas, _ = conferir_acessorios.conferir(self.dump({}), self.grupo(controle))
        self.assertEqual(len(problemas), 1)
        self.assertIn("nao tem a opcao k", problemas[0])

    def test_valor_que_o_nucleo_nao_aceita(self):
        controle = {"id": "c", "tipo": "escolha", "alvo": {"opcao": "k"}, "padrao": "", "escolhas": [["", "x"], ["1x", "a"], ["9x", "b"]]}
        problemas, _ = conferir_acessorios.conferir(self.dump({"k": self.opcao("1x", "2x")}), self.grupo(controle))
        self.assertEqual(len(problemas), 1)
        self.assertIn("'9x'", problemas[0])

    def test_tipo_de_controle_que_nao_existe_na_porta(self):
        controle = {"id": "c", "tipo": "escolha", "alvo": {"porta": "2"}, "padrao": "", "escolhas": [["", "x"], ["260", "a"], ["999", "b"]]}
        portas = [[{"descricao": "p", "id": 1}], [{"descricao": "p", "id": 1}, {"descricao": "arma", "id": 260}]]
        problemas, _ = conferir_acessorios.conferir(self.dump(portas=portas), self.grupo(controle))
        self.assertEqual(len(problemas), 1)
        self.assertIn("999", problemas[0])

    def test_nucleo_que_nao_foi_lido_so_avisa(self):
        controle = {"id": "c", "tipo": "chave", "alvo": {"opcao": "k"}, "ligado": "a", "desligado": "b", "padrao": False}
        problemas, avisos = conferir_acessorios.conferir({"nucleos": {}}, self.grupo(controle))
        self.assertEqual(problemas, [])
        self.assertEqual(len(avisos), 1)


class CartaoDoPocketStation(unittest.TestCase):
    """O cartao no formato do PlayStation 1 (128 KB) que fica na entrada 1 do PS2 e que o PocketStation le."""

    @staticmethod
    def conferencia(quadro):
        x = 0
        for byte in quadro[:127]:
            x ^= byte
        return x

    def test_estrutura_de_um_cartao_formatado_e_vazio(self):
        cartao = graficos.cartao_ps1_vazio()
        self.assertEqual(len(cartao), 131072)
        quadro = lambda n: cartao[n * 128:(n + 1) * 128]  # noqa: E731
        self.assertEqual(quadro(0)[:2], b"MC")
        for numero in range(0, 56):
            self.assertEqual(quadro(numero)[127], self.conferencia(quadro(numero)), "quadro %d" % numero)
        for numero in range(1, 16):
            self.assertEqual(quadro(numero)[0], 0xA0)                       # diretorio: bloco livre
            self.assertEqual(quadro(numero)[8:10], b"\xff\xff")             # sem proximo bloco
        self.assertEqual(quadro(16)[:4], b"\xff\xff\xff\xff")               # lista de setores ruins vazia
        self.assertEqual(cartao[56 * 128:], b"\xff" * (131072 - 56 * 128))  # os 15 blocos de dados em branco

    def test_a_entrada_2_e_o_pocketstation_e_dois_pocketstation_ganham_arquivos_diferentes(self):
        import tempfile as _tempfile
        import limpeza as _limpeza
        pasta = _tempfile.mkdtemp(prefix="arena_dois_pocketstation_")
        try:
            ini = graficos.preparar_cartoes_do_ps2(pasta, {"slot1_tipo": "ps1", "slot2_tipo": "ps1"})
            self.assertEqual((ini["MemoryCards"]["Slot1_Filename"], ini["MemoryCards"]["Slot2_Filename"]),
                             ("PocketStation.mcr", "PocketStation-2.mcr"))
        finally:
            _limpeza.apagar_pasta(pasta)

    def test_a_entrada_pode_ser_o_pocketstation(self):
        import tempfile
        import limpeza
        pasta = tempfile.mkdtemp(prefix="arena_pocketstation_")
        try:
            ini = graficos.preparar_cartoes_do_ps2(pasta, {"slot1_mb": 64, "slot2_tipo": "ps1"})
            memcards = os.path.join(pasta, "pcsx2", "memcards")
            self.assertEqual(ini["MemoryCards"]["Slot1_Filename"], "Mcd001-64MB.ps2")
            self.assertEqual(ini["MemoryCards"]["Slot2_Filename"], "PocketStation.mcr")
            self.assertEqual(os.path.getsize(os.path.join(memcards, "PocketStation.mcr")), 131072)
            # Um cartao que a pessoa ja usou nunca e' trocado.
            with open(os.path.join(memcards, "PocketStation.mcr"), "r+b") as arquivo:
                arquivo.seek(60 * 128)
                arquivo.write(b"MEU SAVE")
            graficos.preparar_cartoes_do_ps2(pasta, {"slot2_tipo": "ps1"})
            with open(os.path.join(memcards, "PocketStation.mcr"), "rb") as arquivo:
                arquivo.seek(60 * 128)
                self.assertEqual(arquivo.read(8), b"MEU SAVE")
        finally:
            limpeza.apagar_pasta(pasta)

    def test_o_padrao_antigo_continua_sendo_cartao_de_ps2(self):
        self.assertNotIn("slot1_tipo", graficos.limpar_cartoes_ps2(None))
        self.assertEqual(graficos.limpar_cartoes_ps2({"slot1_tipo": "ps1"})["slot1_tipo"], "ps1")
        self.assertNotIn("slot1_tipo", graficos.limpar_cartoes_ps2({"slot1_tipo": "xx"}))


class PocketStationNoWindows(unittest.TestCase):
    def test_o_pokket_vai_pela_ponte_sem_acento(self):
        # O Pokket abre o pocketstation.bin em ANSI: com "Pedagógicos" no caminho o conteudo falhava (24/10/2026).
        import ponte_sem_acento
        self.assertEqual(ponte_sem_acento.NUCLEOS["pokket_libretro.dll"], ["pocketstation.bin"])


class ConfigDoArena(unittest.TestCase):
    def test_a_configuracao_padrao_tem_a_chave_dos_acessorios(self):
        import arena
        self.assertEqual(arena.config_padrao()["acessorios"], {})


if __name__ == "__main__":
    unittest.main()
