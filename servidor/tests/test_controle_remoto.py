# -*- coding: utf-8 -*-
"""O celular como controle (servidor\\controle_remoto.py): o WebSocket, o codigo, o estado dos botoes, o datagrama do
Network RetroPad, e o que acontece quando o celular some. A conversa com o servidor e' de verdade (soquetes em
127.0.0.1, pelo "celular de mentira" de testes\\cliente_controle.py); so o UDP do RetroArch e' trocado por uma lista."""
import os
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
for pasta in (PASTA_SERVIDOR, os.path.join(RAIZ, "testes")):
    if pasta not in sys.path:
        sys.path.insert(0, pasta)

import cliente_controle as cc  # noqa: E402
import controle_remoto as cr  # noqa: E402
import limpeza  # noqa: E402


def esperar(condicao, segundos=3.0):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        if condicao():
            return True
        time.sleep(0.01)
    return condicao()


def quadro_do_cliente(opcode, dados=b"", **opcoes):
    """Um quadro mascarado de verdade, como o navegador manda."""
    return cc.ClienteDeControle.quadro(None, opcode, dados, **opcoes)


class OWebSocketPorDentro(unittest.TestCase):

    def test_a_chave_de_aceite_do_exemplo_da_rfc(self):
        # RFC 6455, 1.3: este par de valores esta no proprio texto da norma
        self.assertEqual(cr.chave_de_aceite("dGhlIHNhbXBsZSBub25jZQ=="), "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")

    def test_chave_valida(self):
        self.assertTrue(cr.chave_valida("dGhlIHNhbXBsZSBub25jZQ=="))
        self.assertFalse(cr.chave_valida("curta"))
        self.assertFalse(cr.chave_valida("!" * 24))
        self.assertFalse(cr.chave_valida(""))

    def test_quadros_de_todos_os_tamanhos(self):
        base = bytes(range(256)) * 17                      # 4352 bytes
        for n in (0, 5, 125, 126, 1000, 4096):
            buffer = bytearray(quadro_do_cliente(0x2, base[:n]))
            self.assertEqual(cr.extrair_quadro(buffer), (0x2, base[:n]))
            self.assertEqual(len(buffer), 0)

    def test_quadro_incompleto_espera_o_resto_sem_perder_nada(self):
        inteiro = quadro_do_cliente(0x2, b"abcdefghij")
        buffer = bytearray()
        for i in range(len(inteiro) - 1):
            buffer.append(inteiro[i])
            self.assertIsNone(cr.extrair_quadro(buffer))
            self.assertEqual(len(buffer), i + 1)         # nada foi tirado
        buffer.append(inteiro[-1])
        self.assertEqual(cr.extrair_quadro(buffer), (0x2, b"abcdefghij"))

    def test_dois_quadros_colados(self):
        buffer = bytearray(quadro_do_cliente(0x1, b"um") + quadro_do_cliente(0x2, b"dois") + quadro_do_cliente(0x9)[:1])
        self.assertEqual(cr.extrair_quadro(buffer), (0x1, b"um"))
        self.assertEqual(cr.extrair_quadro(buffer), (0x2, b"dois"))
        self.assertIsNone(cr.extrair_quadro(buffer))

    def test_o_que_quebra_o_protocolo(self):
        casos = [
            ("sem mascara", quadro_do_cliente(0x2, b"x", mascarar=False), 1002),
            ("bits reservados", quadro_do_cliente(0x2, b"x", reservado=0x40), 1002),
            ("em pedacos", quadro_do_cliente(0x2, b"x", fim=False), 1003),
            ("continuacao solta", quadro_do_cliente(0x0, b"x"), 1003),
            ("tipo desconhecido", quadro_do_cliente(0x3, b"x"), 1003),
            ("controle grande demais", quadro_do_cliente(0x9, b"x" * 126), 1002),
            ("grande demais", quadro_do_cliente(0x2, b"x" * (cr.TAMANHO_MAXIMO_DO_QUADRO + 1)), 1009),
        ]
        for nome, bruto, codigo in casos:
            with self.subTest(nome):
                with self.assertRaises(cr.ErroDeProtocolo) as dentro:
                    cr.extrair_quadro(bytearray(bruto))
                self.assertEqual(dentro.exception.codigo, codigo)

    def test_o_servidor_manda_quadros_sem_mascara(self):
        self.assertEqual(cr.montar_quadro(0x1, b"oi"), b"\x81\x02oi")
        self.assertEqual(cr.montar_quadro(0x2, b"x" * 200)[:4], b"\x82\x7e\x00\xc8")


