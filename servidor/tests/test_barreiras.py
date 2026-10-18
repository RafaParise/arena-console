# -*- coding: utf-8 -*-
"""Testes para servidor/barreiras.py -- a parte que DECIDE (avaliar), com
fatos inventados: nao dependem da maquina onde rodam."""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import barreiras  # noqa: E402


def ids(lista):
    return [b["id"] for b in lista]


class TestBarreiras(unittest.TestCase):

    def test_sem_fatos_nao_quebra(self):
        self.assertEqual(barreiras.avaliar({}), [])

    def test_maquina_em_ordem_nao_acusa_nada(self):
        fatos = {"memoria_total_mb": 4000, "memoria_livre_mb": 2200, "memoria_em_uso_pct": 45,
                 "na_tomada": True, "tem_bateria": True, "game_dvr": 0, "modo_de_jogo": 1,
                 "efeitos_visuais": 2, "transparencia": 0, "apps_segundo_plano_desligados": 1,
                 "disco_windows_livre_pct": 40, "disco_windows_livre_gb": 60,
                 "processador_maximo_tomada": 100, "processador_maximo_bateria": 100,
                 "arquivo_de_paginacao": ["?:\\pagefile.sys"], "ligado_ha_horas": 5,
                 "antivirus": [{"nome": "Windows Defender", "ligado": True}]}
        self.assertEqual(barreiras.avaliar(fatos), [])

    def test_memoria_quase_cheia_e_alta_e_vem_primeiro(self):
        fatos = {"memoria_total_mb": 4000, "memoria_livre_mb": 600, "memoria_em_uso_pct": 88,
                 "transparencia": 1}
        lista = barreiras.avaliar(fatos)
        self.assertEqual(lista[0]["id"], "memoria")
        self.assertEqual(lista[0]["gravidade"], "alta")

    def test_programas_fechaveis_viram_botao(self):
        fatos = {"processos": [{"nome": "onedrive", "mb": 90, "cpu": 1},
                               {"nome": "teams", "mb": 300, "cpu": 2},
                               {"nome": "winword", "mb": 200, "cpu": 0}]}
        item = next(b for b in barreiras.avaliar(fatos) if b["id"] == "fechaveis")
        self.assertEqual([p["processo"] for p in item["fechar"]], ["onedrive", "teams"])
        self.assertEqual([p["nome"] for p in item["fechar"]], ["OneDrive", "Microsoft Teams"])
        self.assertNotIn("winword", [p["processo"] for p in item["fechar"]])  # nunca o que tem trabalho do aluno

    def test_dois_antivirus_ligados(self):
        fatos = {"antivirus": [{"nome": "Windows Defender", "ligado": True},
                               {"nome": "McAfee", "ligado": True}]}
        item = next(b for b in barreiras.avaliar(fatos) if b["id"] == "antivirus_duplo")
        self.assertEqual((item["gravidade"], item["quem"]), ("alta", barreiras.ACOES_TI))

    def test_um_antivirus_so_nao_acusa(self):
        fatos = {"antivirus": [{"nome": "Windows Defender", "ligado": True},
                               {"nome": "Avast", "ligado": False}]}
        self.assertNotIn("antivirus_duplo", ids(barreiras.avaliar(fatos)))

    def test_bateria_e_economia(self):
        fatos = {"tem_bateria": True, "na_tomada": False, "bateria_pct": 40,
                 "economia_de_bateria": True, "processador_maximo_bateria": 50}
        achados = ids(barreiras.avaliar(fatos))
        for esperado in ("bateria", "economia_bateria", "processador_limitado_bateria"):
            self.assertIn(esperado, achados)

    def test_desktop_sem_bateria_nao_acusa_bateria(self):
        self.assertNotIn("bateria", ids(barreiras.avaliar({"tem_bateria": False, "na_tomada": None})))

    def test_gravacao_em_segundo_plano(self):
        self.assertIn("gravacao_fundo", ids(barreiras.avaliar({"game_dvr": 1})))
        self.assertIn("gravacao_fundo", ids(barreiras.avaliar({"captura_de_jogo": 1})))

    def test_inicializacao_conta_so_os_ligados(self):
        itens = [{"nome": "p%d" % i, "onde": "usuario", "desligado": False} for i in range(5)]
        itens.append({"nome": "desligado", "onde": "usuario", "desligado": True})
        self.assertNotIn("inicializacao", ids(barreiras.avaliar({"inicializacao": itens})))
        itens.append({"nome": "p6", "onde": "computador", "desligado": False})
        item = next(b for b in barreiras.avaliar({"inicializacao": itens}) if b["id"] == "inicializacao")
        self.assertEqual(item["quem"], barreiras.ACOES_ALUNO)

    def test_telemetria_so_sem_limite_de_politica(self):
        rodando = {"servicos": [{"nome": "DiagTrack", "rodando": True}]}
        self.assertIn("telemetria", ids(barreiras.avaliar(dict(rodando, telemetria_politica=None))))
        self.assertNotIn("telemetria", ids(barreiras.avaliar(dict(rodando, telemetria_politica=1))))

    def test_servicos_de_disco_so_pesam_em_hd(self):
        fatos = {"servicos": [{"nome": "SysMain", "rodando": True}, {"nome": "WSearch", "rodando": True}]}
        self.assertNotIn("servicos_disco", ids(barreiras.avaliar(fatos)))
        self.assertIn("servicos_disco", ids(barreiras.avaliar(dict(fatos, disco_mecanico=True))))

    def test_hd_dito_pelo_windows_tambem_conta(self):
        fatos = {"servicos": [{"nome": "SysMain", "rodando": True}], "disco_windows_tipo": "HDD"}
        self.assertIn("servicos_disco", ids(barreiras.avaliar(fatos)))
        fatos["disco_windows_tipo"] = "SSD"
        self.assertNotIn("servicos_disco", ids(barreiras.avaliar(fatos)))

    def test_checagem_rapida_so_traz_o_grave(self):
        fatos = {"memoria_total_mb": 4000, "memoria_livre_mb": 500, "memoria_em_uso_pct": 90,
                 "tem_bateria": True, "na_tomada": False, "transparencia": 1}
        lista = barreiras.avaliar_rapido(fatos)
        self.assertEqual(sorted(b["id"] for b in lista), ["bateria", "memoria"])

    def test_disco_cheio_sem_paginacao_e_driver_basico(self):
        fatos = {"disco_windows_livre_pct": 4, "disco_windows_livre_gb": 3, "arquivo_de_paginacao": "",
                 "video": "Microsoft Basic Display Adapter"}
        achados = barreiras.avaliar(fatos)
        for esperado in ("disco_cheio", "sem_paginacao", "driver_video"):
            self.assertIn(esperado, ids(achados))
        self.assertTrue(all(b["gravidade"] == "alta" for b in achados))

    def test_windows_atualizando_e_reinicio(self):
        fatos = {"processos": [{"nome": "tiworker", "mb": 300, "cpu": 25}], "reinicio_pendente": True}
        achados = ids(barreiras.avaliar(fatos))
        self.assertIn("atualizando", achados)
        self.assertIn("reiniciar", achados)
        self.assertNotIn("pesados", achados)     # atualizacao nao aparece duas vezes

    def test_servicos_inuteis_e_indexacao(self):
        fatos = {"servicos": [{"nome": "Fax", "rodando": True}, {"nome": "XblGameSave", "rodando": True},
                              {"nome": "Spooler", "rodando": True}],
                 "processos": [{"nome": "searchindexer", "mb": 60, "cpu": 22}]}
        lista = barreiras.avaliar(fatos)
        inuteis = next(b for b in lista if b["id"] == "servicos_inuteis")
        self.assertIn("Fax", inuteis["achado"])
        self.assertNotIn("Spooler", inuteis["achado"])     # impressora serve na escola
        self.assertIn("indexando", ids(lista))
        self.assertNotIn("pesados", ids(lista))            # nao aparece duas vezes

    def test_bloatware(self):
        item = next(b for b in barreiras.avaliar({"bloatware_instalado": ["McAfee LiveSafe", "WildTangent Games",
                                                                           "Candy Crush Saga"]})
                    if b["id"] == "bloatware")
        self.assertEqual(item["gravidade"], "media")

    def test_ordem_por_gravidade(self):
        fatos = {"transparencia": 1, "tem_bateria": True, "na_tomada": False, "game_dvr": 1}
        gravidades = [b["gravidade"] for b in barreiras.avaliar(fatos)]
        self.assertEqual(gravidades, sorted(gravidades, key=barreiras.GRAVIDADE.get))

    def test_toda_barreira_diz_o_que_fazer_e_quem(self):
        fatos = {"memoria_total_mb": 4000, "memoria_livre_mb": 500, "memoria_em_uso_pct": 90,
                 "game_dvr": 1, "modo_de_jogo": 0, "transparencia": 1, "apps_segundo_plano_desligados": 0,
                 "reinicio_pendente": True, "ligado_ha_horas": 100, "temp_mb": 5000,
                 "plano_de_energia": "Economia de energia"}
        for b in barreiras.avaliar(fatos):
            self.assertTrue(b["acao"] and b["por_que"] and b["achado"], b["id"])
            self.assertIn(b["quem"], (barreiras.ACOES_ALUNO, barreiras.ACOES_TI))

    @unittest.skipUnless(sys.platform.startswith("win"), "so no Windows")
    def test_powershell_bloqueado_nao_quebra(self):
        # Escola que bloqueia o PowerShell para aluno (politica/AppLocker):
        # o diagnostico segue com o que da para ler sem ele.
        original = barreiras._powershell_fatos

        def bloqueado(*a, **k):
            raise PermissionError("O acesso ao PowerShell foi bloqueado pela politica")
        barreiras._powershell_fatos = bloqueado
        try:
            resultado = barreiras.diagnosticar()
        finally:
            barreiras._powershell_fatos = original
        self.assertIsInstance(resultado["barreiras"], list)
        self.assertTrue(any("PowerShell" in m for m in resultado["nao_deu_para_ler"]))
        self.assertIn("memoria_total_mb", resultado["fatos"])   # o que nao depende dele continua

    def test_fechar_so_da_lista(self):
        ok, mensagem = barreiras.fechar_programa("explorer")
        self.assertFalse(ok)
        ok, mensagem = barreiras.fechar_programa("../../winword")
        self.assertFalse(ok)



