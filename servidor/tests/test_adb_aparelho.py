# -*- coding: utf-8 -*-
"""O celular ligado no cabo, visto pelo computador (servidor\\adb_aparelho.py,
ETAPA 1 do roteiro de 23/10/2026).

A leitura de um Galaxy A12 (Android 12) esta gravada aqui, SEM nenhum
identificador do aparelho (o numero de serie e o IMEI do "getprop" completo
entram de proposito, falsos, para provar que nunca saem). O teste de verdade,
com o celular no cabo, e' rodar servidor\\adb_aparelho.py."""
import json
import os
import random
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import adb_aparelho  # noqa: E402
import plataforma  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes"))
import limpeza  # noqa: E402

SERIAL_FALSO = "SERIAL-QUE-NAO-PODE-APARECER"
IMEI_FALSO = "490154203237518"

NUCLEOS = "".join(
    "processor\t: %d\nBogoMIPS\t: 26.00\nFeatures\t: fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid\n"
    "CPU implementer\t: 0x41\nCPU architecture: 8\nCPU variant\t: 0x0\nCPU part\t: 0xd03\nCPU revision\t: 4\n\n" % i
    for i in range(8)) + "Hardware\t: MT6765V/CB\n"

PROPS_A12 = """[ro.product.model]: [SM-A125M]
[ro.product.manufacturer]: [samsung]
[ro.product.device]: [a12]
[ro.build.version.release]: [12]
[ro.build.version.sdk]: [31]
[ro.build.version.security_patch]: [2024-10-01]
[ro.build.display.id]: [SP1A.210812.016.A125MUBS6CXJ1]
[ro.hardware]: [mt6765]
[ro.board.platform]: [mt6765]
[ro.soc.model]: [MT6765V/CB]
[ro.soc.manufacturer]: [Mediatek]
[ro.product.cpu.abilist]: [arm64-v8a,armeabi-v7a,armeabi]
[ro.product.cpu.abilist64]: [arm64-v8a]
[ro.opengles.version]: [196610]
[ro.serialno]: [%s]
[ril.imei]: [%s]
[persist.sys.device_name]: [Celular de Fulano]
""" % (SERIAL_FALSO, IMEI_FALSO)

BATERIA_A12 = """Current Battery Service state:
  AC powered: false
  USB powered: true
  Wireless powered: false
  Max charging current: 0
  Charge counter: 1405000
  status: 2
  health: 2
  present: true
  level: 28
  scale: 100
  voltage: 3711
  temperature: 337
  technology: Li-ion
  current now: -187
  charge counter: 1405000
BatteryInfoBackUp
  mSavedBatteryAsoc: 86
  mSavedBatteryMaxTemp: 580
"""

CAPACIDADE_A12 = """  Estimated battery capacity: 5000 mAh
  Last learned battery capacity: 5000 mAh
  Min learned battery capacity: 5000 mAh
  Max learned battery capacity: 5000 mAh
    Capacity: 5000, Typical: 5000, Computed drain: 8060, actual drain: 7900-8150
"""

NEGADO = "cat: %s: Permission denied"
SEM_ARQUIVO = "cat: %s: No such file or directory"


def sys_a12(extra=None):
    """Os arquivos da bateria como o A12 responde: o "battery" nega tudo."""
    linhas = []
    for no, resposta in (("battery", NEGADO), ("sm5714-fuelgauge", SEM_ARQUIVO), ("usb", NEGADO)):
        for arquivo in ("charge_counter", "charge_full_design", "charge_full", "energy_full_design",
                        "capacity", "cycle_count"):
            caminho = "/sys/class/power_supply/%s/%s" % (no, arquivo)
            linhas.append("%s|%s" % (caminho, resposta % caminho))
    texto = "\n".join(linhas)
    for caminho, valor in (extra or {}).items():
        texto = texto.replace("%s|%s" % (caminho, NEGADO % caminho), "%s|%s" % (caminho, valor))
    return texto


