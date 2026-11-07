# -*- coding: utf-8 -*-
"""O celular como controle pelo cabo USB (servidor\\controle_usb.py), com um adb de mentira: nada toca em celular de verdade."""
import contextlib
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import adb_aparelho as adb  # noqa: E402
import controle_remoto as cr  # noqa: E402
import controle_usb as usb  # noqa: E402

LISTA_UM = "List of devices attached\nABC12345\tdevice product:a12 model:SM_A125M\n"
LISTA_DOIS = LISTA_UM + "XYZ98765\tdevice model:Pixel_7\n"
LISTA_SEM_PERMISSAO = "List of devices attached\nABC12345\tunauthorized\n"


class AdbDeMentira:
    def __init__(self, lista, falha_no_reverse=False):
        self.lista, self.falha, self.chamadas = lista, falha_no_reverse, []

    def executar(self, caminho, argumentos, entrada=None, tempo=15):
        self.chamadas.append(list(argumentos))
        if argumentos[:1] == ["devices"]:
            return 0, self.lista
        if "reverse" in argumentos and "--remove" not in argumentos:
            return (1, "error: closed") if self.falha else (0, "8780\n")
        return 0, "Starting: Intent { act=android.intent.action.VIEW }"


@contextlib.contextmanager
def com_adb(falso):
    with mock.patch.object(adb, "achar_adb", return_value=("adb-falso", "teste")), \
            mock.patch.object(adb, "executar", side_effect=falso.executar), \
            mock.patch.object(adb, "servidor_do_adb_de_pe", return_value=True):
        yield


