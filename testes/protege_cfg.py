r"""Protege o retroarch.cfg REAL enquanto um teste abre o RetroArch.

Achado real (revisao pos-auditoria): o RetroArch grava a configuracao ao
fechar (config_save_on_exit), e leva junto os valores que o teste mandou
por --appendconfig -- pastas temporarias que depois sao apagadas. O
retroarch.cfg de verdade ficou com saves e historico apontando para o Temp.

Uso, no fim de todo script que abre o RetroArch:

    if __name__ == "__main__":
        sys.exit(protege_cfg.rodar(main))

Guarda uma copia do arquivo antes, e devolve igualzinho no fim -- passou,
falhou ou deu erro no meio.
"""
import os
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")


def rodar(funcao):
    if not os.path.isfile(CFG):
        return funcao()
    guarda = tempfile.mkdtemp(prefix="arena_protege_cfg_")
    copia = os.path.join(guarda, "retroarch.cfg")
    shutil.copy2(CFG, copia)
    try:
        return funcao()
    finally:
        shutil.copy2(copia, CFG)
        shutil.rmtree(guarda, ignore_errors=True)
        print("[protege_cfg] retroarch.cfg real devolvido como estava antes do teste.")