def saida_a12(sys_texto=None, bateria=BATERIA_A12):
    return "\n".join([
        "@@props", PROPS_A12,
        "@@meminfo", "MemTotal:        3841188 kB\nMemFree:           74828 kB\nMemAvailable:    1204756 kB\n"
                     "SwapTotal:       2097148 kB",
        "@@cpuinfo", NUCLEOS,
        "@@freq", "\n".join("/sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_max_freq %d" % (i, 2301000 if i < 4 else 1800000)
                            for i in range(8)),
        "@@bateria", bateria,
        "@@capacidade", CAPACIDADE_A12,
        "@@sys", sys_texto if sys_texto is not None else sys_a12(),
        "@@tela", "Physical size: 720x1600\nPhysical density: 300\nfps=60.0",
        "@@disco", "Filesystem            1K-blocks     Used Available Use% Mounted on\n"
                   "/dev/block/mmcblk0p49  53762032 44973124   8657836  84% /data/user/0",
        "@@kernel", "4.19.188-25461540-abA125MUBS6CXJ1\n18921.16 68392.02",
        "@@gpu", "GLES: Imagination Technologies, PowerVR Rogue GE8320, OpenGL ES 3.2 build 1.13@5776728",
        "@@recursos", "feature:android.hardware.opengles.aep\nfeature:android.hardware.vulkan.compute\n"
                      "feature:android.hardware.vulkan.version=4198400\nfeature:android.hardware.usb.host\n"
                      "feature:android.hardware.bluetooth\nfeature:android.hardware.bluetooth_le\n"
                      "feature:android.hardware.sensor.accelerometer\n"
                      "feature:android.hardware.touchscreen.multitouch.jazzhand",
        "@@fim", ""])


LISTA = """List of devices attached
R58N20ABCDE            device product:a12ub model:SM_A125M device:a12 transport_id:7
"""


def texto_do_painel(painel):
    return "\n".join("%s: %s" % (rotulo, valor) for grupo in painel for rotulo, valor in grupo["linhas"])


class Lista(unittest.TestCase):

    def test_celular_pronto(self):
        achados = adb_aparelho.interpretar_lista(LISTA)
        self.assertEqual(len(achados), 1)
        self.assertEqual((achados[0]["serial"], achados[0]["estado"], achados[0]["pronto"]),
                         ("R58N20ABCDE", "device", True))
        self.assertEqual(achados[0]["modelo"], "SM A125M")
        self.assertEqual(achados[0]["serial_curto"], "…BCDE")

    def test_estados_que_pedem_uma_acao(self):
        texto = ("* daemon not running; starting now at tcp:5037\n* daemon started successfully\n"
                 "List of devices attached\n"
                 "AAAA1111  unauthorized usb:1-2 transport_id:1\n"
                 "BBBB2222  offline\n"
                 "CCCC3333  no permissions (user in plugdev group; are your udev rules wrong?); see [http://x]\n"
                 "emulator-5554 device product:sdk_gphone64_x86_64 model:sdk_gphone64_x86_64 device:emu64xa\n")
        achados = {a["serial"]: a for a in adb_aparelho.interpretar_lista(texto)}
        self.assertEqual(set(achados), {"AAAA1111", "BBBB2222", "CCCC3333", "emulator-5554"})
        self.assertFalse(achados["AAAA1111"]["pronto"])
        self.assertIn("Permitir", achados["AAAA1111"]["estado_texto"])
        self.assertIn("cabo", achados["BBBB2222"]["estado_texto"])
        self.assertEqual(achados["CCCC3333"]["estado"], "no permissions")
        self.assertTrue(achados["emulator-5554"]["pronto"])

    def test_sem_celular_e_lixo(self):
        self.assertEqual(adb_aparelho.interpretar_lista("List of devices attached\n\n"), [])
        self.assertEqual(adb_aparelho.interpretar_lista(""), [])
        self.assertEqual(adb_aparelho.interpretar_lista(
            "error: algo\n; rm -rf /\n--help device\nadb server version (41) doesn't match this client (40); killing...\n"
            "error: cannot connect to daemon"), [])
        # modo que existe no adb mas o ARENA nao le: aparece, com a explicacao
        achados = adb_aparelho.interpretar_lista("List of devices attached\nDDDD4444  recovery\n")
        self.assertEqual((achados[0]["pronto"], achados[0]["estado"]), (False, "recovery"))
        self.assertIn("modo que o ARENA não lê", achados[0]["estado_texto"])


