# -*- coding: utf-8 -*-
"""O painel "Este celular" do ARENA do Android (servidor\\painel_do_aparelho.py).

Pedido do Rafael (25/10/2026): sem informacao repetida (o processador aparecia duas vezes), e com a saude da bateria, os
miliamperes, o gasto de energia agora, a temperatura e a memoria RAM em tempo real.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import painel_do_aparelho as p  # noqa: E402

# Uma leitura de verdade (o Galaxy A12 do Rafael, com os numeros arredondados e sem o nome do aparelho).
LEITURA = {
    "fabricante": "samsung", "modelo": "SM-A125M", "nome": "Meu A12", "android": "12", "android_sdk": 31,
    "seguranca": "2024-10-01", "versao_do_sistema": "SP1A.210812.016.A125MUBSEDXB1", "kernel": "4.19.191",
    "ligado_ha_s": 3 * 86400 + 4 * 3600 + 12 * 60,
    "processador": "Mediatek MT6765V/CB", "hardware": "mt6765", "nucleos": 8,
    "nucleos_mhz": [2300, 2300, 2300, 2300, 1800, 1800, 1800, 1800],
    "nucleos_agora_mhz": [1200, 1200, 1200, 1200, 900, 900, 900, 900],
    "arquiteturas": ["arm64-v8a", "armeabi-v7a", "armeabi"], "placa_de_video": "PowerVR Rogue GE8320",
    "opengl_es": "3.2", "vulkan": True, "vulkan_versao": "1.1",
    "memoria_total_mb": 3700, "memoria_livre_mb": 1400, "memoria_baixa": False,
    "troca_total_mb": 1024, "troca_livre_mb": 900,
    "armazenamento_total_mb": 52531, "armazenamento_livre_mb": 6554,
    "tela": "720x1600", "tela_polegadas": 6.5, "tela_dpi": 320, "tela_hz": 60, "tela_modos_hz": [60],
    "tem_bateria": True, "bateria_pct": 92, "na_tomada": True, "economia": False,
    "bateria_estado": 2, "tomada": 1, "bateria_saude": 2, "bateria_temperatura_c": 26.9, "bateria_voltagem_mv": 4230,
    "bateria_tecnologia": "Li-ion", "corrente_ua": 1820000, "bateria_carga_mah": 4600, "bateria_capacidade_mah": 4900,
    "falta_para_encher_s": 2700, "termico": 0, "margem_termica": 0.45,
    "recursos": {"usb_host": True, "bluetooth": True, "bluetooth_le": True, "giroscopio": False, "acelerometro": True,
                 "multitoque": True, "vibracao": True},
    "controles": [{"nome": "GameSir-Nova Lite", "jogador": 1}, {"nome": "GameSir-Nova Lite", "jogador": 2}],
    "wifi_ligado": True, "wifi": {"sinal_dbm": -52, "velocidade_mbps": 72, "frequencia_mhz": 5180},
}
EXTRAS = {"motor": "gl", "velocidade_relativa": 0.18, "gravacao_mbs": 135.2, "internet": False, "economico": True}


def linhas_de(grupos):
    return {rotulo: valor for g in grupos for rotulo, valor, *_ in g["linhas"]}


class ONaoRepete(unittest.TestCase):
    def test_nenhum_rotulo_aparece_duas_vezes(self):
        rotulos = [linha[0] for g in p.painel(LEITURA, EXTRAS) for linha in g["linhas"]]
        repetidos = sorted({r for r in rotulos if rotulos.count(r) > 1})
        self.assertEqual(repetidos, [], "o mesmo campo em dois lugares (o processador aparecia duas vezes)")

    def test_processador_e_memoria_aparecem_uma_vez_so_e_completos(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Processador (SoC)"], "Mediatek MT6765V/CB")      # "mt6765" ja esta dentro do nome: nao repete
        outro = linhas_de(p.painel(dict(LEITURA, processador="Qualcomm SM8450", hardware="kalama"), EXTRAS))
        self.assertEqual(outro["Processador (SoC)"], "Qualcomm SM8450 (kalama)")
        self.assertEqual(tudo["Núcleos"], "8 núcleos: 4 × até 2,3 GHz + 4 × até 1,8 GHz")
        self.assertEqual(tudo["Memória RAM"], "3,6 GB: 2,2 GB em uso · 1,4 GB livres")

    def test_os_grupos_vem_na_ordem_que_o_aluno_procura(self):
        titulos = [g["titulo"] for g in p.painel(LEITURA, EXTRAS)]
        self.assertEqual(titulos, ["O aparelho", "Processador e vídeo", "Memória e armazenamento",
                                   "Bateria e energia", "Para jogar com controle", "Rede", "O ARENA neste aparelho"])


class ABateria(unittest.TestCase):
    def test_carregando_diz_quanto_entra_e_a_potencia(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Entrando na bateria agora"], "1.820 mA (≈ 7,7 W)")
        self.assertNotIn("Gastando agora", tudo)
        self.assertEqual(tudo["Nível"], "92% · carregando pela tomada")
        self.assertEqual(tudo["Voltagem"], "4,23 V")
        self.assertEqual(tudo["Temperatura da bateria"], "26,9 °C")
        self.assertEqual(tudo["Falta para encher"], "uns 45 min")

    def test_no_aparelho_sem_tomada_diz_quanto_gasta(self):
        leitura = dict(LEITURA, bateria_estado=3, tomada=0, na_tomada=False, corrente_ua=-420000)
        tudo = linhas_de(p.painel(leitura, EXTRAS))
        self.assertEqual(tudo["Gastando agora"], "420 mA (≈ 1,8 W)")
        self.assertNotIn("Entrando na bateria agora", tudo)
        self.assertEqual(tudo["Nível"], "92% · usando a bateria")

    def test_o_sinal_da_corrente_nao_decide(self):
        # Cada fabricante poe o sinal de um jeito: o ESTADO e' que diz se carrega ou gasta.
        positivo = linhas_de(p.painel(dict(LEITURA, bateria_estado=3, tomada=0, na_tomada=False, corrente_ua=420000), EXTRAS))
        negativo = linhas_de(p.painel(dict(LEITURA, bateria_estado=3, tomada=0, na_tomada=False, corrente_ua=-420000), EXTRAS))
        self.assertEqual(positivo["Gastando agora"], negativo["Gastando agora"])

    def test_aparelho_que_da_a_corrente_em_miliampere(self):
        self.assertEqual(p.milis(420), 420.0)             # "algumas centenas": so pode ser mA
        self.assertEqual(p.milis(-166), 166.0)            # o Galaxy A12 do Rafael, carregando
        self.assertEqual(p.milis(5200), 5200.0)           # carregador forte, num aparelho que diz mA
        self.assertEqual(p.milis(420000), 420.0)          # microampere, como o Android manda
        self.assertEqual(p.milis(-1820000), 1820.0)
        self.assertEqual(p.milis(0), 0.0)
        self.assertIsNone(p.milis(None))

    def test_na_tomada_sem_carregar_nao_inventa_corrente(self):
        for estado in (4, 5):
            tudo = linhas_de(p.painel(dict(LEITURA, bateria_estado=estado, corrente_ua=2300), EXTRAS))
            self.assertIn("quase nenhuma", tudo["Corrente na bateria"])
            self.assertNotIn("Gastando agora", tudo)
            self.assertNotIn("Entrando na bateria agora", tudo)

    def test_sem_tomada_o_estado_4_mostra_a_corrente_medida(self):
        leitura = dict(LEITURA, bateria_estado=4, tomada=0, na_tomada=False)
        self.assertIn("Gastando agora", linhas_de(p.painel(leitura, EXTRAS)))

    def test_a_conta_da_capacidade_diz_que_e_so_pista(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertIn("só uma pista", tudo["Conta: carga ÷ nível"])
        self.assertEqual(tudo["Capacidade de fábrica"], "4.900 mAh (o que o perfil de energia do próprio Android declara)")
        # com a bateria quase vazia a conta nao vale nada: some
        vazia = linhas_de(p.painel(dict(LEITURA, bateria_pct=8), EXTRAS))
        self.assertNotIn("Conta: carga ÷ nível", vazia)

    def test_bateria_fraca_fora_da_tomada_acende_o_alerta(self):
        leitura = dict(LEITURA, bateria_pct=9, bateria_estado=3, tomada=0, na_tomada=False)
        nivel = next(l for g in p.painel(leitura, EXTRAS) for l in g["linhas"] if l[0] == "Nível")
        self.assertEqual(nivel[2]["nivel"], "ruim")

    def test_calor_do_aparelho_vem_do_proprio_android(self):
        quente = linhas_de(p.painel(dict(LEITURA, termico=3, margem_termica=0.97), EXTRAS))
        self.assertIn("muito quente", quente["Calor do aparelho"])
        self.assertIn("97%", quente["Calor do aparelho"])
        self.assertTrue(linhas_de(p.painel(LEITURA, EXTRAS))["Calor do aparelho"].startswith("normal"))

    def test_so_aparece_o_que_o_aparelho_deu(self):
        leitura = {k: v for k, v in LEITURA.items() if k not in ("corrente_ua", "bateria_voltagem_mv", "termico",
                                                                  "margem_termica", "bateria_capacidade_mah")}
        tudo = linhas_de(p.painel(leitura, EXTRAS))
        for ausente in ("Gastando agora", "Entrando na bateria agora", "Voltagem", "Calor do aparelho", "Capacidade de fábrica"):
            self.assertNotIn(ausente, tudo)

    def test_celular_sem_bateria(self):
        tudo = linhas_de(p.painel({"tem_bateria": False}, {}))
        self.assertEqual(tudo, {"Bateria": "este aparelho não tem bateria"})


class AMemoria(unittest.TestCase):
    def nivel_da_ram(self, livre, **mais):
        linha = next(l for g in p.painel(dict(LEITURA, memoria_livre_mb=livre, **mais), EXTRAS) for l in g["linhas"]
                     if l[0] == "Memória RAM")
        return linha[2]["nivel"]

    def test_a_barra_muda_de_cor_com_a_memoria(self):
        self.assertEqual(self.nivel_da_ram(2000), "ok")
        self.assertEqual(self.nivel_da_ram(600), "atencao")
        self.assertEqual(self.nivel_da_ram(200), "ruim")
        self.assertEqual(self.nivel_da_ram(2000, memoria_baixa=True), "ruim")

    def test_pouca_memoria_so_na_frase_quando_o_android_diz(self):
        linha = next(l for g in p.painel(dict(LEITURA, memoria_livre_mb=200, memoria_baixa=False), EXTRAS) for l in g["linhas"]
                     if l[0] == "Memória RAM")
        self.assertNotIn("pouca memória", linha[1])
        self.assertEqual(linha[2]["nivel"], "ruim")                       # a cor avisa; a frase espera o Android dizer

    def test_a_barra_mostra_o_quanto_esta_em_uso(self):
        linha = next(l for g in p.painel(LEITURA, EXTRAS) for l in g["linhas"] if l[0] == "Memória RAM")
        self.assertEqual(linha[2]["pct"], 62)

    def test_armazenamento_cheio_avisa(self):
        linha = next(l for g in p.painel(dict(LEITURA, armazenamento_livre_mb=500), EXTRAS) for l in g["linhas"]
                     if l[0] == "Armazenamento")
        self.assertEqual(linha[2]["nivel"], "ruim")


class OResto(unittest.TestCase):
    def test_painel_vazio_nao_inventa_nada(self):
        self.assertEqual(p.painel({}, {}), [])

    def test_controles_ligados_na_ordem_dos_jogadores(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Controles ligados agora"], "2: GameSir-Nova Lite (jogador 1), GameSir-Nova Lite (jogador 2)")
        sem = linhas_de(p.painel(dict(LEITURA, controles=[]), EXTRAS))
        self.assertIn("controle de toque", sem["Controles ligados agora"])
        com_teclado = linhas_de(p.painel(dict(LEITURA, controles=[{"nome": "Teclado X", "teclado": True}]), EXTRAS))
        self.assertIn("teclado: Teclado X", com_teclado["Controles ligados agora"])

    def test_o_que_o_aparelho_tem_para_jogar(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Controle por Bluetooth"], "tem (e Bluetooth LE)")
        self.assertEqual(tudo["Giroscópio"], "não tem")
        self.assertEqual(tudo["Controle por cabo (USB-C ou OTG)"], "tem")

    def test_wifi_e_internet(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Wi-Fi"], "sinal excelente (-52 dBm) · 72 Mb/s · 5 GHz")
        self.assertIn("sem internet", tudo["Internet"])
        self.assertEqual(linhas_de(p.painel({"wifi_ligado": False}, {}))["Wi-Fi"], "desligado")
        self.assertEqual(linhas_de(p.painel({"wifi_ligado": True}, {}))["Wi-Fi"], "ligado, mas sem rede conectada")

    def test_motor_de_video_e_velocidade_medida(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Motor de vídeo"], "OpenGL ES")
        self.assertEqual(tudo["Gravação medida"], "135 MB por segundo")
        self.assertTrue(tudo["Modo do ARENA"].startswith("Econômico"))
        self.assertEqual(tudo["Velocidade medida"], "0,18× o notebook mais fraco da escola, por núcleo")
        self.assertEqual(tudo["Vulkan"], "1.1")

    def test_tela_com_varias_taxas(self):
        tela = linhas_de(p.painel(dict(LEITURA, tela_hz=90, tela_modos_hz=[60, 90]), EXTRAS))["Tela"]
        self.assertEqual(tela, "720 × 1600 pontos · 6,5 polegadas · 320 dpi · 90 Hz (a tela aceita 60, 90 Hz)")

    def test_modelo_android_e_tempo_ligado(self):
        tudo = linhas_de(p.painel(LEITURA, EXTRAS))
        self.assertEqual(tudo["Modelo"], "samsung SM-A125M (“Meu A12”)")
        self.assertEqual(tudo["Android"], "12 (API 31) · atualização de segurança de 01/10/2024")
        self.assertEqual(tudo["Ligado há"], "3 d 4 h 12 min")

    def test_velocidade_dos_nucleos_agora(self):
        linha = next(l for g in p.painel(LEITURA, EXTRAS) for l in g["linhas"] if l[0] == "Velocidade agora")
        self.assertEqual(linha[1], "1,2 GHz no mais rápido · núcleos ligados a 51% do máximo")
        self.assertEqual(linha[2]["pct"], 51)
        # nucleos desligados (frequencia 0): cada um conta contra o maximo DELE, nao contra os maiores da lista
        desligados = dict(LEITURA, nucleos_agora_mhz=[0, 0, 0, 0, 900, 900, 900, 900])
        linha = next(l for g in p.painel(desligados, EXTRAS) for l in g["linhas"] if l[0] == "Velocidade agora")
        self.assertEqual(linha[2]["pct"], 50)                             # 3600 / 7200: os de 1,8 GHz no maximo


if __name__ == "__main__":
    unittest.main()
