# -*- coding: utf-8 -*-
"""Teste da correcao automatica de caminhos no retroarch.cfg.

Roda: servidor\\python\\python.exe ferramentas\\teste_correcao_caminhos.py

1. Faz uma copia do retroarch.cfg real.
2. Troca algumas linhas por caminhos de uma pasta antiga inventada,
   simulando o pen drive que mudou de letra / pasta que foi movida.
3. Chama a mesma funcao que o ARENA chama sozinho ao abrir.
4. Confere se os caminhos voltaram a apontar pra pasta atual.
5. Restaura o arquivo original no final, sempre - com sucesso ou erro.
"""
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import graficos  # noqa: E402

CAMINHO_CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")
BACKUP = CAMINHO_CFG + ".teste_backup"

PASTA_ANTIGA_FALSA = r"E:\pendrive\ARENA-velho"


def main():
    shutil.copy2(CAMINHO_CFG, BACKUP)
    try:
        with open(CAMINHO_CFG, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        alvo = {
            "log_dir": '%s\\dados' % PASTA_ANTIGA_FALSA,
            "playlist_directory": '%s\\dados' % PASTA_ANTIGA_FALSA,
            "content_favorites_path":
                '%s\\dados\\builtin\\content_favorites.lpl' % PASTA_ANTIGA_FALSA,
        }
        trocadas_no_teste = 0
        for i, linha in enumerate(linhas):
            for chave, valor_falso in alvo.items():
                if linha.startswith(chave + " ="):
                    linhas[i] = '%s = "%s"\n' % (chave, valor_falso)
                    trocadas_no_teste += 1
        with open(CAMINHO_CFG, "w", encoding="utf-8") as f:
            f.writelines(linhas)
        print("Sujado de proposito: %d linha(s) com pasta antiga falsa." % trocadas_no_teste)

        trocados = graficos.corrigir_caminhos_retroarch_cfg()
        print("corrigir_caminhos_retroarch_cfg() trocou: %d linha(s)" % trocados)

        with open(CAMINHO_CFG, "r", encoding="utf-8") as f:
            texto_novo = f.read()

        if PASTA_ANTIGA_FALSA.lower() in texto_novo.lower():
            print("FALHOU: ainda sobrou referencia a pasta antiga.")
            return 1

        import re
        ok = True
        for chave in alvo:
            m = re.search(r'^%s = "([^"]+)"' % chave, texto_novo, re.MULTILINE)
            if not m:
                print("FALHOU: nao achei a chave %s no arquivo corrigido." % chave)
                ok = False
                continue
            valor = m.group(1)
            if not valor.lower().startswith(RAIZ.lower()):
                print("FALHOU: %s = %s (nao comeca pela pasta atual)" % (chave, valor))
                ok = False
            else:
                print("OK: %s = %s" % (chave, valor))
        return 0 if ok else 1
    finally:
        shutil.copy2(BACKUP, CAMINHO_CFG)
        os.remove(BACKUP)
        print("Arquivo original restaurado.")


if __name__ == "__main__":
    sys.exit(main())