class LeituraDoA12(unittest.TestCase):

    def setUp(self):
        self.leitura = adb_aparelho.interpretar(saida_a12())

    def test_o_aparelho_e_o_android(self):
        a = self.leitura["aparelho"]
        self.assertEqual((a["fabricante"], a["modelo"], a["android"], a["sdk"]), ("Samsung", "SM-A125M", "12", 31))
        self.assertEqual(a["seguranca"], "2024-10-01")
        self.assertEqual(a["ligado_ha_segundos"], 18921)

    def test_o_processador_agrupa_os_nucleos_iguais(self):
        p = self.leitura["processador"]
        self.assertEqual((p["soc"], p["fabricante_do_soc"], p["nucleos"]), ("MT6765V/CB", "Mediatek", 8))
        self.assertEqual(p["grupos"], [{"nome": "Cortex-A53", "quantidade": 4, "mhz_max": 2301},
                                       {"nome": "Cortex-A53", "quantidade": 4, "mhz_max": 1800}])
        self.assertTrue(p["de_64_bits"])

    def test_memoria_disco_tela_e_video(self):
        self.assertEqual(self.leitura["memoria"]["total_mb"], 3751)
        self.assertEqual(self.leitura["armazenamento"]["usado_pct"], 84)
        self.assertEqual((self.leitura["tela"]["largura"], self.leitura["tela"]["altura"],
                          self.leitura["tela"]["dpi"], self.leitura["tela"]["hz"]), (720, 1600, 300, 60.0))
        g = self.leitura["grafico"]
        self.assertEqual((g["placa"], g["fabricante"], g["opengl_es"]),
                         ("PowerVR Rogue GE8320", "Imagination Technologies", "3.2"))
        r = self.leitura["recursos"]
        self.assertEqual(r["vulkan"], "1.1")
        self.assertTrue(r["usb_host"] and r["bluetooth"] and r["acelerometro"] and r["multitoque"])
        self.assertFalse(r["giroscopio"])

    def test_a_bateria_em_miliamperes(self):
        b = self.leitura["bateria"]
        self.assertEqual((b["nivel_pct"], b["voltagem_mv"], b["temperatura_c"]), (28, 3711, 33.7))
        self.assertEqual((b["saude"], b["tecnologia"], b["fonte"], b["carregando"]), ("boa", "Li-ion", "USB", True))
        self.assertEqual(b["carga_agora_mah"], 1405.0)
        self.assertEqual(b["capacidade_de_fabrica_mah"], 5000.0)
        self.assertEqual(b["capacidade_aprendida_mah"], 5000.0)
        self.assertEqual(b["saude_samsung_pct"], 86)
        self.assertEqual(b["capacidade_pela_conta_mah"], 5018)
        menor, maior = b["capacidade_pela_conta_faixa_mah"]
        self.assertLess(menor, 5018)
        self.assertGreater(maior, 5018)

    def test_charge_full_design_indisponivel_e_nao_inventado(self):
        b = self.leitura["bateria"]
        self.assertNotIn("capacidade_de_projeto_mah", b)
        self.assertIn("root", b["capacidade_de_projeto_motivo"])
        self.assertEqual(b["capacidade_de_fabrica_fonte"], "o perfil de energia do próprio Android")
        texto = texto_do_painel(adb_aparelho.linhas_do_painel(self.leitura))
        self.assertIn("Capacidade de projeto (charge_full_design): indisponível neste aparelho", texto)

    def test_nenhum_identificador_do_aparelho_vaza(self):
        # O getprop completo tem o numero de serie, o IMEI e o nome que a pessoa deu ao celular.
        tudo = json.dumps(self.leitura, ensure_ascii=False) + texto_do_painel(adb_aparelho.linhas_do_painel(self.leitura))
        for segredo in (SERIAL_FALSO, IMEI_FALSO, "Celular de Fulano"):
            self.assertNotIn(segredo, tudo)

    def test_sem_falhas_na_leitura_inteira(self):
        self.assertEqual(self.leitura["falhas"], [])


class ArquivoDeProjetoLegivel(unittest.TestCase):

    def test_charge_full_design_em_microamperes(self):
        caminho = "/sys/class/power_supply/battery/charge_full_design"
        leitura = adb_aparelho.interpretar(saida_a12(sys_a12({caminho: "4900000"})))
        b = leitura["bateria"]
        self.assertEqual(b["capacidade_de_projeto_mah"], 4900.0)
        self.assertEqual(b["capacidade_de_fabrica_mah"], 4900.0)
        self.assertEqual(b["capacidade_de_fabrica_fonte"], "o arquivo charge_full_design do celular")
        self.assertEqual(b["capacidade_de_projeto_arquivo"], caminho)
        texto = texto_do_painel(adb_aparelho.linhas_do_painel(leitura))
        self.assertNotIn("indisponível", texto)

    def test_charge_full_design_ja_em_miliamperes(self):
        caminho = "/sys/class/power_supply/battery/charge_full_design"
        b = adb_aparelho.interpretar(saida_a12(sys_a12({caminho: "4500"})))["bateria"]
        self.assertEqual(b["capacidade_de_projeto_mah"], 4500.0)

    def test_para_mah(self):
        self.assertEqual(adb_aparelho.para_mah(5000000), 5000.0)
        self.assertEqual(adb_aparelho.para_mah(4500), 4500.0)
        self.assertEqual(adb_aparelho.para_mah(1405000), 1405.0)
        self.assertIsNone(adb_aparelho.para_mah(None))

    def test_o_motivo_muda_quando_o_arquivo_nem_existe(self):
        so_inexistentes = "\n".join("/sys/class/power_supply/battery/%s|%s" % (f, SEM_ARQUIVO % f)
                                    for f in ("charge_full_design", "charge_counter"))
        b = adb_aparelho.interpretar(saida_a12(so_inexistentes))["bateria"]
        self.assertIn("não tem esse arquivo", b["capacidade_de_projeto_motivo"])


