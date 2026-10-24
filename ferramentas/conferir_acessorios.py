# -*- coding: utf-8 -*-
"""Confere o catalogo de acessorios (servidor\\acessorios.json) com o que os nucleos libretro dizem de si mesmos.

Cada chave de opcao e cada tipo de controle do catalogo tem que existir no nucleo, e cada valor tem que estar na lista
que o nucleo aceita. Se um nucleo mudar de nome de opcao numa versao nova, esta conferencia acusa antes de a pessoa
ligar um acessorio que nao faria nada.

Como usar (Windows, com o Python embutido; precisa dos nucleos em retroarch\\cores):
    servidor\\python\\python.exe ferramentas\\levantar_opcoes_dos_nucleos.py --saida opcoes_dos_nucleos.json
    servidor\\python\\python.exe ferramentas\\conferir_acessorios.py opcoes_dos_nucleos.json
Sai com codigo 1 se achar problema. Grupos de nucleos que nao existem no computador (como o ARMSX2 do Android) sao so
avisados: nao ha o que perguntar a eles aqui.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))

import acessorios  # noqa: E402


def conferir(dump, grupos=None):
    """Devolve (problemas, avisos): listas de frases. 'dump' e' o JSON de levantar_opcoes_dos_nucleos.py."""
    problemas, avisos = [], []
    nucleos = dump.get("nucleos", {})
    for grupo in (grupos if grupos is not None else acessorios.carregar()):
        arquivo = "%s_libretro.dll" % grupo["nucleo"]
        lido = nucleos.get(arquivo)
        if lido is None or "erro" in lido:
            avisos.append("%s: nao foi lido neste computador (%s); %d acessorio(s) sem conferir"
                          % (grupo["nucleo"], (lido or {}).get("erro", "arquivo ausente"), len(grupo["acessorios"])))
            continue
        opcoes = lido.get("opcoes", {})
        portas = lido.get("controles", [])
        for acessorio in grupo["acessorios"]:
            for controle in acessorio.get("controles", []):
                alvo = controle.get("alvo") or {}
                onde = "%s / %s / %s" % (grupo["nucleo"], acessorio.get("id"), controle.get("id"))
                if alvo.get("opcao"):
                    opcao = opcoes.get(alvo["opcao"])
                    if opcao is None:
                        problemas.append("%s: o nucleo nao tem a opcao %s" % (onde, alvo["opcao"]))
                        continue
                    aceitos = {v["valor"] for v in opcao.get("valores", [])}
                    if controle.get("tipo") == "chave":
                        pedidos = [controle.get("ligado"), controle.get("desligado")]
                    else:
                        pedidos = [str(par[0]) for par in controle.get("escolhas", []) if par and str(par[0]) != ""]
                        padrao = controle.get("padrao", "")
                        if padrao != "" and str(padrao) not in aceitos:
                            problemas.append("%s: o padrao %r nao esta entre os valores do nucleo" % (onde, padrao))
                    for valor in pedidos:
                        if aceitos and valor not in aceitos:
                            problemas.append("%s: o valor %r nao e' aceito pela opcao %s (aceita: %s)"
                                             % (onde, valor, alvo["opcao"], ", ".join(sorted(aceitos)[:8])))
                elif alvo.get("porta") is not None:
                    numero = int(alvo["porta"])
                    if numero > len(portas):
                        problemas.append("%s: o nucleo so tem %d porta(s) de controle, e o catalogo pede a %d"
                                         % (onde, len(portas), numero))
                        continue
                    ids = {str(t["id"]) for t in portas[numero - 1]}
                    for par in controle.get("escolhas", []):
                        valor = str(par[0]) if par else ""
                        if valor != "" and valor not in ids:
                            problemas.append("%s: o tipo de controle %s nao existe na porta %d do nucleo"
                                             % (onde, valor, numero))
    return problemas, avisos


def principal(argumentos):
    if len(argumentos) != 2:
        print(__doc__)
        return 2
    with open(argumentos[1], encoding="utf-8") as arquivo:
        dump = json.load(arquivo)
    problemas, avisos = conferir(dump)
    for frase in avisos:
        print("AVISO:", frase)
    for frase in problemas:
        print("PROBLEMA:", frase)
    todos = sum(len(g["acessorios"]) for g in acessorios.carregar())
    print("%d acessorios no catalogo, %d problema(s), %d aviso(s)." % (todos, len(problemas), len(avisos)))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv))
