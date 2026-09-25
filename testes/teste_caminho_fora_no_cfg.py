# -*- coding: utf-8 -*-
"""Revisao pos-auditoria: retroarch.cfg com caminho para FORA do ARENA.

Achado real: um teste abriu o RetroArch com pastas temporarias, o RetroArch
gravou isso ao fechar (config_save_on_exit), e o retroarch.cfg de verdade
ficou com saves, estados, log e historico apontando para uma pasta do Temp
ja apagada. A correcao automatica (graficos.corrigir_caminhos_retroarch_cfg)
so sabia consertar caminho que tivesse "dados", "retroarch"... no meio.

Numa copia isolada, monta um retroarch.cfg com esses caminhos de fora e
confere que, depois da correcao, TODOS apontam para dentro da pasta.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORA = r"C:\Users\alguem\AppData\Local\Temp\arena_teste_xyz\imagem"

LINHAS = {
    "savefile_directory": FORA + r"\saves",
    "savestate_directory": FORA + r"\states",
    "log_dir": FORA,
    "playlist_directory": FORA,
    "content_history_path": FORA + r"\builtin\content_history.lpl",
    "content_favorites_path": FORA + r"\builtin\content_favorites.lpl",
}


def main():
    destino = tempfile.mkdtemp(prefix="arena_cfg_fora_")
    try:
        shutil.copytree(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"),
                        ignore=shutil.ignore_patterns("__pycache__", "tests", "python"))
        os.makedirs(os.path.join(destino, "retroarch"))
        cfg = os.path.join(destino, "retroarch", "retroarch.cfg")
        with open(cfg, "w", encoding="utf-8") as f:
            for chave, valor in LINHAS.items():
                f.write('%s = "%s"\n' % (chave, valor))
            f.write('video_driver = "gl"\n')  # linha que nao e caminho: nao pode mudar

        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location(
            "graficos_cfg_fora", os.path.join(destino, "servidor", "graficos.py"))
        graficos = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(graficos)

        trocados = graficos.corrigir_caminhos_retroarch_cfg()
        texto = open(cfg, encoding="utf-8").read()
        print(texto)

        ok = True
        for chave in LINHAS:
            linha = [l for l in texto.splitlines() if l.startswith(chave + " ")][0]
            dentro = destino.lower() in linha.lower()
            ok = ok and dentro
            print("  %-26s %s" % (chave, "dentro do ARENA" if dentro else "AINDA FORA (bug)"))
        esperado_saves = os.path.join(destino, "retroarch", "saves")
        ok = ok and ('savefile_directory = "%s"' % esperado_saves) in texto
        ok = ok and 'video_driver = "gl"' in texto
        ok = ok and FORA.lower() not in texto.lower()
        print("\nLinhas trocadas:", trocados)
        print("RESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        sys.path = [p for p in sys.path if not p.startswith(destino)]
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