class FalhasIsoladas(unittest.TestCase):

    def test_so_o_modelo_responde(self):
        leitura = adb_aparelho.interpretar("@@props\n[ro.product.model]: [XYZ-1]\n[ro.product.manufacturer]: [acme]\n@@fim\n")
        self.assertEqual(leitura["aparelho"]["modelo"], "XYZ-1")
        self.assertNotIn("memoria", leitura)
        self.assertTrue(any(f.startswith("memoria") for f in leitura["falhas"]))
        self.assertTrue(any(f.startswith("tela") for f in leitura["falhas"]))

    def test_uma_leitura_quebrada_nao_derruba_as_outras(self):
        texto = saida_a12().replace("MemTotal:        3841188 kB", "MemTotal: lixo")
        leitura = adb_aparelho.interpretar(texto)
        self.assertNotIn("memoria", leitura)
        self.assertEqual(leitura["bateria"]["nivel_pct"], 28)
        self.assertEqual(leitura["processador"]["nucleos"], 8)
        self.assertEqual(len(leitura["falhas"]), 1)

    def test_celular_que_nao_respondeu_nada(self):
        for vazio in ("", "error: closed", "@@props\n@@fim"):
            with self.assertRaises(adb_aparelho.FalhaDoAdb, msg=vazio):
                adb_aparelho.interpretar(vazio)

    def test_aparelho_sem_bateria(self):
        leitura = adb_aparelho.interpretar(saida_a12(bateria="  present: false\n"))
        self.assertEqual(leitura["bateria"], {"presente": False})
        painel = adb_aparelho.linhas_do_painel(leitura)
        self.assertIn("não tem bateria", texto_do_painel(painel))

    def test_dado_de_fora_nunca_derruba(self):
        sorteio = random.Random(20261023)
        base = saida_a12()
        for _ in range(300):
            pedaco = list(base)
            for _ in range(40):
                pedaco[sorteio.randrange(len(pedaco))] = sorteio.choice("@[]:|\x00 \n9é-/")
            texto = "".join(pedaco)
            try:
                leitura = adb_aparelho.interpretar(texto)
                adb_aparelho.linhas_do_painel(leitura)
                adb_aparelho.texto_dos_caminhos(leitura)
            except adb_aparelho.FalhaDoAdb:
                pass
        enorme = "@@props\n" + ("[ro.product.model]: [x]\n" * 400000)
        adb_aparelho.interpretar(enorme)    # passa do limite de 4 MB: corta, nao trava