class OEstadoDosBotoes(unittest.TestCase):

    def test_ida_e_volta(self):
        dados = cr.codificar_estado(0b1010000000000101, [-32768, 32767, 0, -1])
        self.assertEqual(len(dados), 11)
        self.assertEqual(cr.decodificar_estado(dados), (0b1010000000000101, [-32768, 32767, 0, -1]))

    def test_estado_torto_nao_vale(self):
        self.assertIsNone(cr.decodificar_estado(b"\x01\x00"))
        self.assertIsNone(cr.decodificar_estado(b"\x02" + bytes(10)))

    def test_eixo_fora_da_faixa_e_cortado(self):
        self.assertEqual(cr.decodificar_estado(cr.codificar_estado(0, [99999, -99999, 0, 0]))[1], [32767, -32768, 0, 0])

    def test_o_datagrama_do_retroarch_tem_20_bytes(self):
        # struct remote_message { int port; int device; int index; int id; uint16_t state; } (+2 de enchimento)
        pacote = cr.pacote_do_retropad(55401, cr.DISPOSITIVO_JOYPAD, 0, 8, 1)
        self.assertEqual(len(pacote), 20)
        self.assertEqual(struct.unpack("<iiiiH", pacote[:18]), (55401, 1, 0, 8, 1))

    def test_eixo_negativo_vai_como_16_bits_sem_sinal(self):
        pacote = cr.pacote_do_retropad(55400, cr.DISPOSITIVO_ANALOGICO, 1, 0, -2)
        self.assertEqual(struct.unpack("<iiiiH", pacote[:18])[4], 0xFFFE)


def lido(mandados):
    """[(jogador, dados)] -> [(jogador, dispositivo, indice, id, valor, porta)]."""
    saida = []
    for jogador, dados in mandados:
        porta, dispositivo, indice, identificador, valor = struct.unpack("<iiiiH", dados[:18])
        saida.append((jogador, dispositivo, indice, identificador, valor, porta))
    return saida


class OEnviadorDoRetroPad(unittest.TestCase):

    def novo(self, base=56000):
        return cr.EnviadorRetroPad(enviar=lambda dados, porta: None, porta_base=base)

    def test_um_datagrama_por_jogador_por_quadro(self):
        e = self.novo()
        e.definir(1, 0b101, [0, 0, 0, 0])             # dois botoes: ids 0 e 2
        e.definir(2, 0b10, [0, 0, 0, 0])
        primeiro = lido(e.passo())
        self.assertEqual(len(primeiro), 2)            # um de cada jogador, nao dois do mesmo
        segundo = lido(e.passo())
        self.assertEqual([(j, i) for j, _d, _x, i, _v, _p in primeiro], [(1, 0), (2, 1)])
        self.assertEqual([(j, i) for j, _d, _x, i, _v, _p in segundo], [(1, 2)])
        self.assertEqual(e.passo(), [])               # acabou: nada de repetir sem necessidade

    def test_a_porta_e_a_base_mais_o_jogador(self):
        e = self.novo(56100)
        e.definir(3, 1, [0, 0, 0, 0])
        self.assertEqual(lido(e.passo())[0][5], 56102)

    def test_aperta_e_solta_antes_de_sair_nao_manda_nada(self):
        e = self.novo()
        e.definir(1, 0b1, [0, 0, 0, 0])
        e.definir(1, 0, [0, 0, 0, 0])
        self.assertEqual(e.passo(), [])

    def test_o_mesmo_eixo_vira_um_datagrama_com_o_valor_mais_novo(self):
        e = self.novo()
        e.definir(1, 0, [1000, 0, 0, 0])
        e.definir(1, 0, [2000, 0, 0, 0])
        e.definir(1, 0, [5000, 0, 0, 0])
        mandados = lido(e.passo())
        self.assertEqual(len(mandados), 1)
        self.assertEqual(mandados[0][1:5], (cr.DISPOSITIVO_ANALOGICO, 0, 0, 5000))
        self.assertEqual(e.passo(), [])

    def test_eixo_da_direita_vai_no_indice_1(self):
        e = self.novo()
        e.definir(1, 0, [0, 0, 0, -3000])             # ry
        self.assertEqual(lido(e.passo())[0][1:5], (cr.DISPOSITIVO_ANALOGICO, 1, 1, (-3000) & 0xFFFF))

    def test_tremida_pequena_do_dedo_nao_gasta_datagrama(self):
        e = self.novo()
        e.definir(1, 0, [10000, 0, 0, 0])
        e.passo()
        e.definir(1, 0, [10000 + cr.ZONA_DO_ANALOGICO - 1, 0, 0, 0])
        self.assertEqual(e.passo(), [])
        e.definir(1, 0, [100, 0, 0, 0])              # saiu de verdade
        self.assertEqual(len(e.passo()), 1)

    def test_voltar_ao_zero_sempre_vale(self):
        e = self.novo()
        e.definir(1, 0, [100, 0, 0, 0])               # menor que a zona: nem sai
        self.assertEqual(e.passo(), [])
        e.definir(1, 0, [9000, 0, 0, 0])
        e.passo()
        e.definir(1, 0, [0, 0, 0, 0])
        self.assertEqual(lido(e.passo())[0][4], 0)

    def test_zerar_solta_o_que_estava_apertado_e_varre_todos_os_controles(self):
        e = self.novo()
        e.definir(1, 0b100100, [7000, 0, 0, 0])       # ids 2 e 5 e um eixo
        for _ in range(3):
            e.passo()
        e.zerar(1)
        vistos = []
        for _ in range(cr.CONTROLES + 5):
            vistos += lido(e.passo())
        # os que estavam ligados saem primeiro, com valor zero; depois a varredura cobre os 20 controles
        self.assertEqual({v[4] for v in vistos}, {0})
        controles = {(v[1], v[2], v[3]) for v in vistos}
        self.assertEqual(len(controles), cr.CONTROLES)
        self.assertEqual(e.passo(), [])

    def test_com_celular_ligado_a_fila_vazia_repete_um_controle_de_vez_em_quando(self):
        e = self.novo()
        e.ativar(1)
        mandados = []
        for _ in range(cr.RESSINCRONIZAR_A_CADA * 3):
            mandados += lido(e.passo())
        self.assertEqual(len(mandados), 3)             # um a cada RESSINCRONIZAR_A_CADA quadros, nunca uma enxurrada
        self.assertEqual([m[3] for m in mandados], [0, 1, 2])
        e.ativar(1, False)
        self.assertEqual([e.passo() for _ in range(40)], [[]] * 40)

    def test_o_relogio_para_quando_nao_ha_nada_a_fazer(self):
        e = cr.EnviadorRetroPad(enviar=lambda d, p: None)
        e.iniciar()
        try:
            self.assertFalse(e.ocupado())
            e.ativar(2)
            self.assertTrue(e.ocupado())
        finally:
            e.parar()

    def test_o_relogio_manda_pelo_enviar_injetado(self):
        recebidos = []
        e = cr.EnviadorRetroPad(enviar=lambda dados, porta: recebidos.append((dados, porta)), porta_base=57000)
        e.iniciar()
        try:
            e.definir(2, 1 << 8, [0, 0, 0, 0])          # o botao A
            self.assertTrue(esperar(lambda: recebidos))
            dados, porta = recebidos[0]
            self.assertEqual(porta, 57001)
            self.assertEqual(struct.unpack("<iiiiH", dados[:18]), (57001, 1, 0, 8, 1))
        finally:
            e.parar()


