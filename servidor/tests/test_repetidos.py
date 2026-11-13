# -*- coding: utf-8 -*-
"""Os jogos repetidos (servidor\\repetidos.py) e o exportar para o cartao SD (servidor\\exportar.py e o
manter_original do cartao_de_jogos.levar_jogo). Pedido do Rafael, 13/11/2026.

Uma pasta temporaria faz o papel da pasta do ARENA: nada toca nos jogos de verdade.
"""
import os
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(AQUI)), "testes"))
import cartao_de_jogos as cj  # noqa: E402
import exportar  # noqa: E402
import limpeza  # noqa: E402
import repetidos  # noqa: E402

UM_MEGA = 1024 * 1024


def escrever(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo)


def jogo(identificador, arquivo, titulo, plataforma="snes", origem="pessoais", **extra):
    return dict({"id": identificador, "arquivo": arquivo, "titulo": titulo, "ordenacao": titulo.lower(),
                 "plataforma": plataforma, "plataforma_nome": plataforma.upper(), "origem": origem,
                 "origem_rotulo": "Meus jogos"}, **extra)


class TestRepetidos(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_repetidos_")
        self.addCleanup(limpeza.apagar_pasta, self.raiz)
        conteudo = os.urandom(UM_MEGA)
        self.a = os.path.join("jogos", "pessoais", "SNES", "Mario.sfc")
        self.b = os.path.join("jogos", "pessoais", "SNES", "baixados", "Mario (1).sfc")
        escrever(os.path.join(self.raiz, self.a), conteudo)
        escrever(os.path.join(self.raiz, self.b), conteudo)
        # mesmo tamanho, conteudo diferente no fim: NAO e' igual
        quase = bytearray(conteudo)
        quase[-10] ^= 0xFF
        self.c = os.path.join("jogos", "pessoais", "SNES", "Outro.sfc")
        escrever(os.path.join(self.raiz, self.c), bytes(quase))
        # mesmo titulo, outra regiao (arquivo diferente)
        self.d = os.path.join("jogos", "pessoais", "SNES", "Zelda (USA).sfc")
        self.e = os.path.join("jogos", "pessoais", "SNES", "Zelda (Europe).sfc")
        escrever(os.path.join(self.raiz, self.d), os.urandom(2048))
        escrever(os.path.join(self.raiz, self.e), os.urandom(4096))
        self.jogos = [jogo("a", self.a, "Mario"), jogo("b", self.b, "Mario"), jogo("c", self.c, "Outro"),
                      jogo("d", self.d, "Zelda"), jogo("e", self.e, "Zelda"),
                      jogo("loja", "C:/Steam/x.exe", "Mario", origem="steam")]

    def procurar(self, favoritos=(), recentes=()):
        return repetidos.procurar(self.jogos, self.raiz, favoritos, recentes)

    def test_acha_os_iguais_e_marca_o_que_sobra(self):
        r = self.procurar()
        self.assertEqual(len(r["iguais"]), 1)
        itens = {i["id"]: i for i in r["iguais"][0]["itens"]}
        self.assertEqual(set(itens), {"a", "b"})
        self.assertTrue(itens["a"]["fica"])                 # o caminho mais curto fica
        self.assertTrue(itens["b"]["marcado"])
        self.assertEqual(r["livra_bytes"], UM_MEGA)

    def test_o_mesmo_arquivo_por_dois_caminhos_nao_e_repetido(self):
        # duas pastas da lista que levam ao mesmo lugar: o mesmo arquivo, nunca "duas copias"
        outro = jogo("a2", os.path.join("jogos", "pessoais", "SNES", ".", "Mario.sfc"), "Mario")
        self.jogos.append(outro)
        r = self.procurar()
        ids = {i["id"] for g in r["iguais"] for i in g["itens"]}
        self.assertEqual(len([i for i in ids if i in ("a", "a2")]), 1)

    def test_fica_a_copia_da_pasta_do_arena_e_depois_a_do_cartao(self):
        # achado no A12 (13/11/2026): ficava a copia de uma pasta velha de projeto e saia a da ARENA-jogos
        self.assertEqual(repetidos._lugar("/storage/X/ARENA-jogos/PS2/a.iso", "cartao-1"), 1)
        self.assertEqual(repetidos._lugar("/storage/X/Projetos/arena/jogos/pessoais/PS2/a.iso", "cartao-2"), 2)
        self.assertEqual(repetidos._lugar("/qualquer/lugar/a.iso", "pessoais"), 0)

    def test_mesmo_tamanho_com_conteudo_diferente_nao_e_igual(self):
        r = self.procurar()
        ids = {i["id"] for g in r["iguais"] for i in g["itens"]}
        self.assertNotIn("c", ids)

    def test_traducao_que_muda_so_o_meio_do_arquivo_nao_e_igual(self):
        # o achado do A12 (13/11/2026): o patch muda poucos bytes longe do comeco, do meio e do fim
        conteudo = bytearray(open(os.path.join(self.raiz, self.a), "rb").read())
        conteudo[200000:200010] = b"TRADUZIDO!"
        caminho = os.path.join("jogos", "pessoais", "SNES", "Mario [T+Por].sfc")
        escrever(os.path.join(self.raiz, caminho), bytes(conteudo))
        self.jogos.append(jogo("t", caminho, "Mario"))
        r = self.procurar()
        iguais = {i["id"] for g in r["iguais"] for i in g["itens"]}
        self.assertNotIn("t", iguais)
        self.assertEqual(iguais, {"a", "b"})

    def test_mesmo_jogo_em_arquivos_diferentes_vem_sem_marca(self):
        r = self.procurar()
        self.assertEqual(len(r["mesmo_jogo"]), 1)
        self.assertEqual({i["id"] for i in r["mesmo_jogo"][0]["itens"]}, {"d", "e"})
        self.assertFalse(any(i["marcado"] for i in r["mesmo_jogo"][0]["itens"]))

    def test_jogo_de_loja_fica_de_fora(self):
        r = self.procurar()
        ids = {i["id"] for g in r["iguais"] + r["mesmo_jogo"] for i in g["itens"]}
        self.assertNotIn("loja", ids)

    def test_o_favorito_e_o_que_fica(self):
        r = self.procurar(favoritos=["b"])
        itens = {i["id"]: i for i in r["iguais"][0]["itens"]}
        self.assertTrue(itens["b"]["fica"])
        self.assertTrue(itens["a"]["marcado"])

    def test_apagar_tira_so_o_marcado(self):
        r = self.procurar()
        feito = repetidos.apagar(["b"], r, self.jogos, self.raiz, apagar_arquivo=lambda cs: [os.remove(c) for c in cs])
        self.assertEqual(feito["apagados"], ["Mario"])
        self.assertFalse(os.path.exists(os.path.join(self.raiz, self.b)))
        self.assertTrue(os.path.exists(os.path.join(self.raiz, self.a)))

    def test_nunca_apaga_todas_as_copias(self):
        r = self.procurar()
        repetidos.apagar(["a", "b"], r, self.jogos, self.raiz, apagar_arquivo=lambda cs: [os.remove(c) for c in cs])
        self.assertTrue(os.path.exists(os.path.join(self.raiz, self.a)))      # a que fica, fica

    def test_nunca_apaga_o_que_nao_esta_na_procura(self):
        r = self.procurar()
        repetidos.apagar(["c", "loja"], r, self.jogos, self.raiz, apagar_arquivo=lambda cs: [os.remove(c) for c in cs])
        self.assertTrue(os.path.exists(os.path.join(self.raiz, self.c)))

    def test_cue_leva_as_trilhas_mas_nao_as_de_outro_jogo(self):
        pasta = os.path.join(self.raiz, "jogos", "pessoais", "PS1")
        trilha = os.urandom(3000)
        for nome in ("Crash.bin", "Crash2.bin"):
            escrever(os.path.join(pasta, nome), trilha)
        escrever(os.path.join(pasta, "Crash.cue"), b'FILE "Crash.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        escrever(os.path.join(pasta, "Crash2.cue"), b'FILE "Crash2.bin" BINARY\n  TRACK 01 MODE2/2352\n')
        jogos = [jogo("x", os.path.join("jogos", "pessoais", "PS1", "Crash.cue"), "Crash", "ps1"),
                 jogo("y", os.path.join("jogos", "pessoais", "PS1", "Crash2.cue"), "Crash", "ps1")]
        r = repetidos.procurar(jogos, self.raiz)
        self.assertEqual(len(r["iguais"]), 1)
        marcado = [i for i in r["iguais"][0]["itens"] if i["marcado"]][0]
        self.assertEqual(marcado["arquivos"], 2)
        repetidos.apagar([marcado["id"]], r, jogos, self.raiz, apagar_arquivo=lambda cs: [os.remove(c) for c in cs])
        sobra = sorted(os.listdir(pasta))
        self.assertEqual(len(sobra), 2)          # o .cue e o .bin do que ficou

    def test_lista_de_discos_nao_se_apaga(self):
        caminho = os.path.join("jogos", "pessoais", "PS1", "Jogo.m3u")
        escrever(os.path.join(self.raiz, caminho), b"Jogo (Disc 1).chd\n")
        arquivos, motivo = repetidos.arquivos_do_jogo(jogo("m", caminho, "Jogo", "ps1"), self.raiz)
        self.assertTrue(motivo)

    def test_a_procura_em_segundo_plano_termina(self):
        procura = repetidos.Procura()
        self.assertTrue(procura.comecar(self.jogos, self.raiz))
        for _ in range(200):
            if not procura.estado()["rodando"]:
                break
            import time
            time.sleep(0.05)
        self.assertEqual(len(procura.resultado()["iguais"]), 1)


class TestEtiquetasELixeira(unittest.TestCase):
    """As variantes dos conjuntos de ROMs (GoodTools/No-Intro) e a Lixeira do ARENA (13/11/2026)."""

    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_variantes_")
        self.addCleanup(limpeza.apagar_pasta, self.raiz)
        self.pasta = os.path.join("jogos", "pessoais", "SNES")
        nomes = ["Mario (U) [!].smc", "Mario (U) [b1].smc", "Mario (U) [a1][hI].smc", "Mario (J).smc",
                 "Mario (J) [o1].smc", "Mario (E) [b1].smc", "Mario (U) [T+Por].smc", "Mario (U) [T+Por][h1].smc"]
        self.jogos = []
        for n, nome in enumerate(nomes):
            escrever(os.path.join(self.raiz, self.pasta, nome), os.urandom(1000 + n))
            self.jogos.append(jogo(str(n), os.path.join(self.pasta, nome), "Mario"))

    def marcados(self, r):
        return sorted(os.path.basename(i["arquivo"]) for g in r["mesmo_jogo"] for i in g["itens"] if i["marcado"])

    def test_so_as_variantes_ruins_com_copia_limpa_da_mesma_regiao(self):
        r = repetidos.procurar(self.jogos, self.raiz)
        # (E) [b1] nao tem copia limpa europeia: fica; traducoes em portugues ficam sempre
        self.assertEqual(self.marcados(r), ["Mario (J) [o1].smc", "Mario (U) [a1][hI].smc", "Mario (U) [b1].smc"])
        fica = sorted(os.path.basename(i["arquivo"]) for g in r["mesmo_jogo"] for i in g["itens"] if i["fica"])
        self.assertEqual(fica, ["Mario (J).smc", "Mario (U) [!].smc"])

    def test_apagar_fora_do_windows_vai_para_a_lixeira_do_arena_e_volta(self):
        r = repetidos.procurar(self.jogos, self.raiz)
        ids = [i["id"] for g in r["mesmo_jogo"] for i in g["itens"] if i["marcado"]]
        pasta_dos_jogos = os.path.join(self.raiz, "jogos")
        original = repetidos.vai_para_a_lixeira
        repetidos.vai_para_a_lixeira = lambda caminho: False        # como no celular e no Linux
        try:
            feito = repetidos.apagar(ids, r, self.jogos, self.raiz, pasta_dos_jogos=pasta_dos_jogos)
        finally:
            repetidos.vai_para_a_lixeira = original
        self.assertEqual(feito["lixeira"], "arena")
        self.assertEqual(len(feito["apagados"]), 3)
        self.assertFalse(os.path.exists(os.path.join(self.raiz, self.pasta, "Mario (U) [b1].smc")))
        cheias = repetidos.lixeiras(pasta_dos_jogos, ["pessoais"])
        self.assertEqual(cheias[0]["arquivos"], 3)
        self.assertNotIn(repetidos.NOME_DA_LIXEIRA, os.listdir(os.path.join(pasta_dos_jogos, "pessoais")))
        devolvidos, erros = repetidos.devolver_da_lixeira(cheias[0])
        self.assertEqual((devolvidos, erros), (3, []))
        self.assertTrue(os.path.exists(os.path.join(self.raiz, self.pasta, "Mario (U) [b1].smc")))
        self.assertEqual(repetidos.lixeiras(pasta_dos_jogos, ["pessoais"]), [])

    def test_esvaziar_apaga_de_vez(self):
        pasta_dos_jogos = os.path.join(self.raiz, "jogos")
        alvo = os.path.join(self.raiz, self.pasta, "Mario (U) [b1].smc")
        repetidos.para_a_lixeira_do_arena([alvo], os.path.realpath(os.path.join(pasta_dos_jogos, "pessoais")))
        cheia = repetidos.lixeiras(pasta_dos_jogos, ["pessoais"])[0]
        total, erros = repetidos.esvaziar_lixeira(cheia)
        self.assertEqual((total, erros), (1001, []))
        self.assertEqual(repetidos.lixeiras(pasta_dos_jogos, ["pessoais"]), [])


class TestExportar(unittest.TestCase):
    def test_copia_e_o_original_fica(self):
        raiz = tempfile.mkdtemp(prefix="arena_exportar_")
        self.addCleanup(limpeza.apagar_pasta, raiz)
        console = os.path.join(raiz, "jogos", "pessoais", "SNES")
        escrever(os.path.join(console, "Mario.sfc"), os.urandom(5000))
        destino = os.path.join(raiz, "cartao", cj.NOME_DA_PASTA, "SNES")
        novo = cj.levar_jogo(os.path.join(console, "Mario.sfc"), console, destino, manter_original=True)
        self.assertTrue(os.path.isfile(novo))
        self.assertTrue(os.path.isfile(os.path.join(console, "Mario.sfc")))

    def test_destinos_nao_quebra(self):
        lista = exportar.destinos()
        self.assertIsInstance(lista, list)
        for d in lista:
            self.assertIn("raiz", d)
            self.assertTrue(d["pasta"].endswith(cj.NOME_DA_PASTA))


if __name__ == "__main__":
    unittest.main()