class TestBarreirasDoLinux(unittest.TestCase):
    """O mesmo painel no Linux (item 13): avaliar_linux com fatos
    inventados, e a coleta de verdade quando o teste roda no Linux."""

    def test_maquina_em_ordem_nao_acusa_nada(self):
        fatos = {"sistema": "linux", "memoria_total_mb": 7800, "memoria_livre_mb": 5000, "memoria_em_uso_pct": 36,
                 "tem_bateria": True, "na_tomada": True, "economia_de_bateria": False, "ligado_ha_horas": 3,
                 "disco_windows_livre_pct": 50, "disco_windows_livre_gb": 80, "memoria_virtual_mb": 2048,
                 "video": "i915", "processos": [{"nome": "gnome-shell", "mb": 500, "cpu": 3}]}
        self.assertEqual(barreiras.avaliar_linux(fatos), [])

    def test_o_que_pesa_no_linux(self):
        fatos = {"memoria_total_mb": 4000, "memoria_livre_mb": 500, "memoria_em_uso_pct": 88,
                 "tem_bateria": True, "na_tomada": False, "bateria_pct": 40, "economia_de_bateria": True,
                 "memoria_virtual_mb": 0, "video": "simpledrm", "reinicio_pendente": True,
                 "processos": [{"nome": "discord", "mb": 300, "cpu": 2}, {"nome": "unattended-upgr", "mb": 90, "cpu": 20}]}
        achados = ids(barreiras.avaliar_linux(fatos))
        for esperado in ("memoria", "bateria", "economia_bateria", "sem_paginacao", "driver_video",
                         "reiniciar", "atualizando", "fechaveis"):
            self.assertIn(esperado, achados)
        texto = str(barreiras.avaliar_linux(fatos))
        self.assertNotIn("Windows", texto)
        self.assertNotIn("Gerenciador de Tarefas", texto)

    def test_placa_com_driver_nao_acusa(self):
        self.assertNotIn("driver_video", ids(barreiras.avaliar_linux({"video": "amdgpu, simpledrm"})))

    def test_fechar_so_da_lista_do_linux(self):
        ok, _mensagem = barreiras._fechar_no_linux("gnome-shell")
        self.assertFalse(ok)

    @unittest.skipUnless(sys.platform.startswith("linux"), "le o /proc e o /sys do Linux")
    def test_coleta_de_verdade(self):
        fatos = barreiras.coletar_fatos_linux()
        self.assertEqual(fatos["sistema"], "linux")
        self.assertGreater(fatos["memoria_total_mb"], 0)
        self.assertTrue(fatos["processos"])
        resultado = barreiras.diagnosticar()
        self.assertIsInstance(resultado["barreiras"], list)


if __name__ == "__main__":
    unittest.main()
