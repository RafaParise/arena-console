# -*- coding: utf-8 -*-
r"""Confere o servidor\multitap.json contra os nucleos que estao NESTA pasta.

O valor que liga o adaptador muda de nucleo para nucleo e as vezes entre
versoes do mesmo nucleo. Este script le os textos de dentro de cada .dll e
confere que a chave, cada valor e o "desligado" do mapa existem ali. Se um
nucleo for atualizado e renomear alguma coisa, e' aqui que aparece -- antes
de o aluno descobrir na aula.

O numero de um "dispositivo" (ex.: 257) nao fica escrito no .dll; para ele
o script confere o NOME do dispositivo, e o numero vem da fonte anotada no
mapa.

Uso:
    servidor\python\python.exe ferramentas\conferir_mapa_multitap.py
Sai com codigo 1 se alguma coisa nao bater.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def textos_do_arquivo(caminho):
    dados = open(caminho, "rb").read()
    return set(m.group(0).decode("ascii") for m in re.finditer(rb"[\x20-\x7e]{2,}", dados))


def principal():
    mapa = json.load(open(os.path.join(RAIZ, "servidor", "multitap.json"), encoding="utf-8"))
    falhas = 0

    exe = os.path.join(RAIZ, "retroarch", "retroarch.exe")
    chaves_ra = [mapa["retroarch"]["limite_jogar_junto"]["chave"],
                 mapa["retroarch"]["controles_no_mesmo_computador"]["chave"]]
    textos_exe = textos_do_arquivo(exe)
    for chave in chaves_ra:
        ok = chave in textos_exe
        falhas += not ok
        print("[%s] retroarch.exe conhece '%s'" % ("OK" if ok else "FALHOU", chave))

    for nucleo, info in mapa["nucleos"].items():
        caminho = os.path.join(RAIZ, "retroarch", "cores", nucleo)
        if not os.path.isfile(caminho):
            print("[FALHOU] %s: nucleo nao esta na pasta" % nucleo)
            falhas += 1
            continue
        adaptador = info["adaptador"]
        tipo = adaptador["tipo"]
        textos = textos_do_arquivo(caminho)
        procurar = []
        if tipo == "opcao_do_nucleo":
            procurar += list(adaptador["chaves"].keys())
            procurar += [v for v in adaptador["chaves"].values()]
            procurar.append(adaptador["desligado"])
            procurar += list(adaptador.get("valores_possiveis", {}))
            procurar += list(adaptador.get("segundo_adaptador", {}).get("chaves", {}))
        elif tipo == "dispositivo":
            # O nome como o nucleo mostra no menu (sem o que esta entre parenteses).
            procurar.append(adaptador["nome_no_nucleo"].split(" (")[0])
        faltando = [t for t in dict.fromkeys(procurar) if t not in textos]
        if tipo == "nenhum":
            print("[OK] %s: sem adaptador (%d jogadores de fabrica)" % (nucleo, info["jogadores_sem_adaptador"]))
            continue
        falhas += bool(faltando)
        print("[%s] %s: %s" % ("FALHOU" if faltando else "OK", nucleo,
                               "faltando no .dll: %s" % faltando if faltando else
                               "%d textos conferidos (%s)" % (len(dict.fromkeys(procurar)), tipo)))

    print("\n%s" % ("Mapa confere com os nucleos da pasta." if not falhas else
                    "%d item(ns) nao bate(m): atualize o mapa antes de usar." % falhas))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(principal())
