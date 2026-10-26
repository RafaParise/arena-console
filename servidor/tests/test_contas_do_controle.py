# -*- coding: utf-8 -*-
"""As contas da tela do controle no celular (launcher\\controle\\controle.js): zona morta, curva, diagonais e volante.

Inspiradas no DroidJoy e no GameSir Nexus (pedido do Rafael, 25/10/2026). O JavaScript e' o da propria pagina, rodado no
Node.js (so se ele estiver na maquina; sem ele o teste e' pulado): sao so funcoes puras, entre as marcas
"contas puras" e "fim das contas puras".
"""
import json
import math
import os
import re
import shutil
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NODE = shutil.which("node")


def rodar(expressao):
    """Roda uma expressao JavaScript com as contas da pagina e devolve o resultado (JSON)."""
    with open(os.path.join(RAIZ, "launcher", "controle", "controle.js"), encoding="utf-8") as arquivo:
        fonte = arquivo.read()
    achou = re.search(r"// ==== contas puras.*?// ==== fim das contas puras ====", fonte, re.S)
    if not achou:
        raise AssertionError("as marcas das contas puras sumiram do controle.js")
    programa = achou.group(0) + "\nconsole.log(JSON.stringify(%s));" % expressao
    feito = subprocess.run([NODE, "-e", programa], capture_output=True, timeout=30)
    if feito.returncode:
        raise AssertionError(feito.stderr.decode("utf-8", "replace"))
    return json.loads(feito.stdout.decode("utf-8"))


@unittest.skipUnless(NODE, "sem o Node.js nesta maquina")
class AZonaMortaEACurva(unittest.TestCase):
    def test_dentro_da_zona_morta_nao_vale_nada(self):
        self.assertEqual(rodar("aplicarZonaECurva(0.1, 0, 0.12, 'linear')"), [0, 0])
        self.assertEqual(rodar("aplicarZonaECurva(0, 0, 0, 'linear')"), [0, 0])

    def test_depois_da_zona_o_curso_comeca_do_zero(self):
        # zona de 20%: o dedo em 60% do curso vale (0,6 - 0,2) / 0,8 = 50%
        self.assertAlmostEqual(rodar("aplicarZonaECurva(0.6, 0, 0.2, 'linear')")[0], 0.5)
        self.assertEqual(rodar("aplicarZonaECurva(1, 0, 0.2, 'linear')"), [1, 0])

    def test_as_curvas(self):
        suave = rodar("aplicarZonaECurva(0.6, 0, 0.2, 'suave')")[0]
        rapida = rodar("aplicarZonaECurva(0.6, 0, 0.2, 'rapida')")[0]
        self.assertAlmostEqual(suave, 0.25)                    # fina no comeco
        self.assertAlmostEqual(rapida, math.sqrt(0.5))         # forte no comeco

    def test_a_direcao_do_dedo_se_mantem(self):
        x, y = rodar("aplicarZonaECurva(0.3, 0.4, 0.1, 'linear')")
        self.assertAlmostEqual(math.atan2(y, x), math.atan2(0.4, 0.3))
        self.assertAlmostEqual(math.hypot(x, y), (0.5 - 0.1) / 0.9)

    def test_nunca_passa_do_curso_inteiro(self):
        for entrada in ("(2, 0, 0.1, 'linear')", "(0.8, 0.8, 0.3, 'rapida')", "(-5, 5, 0, 'suave')"):
            x, y = rodar("aplicarZonaECurva%s" % entrada)
            self.assertLessEqual(math.hypot(x, y), 1.0000001, entrada)


@unittest.skipUnless(NODE, "sem o Node.js nesta maquina")
class OsDirecionais(unittest.TestCase):
    CIMA, BAIXO, ESQUERDA, DIREITA = 1 << 4, 1 << 5, 1 << 6, 1 << 7

    def bits(self, dx, dy, limite=0.38):
        return rodar("bitsDoDirecional(%s, %s, 100, %s)" % (dx, dy, limite))

    def test_no_meio_nao_vale_nada(self):
        self.assertEqual(self.bits(5, 5), 0)

    def test_as_quatro_direcoes(self):
        self.assertEqual(self.bits(0, -40), self.CIMA)
        self.assertEqual(self.bits(0, 40), self.BAIXO)
        self.assertEqual(self.bits(-40, 0), self.ESQUERDA)
        self.assertEqual(self.bits(40, 0), self.DIREITA)

    def test_diagonal_perto_dos_45_graus(self):
        self.assertEqual(self.bits(30, -30), self.CIMA | self.DIREITA)
        self.assertEqual(self.bits(-30, 30), self.BAIXO | self.ESQUERDA)

    def test_o_ajuste_das_diagonais_muda_o_tamanho_da_zona(self):
        # a 30 graus acima da direita (seno 0,5): com limite 0,25 ja pega a diagonal; com 0,55, so a direita
        dx, dy = 40 * math.cos(math.radians(30)), -40 * math.sin(math.radians(30))     # 30 graus acima da direita
        self.assertEqual(self.bits(dx, dy, 0.25), self.CIMA | self.DIREITA)            # diagonal facil
        self.assertEqual(self.bits(dx, dy, 0.55), self.DIREITA)                        # diagonal dificil
        # a 45 graus certinho, a diagonal sai nos dois (ate 0,70)
        self.assertEqual(self.bits(30, -30, 0.55), self.CIMA | self.DIREITA)


@unittest.skipUnless(NODE, "sem o Node.js nesta maquina")
class OVolante(unittest.TestCase):
    def eixo(self, angulo, maximo=40, zona=0, curva="linear", inverter="false"):
        return rodar("eixoDaInclinacao(%s, %s, %s, '%s', %s)" % (angulo, maximo, zona, curva, inverter))

    def test_reto_nao_vira(self):
        self.assertEqual(self.eixo(0), 0)

    def test_o_curso_inteiro_no_giro_maximo_e_nunca_mais(self):
        self.assertEqual(self.eixo(40), 32767)
        self.assertEqual(self.eixo(90), 32767)
        self.assertEqual(self.eixo(-90), -32767)

    def test_metade_do_giro_e_meio_curso(self):
        self.assertEqual(self.eixo(20), round(0.5 * 32767))

    def test_inverter_troca_o_lado(self):
        self.assertLessEqual(abs(self.eixo(20, inverter="true") + self.eixo(20)), 1)          # o Math.round do JS arredonda -0,5 para cima

    def test_zona_morta_do_volante(self):
        self.assertEqual(self.eixo(2, zona=0.1), 0)                    # 2/40 = 5% < 10%
        self.assertGreater(self.eixo(10, zona=0.1), 0)


if __name__ == "__main__":
    unittest.main()
