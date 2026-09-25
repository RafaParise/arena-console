# -*- coding: utf-8 -*-
"""Fase 6: confere a deteccao de FAT32 + arquivo maior que 4GB no
diagnostico.py (VERIFICAR.bat). Usa uma copia isolada, um arquivo
ESPARSO (ocupa quase nada de disco de verdade, so reserva o tamanho) e
finge que o disco e' FAT32 via monkeypatch -- nao precisa formatar um
pen drive de verdade pra provar a logica.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    destino = tempfile.mkdtemp(prefix="arena_fat32_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
        pasta_jogo = os.path.join(destino, "jogos", "pessoais", "PS2")
        os.makedirs(pasta_jogo, exist_ok=True)
        os.makedirs(os.path.join(destino, "backup"), exist_ok=True)
        os.makedirs(os.path.join(destino, "launcher"), exist_ok=True)
        os.makedirs(os.path.join(destino, "retroarch"), exist_ok=True)

        # Arquivos esparsos -- so reservam o tamanho, nao escrevem gigabytes
        # de verdade no disco. Corrigido na Fase 8: a versao anterior usava
        # 4,5 GB, tamanho que NAO PODE existir num FAT32 de verdade (o teste
        # passava num caso impossivel). Agora:
        #  - um no tamanho maximo do FAT32 (4 GB - 1 byte) = copia cortada,
        #    TEM que ser acusado;
        #  - um de 3 GB = jogo normal, NAO pode ser acusado.
        def esparso(nome, tamanho):
            with open(os.path.join(pasta_jogo, nome), "wb") as f:
                f.seek(tamanho - 1)
                f.write(b"\x00")
        esparso("Jogo Grande de Teste.iso", 4 * 1024 * 1024 * 1024 - 1)
        esparso("Jogo Normal de Teste.iso", 3 * 1024 * 1024 * 1024)

        sys.path.insert(0, os.path.join(destino, "servidor"))
        spec = importlib.util.spec_from_file_location("hardware_fat32_teste", os.path.join(destino, "servidor", "hardware.py"))
        hardware = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hardware)
        hardware.sistema_de_arquivos = lambda pasta: "FAT32"  # finge FAT32
        sys.modules["hardware"] = hardware

        sys.argv = ["diagnostico.py", "--so-ver"]
        caminho_diag_original = os.path.join(destino, "servidor", "diagnostico.py")
        codigo = open(caminho_diag_original, encoding="utf-8").read()
        codigo = codigo.replace('RAIZ = os.path.dirname(PASTA_SERVIDOR)',
                                'RAIZ = %r' % destino)

        import io
        import contextlib
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            try:
                exec(compile(codigo, caminho_diag_original, "exec"),
                     {"__name__": "__main__", "__file__": caminho_diag_original})
            except SystemExit:
                pass

        texto = saida.getvalue()
        print(texto[texto.find("8. Espaco"):texto.find("9. Copias")])

        achou_arquivo = "Jogo Grande de Teste.iso" in texto
        achou_grave = "GRAVE" in texto and "FAT32" in texto
        acusou_normal = "Jogo Normal de Teste.iso" in texto
        print("Detectou o arquivo cortado no limite:", achou_arquivo)
        print("Marcou como GRAVE:", achou_grave)
        print("Acusou o jogo normal por engano:", acusou_normal)

        ok = achou_arquivo and achou_grave and not acusou_normal
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
