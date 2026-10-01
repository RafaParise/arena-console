# -*- coding: utf-8 -*-
"""
ARENA - Testes automatizados
============================
Rodar:  python servidor/tests/run.py

Sem 'pip install'. Só stdlib. Cada teste cria seus próprios arquivos
temporários e não toca no banco, catálogo ou configuração reais.
"""

import os
import sys
import tempfile
import shutil
import unittest
import time

# Permite importar os módulos do servidor a partir da raiz.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pasta_temp():
    return tempfile.mkdtemp(prefix="arena_test_")


# ============================================================================
# 1. indexador.py
# ============================================================================

class TestIndexador(unittest.TestCase):

    def setUp(self):
        import indexador
        self.mod = indexador
        self.dir = pasta_temp()
        self._old_pj = self.mod.PASTA_JOGOS
        self._old_pd = self.mod.PASTA_DADOS
        self.mod.PASTA_JOGOS = os.path.join(self.dir, "jogos")
        self.mod.PASTA_DADOS = os.path.join(self.dir, "dados")
        os.makedirs(self.mod.PASTA_JOGOS, exist_ok=True)
        os.makedirs(self.mod.PASTA_DADOS, exist_ok=True)

    def tearDown(self):
        self.mod.PASTA_JOGOS = self._old_pj
        self.mod.PASTA_DADOS = self._old_pd
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_limpar_titulo_varios_casos(self):
        casos = [
            ("super_jogo_(Brazil)_[!].sfc", "Super Jogo"),
            ("pokemon_fire_red.gba", "Pokemon Fire Red"),
            ("the_elder_scrolls.nes", "The Elder Scrolls"),
            ("jogo_sem_titulo", "Jogo Sem Titulo"),
            ("ABC.123.xyz", "ABC 123"),
            ("", "Sem titulo"),
            ("minha_coisa---[coisa].zip", "Minha Coisa"),
        ]
        for arquivo, esperado in casos:
            with self.subTest(arquivo=arquivo):
                self.assertEqual(self.mod.limpar_titulo(arquivo), esperado)

    def test_chave_ordenacao(self):
        casos = [
            ("Ácido", "acido"),
            ("Pôr do sol", "por do sol"),
            ("ÃE", "ae"),
            ("nao_acentuado", "nao_acentuado"),
        ]
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(self.mod.chave_ordenacao(texto), esperado)

    def test_assinatura_das_pastas(self):
        os.makedirs(os.path.join(self.mod.PASTA_JOGOS, "livres"), exist_ok=True)
        antes = self.mod.assinatura_das_pastas()
        # Força mudança de mtime com os.utime (evita resolução do filesystem).
        caminho_dir = os.path.join(self.mod.PASTA_JOGOS, "livres")
        os.utime(caminho_dir, (time.time() + 60, time.time() + 60))
        depois = self.mod.assinatura_das_pastas()
        self.assertNotEqual(antes, depois)

    def test_ignorar(self):
        self.assertIn("leia.txt", self.mod.IGNORAR)
        self.assertIn("thumbs.db", self.mod.IGNORAR)

    def test_disco_em_trilhas_vira_um_jogo(self):
        # Achado 25/09/2026: Saturn Bomberman aparecia 31 vezes (trilhas).
        por_id, por_ext = self.mod.carregar_plataformas()
        pessoais = os.path.join(self.mod.PASTA_JOGOS, "pessoais")
        dc = os.path.join(pessoais, "Dreamcast", "Capcom vs. SNK 2 (English v1.2)")
        sat = os.path.join(pessoais, "Sega Saturn", "Bomber")
        ps1 = os.path.join(pessoais, "PS1")
        for pasta in (dc, sat, ps1):
            os.makedirs(pasta)

        def criar(pasta, nome, texto="x"):
            with open(os.path.join(pasta, nome), "w") as f:
                f.write(texto)

        criar(dc, "disc.gdi", '2\n1 0 4 2352 track01.bin 0\n2 600 0 2352 "track 02.raw" 0\n')
        criar(dc, "track01.bin")
        criar(dc, "track 02.raw")
        criar(sat, "Bomber (USA).cue",
              'FILE "Bomber (USA) (Track 01).bin" BINARY\n  TRACK 01 MODE1/2352\n'
              'FILE "Bomber (USA) (Track 02).bin" BINARY\n  TRACK 02 AUDIO\n')
        criar(sat, "Bomber (USA) (Track 01).bin")
        criar(sat, "Bomber (USA) (Track 02).bin")
        criar(ps1, "Jogo (USA).chd")
        criar(ps1, "Jogo (USA).cue", 'FILE "Jogo (USA).bin" BINARY\n')
        criar(ps1, "Jogo (USA).bin")
        criar(pessoais, "neogeo.mame.zip")
        # Fliperama: o .chd do kinst mora em Arcade\kinst\ e nao e' jogo;
        # a BIOS pgm.zip tambem nao.
        arcade = os.path.join(pessoais, "Arcade")
        os.makedirs(os.path.join(arcade, "kinst"))
        criar(arcade, "kinst.zip")
        criar(os.path.join(arcade, "kinst"), "kinst.chd")
        criar(arcade, "pgm.zip")

        achados = self.mod.varrer_pasta(pessoais, "pessoais", por_ext, por_id)
        arquivos = sorted(os.path.basename(j["arquivo"]) for j in achados)
        self.assertEqual(arquivos, ["Bomber (USA).cue", "Jogo (USA).chd", "disc.gdi", "kinst.zip"])
        titulos = {os.path.basename(j["arquivo"]): j["titulo"] for j in achados}
        self.assertEqual(titulos["disc.gdi"], "Capcom Vs SNK 2")

    def test_identificador_reconhece_ps3_e_xbox360(self):
        # Achado 26/09/2026: Dead Space 3 de PS3 na pasta do Xbox 360; o
        # identificador nao conhecia nenhum dos dois e nao avisava.
        import identificador
        pasta = tempfile.mkdtemp()
        try:
            ps3 = os.path.join(pasta, "ps3.iso")
            with open(ps3, "wb") as f:
                f.write(b"\0" * 0x800 + b"PlayStation3\0\0\0\0BLES-01733" + b"\0" * 0x20000)
            x360 = os.path.join(pasta, "x360.iso")
            with open(x360, "wb") as f:
                f.write(b"\0" * 0x10000 + b"MICROSOFT*XBOX*MEDIA" + b"\0" * 0x10000)
            todos = ["ps2", "ps3", "xbox360"]
            self.assertEqual(identificador.identificar(ps3, todos), "ps3")
            self.assertEqual(identificador.identificar(x360, todos), "xbox360")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