class TextoDoPainel(unittest.TestCase):

    def setUp(self):
        self.painel = adb_aparelho.linhas_do_painel(adb_aparelho.interpretar(saida_a12()))
        self.texto = texto_do_painel(self.painel)

    def test_os_grupos(self):
        self.assertEqual([g["titulo"] for g in self.painel],
                         ["O aparelho", "Processador e vídeo", "Memória, armazenamento e tela",
                          "Para jogar com controle", "Bateria"])

    def test_numeros_em_portugues(self):
        for esperado in ("Samsung SM-A125M", "12 (API 31) · atualização de segurança de 01/10/2024",
                         "8 núcleos: 4 × Cortex-A53 até 2,3 GHz + 4 × Cortex-A53 até 1,8 GHz",
                         "PowerVR Rogue GE8320 (Imagination Technologies)", "Vulkan: 1.1",
                         "Memória RAM: 3,7 GB (1,1 GB livres agora)", "Armazenamento: 51,3 GB (8,3 GB livres, 84% usado)",
                         "720 × 1600 pontos · 300 dpi · 60 Hz", "Nível da bateria: 28% · carregando pelo USB",
                         "Carga guardada agora: 1.405 mAh", "Capacidade de fábrica: 5.000 mAh",
                         "Voltagem: 3,711 V", "Temperatura da bateria: 33,7 °C", "Giroscópio: não tem",
                         "Ligado há: 5 h 15 min"):
            self.assertIn(esperado, self.texto)

    def test_a_conta_e_o_indice_da_samsung_dizem_que_sao_aproximados(self):
        self.assertRegex(self.texto, r"Conta: carga ÷ nível: uns 5\.018 mAh \(entre [\d.]+ e [\d.]+\), ou 100% da de fábrica\. É só uma pista")
        indice = re.search(r"Índice de saúde da Samsung \(ASOC\): ([^\n]+)", self.texto)
        self.assertIsNotNone(indice)
        self.assertIn("aproximado", indice.group(1) if indice else "")

    def test_conta_so_com_a_bateria_com_alguma_carga(self):
        vazia = BATERIA_A12.replace("level: 28", "level: 9")
        texto = texto_do_painel(adb_aparelho.linhas_do_painel(adb_aparelho.interpretar(saida_a12(bateria=vazia))))
        self.assertNotIn("Conta:", texto)

    def test_arquivos_tentados_so_os_que_interessam(self):
        leitura = adb_aparelho.interpretar(saida_a12())
        resumo, caminhos = adb_aparelho.texto_dos_caminhos(leitura)
        self.assertIn("Nenhum dos 18 arquivos testados respondeu", resumo)
        nomes = {c["caminho"].split("/")[4] for c in caminhos}
        self.assertEqual(nomes, {"battery", "sm5714-fuelgauge"})      # o "usb" fica de fora
        self.assertTrue(all(not c["ok"] for c in caminhos))

    def test_formatos(self):
        self.assertEqual(adb_aparelho.br(1234.5, 1), "1.234,5")
        self.assertEqual(adb_aparelho.br(5000), "5.000")
        self.assertEqual(adb_aparelho.tamanho(512), "512 MB")
        self.assertEqual(adb_aparelho.tamanho(3751), "3,7 GB")
        self.assertEqual(adb_aparelho.duracao(59), "0 min")
        self.assertEqual(adb_aparelho.duracao(90061), "1 d 1 h 1 min")
        self.assertEqual(adb_aparelho.data_br("2024-10-01"), "01/10/2024")
        self.assertEqual(adb_aparelho.data_br("lixo"), "lixo")


class NucleosDoProcessador(unittest.TestCase):

    def test_nome_pelo_codigo_do_linux(self):
        nome = adb_aparelho.nome_do_nucleo
        self.assertEqual(nome({"implementador": "0x41", "parte": "0xd05"}), "Cortex-A55")
        self.assertEqual(nome({"implementador": "0x41", "parte": "0xc07"}), "Cortex-A7")
        # sem chute: codigo que a tabela nao tem aparece como codigo
        self.assertEqual(nome({"implementador": "0x51", "parte": "0x801"}), "núcleo Qualcomm (0x801)")
        self.assertEqual(nome({"implementador": "0x41", "parte": "0xffff"}), "núcleo Arm (0xffff)")
        self.assertEqual(nome({"modelo": "Intel(R) Core(TM) i5"}), "Intel(R) Core(TM) i5")
        self.assertIsNone(nome({}))

    def test_big_little(self):
        nucleos = [{"implementador": "0x41", "parte": "0xd0b"}] * 2 + [{"implementador": "0x41", "parte": "0xd05"}] * 6
        frequencias = {0: 2400000, 1: 2400000, **{i: 1800000 for i in range(2, 8)}}
        grupos = adb_aparelho.agrupar_nucleos(nucleos, frequencias)
        self.assertEqual(grupos, [{"nome": "Cortex-A76", "quantidade": 2, "mhz_max": 2400},
                                  {"nome": "Cortex-A55", "quantidade": 6, "mhz_max": 1800}])

    def test_a_tabela_nao_tem_codigo_repetido_nem_mal_escrito(self):
        for codigo, nome in adb_aparelho.NUCLEOS_ARM.items():
            self.assertRegex(codigo, r"^0x[0-9a-f]{3}$")
            self.assertTrue(nome.startswith("Cortex-"))