class QuemPodeEntrar(unittest.TestCase):

    def test_so_a_rede_local(self):
        for ok in ("127.0.0.1", "10.0.0.7", "172.16.4.2", "172.31.255.1", "192.168.0.10", "169.254.3.4", "::1",
                   "::ffff:192.168.1.5", "fe80::1%eth0"):
            self.assertTrue(cr.rede_privada(ok), ok)
        for fora in ("8.8.8.8", "172.32.0.1", "200.10.20.30", "2606:4700:4700::1111", "abc", ""):
            self.assertFalse(cr.rede_privada(fora), fora)

    def test_origem_e_host(self):
        meus = {"192.168.0.5:8780", "127.0.0.1:8780"}
        self.assertTrue(cr.origem_confiavel("http://192.168.0.5:8780", "192.168.0.5:8780", meus))
        self.assertTrue(cr.origem_confiavel(None, "192.168.0.5:8780", meus))      # sem Origin: nao e' navegador
        self.assertFalse(cr.origem_confiavel("http://site-do-mal.example", "192.168.0.5:8780", meus))
        self.assertFalse(cr.origem_confiavel("http://192.168.0.5:9999", "192.168.0.5:8780", meus))
        self.assertFalse(cr.origem_confiavel("null", "192.168.0.5:8780", meus))
        self.assertFalse(cr.origem_confiavel("ftp://192.168.0.5:8780", "192.168.0.5:8780", meus))

    def test_dns_rebinding_o_nome_do_site_nao_esta_na_lista(self):
        # O site mal intencionado faz "evil.example" apontar para o IP do computador: o navegador manda Origin e Host
        # IGUAIS (os dois com o nome do site). So comparar um com o outro deixaria passar; a lista fechada nao.
        meus = {"192.168.0.5:8780", "127.0.0.1:8780"}
        self.assertFalse(cr.origem_confiavel("http://evil.example:8780", "evil.example:8780", meus))
        self.assertFalse(cr.origem_confiavel(None, "evil.example:8780", meus))
        self.assertFalse(cr.origem_confiavel(None, "", meus))
        self.assertFalse(cr.origem_confiavel(None, None, meus))

    def test_codigo_com_os_digitos_pedidos(self):
        for _ in range(50):
            codigo = cr.codigo_novo()
            self.assertEqual(len(codigo), cr.DIGITOS_DO_CODIGO)
            self.assertTrue(codigo.isdigit())

    def test_as_chaves_do_retroarch(self):
        chaves = cr.opcoes_do_retroarch(55400)
        self.assertEqual(chaves["network_remote_enable"], "true")
        self.assertEqual(chaves["network_remote_base_port"], "55400")
        self.assertEqual([n for n in chaves if n.startswith("network_remote_enable_user_p")],
                         ["network_remote_enable_user_p%d" % i for i in range(1, cr.JOGADORES + 1)])
        self.assertTrue(all(chaves["network_remote_enable_user_p%d" % i] == "true" for i in range(1, cr.JOGADORES + 1)))

    def test_so_os_jogadores_pedidos_abrem_no_retroarch(self):
        chaves = cr.opcoes_do_retroarch(55400, [2, 4])
        self.assertEqual([chaves["network_remote_enable_user_p%d" % i] for i in range(1, 5)],
                         ["false", "true", "false", "true"])

    def test_porta_base_livre_deixa_as_quatro_portas_soltas(self):
        import socket as sk
        base = cr.porta_base_livre()
        for n in range(cr.JOGADORES):
            with sk.socket(sk.AF_INET, sk.SOCK_DGRAM) as s:
                s.bind(("127.0.0.1", base + n))


