r"""Revisao pos-auditoria: limpa o retroarch.cfg real antes de distribuir.

1. Roda a mesma correcao automatica de caminhos que o ARENA roda a cada
   abertura (traz para dentro da pasta tudo que ficou apontando para fora).
2. Troca o netplay_nickname por "jogador": o arquivo vai para o pen drive de
   todo aluno, e estava com o nome completo de quem montou o pacote. O ARENA
   ja troca pelo apelido em toda partida; isto so vale para quem abrir o
   netplay pelo menu do proprio RetroArch.

Guarda uma copia do arquivo antes em backup\.

Uso:
    servidor\python\python.exe ferramentas\limpar_retroarch_cfg.py
"""
import os
import re
import shutil
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")

copia = os.path.join(RAIZ, "backup", "retroarch.cfg.antes-da-limpeza-" + time.strftime("%Y%m%d-%H%M%S"))
shutil.copy2(CFG, copia)
print("Copia guardada em", copia)

print("Caminhos corrigidos:", graficos.corrigir_caminhos_retroarch_cfg())

with open(CFG, encoding="utf-8", errors="replace") as f:
    texto = f.read()
novo, n = re.subn(r'(?m)^netplay_nickname = ".*"$', 'netplay_nickname = "jogador"', texto)
if n:
    graficos.gravar_atomico(CFG, novo)
print("Apelido de netplay trocado:", bool(n))