class OndeEstaOAdb(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_adb_")

    def tearDown(self):
        limpeza.apagar_pasta(self.pasta)

    def adb_falso(self, *partes):
        caminho = os.path.join(self.pasta, *partes, adb_aparelho.NOME_DO_ADB)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "wb") as arquivo:
            arquivo.write(b"x")
        return caminho

    def test_a_ordem_de_procura(self):
        proprio = self.adb_falso("meu")
        do_arena = self.adb_falso("raiz", "platform-tools")
        ambiente = {"ARENA_ADB": proprio, "LOCALAPPDATA": "", "ANDROID_HOME": "", "ANDROID_SDK_ROOT": ""}
        with mock.patch.dict(os.environ, ambiente), mock.patch.object(adb_aparelho, "RAIZ", os.path.join(self.pasta, "raiz")), \
                mock.patch.object(adb_aparelho.shutil, "which", return_value=None):
            self.assertEqual(adb_aparelho.achar_adb(), (proprio, "a variável ARENA_ADB"))
            os.remove(proprio)
            self.assertEqual(adb_aparelho.achar_adb(), (do_arena, "a pasta platform-tools do ARENA"))
            os.remove(do_arena)
            self.assertEqual(adb_aparelho.achar_adb(), (None, None))

    def test_sdk_do_computador_e_path(self):
        sdk = self.adb_falso("sdk", "platform-tools")
        ambiente = {"ARENA_ADB": "", "LOCALAPPDATA": "", "ANDROID_HOME": os.path.join(self.pasta, "sdk"), "ANDROID_SDK_ROOT": ""}
        with mock.patch.dict(os.environ, ambiente), mock.patch.object(adb_aparelho, "RAIZ", os.path.join(self.pasta, "vazia")), \
                mock.patch.object(adb_aparelho.shutil, "which", return_value=None):
            self.assertEqual(adb_aparelho.achar_adb(), (sdk, "o Android SDK deste computador"))
        com_path = self.adb_falso("no_path")
        with mock.patch.dict(os.environ, dict(ambiente, ANDROID_HOME="")), mock.patch.object(adb_aparelho, "RAIZ", os.path.join(self.pasta, "vazia")), \
                mock.patch.object(adb_aparelho.shutil, "which", return_value=com_path):
            self.assertEqual(adb_aparelho.achar_adb(), (com_path, "o adb deste computador (PATH)"))


class ServidorDoAdb(unittest.TestCase):
    """O programa de fundo do adb so e' desligado se foi o painel que o ligou."""

    def rodar(self, de_pe):
        chamadas = []
        with mock.patch.object(adb_aparelho, "servidor_do_adb_de_pe", side_effect=de_pe), \
                mock.patch.object(adb_aparelho, "executar", side_effect=lambda _adb, args, **_k: chamadas.append(args) or (0, "")):
            with adb_aparelho.sessao("adb"):
                pass
        return chamadas

    def test_ja_estava_ligado_ninguem_mexe(self):
        self.assertEqual(self.rodar([True, True]), [])

    def test_o_painel_ligou_o_painel_desliga(self):
        self.assertEqual(self.rodar([False, True]), [["kill-server"]])

    def test_nao_ligou_nada_nao_desliga(self):
        self.assertEqual(self.rodar([False, False]), [])

    def test_desliga_ate_quando_a_leitura_da_erro(self):
        chamadas = []
        with mock.patch.object(adb_aparelho, "servidor_do_adb_de_pe", side_effect=[False, True]), \
                mock.patch.object(adb_aparelho, "executar", side_effect=lambda _adb, args, **_k: chamadas.append(args) or (0, "")):
            with self.assertRaises(ZeroDivisionError):
                with adb_aparelho.sessao("adb"):
                    raise ZeroDivisionError("a leitura deu erro")
        self.assertEqual(chamadas, [["kill-server"]])

    def test_duas_sessoes_nao_se_atropelam(self):
        dentro, maximo = [0], [0]

        def sessao_lenta():
            with adb_aparelho.sessao("adb"):
                dentro[0] += 1
                maximo[0] = max(maximo[0], dentro[0])
                threading.Event().wait(0.05)
                dentro[0] -= 1
        with mock.patch.object(adb_aparelho, "servidor_do_adb_de_pe", return_value=True):
            fios = [threading.Thread(target=sessao_lenta) for _ in range(4)]
            for fio in fios:
                fio.start()
            for fio in fios:
                fio.join(10)
        self.assertEqual(maximo[0], 1)