class OServicoPorDentro(unittest.TestCase):
    """O servidor de verdade, na porta que o sistema escolher, com o UDP trocado por uma lista."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="arena_ctl_")
        for nome, texto in (("index.html", "<h1>controle</h1>"), ("controle.js", "var x=1;"), ("controle.css", "b{}")):
            with open(os.path.join(self.pasta, nome), "w", encoding="utf-8") as f:
                f.write(texto)
        self.udp = []
        self.enviador = cr.EnviadorRetroPad(enviar=lambda dados, porta: self.udp.append((dados, porta)), porta_base=58000)
        self.controle = cr.ControleRemoto(enviador=self.enviador, enderecos=lambda: ["127.0.0.1"],
                                          pasta_da_pagina=self.pasta, porta=0)
        self.estado = self.controle.ligar()
        self.porta = self.estado["porta_da_pagina"]
        self.codigo = self.estado["codigo"]
        self.abertos = []

    def tearDown(self):
        for c in self.abertos:
            c.fechar()
        self.controle.desligar()
        self.enviador.parar()
        limpeza.apagar_pasta(self.pasta)

    def celular(self, **opcoes):
        c = cc.ClienteDeControle(porta=self.porta, **opcoes)
        self.abertos.append(c)
        return c

    def entrar(self, jogador=2, codigo=None, apelido="Ana"):
        c = self.celular()
        c.enviar_texto('{"t":"oi","codigo":"%s","jogador":%d,"apelido":"%s"}' % (codigo or self.codigo, jogador, apelido))
        return c, c.receber(3.0)

    def udp_lido(self):
        return lido([(0, d) for d, _p in list(self.udp)])

    # -- a pagina ---------------------------------------------------------------------------------
    def test_ligado_mostra_o_endereco_e_o_codigo(self):
        self.assertTrue(self.estado["ligado"])
        self.assertEqual(len(self.codigo), cr.DIGITOS_DO_CODIGO)
        self.assertEqual(self.estado["enderecos"], ["http://127.0.0.1:%d/" % self.porta])

    def test_so_a_pagina_do_controle(self):
        import http.client
        for caminho, status in (("/", 200), ("/controle.js", 200), ("/controle.css", 200), ("/api/estado", 404),
                                ("/../servidor/arena.py", 404), ("/index.html", 200), ("/ws", 400)):
            conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
            conexao.request("GET", caminho)
            resposta = conexao.getresponse()
            resposta.read()
            self.assertEqual(resposta.status, status, caminho)
            if status == 200:
                self.assertEqual(resposta.getheader("X-Content-Type-Options"), "nosniff")
                self.assertIn("frame-ancestors 'none'", resposta.getheader("Content-Security-Policy"))
            conexao.close()

    def test_post_nao_existe(self):
        import http.client
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        conexao.request("POST", "/api/config", body=b"{}", headers={"Content-Type": "application/json"})
        self.assertEqual(conexao.getresponse().status, 405)
        conexao.close()

    # -- o aperto de mao e o codigo ---------------------------------------------------------------
    def test_o_aperto_de_mao_responde_com_a_chave_certa(self):
        c = self.celular(chave="dGhlIHNhbXBsZSBub25jZQ==")
        self.assertIn("s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", c.cabecas_da_resposta)

    def test_site_de_outra_origem_e_recusado(self):
        with self.assertRaises(cc.RecusouAConexao) as dentro:
            cc.ClienteDeControle(porta=self.porta, origem="http://site-do-mal.example")
        self.assertIn("403", str(dentro.exception))

    def test_codigo_certo_entra_e_aparece_na_lista(self):
        c, resposta = self.entrar(jogador=3, apelido="Bia")
        self.assertEqual(resposta[0], 0x1)
        self.assertIn(b'"ok"', resposta[1])
        self.assertTrue(esperar(lambda: self.controle.estado()["conectados"]))
        item = self.controle.estado()["conectados"][0]
        self.assertEqual((item["jogador"], item["apelido"]), (3, "Bia"))

    def test_codigo_errado_nao_entra(self):
        errado = "0000" if self.codigo != "0000" else "1111"
        c, resposta = self.entrar(codigo=errado)
        self.assertIn(b'"codigo"', resposta[1])
        self.assertEqual(self.controle.estado()["conectados"], [])

    def test_cinco_erros_bloqueiam_ate_o_codigo_certo(self):
        errado = "0000" if self.codigo != "0000" else "1111"
        for _ in range(cr.ERROS_ANTES_DO_BLOQUEIO):
            self.entrar(codigo=errado)
        _c, resposta = self.entrar()                 # agora com o codigo CERTO
        self.assertIn(b'"bloqueado"', resposta[1])

    def test_bloqueio_acaba(self):
        for i in range(cr.ERROS_ANTES_DO_BLOQUEIO):
            self.controle.conferir_o_codigo("10.0.0.9", "x", agora=1000.0 + i)
        self.assertEqual(self.controle.conferir_o_codigo("10.0.0.9", self.codigo, agora=1100.0)[:2], (False, "bloqueado"))
        self.assertEqual(self.controle.conferir_o_codigo("10.0.0.9", self.codigo, agora=1000.0 + cr.BLOQUEIO_S + 10)[0], True)
        # outro endereco nao foi bloqueado
        self.assertTrue(self.controle.conferir_o_codigo("10.0.0.10", self.codigo, agora=1100.0)[0])

    def test_muitos_erros_no_total_trocam_o_codigo(self):
        passo = cr.JANELA_GLOBAL_S + 1                         # devagar o bastante para nao esbarrar no limite global
        for i in range(cr.ERROS_ANTES_DE_TROCAR_O_CODIGO - 1):
            self.controle.conferir_o_codigo("10.1.%d.1" % i, "nada", agora=2000.0 + i * passo)    # cada um de um endereco
        self.assertEqual(self.controle._erros_no_total, cr.ERROS_ANTES_DE_TROCAR_O_CODIGO - 1)
        with mock.patch.object(cr, "codigo_novo", return_value="424242"):
            self.controle.conferir_o_codigo("10.1.99.1", "nada", agora=2000.0 + 30 * passo)
        self.assertEqual(self.controle.codigo, "424242")                  # o codigo que o tentador tinha nao vale mais
        self.assertEqual(self.controle._erros_no_total, 0)

    def test_limite_global_segura_so_quem_ja_errou(self):
        # O atacante troca de endereco a cada tentativa: o bloqueio por endereco nunca dispara.
        for i in range(cr.TENTATIVAS_POR_JANELA):
            r = self.controle.conferir_o_codigo("10.2.%d.1" % i, "nada", agora=3000.0 + i * 0.1)
            self.assertEqual(r[1], "codigo")
        # Passou do limite: quem ja errou espera a janela passar...
        self.assertEqual(self.controle.conferir_o_codigo("10.2.0.1", "nada", agora=3002.0)[:2], (False, "muitas"))
        self.assertEqual(self.controle.conferir_o_codigo("10.2.0.1", self.codigo, agora=3002.0)[:2], (False, "muitas"))
        # ...mas o celular que ainda nao errou entra com o codigo certo, mesmo no meio do despejo (achado da revisao de
        # seguranca: o limite global antigo contava TODAS as tentativas e deixava um atacante trancar a porta de todos).
        self.assertEqual(self.controle.conferir_o_codigo("10.3.0.1", self.codigo, agora=3002.0)[:2], (True, ""))
        # O despejo continua custando um erro por endereco novo: o codigo troca a cada ERROS_ANTES_DE_TROCAR_O_CODIGO.
        self.assertEqual(self.controle.conferir_o_codigo("10.3.0.2", "nada", agora=3002.0)[:2], (False, "codigo"))
        # Passada a janela, quem errou volta a poder tentar.
        self.assertEqual(self.controle.conferir_o_codigo("10.2.0.1", self.codigo, agora=3000.0 + cr.JANELA_GLOBAL_S + 5)[:2],
                         (True, ""))

    def test_teto_duro_segura_ate_quem_nao_errou(self):
        # Muitos enderecos novos, um erro de cada: sem teto, ninguem os segurava (segunda revisao de seguranca). Com
        # TENTATIVAS_LIMITE_DURO erros em uma janela, espera todo mundo, ate com o codigo certo (sem dar pista).
        with mock.patch.object(cr, "codigo_novo", return_value="424242"):
            for i in range(cr.TENTATIVAS_LIMITE_DURO):
                self.controle.conferir_o_codigo("10.7.%d.1" % i, "nada", agora=6000.0 + i * 0.1)
        self.assertEqual(self.controle.conferir_o_codigo("10.8.0.1", "424242", agora=6004.0)[:2], (False, "muitas"))
        self.assertEqual(self.controle.conferir_o_codigo("10.8.0.1", "nada", agora=6004.0)[:2], (False, "muitas"))
        # passada a janela, a porta abre de novo: a rajada prendeu todo mundo por, no maximo, JANELA_GLOBAL_S
        depois = 6000.0 + cr.JANELA_GLOBAL_S + 5
        self.assertEqual(self.controle.conferir_o_codigo("10.8.0.1", "424242", agora=depois)[:2], (True, ""))
        self.assertGreaterEqual(self.controle.estado()["trocas_do_codigo"], 1)

    def test_o_codigo_que_o_atacante_tinha_nao_vale_depois_do_despejo(self):
        antigo = self.codigo
        with mock.patch.object(cr, "codigo_novo", return_value="424242"):
            for i in range(cr.ERROS_ANTES_DE_TROCAR_O_CODIGO):
                self.controle.conferir_o_codigo("10.5.%d.1" % i, "nada", agora=5000.0 + i * 0.1)
        self.assertEqual(self.controle.estado()["trocas_do_codigo"], 1)         # o professor ve que algo errou demais
        self.assertEqual(self.controle.conferir_o_codigo("10.6.0.1", antigo, agora=5010.0)[:2], (False, "codigo"))
        self.assertEqual(self.controle.conferir_o_codigo("10.6.0.2", "424242", agora=5010.0)[:2], (True, ""))

    def test_conferir_o_codigo_e_atomico_com_varias_conexoes_ao_mesmo_tempo(self):
        # 60 conexoes ao mesmo tempo, TODAS do mesmo endereco: so ERROS_ANTES_DO_BLOQUEIO chegam a comparar o codigo,
        # as outras ja encontram o endereco bloqueado (conferir e anotar o erro nao se separam).
        saidas, trava = [], threading.Lock()
        porta_de_largada = threading.Barrier(60)

        def tentar():
            porta_de_largada.wait()
            r = self.controle.conferir_o_codigo("10.4.0.1", "nada", agora=4000.0)[1]
            with trava:
                saidas.append(r)
        fios = [threading.Thread(target=tentar) for _ in range(60)]
        for f in fios:
            f.start()
        for f in fios:
            f.join(10)
        self.assertEqual(saidas.count("codigo"), cr.ERROS_ANTES_DO_BLOQUEIO)
        self.assertEqual(saidas.count("bloqueado"), 60 - cr.ERROS_ANTES_DO_BLOQUEIO)

    def test_jogador_que_nao_existe(self):
        _c, resposta = self.entrar(jogador=9)
        self.assertIn(b'"jogador"', resposta[1])

    def test_primeira_mensagem_tem_que_ser_o_oi(self):
        c = self.celular()
        c.enviar_texto('{"t":"qualquer"}')
        fechou = c.receber_ate(0x8, 3.0)
        self.assertIsNotNone(fechou)
        self.assertEqual(struct.unpack(">H", fechou[1][:2])[0], 1008)

    def test_jogador_ocupado_por_outro_aparelho(self):
        # dois celulares no mesmo computador de teste tem o mesmo endereco: o segundo "vence" (e' o Wi-Fi que piscou)
        primeiro, _ = self.entrar(jogador=2)
        segundo, resposta = self.entrar(jogador=2)
        self.assertIn(b'"ok"', resposta[1])
        self.assertTrue(esperar(lambda: primeiro.receber(0.2) is None))          # o primeiro foi fechado

    # -- o que o celular manda e o RetroArch ouve ------------------------------------------------
    def test_botao_apertado_vira_datagrama_na_porta_do_jogador(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_binario(cc.estado(botoes=1 << 8))                        # A
        self.assertTrue(esperar(lambda: any(v[3] == 8 and v[4] == 1 for v in self.udp_lido())))
        porta = [p for d, p in self.udp][0]
        self.assertEqual(porta, 58001)
        c.enviar_binario(cc.estado(botoes=0))
        self.assertTrue(esperar(lambda: any(v[3] == 8 and v[4] == 0 for v in self.udp_lido())))

    def test_analogico(self):
        c, _ = self.entrar(jogador=3)
        c.enviar_binario(cc.estado(lx=20000, ry=-15000))
        self.assertTrue(esperar(lambda: any(v[1] == 5 and v[2] == 0 and v[3] == 0 and v[4] == 20000 for v in self.udp_lido())))
        self.assertTrue(esperar(lambda: any(v[1] == 5 and v[2] == 1 and v[3] == 1 and v[4] == (-15000) & 0xFFFF for v in self.udp_lido())))

    def test_fechar_a_conexao_solta_os_botoes(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_binario(cc.estado(botoes=0b101))
        self.assertTrue(esperar(lambda: sum(1 for v in self.udp_lido() if v[4] == 1) >= 2))
        c.fechar()
        for botao in (0, 2):
            self.assertTrue(esperar(lambda: any(v[3] == botao and v[4] == 0 for v in self.udp_lido()), 4.0), botao)

    def test_tchau_solta_os_botoes(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_binario(cc.estado(botoes=1))
        self.assertTrue(esperar(lambda: any(v[3] == 0 and v[4] == 1 for v in self.udp_lido())))
        c.enviar_texto('{"t":"tchau"}')
        self.assertTrue(esperar(lambda: any(v[3] == 0 and v[4] == 0 for v in self.udp_lido()), 4.0))

    def test_sem_sinal_solta_os_botoes_e_avisa(self):
        with mock.patch.object(cr, "SEGUNDOS_SEM_SINAL", 0.4):
            c, _ = self.entrar(jogador=2)
            c.enviar_binario(cc.estado(botoes=1 << 3))
            self.assertTrue(esperar(lambda: any(v[3] == 3 and v[4] == 1 for v in self.udp_lido())))
            aviso = c.receber_ate(0x1, 4.0)                              # sem mandar mais nada
            self.assertIsNotNone(aviso)
            self.assertIn(b"sem_sinal", aviso[1])
            self.assertTrue(esperar(lambda: any(v[3] == 3 and v[4] == 0 for v in self.udp_lido()), 4.0))

    def test_o_ping_do_navegador_e_respondido(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_ping(b"oi")
        self.assertEqual(c.receber_ate(0xA, 3.0), (0xA, b"oi"))

    def test_estado_torto_derruba_a_conexao(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_binario(b"\x07\x00")
        fechou = c.receber_ate(0x8, 3.0)
        self.assertEqual(struct.unpack(">H", fechou[1][:2])[0], 1003)

    def test_excesso_de_quadros_e_jogado_fora_sem_derrubar(self):
        c, _ = self.entrar(jogador=2)
        for i in range(cr.QUADROS_POR_SEGUNDO_MAXIMO * 3):
            c.enviar_binario(cc.estado(botoes=i & 1))
        c.enviar_binario(cc.estado(botoes=0))
        c.enviar_ping(b"ainda aqui")
        self.assertEqual(c.receber_ate(0xA, 5.0), (0xA, b"ainda aqui"))

    def test_desligar_fecha_a_porta_e_solta_tudo(self):
        c, _ = self.entrar(jogador=2)
        c.enviar_binario(cc.estado(botoes=1 << 9))
        self.assertTrue(esperar(lambda: any(v[3] == 9 and v[4] == 1 for v in self.udp_lido())))
        self.controle.desligar()
        self.assertFalse(self.controle.estado()["ligado"])
        self.assertTrue(esperar(lambda: any(v[3] == 9 and v[4] == 0 for v in self.udp_lido()), 4.0))
        with self.assertRaises(OSError):
            cc.ClienteDeControle(porta=self.porta, segundos=1.0)

    def test_preparar_partida_sorteia_a_base_e_abre_so_os_liberados(self):
        chaves = self.controle.preparar_partida()                               # um jogo de 4 jogadores
        self.assertEqual(chaves["network_remote_enable"], "true")
        self.assertEqual(int(chaves["network_remote_base_port"]), self.enviador.porta_base)
        self.assertEqual([chaves["network_remote_enable_user_p%d" % i] for i in range(1, 5)],
                         ["false", "true", "true", "true"])                     # de fabrica: 2, 3 e 4 (o 1 e' o teclado)
        self.controle.desligar()
        self.assertEqual(self.controle.preparar_partida(), {})                  # desligado: o jogo abre como sempre

    def test_jogo_de_2_jogadores_abre_so_o_jogador_2(self):
        chaves = self.controle.preparar_partida(2)
        self.assertEqual([chaves["network_remote_enable_user_p%d" % i] for i in range(1, 5)],
                         ["false", "true", "false", "false"])

    def test_sem_jogador_liberado_que_o_jogo_tenha_nada_abre(self):
        self.controle.liberar_jogadores([3, 4])
        self.assertEqual(self.controle.preparar_partida(2), {})                 # o jogo so tem 1 e 2
        self.assertEqual(self.controle.preparar_partida(4)["network_remote_enable_user_p3"], "true")
        self.controle.liberar_jogadores([])
        self.assertEqual(self.controle.preparar_partida(4), {})

    def test_o_professor_libera_o_jogador_1(self):
        self.controle.liberar_jogadores([1])
        chaves = self.controle.preparar_partida(1)                              # um jogo de 1 jogador, vale 1 e 2
        self.assertEqual(chaves["network_remote_enable_user_p1"], "true")
        self.assertEqual(self.controle.jogadores(), [1])

    def test_liberar_jogadores_ignora_lixo(self):
        # Vale de 1 a 8 (cr.JOGADORES); 0 e 9 estao fora, e texto que nao e' numero, None e fracao sao descartados.
        self.assertEqual(self.controle.liberar_jogadores([0, 1, "2", "x", 5, 9, None, 3.5]), [1, 2, 5])
        self.assertEqual(self.controle.liberar_jogadores(range(0, cr.JOGADORES + 2)), list(range(1, cr.JOGADORES + 1)))

    def test_jogador_nao_liberado_nao_entra(self):
        self.controle.liberar_jogadores([3])
        _c, resposta = self.entrar(jogador=2)
        self.assertIn(b'"jogador"', resposta[1])
        self.assertIn(b'"jogadores": [3]', resposta[1])
        _c, resposta = self.entrar(jogador=3)
        self.assertIn(b'"ok"', resposta[1])

    def test_a_pagina_pergunta_quais_jogadores_estao_liberados(self):
        import http.client
        import json as j
        self.controle.liberar_jogadores([2, 4])
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        conexao.request("GET", "/jogadores")
        resposta = conexao.getresponse()
        corpo = j.loads(resposta.read())
        conexao.close()
        self.assertEqual((resposta.status, corpo), (200, {"jogadores": [2, 4], "digitos": cr.DIGITOS_DO_CODIGO}))

    def test_host_de_site_que_apontou_para_o_computador_e_recusado(self):
        # DNS rebinding: o nome do site aponta para este computador; Host e Origin chegam iguais, com o nome do site.
        with self.assertRaises(cc.RecusouAConexao) as dentro:
            cc.ClienteDeControle(porta=self.porta, origem="http://evil.example:%d" % self.porta,
                                 host_falso="evil.example:%d" % self.porta)
        self.assertIn("403", str(dentro.exception))
        import http.client
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        conexao.request("GET", "/", headers={"Host": "evil.example:%d" % self.porta})
        self.assertEqual(conexao.getresponse().status, 403)                      # nem a pagina
        conexao.close()

    def test_ligar_duas_vezes_nao_troca_o_codigo(self):
        de_novo = self.controle.ligar()
        self.assertEqual(de_novo["codigo"], self.codigo)
        self.assertEqual(de_novo["porta_da_pagina"], self.porta)

    def test_conexoes_demais_sao_recusadas(self):
        with mock.patch.object(cr, "CONEXOES_MAXIMAS", 3):
            abertos = []
            try:
                for _ in range(3):
                    s = __import__("socket").create_connection(("127.0.0.1", self.porta), timeout=2)
                    abertos.append(s)
                time.sleep(0.2)
                s = __import__("socket").create_connection(("127.0.0.1", self.porta), timeout=2)
                abertos.append(s)
                s.sendall(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
                s.settimeout(2)
                try:
                    dados = s.recv(100)
                except OSError:
                    dados = b""
                self.assertEqual(dados, b"")                                    # fechada sem resposta
            finally:
                for s in abertos:
                    s.close()


class FalsoManipulador:
    """So o que as rotas usam do manipulador de pedidos (o mesmo molde do test_auditoria_25_10)."""

    def __init__(self):
        self.respostas = []

    def responder_json(self, corpo, *_):
        self.respostas.append(("json", corpo))

    def erro(self, mensagem, codigo=400):
        self.respostas.append(("erro", mensagem, codigo))


class AsRotasDoArena(unittest.TestCase):
    """/api/controle-remoto, /ligar e /desligar: deste computador, desligado de fabrica, e nunca no Android."""

    def setUp(self):
        import arena
        self.arena = arena
        self.antes = arena.CONTROLE_REMOTO
        self.udp = []
        self.servico = cr.ControleRemoto(enviador=cr.EnviadorRetroPad(enviar=lambda d, p: self.udp.append((d, p))),
                                         enderecos=lambda: ["127.0.0.1"], porta=0)
        arena.CONTROLE_REMOTO = self.servico

    def tearDown(self):
        self.servico.desligar()
        self.servico.enviador.parar()
        self.arena.CONTROLE_REMOTO = self.antes

    def pedir(self, caminho, post=False):
        falso = FalsoManipulador()
        if post:
            self.arena.Manipulador.api_post(falso, caminho, {})
        else:
            self.arena.Manipulador.api_get(falso, caminho)
        return falso.respostas[-1]

    def test_nasce_desligado(self):
        tipo, corpo = self.pedir("/api/controle-remoto")
        self.assertEqual((tipo, corpo["ok"], corpo["ligado"]), ("json", True, False))

    def test_liga_mostra_o_codigo_e_desliga(self):
        _, ligado = self.pedir("/api/controle-remoto/ligar", post=True)
        self.assertTrue(ligado["ok"] and ligado["ligado"])
        self.assertEqual(len(ligado["codigo"]), cr.DIGITOS_DO_CODIGO)
        self.assertEqual(ligado["jogadores_liberados"], [2, 3, 4])
        self.assertTrue(ligado["enderecos"][0].startswith("http://127.0.0.1:"))
        _, olhando = self.pedir("/api/controle-remoto")
        self.assertEqual(olhando["codigo"], ligado["codigo"])
        _, desligado = self.pedir("/api/controle-remoto/desligar", post=True)
        self.assertEqual((desligado["ok"], desligado["ligado"]), (True, False))
        self.assertNotIn("codigo", desligado)             # desligado, o codigo nao fica a mostra

    def test_a_rota_nao_esta_aberta_a_rede(self):
        for rota in ("/api/controle-remoto", "/api/controle-remoto/ligar", "/api/controle-remoto/desligar",
                     "/api/controle-remoto/jogadores"):
            self.assertNotIn(rota, self.arena.ROTAS_REDE_EXTERNA)

    def test_o_professor_escolhe_os_jogadores_do_celular(self):
        falso = FalsoManipulador()
        self.arena.Manipulador.api_post(falso, "/api/controle-remoto/jogadores", {"jogadores": [1, 3]})
        tipo, corpo = falso.respostas[-1]
        self.assertEqual((tipo, corpo["ok"], corpo["jogadores_liberados"]), ("json", True, [1, 3]))
        self.assertEqual(self.servico.jogadores(), [1, 3])
        # desligado tambem guarda a escolha (o professor marca antes de ligar)
        self.assertEqual(self.pedir("/api/controle-remoto")[1]["jogadores_liberados"], [1, 3])
        falso = FalsoManipulador()
        self.arena.Manipulador.api_post(falso, "/api/controle-remoto/jogadores", {"jogadores": "todos"})
        self.assertEqual(falso.respostas[-1][0], "erro")

    def test_no_android_nao_liga(self):
        with mock.patch.object(self.arena.plataforma_do_sistema, "ANDROID", True):
            for rota, post in (("/api/controle-remoto", False), ("/api/controle-remoto/ligar", True)):
                resposta = self.pedir(rota, post)
                self.assertEqual(resposta[0], "erro")
                self.assertEqual(resposta[2], 404)
        self.assertFalse(self.servico.estado()["ligado"])

    def test_porta_ocupada_vira_mensagem(self):
        with mock.patch.object(self.servico, "ligar", side_effect=OSError("portas ocupadas")):
            resposta = self.pedir("/api/controle-remoto/ligar", post=True)
        self.assertEqual(resposta[0], "erro")
        self.assertEqual(resposta[2], 500)


if __name__ == "__main__":
    unittest.main()