# ============================================================================
# 2. cheats.py
# ============================================================================

class TestCheats(unittest.TestCase):

    def setUp(self):
        import cheats
        self.mod = cheats
        self.dir = pasta_temp()
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        # As constantes de caminho sao calculadas no import — recalcula para
        # a pasta temporaria.
        self.mod.PASTA_RETROARCH = os.path.join(self.dir, "retroarch")
        self.mod.PASTA_STATES = os.path.join(self.mod.PASTA_RETROARCH, "states")
        self.mod.PASTA_SAVES = os.path.join(self.mod.PASTA_RETROARCH, "saves")
        self.mod.PASTA_CHEATS = os.path.join(self.mod.PASTA_RETROARCH, "cheats")
        self.cheats_pasta = os.path.join(self.mod.PASTA_CHEATS, "PlayStation")
        os.makedirs(self.cheats_pasta, exist_ok=True)
        self.jogo = {
            "arquivo": "jogos/pessoais/PS1/MeuJogo.iso",
            "plataforma_nome": "PlayStation",
            "titulo": "Meu Jogo",
        }

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_validar_codigo_formato_correto(self):
        casos = ["7E0DBE:09", "7E0DBE09 7E0DBF09", "4100:A000:8000:C0DE",
                 "12345678:ABCDEF01"]
        for codigo in casos:
            with self.subTest(codigo=codigo):
                limpo, erro = self.mod.validar_codigo(codigo)
                self.assertIsNone(erro, erro)
                self.assertIsNotNone(limpo)

    def test_validar_codigo_invalido(self):
        casos = [
            # Auditoria 2, Fase 7: a mensagem ganhou acento (vai para a tela).
            ("", "Digite o código."),
            ("XYZ", "Código inválido."),
            ("7E0DBE:ZZZ", "Código inválido."),
        ]
        for codigo, mensagem in casos:
            with self.subTest(codigo=codigo[:40]):
                limpo, erro = self.mod.validar_codigo(codigo)
                self.assertIsNone(limpo)
                self.assertIsNotNone(erro)
                self.assertIn(mensagem.split(".")[0], erro or "")

    def test_gravar_e_ler_cheats(self):
        cheats = [
            {"descricao": "Vidas infinitas", "codigo": "7E0DBE:09", "ligado": True},
            {"descricao": "Invencibilidade", "codigo": "7E0DBF:01", "ligado": False},
        ]
        caminho = self.mod.gravar_cheats(self.jogo, cheats)
        self.assertTrue(caminho.endswith(".cht"))
        self.assertTrue(os.path.isfile(caminho))

        lidos = self.mod.ler_cheats(self.jogo)
        self.assertEqual(len(lidos), 2)
        self.assertEqual(lidos[0]["descricao"], "Vidas infinitas")
        self.assertTrue(lidos[0]["ligado"])
        self.assertFalse(lidos[1]["ligado"])

        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("cheats = 2", texto)
        self.assertIn("7E0DBE:09", texto)

    def test_adicionar_cheat(self):
        self.mod.gravar_cheats(self.jogo, [])
        novos, erro = self.mod.adicionar_cheat(
            self.jogo, "Vidas ilimitadas", "7E0DBE:09", ligado=True)
        self.assertIsNone(erro)
        self.assertEqual(len(novos), 1)
        self.assertEqual(novos[0]["descricao"], "Vidas ilimitadas")

    def test_limite_cheat(self):
        cheats = [{"descricao": f"C{i}", "codigo": "7E0DBE:09", "ligado": True}
                 for i in range(60)]
        self.mod.gravar_cheats(self.jogo, cheats)
        _, erro = self.mod.adicionar_cheat(self.jogo, "Extra", "1234:5678")
        self.assertIsNotNone(erro)
        self.assertIn("60", erro)

    def test_apagar_cheat(self):
        cheats = [
            {"descricao": "A", "codigo": "1111:2222", "ligado": True},
            {"descricao": "B", "codigo": "3333:4444", "ligado": False},
        ]
        self.mod.gravar_cheats(self.jogo, cheats)
        resultado, _ = self.mod.alterar_cheat(self.jogo, 0, apagar=True)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["descricao"], "B")

    def test_apagar_estado(self):
        states_pasta = os.path.join(self.dir, "retroarch", "states")
        os.makedirs(states_pasta, exist_ok=True)
        base = "MeuJogo"
        open(os.path.join(states_pasta, base + ".state"), "wb").close()
        todos = self.mod.listar_estados(self.jogo)
        self.assertTrue(todos[0]["existe"])
        self.assertTrue(self.mod.apagar_estado(self.jogo, 0))
        self.assertFalse(os.path.isfile(os.path.join(states_pasta,
                                                      base + ".state")))


