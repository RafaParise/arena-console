r"""Poe o protetor do retroarch.cfg (testes\protege_cfg.py) em todo script
de teste que abre o RetroArch com --appendconfig. Roda uma vez so.
"""
import glob
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIM_ANTIGO = 'if __name__ == "__main__":\n    sys.exit(main())'
FIM_NOVO = (
    'if __name__ == "__main__":\n'
    '    # Devolve o retroarch.cfg real como estava (o RetroArch grava ao\n'
    '    # fechar, e levaria junto as pastas temporarias deste teste).\n'
    '    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(\n'
    '        os.path.abspath(__file__))), "testes"))\n'
    '    import protege_cfg\n'
    '    sys.exit(protege_cfg.rodar(main))'
)

for pasta in ("testes", "ferramentas"):
    for caminho in sorted(glob.glob(os.path.join(RAIZ, pasta, "*.py"))):
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        if "--appendconfig" not in texto or "protege_cfg" in texto:
            continue
        if FIM_ANTIGO not in texto:
            print("NAO MEXI (fim diferente):", caminho)
            continue
        if "\nimport os\n" not in texto:
            print("NAO MEXI (sem import os):", caminho)
            continue
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto.replace(FIM_ANTIGO, FIM_NOVO))
        print("protegido:", os.path.relpath(caminho, RAIZ))
