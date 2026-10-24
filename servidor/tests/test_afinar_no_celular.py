# -*- coding: utf-8 -*-
"""A medida de quadros por segundo no celular de verdade (auditoria 4, 23/10/2026).

ferramentas\\afinar_no_celular.py le do SurfaceFlinger do Android a hora em
que cada quadro do RetroArch chegou a tela ("dumpsys SurfaceFlinger
--latency"): a primeira linha e' o tempo de uma volta da tela (em
nanossegundos); cada uma das outras, tres horas (pedida, apresentada, pronta).
"""
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import afinar_no_celular as afinar  # noqa: E402

PERIODO = 16666666          # 60 Hz


def saida(intervalos, inicio=10 ** 9):
    linhas, agora = [str(PERIODO)], inicio
    for intervalo in [0] + list(intervalos):
        agora += intervalo
        linhas.append("%d %d %d" % (agora - 1000, agora, agora - 500))
    linhas.append("0 0 0")               # o fim da lista vem com zeros
    return "\n".join(linhas)


class QuadrosPorSegundo(unittest.TestCase):
    def medir(self, texto):
        with mock.patch.object(afinar.base, "adb_texto", return_value=texto):
            return afinar.quadros_por_segundo("SurfaceView[io.github.rafaparise.arena/...RetroActivityFuture]")

    def test_60_quadros_redondos(self):
        fps, lentos = self.medir(saida([PERIODO] * 120))
        self.assertAlmostEqual(fps, 60.0, delta=0.5)
        self.assertEqual(lentos, 0.0)

    def test_jogo_que_cai_para_30(self):
        fps, lentos = self.medir(saida([2 * PERIODO] * 120))
        self.assertAlmostEqual(fps, 30.0, delta=0.5)
        self.assertEqual(lentos, 1.0)

    def test_sem_camada_ou_sem_quadros(self):
        self.assertEqual(afinar.quadros_por_segundo(None), (None, None))
        self.assertEqual(self.medir(str(PERIODO)), (None, None))


if __name__ == "__main__":
    unittest.main()
