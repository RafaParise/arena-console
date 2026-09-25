# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: o VERIFICAR.bat avisa quando o caminho do save
de um jogo passaria do limite do Windows (260 letras)?

Numa copia isolada, cria dois jogos falsos (arquivo vazio): um de nome
curto e um de nome bem comprido. So o comprido pode ser acusado.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    destino = tempfile.mkdtemp(prefix="arena_caminho_")
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        for pasta in ("dados", "backup", "launcher", "retroarch"):
            os.makedirs(os.path.join(destino, pasta), exist_ok=True)
        pasta_jogo = os.path.join(destino, "jogos", "pessoais", "Super Nintendo")
        os.makedirs(pasta_jogo)
        curto = "Jogo Curto (USA).sfc"
        # Nome comprido, mas que ainda cabe como arquivo (o problema e' o SAVE)
        folga = 255 - len(os.path.join(pasta_jogo, "")) - len(".sfc")
        comprido = ("Jogo Com Nome Muito Comprido (USA) (Rev 1) [T-En by Tradutor v1.0] "
                    * 5)[:max(20, folga)].rstrip() + ".sfc"
        for nome in (curto, comprido):
            open(os.path.join(pasta_jogo, nome), "wb").close()

        codigo = open(os.path.join(destino, "servidor", "diagnostico.py"), encoding="utf-8").read()
        sys.argv = ["diagnostico.py", "--so-ver", "--sem-barreiras"]
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            try:
                exec(compile(codigo, os.path.join(destino, "servidor", "diagnostico.py"), "exec"),
                     {"__name__": "__main__",
                      "__file__": os.path.join(destino, "servidor", "diagnostico.py")})
            except SystemExit:
                pass
        texto = saida.getvalue()
        trecho = texto[texto.find("podem nao conseguir salvar"):][:700] if "podem nao" in texto else "(sem aviso)"
        print(trecho)
        acusou_comprido = comprido[:40] in texto
        acusou_curto = curto in texto
        print("\nAcusou o jogo de nome comprido:", acusou_comprido)
        print("Acusou o jogo de nome curto por engano:", acusou_curto)
        ok = acusou_comprido and not acusou_curto
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
