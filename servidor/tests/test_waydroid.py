# -*- coding: utf-8 -*-
"""Os jogos de Android no Linux pelo Waydroid (servidor\\waydroid.py, 13/11/2026).

O Waydroid precisa do binder no nucleo do Linux e de uma sessao Wayland: o computador de testes (Windows e o WSL dele)
nao tem nenhum dos dois. Por isso tudo aqui e' com respostas simuladas, copiadas do formato do proprio Waydroid
(tools/actions/app_manager.py e status.py, github.com/waydroid/waydroid)."""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)
import equipamentos  # noqa: E402
import jogos_pc  # noqa: E402
import waydroid  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402

LISTA = """Name: Settings
packageName: com.android.settings
categories:
\tandroid.intent.category.LAUNCHER
Name: SuperTuxKart
packageName: org.supertuxkart.stk
categories:
\tandroid.intent.category.LAUNCHER
Name: Um servico
packageName: org.exemplo.servico
categories:
\tandroid.intent.category.DEFAULT
Name: 2048
packageName: com.exemplo.jogo2048
categories:
\tandroid.intent.category.LAUNCHER
"""

STATUS_LIGADO = "Session:\tRUNNING\nContainer:\tRUNNING\nVendor type:\tMAINLINE\n"
STATUS_DESLIGADO = "Session:\tSTOPPED\nVendor type:\tMAINLINE\n"


class LerOQueOWaydroidDiz(unittest.TestCase):
    def test_lista_so_com_os_jogos_do_menu(self):
        jogos = waydroid.ler_lista(LISTA)
        self.assertEqual([j["pacote"] for j in jogos], ["com.exemplo.jogo2048", "org.supertuxkart.stk"])
        self.assertEqual(jogos[1]["nome"], "SuperTuxKart")

    def test_pacote_com_lixo_e_limpo(self):
        jogos = waydroid.ler_lista("Name: X\npackageName: com.x.y; rm -rf /\ncategories:\n")
        self.assertEqual(jogos[0]["pacote"], "com.x.yrmrf")

    def test_status(self):
        self.assertTrue(waydroid.ler_status(STATUS_LIGADO))
        self.assertFalse(waydroid.ler_status(STATUS_DESLIGADO))
        self.assertFalse(waydroid.ler_status(""))

    def test_wayland(self):
        self.assertTrue(waydroid.tem_wayland({"WAYLAND_DISPLAY": "wayland-0"}))
        self.assertTrue(waydroid.tem_wayland({"XDG_SESSION_TYPE": "wayland"}))
        self.assertFalse(waydroid.tem_wayland({"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"}))


class RoteiroDeInstalacao(unittest.TestCase):
    def _tem(self, *programas):
        return lambda nome: "/usr/bin/" + nome if nome in programas else None

    def test_ubuntu_com_o_repositorio_oficial(self):
        roteiro, motivo = waydroid.roteiro_de_instalacao({"VERSION_CODENAME": "noble"}, self._tem("apt-get"))
        self.assertEqual(motivo, "")
        self.assertIn("https://repo.waydro.id/ noble main", roteiro)
        self.assertIn("apt-get install -y waydroid", roteiro)
        self.assertIn("waydroid init -c https://ota.waydro.id/system -v https://ota.waydro.id/vendor", roteiro)
        self.assertTrue(roteiro.startswith("set -e"))

    def test_mint_usa_o_nome_do_ubuntu_de_baixo(self):
        roteiro, _ = waydroid.roteiro_de_instalacao({"VERSION_CODENAME": "wilma", "UBUNTU_CODENAME": "noble"},
                                                    self._tem("apt-get"))
        self.assertIn("repo.waydro.id/ noble main", roteiro)

    def test_nome_estranho_nunca_vai_para_o_comando(self):
        roteiro, _ = waydroid.roteiro_de_instalacao({"VERSION_CODENAME": "noble; rm -rf /"}, self._tem("apt-get"))
        self.assertNotIn("rm -rf", roteiro)
        self.assertNotIn("repo.waydro.id", roteiro)       # sem versao conhecida: so o pacote do proprio sistema
        self.assertIn("apt-get install -y waydroid", roteiro)

    def test_fedora_e_sem_instalador(self):
        roteiro, _ = waydroid.roteiro_de_instalacao({}, self._tem("dnf"))
        self.assertIn("dnf install -y waydroid", roteiro)
        roteiro, motivo = waydroid.roteiro_de_instalacao({}, self._tem())
        self.assertIsNone(roteiro)
        self.assertIn("docs.waydro.id", motivo)

    def test_pkexec_pede_a_senha(self):
        with mock.patch.object(waydroid.shutil, "which", return_value="/usr/bin/pkexec"):
            self.assertEqual(waydroid.comando_com_administrador("echo")[:3], ["/usr/bin/pkexec", "/bin/sh", "-c"])
        with mock.patch.object(waydroid.shutil, "which", return_value=None):
            self.assertIsNone(waydroid.comando_com_administrador("echo"))