# ============================================================================
# 3. controles.py
# ============================================================================

class TestControles(unittest.TestCase):

    def setUp(self):
        import controles
        self.mod = controles
        self.dir = pasta_temp()
        self._old_raiz = self.mod.RAIZ
        self.mod.RAIZ = self.dir
        # ARQUIVO e PASTA_DADOS sao calculados na importacao: trocar so a
        # RAIZ fazia a bateria gravar no dados\controles.json DE VERDADE
        # (achado 25/09/2026: o jogador 2 do aluno ficava com "a = botao 0").
        self._old_arquivo, self._old_pasta = self.mod.ARQUIVO, self.mod.PASTA_DADOS
        self.mod.PASTA_DADOS = os.path.join(self.dir, "dados")
        self.mod.ARQUIVO = os.path.join(self.mod.PASTA_DADOS, "controles.json")
        self.dados_pasta = os.path.join(self.dir, "dados")
        os.makedirs(self.dados_pasta, exist_ok=True)
        with open(os.path.join(self.dados_pasta, "controles.json"), "w") as f:
            f.write("{}")

    def tearDown(self):
        self.mod.RAIZ = self._old_raiz
        self.mod.ARQUIVO, self.mod.PASTA_DADOS = self._old_arquivo, self._old_pasta
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_nao_grava_no_controles_json_de_verdade(self):
        self.assertTrue(self.mod.ARQUIVO.startswith(self.dir))

    def test_teclado_sem_controle_fica_no_jogador_1(self):
        opcoes = self.mod.opcoes_do_retroarch(controles_ligados=0)
        self.assertEqual(opcoes["input_player1_start"], "enter")
        self.assertEqual(opcoes["input_player2_start"], "nul")

    def test_teclado_com_3_controles_vai_para_o_jogador_4(self):
        self.mod.definir("1", "b", "teclado", "c")   # tecla mudada pelo aluno
        opcoes = self.mod.opcoes_do_retroarch(controles_ligados=3)
        self.assertEqual(opcoes["input_player1_start"], "nul")
        self.assertEqual(opcoes["input_player1_b"], "nul")
        self.assertEqual(opcoes["input_player4_start"], "enter")
        self.assertEqual(opcoes["input_player4_b"], "c")
        self.assertEqual(opcoes["input_player4_up"], "up")

    def test_botao_de_controle_nao_definido_vai_nul(self):
        self.mod.definir("1", "a", "botao", "1")
        opcoes = self.mod.opcoes_do_retroarch(controles_ligados=1)
        self.assertEqual(opcoes["input_player1_a_btn"], "1")
        self.assertEqual(opcoes["input_player1_start_btn"], "nul")
        self.assertEqual(opcoes["input_player5_start_axis"], "nul")

    def test_validar_teclado(self):
        casos = [
            ("x", ("x", None)),
            ("up", ("up", None)),
            ("z", ("z", None)),
            ("tecla_que_nao_existe", (None, "O RetroArch nao conhece")),
        ]
        for valor, esperado in casos:
            with self.subTest(valor=valor):
                limpo, erro = self.mod.validar("teclado", valor)
                if esperado[0] is None:
                    self.assertIsNone(limpo)
                    self.assertIsNotNone(erro)
                else:
                    self.assertIsNone(erro)
                    self.assertEqual(limpo, esperado[0])

    def test_validar_botao(self):
        self.assertEqual(self.mod.validar("botao", "0"), ("0", None))
        self.assertEqual(self.mod.validar("botao", "31"), ("31", None))
        limpo, erro = self.mod.validar("botao", "32")
        self.assertIsNone(limpo)
        self.assertIsNotNone(erro)

    def test_validar_hat(self):
        self.assertEqual(self.mod.validar("hat", "up"), ("h0up", None))
        self.assertEqual(self.mod.validar("hat", "h0down"), ("h0down", None))
        limpo, erro = self.mod.validar("hat", "diagonal")
        self.assertIsNone(limpo)

    def test_validar_eixo(self):
        self.assertEqual(self.mod.validar("eixo", "-0"), ("-0", None))
        self.assertEqual(self.mod.validar("eixo", "+1"), ("+1", None))
        limpo, erro = self.mod.validar("eixo", "0")
        self.assertIsNone(limpo)

    def test_definir_e_ler(self):
        dados, _ = self.mod.definir("1", "b", "teclado", "x")
        self.assertEqual(dados["1"]["b"], {"tipo": "teclado", "valor": "x"})
        dados2, _ = self.mod.definir("1", "a", "botao", "1")
        self.assertEqual(dados2["1"]["a"], {"tipo": "botao", "valor": "1"})
        lido = self.mod.ler()
        self.assertEqual(lido["1"]["b"], {"tipo": "teclado", "valor": "x"})

    def test_limpar(self):
        self.mod.definir("1", "b", "teclado", "x")
        self.mod.definir("2", "a", "botao", "0")
        self.mod.limpar("1")
        lido = self.mod.ler()
        self.assertNotIn("b", lido.get("1", {}))
        self.assertIn("a", lido.get("2", {}))

    def test_opcoes_do_retroarch(self):
        self.mod.definir("1", "b", "teclado", "x")
        self.mod.definir("1", "a", "botao", "1")
        opcoes = self.mod.opcoes_do_retroarch()
        self.assertEqual(opcoes["input_player1_b"], "x")
        self.assertEqual(opcoes["input_player1_a_btn"], "1")

    def test_padrao_teclado(self):
        dados, _ = self.mod.aplicar_padrao("1")
        self.assertEqual(dados["1"]["b"]["valor"], "z")
        self.assertEqual(dados["1"]["a"]["valor"], "x")
        self.assertEqual(dados["1"]["start"]["valor"], "enter")

    def test_padrao_controle_volta_ao_automatico(self):
        # Antes gravava a numeracao do navegador (Start 9 = R3 no XInput do
        # RetroArch). Agora apaga os botoes de controle e deixa o teclado.
        self.mod.definir("3", "start", "botao", "9")
        self.mod.definir("3", "b", "teclado", "c")
        dados, erro = self.mod.aplicar_padrao_controle("3")
        self.assertIsNone(erro)
        self.assertNotIn("start", dados["3"])
        self.assertEqual(dados["3"]["b"], {"tipo": "teclado", "valor": "c"})

    def test_jogadores_1_a_5(self):
        self.assertEqual(self.mod.JOGADORES, ("1", "2", "3", "4", "5"))
        _, erro = self.mod.definir("5", "a", "botao", "1")
        self.assertIsNone(erro)
        self.assertEqual(self.mod.opcoes_do_retroarch()["input_player5_a_btn"], "1")
        _, erro = self.mod.aplicar_padrao("4")
        self.assertIsNotNone(erro)   # teclado padrao so existe para 1 e 2


