# -*- coding: utf-8 -*-
r"""Auditoria 2: o diagnostico de lentidao funciona com o PowerShell em "modo
de linguagem restrita" (Constrained Language Mode)?

Muita escola liga esse modo para aluno, por politica. Nele o PowerShell
roda, mas recusa [pscustomobject], [math], [Environment], [Convert] e
metodos de objetos que nao sejam texto/numero.

O teste roda o script do diagnostico duas vezes -- normal e com o modo
restrito ligado no inicio -- e compara o CONTEUDO, nao so se o campo existe
(a primeira versao deste teste contava so os campos e deixava passar lista
vazia).

Limite da simulacao: ligar o modo pelo proprio script e' mais duro que a
politica de verdade, porque bloqueia tambem os modulos da Microsoft
(Get-PhysicalDisk, Get-AppxPackage). Numa escola com modo restrito de
verdade esses modulos, assinados, continuam liberados. Por isso os campos
que dependem deles ficam fora da comparacao (CAMPOS_DE_MODULO).
"""
import json
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import barreiras  # noqa: E402

CAMPOS_DE_MODULO = {"disco_windows_tipo"}          # Get-PhysicalDisk (modulo Storage)
LISTAS = ("processos", "inicializacao", "servicos", "antivirus", "instalados")


def rodar(script):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                        "-Command", script], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    texto = r.stdout.strip()
    i = texto.find("{")
    try:
        return json.loads(texto[i:]) if i >= 0 else {}
    except ValueError:
        return {}


def main():
    base = barreiras._SCRIPT.replace("%SERVICOS%", ",".join("'%s'" % s for s in barreiras.SERVICOS_OBSERVADOS))
    normal = rodar(base)
    t = time.perf_counter()
    restrito = rodar('$ExecutionContext.SessionState.LanguageMode = "ConstrainedLanguage"\n' + base)
    segundos = time.perf_counter() - t
    print("Modo restrito respondeu em %.1f s" % segundos)
    ok = segundos < 60
    for lista in LISTAS:
        n, r = len(normal.get(lista) or []), len(restrito.get(lista) or [])
        # 'instalados' junta registro + Get-AppxPackage (modulo): no modo
        # restrito simulado so a parte do registro sobra -- tem que sobrar.
        certo = (r > 0 or n == 0) if lista == "instalados" else (r > 0) == (n > 0)
        ok = ok and certo
        print("  %-14s normal %4d | restrito %4d  %s" % (lista, n, r, "ok" if certo else "PERDEU"))
    escalares = [k for k in normal if k not in LISTAS and k not in CAMPOS_DE_MODULO]
    diferentes = [k for k in escalares if normal.get(k) != restrito.get(k)]
    print("  campos simples iguais nos dois modos: %d de %d%s" % (
        len(escalares) - len(diferentes), len(escalares),
        "" if not diferentes else "  DIFERENTES: %s" % diferentes))
    ok = ok and not diferentes
    lista = barreiras.avaliar(dict(restrito, nao_deu_para_ler=[]))
    print("  avaliar() com os fatos do modo restrito: %d barreira(s), sem erro" % len(lista))
    print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
