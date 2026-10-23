# -*- coding: utf-8 -*-
"""A configuracao que o pacote leva como modelo (pedido de 22/10/2026).

O pedido do Rafael: "a atualizacao deve ser abrir a pasta compactada copiar
tudo e arrastar para o arena e atualiza sem perder nada de progresso, perfil,
saves e nem bios importantes ou suas configuracoes". O pacote completo traz
a configuracao do RetroArch e dos emuladores como "<arquivo>.padrao"
(graficos.CONFIGURACOES_COM_MODELO); o ARENA so copia o modelo quando a de
verdade ainda nao existe. O pacote inteiro copiado por cima de um ARENA em
uso: testes\\teste_atualizar_por_cima.py.
"""
import os
import sys
import tempfile
import unittest

PASTA_SERVIDOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PASTA_SERVIDOR not in sys.path:
    sys.path.insert(0, PASTA_SERVIDOR)

import graficos  # noqa: E402

PASTA_TESTES = os.path.join(os.path.dirname(PASTA_SERVIDOR), "testes")
if PASTA_TESTES not in sys.path:
    sys.path.insert(0, PASTA_TESTES)
import limpeza  # noqa: E402


class Modelos(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="arena_teste_modelo_")

    def tearDown(self):
        limpeza.apagar_pasta(self.raiz)

    def escrever(self, rel, texto):
        caminho = os.path.join(self.raiz, rel)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)

    def ler(self, rel):
        with open(os.path.join(self.raiz, rel), encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_primeira_vez_o_modelo_vira_a_configuracao(self):
        for rel in graficos.CONFIGURACOES_COM_MODELO:
            self.escrever(rel + graficos.SUFIXO_DO_MODELO, "modelo de %s\n" % rel)
        instalados = graficos.instalar_configuracoes_que_faltam(self.raiz)
        self.assertEqual(sorted(instalados), sorted(graficos.CONFIGURACOES_COM_MODELO))
        for rel in graficos.CONFIGURACOES_COM_MODELO:
            self.assertEqual(self.ler(rel), "modelo de %s\n" % rel)
        self.assertEqual(graficos.instalar_configuracoes_que_faltam(self.raiz), [], "segunda vez nao troca nada")

    def test_a_configuracao_de_quem_usa_nunca_e_trocada(self):
        rel = graficos.CONFIGURACOES_COM_MODELO[0]
        self.escrever(rel, 'video_scale = "7"\n')
        self.escrever(rel + graficos.SUFIXO_DO_MODELO, "modelo novo\n")
        self.assertEqual(graficos.instalar_configuracoes_que_faltam(self.raiz), [])
        self.assertEqual(self.ler(rel), 'video_scale = "7"\n')

    def test_sem_modelo_nada_acontece(self):
        self.assertEqual(graficos.instalar_configuracoes_que_faltam(self.raiz), [])
        self.assertEqual(os.listdir(self.raiz), [])

    def test_lista_tem_o_retroarch_e_os_emuladores(self):
        nomes = {os.path.basename(rel) for rel in graficos.CONFIGURACOES_COM_MODELO}
        self.assertTrue({"retroarch.cfg", "PCSX2.ini", "config.yml"} <= nomes)


if __name__ == "__main__":
    unittest.main()