# ============================================================================
# 4. hardware.py
# ============================================================================

class TestHardware(unittest.TestCase):

    def _caps(self, nucleos=2, ram=4, driver="vulkan", disco_classe="rapido",
              gpu_integrada=True):
        return {
            "nucleos": nucleos,
            "ram_total_gb": ram,
            "driver_video": driver,
            "disco": {"classe": disco_classe},
            "gpu": {"integrada": gpu_integrada, "nome": "fake",
                    "conhecida": True},
        }

    def test_capacidade_leve(self):
        import hardware
        caps = self._caps(nucleos=2, ram=4, disco_classe="lento")
        resultado = hardware.capacidade(caps)
        self.assertLessEqual(resultado["nota"], 2)

    def test_capacidade_forte(self):
        import hardware
        caps = self._caps(nucleos=8, ram=16, driver="vulkan",
                          disco_classe="muito_rapido", gpu_integrada=False)
        resultado = hardware.capacidade(caps)
        self.assertEqual(resultado["nota"], 5)
        self.assertEqual(resultado["nota_gpu"], 5)

    def test_gpu_integrada_limitada(self):
        import hardware
        caps = self._caps(nucleos=8, ram=16, gpu_integrada=True)
        resultado = hardware.capacidade(caps)
        self.assertLessEqual(resultado["nota_gpu"], 3)

    def test_placa_da_tela_vence_o_registro(self):
        # Achado 25/09/2026: o registro listava primeiro uma GeForce 210 que
        # ja saiu da maquina; a tela esta na Radeon integrada.
        import hardware
        original = hardware.placa_da_tela_principal
        try:
            hardware.placa_da_tela_principal = lambda: "AMD Radeon(TM) Graphics"
            placa = hardware.placa_video()
            self.assertEqual(placa["nome"], "AMD Radeon(TM) Graphics")
            self.assertTrue(placa["integrada"])
        finally:
            hardware.placa_da_tela_principal = original

    def test_classificar(self):
        import arena
        # classificar() lê CAPACIDADE["nota"] global — mock temporário.
        original = arena.CAPACIDADE
        try:
            arena.CAPACIDADE = {"nota": 5}
            c = arena.classificar(1)
            self.assertEqual(c["chave"], "otimo")
            arena.CAPACIDADE = {"nota": 3}
            c = arena.classificar(3)
            self.assertEqual(c["chave"], "bom")
            arena.CAPACIDADE = {"nota": 1}
            c = arena.classificar(3)
            self.assertEqual(c["chave"], "ruim")
        finally:
            arena.CAPACIDADE = original

    def test_etiqueta_por_maquina_medida(self):
        # Avaliacao nova (30/09/2026): a etiqueta vem da velocidade MEDIDA de
        # um nucleo e das instrucoes do processador, nao da nota (que dava 4
        # ao Celeron e ao Ryzen e chamava o PS2 de "Capenga" nos dois).
        import arena
        consoles = {p["id"]: p for p in arena.carregar_catalogo()}
        celeron = {"velocidade": {"relativa_ao_alvo": 1.0},
                   "instrucoes": {"avx": False, "avx2": False}, "gpu": {"integrada": True}}
        ryzen = {"velocidade": {"relativa_ao_alvo": 2.28},
                 "instrucoes": {"avx": True, "avx2": True}, "gpu": {"integrada": True}}
        dedicada = {"velocidade": {"relativa_ao_alvo": 3.2},
                    "instrucoes": {"avx": True, "avx2": True}, "gpu": {"integrada": False}}

        def chave(console, maquina):
            return arena.classificar_plataforma(consoles[console], maquina)["chave"]

        # Celeron N5100 otimizado: o que o Rafael jogou de verdade.
        self.assertEqual(chave("snes", celeron), "bem")
        self.assertEqual(chave("psp", celeron), "ajustes")     # God of War, abaixo de 60
        self.assertEqual(chave("ps2", celeron), "ajustes")     # PS2 com 4 jogadores
        self.assertEqual(chave("ps3", celeron), "pesado")      # sem AVX2, 4 threads
        self.assertEqual(chave("xbox360", celeron), "nao_abre")
        detalhe = arena.classificar_plataforma(consoles["xbox360"], celeron)["detalhe"]
        self.assertIn("AVX", detalhe)
        self.assertIn("Xenia", detalhe)
        # Ryzen 5 5600G: PS2/PS3/Xbox 360 rodam (placa integrada -> "com ajustes").
        self.assertEqual(chave("psp", ryzen), "bem")
        self.assertEqual(chave("ps2", ryzen), "ajustes")
        self.assertEqual(chave("ps3", ryzen), "ajustes")
        self.assertEqual(chave("xbox360", ryzen), "ajustes")
        # Placa dedicada forte: aqui sim "Roda bem" no PS2.
        self.assertEqual(chave("ps2", dedicada), "bem")
        # Sem medicao (Windows antigo, falha): cai na regra antiga, sem erro.
        self.assertIn(chave("ps2", {}), ("bem", "ajustes", "pesado"))

    def test_velocidade_e_instrucoes_medidas(self):
        import hardware
        v = hardware.velocidade_de_um_nucleo(rodadas=3, tamanho=20000)
        self.assertGreater(v["operacoes_por_segundo"], 0)
        self.assertGreater(v["relativa_ao_alvo"], 0)
        self.assertIn("avx", hardware.instrucoes())

    def test_driver_video(self):
        import hardware
        driver = hardware.driver_video()
        self.assertIn(driver, ("vulkan", "d3d11", "glcore"))