class Procurar(unittest.TestCase):
    """procurar() com o adb imitado: o que o aluno le em cada situacao."""

    def adb(self, lista=LISTA, leitura=None, codigo_da_leitura=0):
        self.chamadas = []

        def executar(_adb, argumentos, entrada=None, tempo=15):
            self.chamadas.append((list(argumentos), entrada))
            if argumentos[:1] == ["devices"]:
                return 0, lista
            if argumentos[2:3] == ["shell"]:
                return codigo_da_leitura, saida_a12() if leitura is None else leitura
            return 0, ""
        return [mock.patch.object(adb_aparelho, "achar_adb", return_value=("/falso/adb", "o adb de teste")),
                mock.patch.object(adb_aparelho, "servidor_do_adb_de_pe", return_value=True),
                mock.patch.object(adb_aparelho, "executar", side_effect=executar)]

    def com(self, trocas, serial=None):
        for troca in trocas:
            troca.start()
        try:
            return adb_aparelho.procurar(serial)
        finally:
            for troca in reversed(trocas):
                troca.stop()

    def test_um_celular_pronto_e_lido_sozinho(self):
        r = self.com(self.adb())
        self.assertIsNone(r["erro"])
        self.assertEqual(r["escolhido"], "R58N20ABCDE")
        self.assertEqual(r["leitura"]["bateria"]["nivel_pct"], 28)
        self.assertEqual(len(r["painel"]), 5)
        self.assertEqual(r["adb"], "o adb de teste")
        # um unico "adb shell", com o roteiro na entrada -- nada de comando montado com o serial
        leituras = [c for c in self.chamadas if c[0][2:3] == ["shell"]]
        self.assertEqual(len(leituras), 1)
        self.assertEqual(leituras[0][0], ["-s", "R58N20ABCDE", "shell"])
        self.assertEqual(leituras[0][1], adb_aparelho.SCRIPT_DE_LEITURA.encode("utf-8"))

    def test_sem_adb_explica_onde_baixar(self):
        with mock.patch.object(adb_aparelho, "achar_adb", return_value=(None, None)):
            r = adb_aparelho.procurar()
        self.assertIsNone(r["adb"])
        self.assertIn("platform-tools", r["como_baixar"])
        self.assertIn("developer.android.com/tools/releases/platform-tools", r["como_baixar"])
        self.assertEqual(r["painel"], [])

    def test_nenhum_celular_ensina_a_ligar_a_depuracao(self):
        r = self.com(self.adb(lista="List of devices attached\n\n"))
        self.assertIsNone(r["leitura"])
        self.assertIn("Depuração USB", r["dica"])
        self.assertIn("Permitir", r["dica"])

    def test_celular_esperando_permissao(self):
        r = self.com(self.adb(lista="List of devices attached\nAAAA1111  unauthorized usb:1-2\n"))
        self.assertIsNone(r["leitura"])
        self.assertIn("Permitir", r["dica"])
        self.assertFalse([c for c in self.chamadas if c[0][2:3] == ["shell"]])

    def test_dois_celulares_o_aluno_escolhe(self):
        dois = "List of devices attached\nAAAA1111  device model:A\nBBBB2222  device model:B\n"
        r = self.com(self.adb(lista=dois))
        self.assertIsNone(r["leitura"])
        self.assertEqual([a["serial"] for a in r["aparelhos"]], ["AAAA1111", "BBBB2222"])
        self.assertIn("Escolha", r["dica"])
        r = self.com(self.adb(lista=dois), serial="BBBB2222")
        self.assertEqual(r["escolhido"], "BBBB2222")
        self.assertIsNotNone(r["leitura"])

    def test_serial_que_nao_esta_no_cabo_ou_perigoso_nunca_chega_ao_adb(self):
        for serial in ("CCCC3333", "-s", "--help", "../x", "a b", "x;y", "", "$(rm)", 5, ["A"]):
            r = self.com(self.adb(), serial=serial)
            self.assertIsNone(r["leitura"], serial)
            self.assertTrue(r["erro"], serial)
            self.assertFalse([c for c in self.chamadas if c[0][2:3] == ["shell"]], serial)

    def test_celular_que_sai_do_cabo_no_meio(self):
        r = self.com(self.adb(leitura="error: closed\n", codigo_da_leitura=1))
        self.assertIsNone(r["leitura"])
        self.assertIn("parou de responder", r["erro"])
        self.assertIn("error: closed", r["erro"])

    def test_adb_que_demora_demais(self):
        trocas = self.adb()
        trocas[2] = mock.patch.object(adb_aparelho, "executar", side_effect=TimeoutError("lento"))
        r = self.com(trocas)
        self.assertIn("demorou demais", r["erro"])

    def test_adb_que_nao_abre(self):
        trocas = self.adb()
        trocas[2] = mock.patch.object(adb_aparelho, "executar", side_effect=OSError(193, "nao e' um aplicativo"))
        r = self.com(trocas)
        self.assertIn("Não consegui abrir o adb", r["erro"])


