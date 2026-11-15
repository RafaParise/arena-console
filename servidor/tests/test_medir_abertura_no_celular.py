# -*- coding: utf-8 -*-
"""Testes do ferramentas/medir_abertura_no_celular.py, só das funções que leem texto (sem celular nenhum).

Os textos de exemplo imitam o que o Galaxy A12 devolve (logcat em threadtime, ps -A, /proc/net/tcp e o
dumpsys activity services), com números inventados.
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import medir_abertura_no_celular as medir  # noqa: E402

LOGCAT = """--------- beginning of main
11-14 14:05:52.393  1265  5704 I ActivityTaskManager: START u0 {act=android.intent.action.MAIN cmp=org.fossify.clock/.activities.SplashActivity} from uid 10050
11-14 14:30:01.100  1265  1318 I ActivityTaskManager: START u0 {flg=0x10000000 cmp=io.github.rafaparise.arena/.ArenaActivity} from uid 2000
11-14 14:30:02.000 27746 27746 I ARENA   : Canvas2D: Multiple readback operations using getImageData are faster
11-14 14:30:03.350 27746 27746 I ARENA   : [ARENA] lista na tela (guardada pelo nativo), 1687 ms depois de a pagina comecar a carregar (http://127.0.0.1:8777/app.js:7771)
"""

PS = """USER           PID  PPID     VSZ    RSS WCHAN            ADDR S NAME
root             1     0 12345678  9000 0                   0 S init
u0_a337      27746   651 31837960 79740 0                   0 S io.github.rafaparise.arena:tela
u0_a337      27831 27746    4972      0 0                   0 S libarenanativo.so
u0_a337      27837 27831 2445668   5640 0                   0 S libarenapython.so
u0_a50        3000   651 1000000  2000 0                   0 S com.outro.app
"""

TCP = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   2: 0100007F:9CDF 00000000:0000 0A 00000000:00000000 00:00000000 00000000 10337        0 72279842 1 0000000000000000 100 0 0 10 0
   3: 0100007F:2249 0100007F:9D00 01 00000000:00000000 00:00000000 00000000 10337        0 72279843 1 0000000000000000 100 0 0 10 0
   4: 00000000:1F90 00000000:0000 0A 00000000:00000000 00:00000000 00000000 10050        0 72279844 1 0000000000000000 100 0 0 10 0
"""

TCP_REDE = TCP + "   5: 00000000:2249 00000000:0000 0A 00000000:00000000 00:00000000 00000000 10337        0 72285025 1 0 100 0 0 10 0\n"

DUMPSYS = """ACTIVITY MANAGER SERVICES (dumpsys activity services)
  User 0 active services:
  * ServiceRecord{4d63e8a u0 io.github.rafaparise.arena/org.chromium.content.app.SandboxedProcessService0:0}
    isForeground=false foregroundId=0
  * ServiceRecord{58a0dfc u0 io.github.rafaparise.arena/.ArenaServico}
    intent={cmp=io.github.rafaparise.arena/.ArenaServico}
    isForeground=true foregroundId=1 foregroundNoti=Notification(channel=arena)
"""


class TestLogcat(unittest.TestCase):
    def test_mede_do_start_ate_a_lista(self):
        medida = medir.medir_no_logcat(LOGCAT)
        self.assertEqual(medida["ms"], 2250)
        self.assertEqual(medida["ms_da_pagina"], 1687)
        self.assertTrue(medida["guardada_pelo_nativo"])

    def test_start_de_outro_app_nao_conta(self):
        so_do_relogio = LOGCAT.splitlines()[1] + "\n" + LOGCAT.splitlines()[4]
        self.assertIsNone(medir.medir_no_logcat(so_do_relogio))

    def test_sem_a_lista_nao_mede(self):
        self.assertIsNone(medir.medir_no_logcat("\n".join(LOGCAT.splitlines()[:3])))

    def test_vale_o_ultimo_start_e_atividade_com_nome_inteiro(self):
        texto = LOGCAT.replace("11-14 14:30:02.000", "11-14 14:30:02.000  1265  1318 I ActivityTaskManager: START u0 "
                               "{cmp=io.github.rafaparise.arena/io.github.rafaparise.arena.ArenaActivity}\n"
                               "11-14 14:30:02.000", 1)
        medida = medir.medir_no_logcat(texto)
        self.assertEqual(medida["ms"], 1350)

    def test_virada_do_ano(self):
        texto = ("12-31 23:59:59.500  1265  1318 I ActivityTaskManager: START u0 {cmp=io.github.rafaparise.arena/"
                 ".ArenaActivity} from uid 2000\n"
                 "01-01 00:00:01.000 27746 27746 I ARENA   : [ARENA] lista na tela, 900 ms depois de a pagina comecar\n")
        medida = medir.medir_no_logcat(texto)
        self.assertEqual(medida["ms"], 1500)
        self.assertFalse(medida["guardada_pelo_nativo"])

    def test_linha_fora_do_formato(self):
        self.assertIsNone(medir.ler_linha("--------- beginning of main"))
        self.assertEqual(medir.ler_linha(LOGCAT.splitlines()[3])["etiqueta"], "ARENA")


class TestProcessos(unittest.TestCase):
    def test_ps_e_os_processos_do_arena(self):
        processos = medir.ler_ps(PS)
        self.assertEqual(len(processos), 5)                         # sem o cabeçalho
        nomes = [p["nome"] for p in medir.processos_do_arena(processos)]
        self.assertEqual(nomes, ["io.github.rafaparise.arena:tela", "libarenanativo.so", "libarenapython.so"])

    def test_uid_do_usuario(self):
        self.assertEqual(medir.uid_do_usuario("u0_a337"), 10337)
        self.assertEqual(medir.uid_do_usuario("u10_a5"), 1010005)
        self.assertEqual(medir.uid_do_usuario("10337"), 10337)
        self.assertIsNone(medir.uid_do_usuario("root"))


class TestEscutas(unittest.TestCase):
    def test_so_local(self):
        portas = medir.escutas(TCP, 10337)
        self.assertEqual(portas, [{"porta": 40159, "endereco": "0100007F", "so_do_aparelho": True}])  # a conexão (01) não conta

    def test_aberta_para_a_rede(self):
        portas = medir.escutas(TCP_REDE, 10337)
        self.assertEqual([p["porta"] for p in portas], [40159, 8777])
        self.assertFalse(all(p["so_do_aparelho"] for p in portas))

    def test_tcp6_do_loopback(self):
        linha = ("   0: 0000000000000000FFFF00000100007F:2249 00000000000000000000000000000000:0000 0A 00000000:00000000 "
                 "00:00000000 00000000 10337        0 1 1 0 100 0 0 10 0\n")
        self.assertTrue(medir.escutas(linha, 10337)[0]["so_do_aparelho"])


class TestServicoFalhasMediana(unittest.TestCase):
    def test_servico_em_primeiro_plano(self):
        self.assertTrue(medir.servico_em_primeiro_plano(DUMPSYS))
        self.assertFalse(medir.servico_em_primeiro_plano(DUMPSYS.replace("isForeground=true", "isForeground=false")))
        self.assertIsNone(medir.servico_em_primeiro_plano(DUMPSYS.split("  * ServiceRecord{58a0dfc")[0]))

    def test_falhas(self):
        texto = ("11-14 14:31:00.000  4000  4000 E AndroidRuntime: FATAL EXCEPTION: main\n"
                 "11-14 14:31:00.000  4000  4000 E AndroidRuntime: Process: com.dti.samsung, PID: 4000\n"
                 "11-14 14:31:05.000 27746 27746 E AndroidRuntime: FATAL EXCEPTION: main\n"
                 "11-14 14:31:05.000 27746 27746 E AndroidRuntime: Process: io.github.rafaparise.arena:tela, PID: 27746\n")
        falhas = medir.falhas_do_crash(texto)
        self.assertEqual(len(falhas["do_arena"]), 1)
        self.assertEqual(falhas["de_outros_apps"], {"com.dti.samsung": 1})
        self.assertEqual(medir.falhas_do_crash(""), {"do_arena": [], "de_outros_apps": {}})

    def test_mediana_e_pior(self):
        self.assertEqual(medir.resumo_dos_tempos([3000, 1000, 2000]), {"mediana_ms": 2000, "pior_ms": 3000})
        self.assertEqual(medir.resumo_dos_tempos([1000, 2000]), {"mediana_ms": 1500, "pior_ms": 2000})
        self.assertEqual(medir.resumo_dos_tempos([]), {"mediana_ms": None, "pior_ms": None})


if __name__ == "__main__":
    unittest.main()