# ============================================================================
# 5. Banco (arena.py)
# ============================================================================
# Ate 25/09/2026 esta classe testava servidor\db.py, uma COPIA das funcoes de
# banco que o ARENA nunca importava -- a bateria passava mesmo com o codigo de
# verdade diferente. Agora testa o arena.py, pelas mesmas funcoes que ele usa
# para gravar (inserir_placar...), e a marca de sincronizacao por numero de
# chegada ("seq:N"), nao por data.

class TestDB(unittest.TestCase):

    def setUp(self):
        import arena
        self.mod = arena
        self.dir = pasta_temp()
        self._old_pd = self.mod.PASTA_DADOS
        self._old_ab = self.mod.ARQUIVO_BANCO
        self.mod.PASTA_DADOS = self.dir
        self.mod.ARQUIVO_BANCO = os.path.join(self.dir, "arena.db")
        self.mod.preparar_banco()

    def tearDown(self):
        self.mod.PASTA_DADOS = self._old_pd
        self.mod.ARQUIVO_BANCO = self._old_ab
        shutil.rmtree(self.dir, ignore_errors=True)

    def placar(self, uuid, apelido, pontos, dispositivo="d1", enviado=0):
        with self.mod.banco() as c:
            return self.mod.inserir_placar(
                c, uuid, apelido, "j1", "Jogo", pontos,
                "2026-01-01T00:00:00Z", dispositivo, enviado)

    def test_schema(self):
        with self.mod.banco() as c:
            tabelas = {l[0] for l in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            colunas = {l[1] for l in c.execute("PRAGMA table_info(placar)")}
        self.assertTrue({"placar", "sessao", "contador"} <= tabelas)
        self.assertIn("seq", colunas)

    def test_insert_e_select(self):
        self.placar("abc", "pedro", 1000)
        with self.mod.banco() as c:
            row = c.execute(
                "SELECT * FROM placar WHERE apelido='pedro'").fetchone()
        self.assertEqual(row["pontos"], 1000)
        self.assertIsNotNone(row["seq"])

    def test_insert_or_ignore(self):
        self.assertEqual(self.placar("abc", "ana", 500, enviado=1), 1)
        self.assertEqual(self.placar("abc", "ana", 500, enviado=1), 0)
        with self.mod.banco() as c:
            n = c.execute(
                "SELECT COUNT(*) FROM placar WHERE uuid='abc'").fetchone()[0]
        self.assertEqual(n, 1)

    def test_marcar_enviados(self):
        self.placar("x1", "bia", 300)
        self.mod.marcar_enviados([{"uuid": "x1"}], [])
        with self.mod.banco() as c:
            row = c.execute(
                "SELECT enviado FROM placar WHERE uuid='x1'").fetchone()
        self.assertEqual(row["enviado"], 1)

    def test_registros_desde(self):
        self.placar("r1", "carlos", 900, "d3")
        _p, _s, marca = self.mod.registros_desde("")
        self.assertTrue(marca.startswith("seq:"))
        self.placar("r2", "daniel", 1200, "d3")
        placares, sessoes, _ = self.mod.registros_desde(marca)
        self.assertEqual([p["apelido"] for p in placares], ["daniel"])

    def test_integrity(self):
        with self.mod.banco() as c:
            self.assertEqual(c.execute(
                "PRAGMA integrity_check").fetchone()[0], "ok")

# ============================================================================
# Runner
# ============================================================================

def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    pasta_testes = os.path.dirname(os.path.abspath(__file__))
    if pasta_testes not in sys.path:
        sys.path.insert(0, pasta_testes)
    for nome in sorted(os.listdir(pasta_testes)):
        if not nome.startswith("test_") or not nome.endswith(".py"):
            continue
        if nome == "run.py":
            continue
        modulo = __import__(nome[:-3], fromlist=[""])
        suite.addTests(loader.loadTestsFromModule(modulo))

    suite.addTests(loader.loadTestsFromTestCase(TestIndexador))
    suite.addTests(loader.loadTestsFromTestCase(TestCheats))
    suite.addTests(loader.loadTestsFromTestCase(TestControles))
    suite.addTests(loader.loadTestsFromTestCase(TestHardware))
    suite.addTests(loader.loadTestsFromTestCase(TestDB))

    if suite.countTestCases() == 0:
        print("Nenhum teste encontrado.")
        return 1

    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