class RotaDoServidor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import arena
        cls.arena = arena
        cls.servidor = arena.Servidor(("127.0.0.1", 0), arena.Manipulador)
        cls.porta = cls.servidor.server_address[1]
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, dados, tipo="application/json", metodo="POST"):
        pedido = urllib.request.Request("http://127.0.0.1:%d/api/celular/procurar" % self.porta,
                                        data=json.dumps(dados).encode("utf-8") if dados is not None else None,
                                        headers={"Content-Type": tipo}, method=metodo)
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                return resposta.status, json.loads(resposta.read() or b"{}")
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read() or b"{}")

    def test_devolve_o_painel(self):
        pronto = {"adb": "x", "painel": [{"titulo": "T", "linhas": [["a", "b"]]}], "erro": None}
        with mock.patch.object(adb_aparelho, "procurar", return_value=pronto) as procurar:
            estado, resposta = self.pedir({"serial": "ABC123"})
        self.assertEqual(estado, 200)
        self.assertTrue(resposta["ok"])
        self.assertEqual(resposta["painel"][0]["titulo"], "T")
        procurar.assert_called_once_with("ABC123")

    def test_sem_serial_procura_o_unico(self):
        with mock.patch.object(adb_aparelho, "procurar", return_value={}) as procurar:
            self.assertEqual(self.pedir({})[0], 200)
        procurar.assert_called_once_with(None)

    def test_serial_que_nao_e_texto(self):
        with mock.patch.object(adb_aparelho, "procurar") as procurar:
            self.assertEqual(self.pedir({"serial": 5})[0], 400)
            self.assertEqual(self.pedir({"serial": ["a"]})[0], 400)
        procurar.assert_not_called()

    def test_so_post_com_json(self):
        with mock.patch.object(adb_aparelho, "procurar") as procurar:
            self.assertEqual(self.pedir({}, tipo="text/plain")[0], 415)
            self.assertNotEqual(self.pedir(None, metodo="GET")[0], 200)
        procurar.assert_not_called()

    def test_no_android_a_rota_nao_existe(self):
        import ponte_android
        with mock.patch.object(plataforma, "ANDROID", True), mock.patch.object(ponte_android, "SEGREDO", "s"), \
                mock.patch.object(adb_aparelho, "procurar") as procurar:
            pedido = urllib.request.Request("http://127.0.0.1:%d/api/celular/procurar" % self.porta, data=b"{}",
                                            headers={"Content-Type": "application/json", "Cookie": "arena_segredo=s"},
                                            method="POST")
            with self.assertRaises(urllib.error.HTTPError) as erro:
                urllib.request.urlopen(pedido, timeout=10)
        self.assertEqual(erro.exception.code, 404)
        procurar.assert_not_called()

    def test_outro_computador_da_rede_nao_chama(self):
        # Fora do ROTAS_REDE_EXTERNA: so este computador manda o ARENA ler um celular no cabo dele.
        self.assertNotIn("/api/celular/procurar", self.arena.ROTAS_REDE_EXTERNA)


class TelaEPacote(unittest.TestCase):

    RAIZ = os.path.dirname(PASTA_SERVIDOR)

    def ler(self, *partes):
        with open(os.path.join(self.RAIZ, *partes), encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_a_tela_tem_o_que_o_script_procura(self):
        html, js = self.ler("launcher", "index.html"), self.ler("launcher", "app.js")
        inicio = js.index("async function procurarCelularNoCabo")
        funcao = js[inicio:js.index("\n}\n", inicio)]
        ids = set(re.findall(r'\$\("#([A-Za-z]+)"\)', funcao)) | {"btnCelularProcurar", "listaCelularNoCabo"}
        self.assertGreaterEqual(len(ids), 8)
        for identificador in ids:
            self.assertIn('id="%s"' % identificador, html, identificador)

    def test_o_bloco_some_no_android_e_no_navegador(self):
        bloco = re.search(r'<div id="blocoCelularNoCabo"([^>]*)>', self.ler("launcher", "index.html"))
        self.assertIsNotNone(bloco)
        atributos = bloco.group(1) if bloco else ""
        self.assertIn("data-fora-do-android", atributos)
        self.assertIn("data-so-windows", atributos)

    def test_o_texto_do_servidor_entra_como_texto_nunca_como_html(self):
        js = self.ler("launcher", "app.js")
        inicio = js.index("async function procurarCelularNoCabo")
        funcao = js[inicio:js.index("\n}\n", inicio)]
        self.assertNotIn("innerHTML", funcao)
        self.assertIn("textContent", funcao)

    def test_o_pacote_conhece_o_modulo_e_o_gitignore_barra_o_adb(self):
        # (o diagnostico.py e' um script que roda ao ser importado: le-se como texto)
        self.assertIn('"servidor/adb_aparelho.py"', self.ler("servidor", "diagnostico.py"))
        self.assertIn("/platform-tools/", self.ler(".gitignore"))


if __name__ == "__main__":
    unittest.main()