class ListaGuardadaEAbrir(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_waydroid_")
        self.addCleanup(limpeza.apagar_pasta, self.raiz)

    def _rodar(self, ligado):
        def rodar(argumentos, segundos=30):
            if argumentos == ["status"]:
                return 0, STATUS_LIGADO if ligado else STATUS_DESLIGADO
            if argumentos == ["app", "list"]:
                return 0, LISTA
            return 0, ""
        return rodar

    def test_ligado_le_e_guarda_desligado_usa_a_guardada(self):
        with mock.patch.object(waydroid, "_programa", return_value="/usr/bin/waydroid"), \
                mock.patch.object(waydroid, "_rodar", side_effect=self._rodar(True)):
            self.assertEqual(len(waydroid.jogos(self.raiz)), 2)
        with mock.patch.object(waydroid, "_programa", return_value="/usr/bin/waydroid"), \
                mock.patch.object(waydroid, "_rodar", side_effect=self._rodar(False)):
            self.assertEqual(len(waydroid.jogos(self.raiz)), 2)
        with open(os.path.join(self.raiz, waydroid.ARQUIVO_DA_LISTA), encoding="utf-8") as arquivo:
            self.assertEqual(json.load(arquivo)[0]["pacote"], "com.exemplo.jogo2048")

    def test_sem_waydroid_lista_vazia(self):
        with mock.patch.object(waydroid, "_programa", return_value=None):
            self.assertEqual(waydroid.jogos(self.raiz), [])

    def test_abrir_sem_wayland_explica(self):
        with mock.patch.object(waydroid, "_programa", return_value="/usr/bin/waydroid"), \
                mock.patch.object(waydroid, "tem_wayland", return_value=False):
            aberto, frase = waydroid.abrir("org.supertuxkart.stk")
        self.assertFalse(aberto)
        self.assertIn("Wayland", frase)

    def test_abrir_liga_e_lanca_o_pacote_limpo(self):
        with mock.patch.object(waydroid, "_programa", return_value="/usr/bin/waydroid"), \
                mock.patch.object(waydroid, "tem_wayland", return_value=True), \
                mock.patch.object(waydroid, "ligar_sessao", return_value=True), \
                mock.patch.object(waydroid.subprocess, "Popen") as popen:
            aberto, _ = waydroid.abrir("org.supertuxkart.stk && reboot")
        self.assertTrue(aberto)
        self.assertEqual(popen.call_args[0][0], ["/usr/bin/waydroid", "app", "launch", "org.supertuxkart.stkreboot"])

    def test_apk_da_pasta_entra_uma_vez(self):
        pasta = os.path.join(self.raiz, waydroid.PASTA_DOS_APKS)
        os.makedirs(pasta)
        with open(os.path.join(pasta, "jogo.apk"), "wb") as arquivo:
            arquivo.write(b"PK")
        chamadas = []

        def rodar(argumentos, segundos=30):
            chamadas.append(argumentos)
            return 0, ""
        with mock.patch.object(waydroid, "_rodar", side_effect=rodar):
            self.assertEqual(waydroid.instalar_apks(self.raiz), 1)
            self.assertEqual(waydroid.instalar_apks(self.raiz), 0)
        self.assertEqual(len(chamadas), 1)
        self.assertEqual(chamadas[0][:2], ["app", "install"])


class NoEquipamentosENaLista(unittest.TestCase):
    def _item(self, situacao, jogos=()):
        with mock.patch.object(waydroid, "situacao", return_value=situacao), \
                mock.patch.object(waydroid, "jogos", return_value=list(jogos)), \
                mock.patch.object(waydroid, "tem_wayland", return_value=True):
            return equipamentos._item_do_waydroid("/x")

    def test_sem_waydroid_pede_administrador_avisando(self):
        item = self._item({"instalado": False, "preparado": False, "binder": True, "wayland": True, "pronto": False})
        self.assertEqual(item["acao"]["tipo"], "admin")
        self.assertIn("administrador", item["acao"]["aviso"])

    def test_sem_binder_diz_antes(self):
        item = self._item({"instalado": True, "preparado": True, "binder": False, "wayland": True, "pronto": False})
        self.assertEqual(item["estado"], "falta")
        self.assertIn("binder", item["detalhe"])

    def test_pronto_conta_os_jogos(self):
        item = self._item({"instalado": True, "preparado": True, "binder": True, "wayland": True, "pronto": True},
                          [{"pacote": "a.b", "nome": "A"}])
        self.assertEqual(item["estado"], "pronto")
        self.assertIn("1 jogos", item["detalhe"])

    def test_lista_do_arena_no_linux(self):
        plataforma = {"id": "android", "nome": "Jogos de Android"}
        with mock.patch.object(jogos_pc.plataforma_do_sistema, "ANDROID", False), \
                mock.patch.object(waydroid, "pronto", return_value=True), \
                mock.patch.object(waydroid, "jogos", return_value=[{"pacote": "org.supertuxkart.stk",
                                                                    "nome": "SuperTuxKart"}]):
            entradas = jogos_pc.entradas_do_aparelho(plataforma)
        self.assertEqual(entradas[0]["arquivo"], "android://org.supertuxkart.stk")
        self.assertEqual(entradas[0]["origem_rotulo"], "No Android deste Linux")

    def test_no_windows_nada(self):
        with mock.patch.object(waydroid, "_programa", return_value=None), \
                mock.patch.object(waydroid.plataforma_do_sistema, "LINUX", False):
            self.assertFalse(waydroid.pronto())


if __name__ == "__main__":
    unittest.main()