class OCabo(unittest.TestCase):
    def test_um_celular_liga_o_cabo_e_abre_a_pagina_com_o_codigo_depois_do_jogato(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            r = usb.abrir_no_celular(8780, "123456", jogador=3)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["escolhido"], "ABC12345")
        reverse = next(c for c in falso.chamadas if "reverse" in c)
        self.assertEqual(reverse, ["-s", "ABC12345", "reverse", "tcp:8780", "tcp:8780"])
        abrir = next(c for c in falso.chamadas if "shell" in c)
        self.assertIn("http://127.0.0.1:8780/#c=123456&j=3", abrir[-1])      # o codigo vai depois do "#", nunca na consulta
        self.assertNotIn("?c=", abrir[-1])

    def test_dois_celulares_pedem_a_escolha(self):
        falso = AdbDeMentira(LISTA_DOIS)
        with com_adb(falso):
            r = usb.abrir_no_celular(8780, "123456")
        self.assertFalse(r["ok"])
        self.assertIn("2 celulares", r["dica"])
        self.assertFalse(any("reverse" in c for c in falso.chamadas))        # sem escolha, nada e' ligado
        with com_adb(AdbDeMentira(LISTA_DOIS)):
            self.assertTrue(usb.abrir_no_celular(8780, "123456", serial="XYZ98765")["ok"])

    def test_celular_que_nao_deixou_depuracao_explica(self):
        with com_adb(AdbDeMentira(LISTA_SEM_PERMISSAO)):
            r = usb.abrir_no_celular(8780, "123456")
        self.assertFalse(r["ok"])
        self.assertIn("Permitir", r["dica"])

    def test_sem_celular_ensina_a_ligar_a_depuracao(self):
        with com_adb(AdbDeMentira("List of devices attached\n")):
            r = usb.abrir_no_celular(8780, "123456")
        self.assertIn("Depuração USB", r["dica"])

    def test_sem_adb_diz_onde_baixar(self):
        with mock.patch.object(adb, "achar_adb", return_value=(None, None)):
            r = usb.abrir_no_celular(8780, "123456")
        self.assertIn("Platform-Tools", r["como_baixar"])

    def test_reverse_que_falha_vira_erro_em_portugues(self):
        with com_adb(AdbDeMentira(LISTA_UM, falha_no_reverse=True)):
            r = usb.abrir_no_celular(8780, "123456")
        self.assertFalse(r["ok"])
        self.assertIn("Depuração USB", r["erro"])

    def test_entrada_estranha_nao_chega_ao_shell_do_celular(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            for codigo in ("12'; rm -rf /", "12 34", "", None, "123"):
                self.assertFalse(usb.abrir_no_celular(8780, codigo)["ok"], codigo)
            self.assertFalse(usb.abrir_no_celular(8780, "123456", serial="a b; c")["ok"])
            self.assertFalse(usb.abrir_no_celular("8780; x", "123456")["ok"])
        self.assertEqual(falso.chamadas, [])


class ODesligar(unittest.TestCase):
    def test_desligar_desfaz_o_cabo(self):
        falso = AdbDeMentira(LISTA_UM)
        controle = cr.ControleRemoto()
        with com_adb(falso):
            controle.ligar()
            try:
                self.assertFalse(controle.ligar_pelo_cabo()["ok"] is False)
                self.assertEqual(len(controle.estado()["cabos"]), 1)
            finally:
                controle.desligar()
        remocao = [c for c in falso.chamadas if "--remove" in c]
        self.assertEqual(len(remocao), 1)
        self.assertEqual(remocao[0][:3], ["-s", "ABC12345", "reverse"])

    def test_sem_ligar_o_controle_nao_liga_cabo(self):
        controle = cr.ControleRemoto()
        r = controle.ligar_pelo_cabo()
        self.assertFalse(r["ok"])
        self.assertIn("Ligue", r["erro"])


class APartidaPeloCabo(unittest.TestCase):
    """Jogar Junto pelo cabo (controle_usb.ligar_partida): a partida do RetroArch e o "cheguei" vao dentro do cabo."""

    def setUp(self):
        usb._partida = None
        usb._controle_ligado = False
        usb._ligamos_o_servidor = False

    tearDown = setUp

    def test_quem_abre_a_partida_faz_reverse_das_duas_portas(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            r = usb.ligar_partida("hospedar")
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["endereco"], "127.0.0.1:18777")
        ligacoes = [c for c in falso.chamadas if "reverse" in c]
        self.assertEqual(ligacoes, [["-s", "ABC12345", "reverse", "tcp:55435", "tcp:55435"],
                                    ["-s", "ABC12345", "reverse", "tcp:18777", "tcp:8777"]])
        self.assertEqual(usb.partida_ligada(), ("ABC12345", "reverse"))

    def test_quem_entra_na_partida_do_celular_faz_forward(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            for papel in ("entrar", "assistir"):
                self.assertTrue(usb.ligar_partida(papel)["ok"])
        ligacoes = [c for c in falso.chamadas if "forward" in c and "--remove" not in c]
        self.assertEqual(ligacoes[0], ["-s", "ABC12345", "forward", "tcp:55435", "tcp:55435"])
        self.assertEqual(ligacoes[1], ["-s", "ABC12345", "forward", "tcp:18777", "tcp:8777"])
        # a segunda partida trocou a primeira: as duas portas da primeira foram tiradas antes
        remocoes = [c for c in falso.chamadas if "--remove" in c]
        self.assertEqual(remocoes, [["-s", "ABC12345", "forward", "--remove", "tcp:55435"],
                                    ["-s", "ABC12345", "forward", "--remove", "tcp:18777"]])

    def test_soltar_tira_as_duas_portas_e_so_uma_vez(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            usb.ligar_partida("hospedar")
            usb.soltar_partida()
            usb.soltar_partida()
        remocoes = [c for c in falso.chamadas if "--remove" in c]
        self.assertEqual(remocoes, [["-s", "ABC12345", "reverse", "--remove", "tcp:55435"],
                                    ["-s", "ABC12345", "reverse", "--remove", "tcp:18777"]])
        self.assertIsNone(usb.partida_ligada())

    def test_porta_ocupada_desfaz_a_metade_e_explica(self):
        class PortaOcupada(AdbDeMentira):
            def executar(self, caminho, argumentos, entrada=None, tempo=15):
                if "tcp:18777" in argumentos and "--remove" not in argumentos:
                    self.chamadas.append(list(argumentos))
                    return 1, "error: cannot bind listener: Address already in use"
                return AdbDeMentira.executar(self, caminho, argumentos, entrada, tempo)
        falso = PortaOcupada(LISTA_UM)
        with com_adb(falso):
            r = usb.ligar_partida("entrar")
        self.assertFalse(r["ok"])
        self.assertIn("ocupada", r["erro"])
        self.assertIn(["-s", "ABC12345", "forward", "--remove", "tcp:55435"], falso.chamadas)     # a primeira saiu
        self.assertIsNone(usb.partida_ligada())

    def test_papel_ou_serial_estranho_nem_chama_o_adb(self):
        falso = AdbDeMentira(LISTA_UM)
        with com_adb(falso):
            self.assertFalse(usb.ligar_partida("apagar")["ok"])
            self.assertFalse(usb.ligar_partida("hospedar", serial="a b; c")["ok"])
        self.assertEqual(falso.chamadas, [])

    def test_dois_celulares_pedem_a_escolha(self):
        falso = AdbDeMentira(LISTA_DOIS)
        with com_adb(falso):
            r = usb.ligar_partida("hospedar")
        self.assertFalse(r["ok"])
        self.assertIn("2 celulares", r["dica"])
        self.assertFalse(any("reverse" in c for c in falso.chamadas))

    def test_o_servidor_do_adb_fica_de_pe_enquanto_a_partida_usa(self):
        falso = AdbDeMentira(LISTA_UM)
        with mock.patch.object(adb, "achar_adb", return_value=("adb-falso", "teste")), \
                mock.patch.object(adb, "executar", side_effect=falso.executar), \
                mock.patch.object(adb, "servidor_do_adb_de_pe", side_effect=[False, True, True, True, True]):
            usb.ligar_partida("hospedar")                       # o ARENA ligou o servidor do adb
            self.assertTrue(usb._ligamos_o_servidor)
            usb.soltar([("ABC12345", 8780)], ultimo=True)      # o controle saiu, mas a partida segue no cabo
            self.assertNotIn(["kill-server"], falso.chamadas)
            usb.soltar_partida()                                 # agora ninguem usa: desliga
        self.assertIn(["kill-server"], falso.chamadas)
        self.assertFalse(usb._ligamos_o_servidor)


class APortaViva(unittest.TestCase):
    """arena.porta_viva: pelo cabo, quem atende e' o adb, mesmo com a partida do outro lado fechada."""

    @classmethod
    def setUpClass(cls):
        import socket
        import threading
        cls.socket, cls.threading = socket, threading

    def servidor(self, fecha_na_hora):
        escuta = self.socket.socket()
        escuta.bind(("127.0.0.1", 0))
        escuta.listen(1)
        aceitas = []

        def atender():
            conexao, _ = escuta.accept()
            if fecha_na_hora:
                conexao.close()
            else:
                aceitas.append(conexao)          # fica calado, como o RetroArch esperando o cabecalho
        self.threading.Thread(target=atender, daemon=True).start()
        self.addCleanup(lambda: [c.close() for c in aceitas])
        self.addCleanup(escuta.close)
        return escuta.getsockname()[1]

    def test_partida_escutando_vale(self):
        import arena
        self.assertTrue(arena.porta_viva("127.0.0.1", self.servidor(False), espera=0.3))

    def test_adb_que_atende_e_fecha_nao_vale(self):
        import arena
        self.assertFalse(arena.porta_viva("127.0.0.1", self.servidor(True), espera=1.0))

    def test_porta_fechada_nao_vale(self):
        import arena
        sobra = self.socket.socket()
        sobra.bind(("127.0.0.1", 0))
        porta = sobra.getsockname()[1]
        sobra.close()
        self.assertFalse(arena.porta_viva("127.0.0.1", porta))


if __name__ == "__main__":
    unittest.main()
