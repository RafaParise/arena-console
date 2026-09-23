"""Confere a correcao da Fase 2: os logs do RetroArch agora tem rodizio
(mantem so os LOGS_MANTIDOS mais recentes), em vez de acumular para sempre.

Testa a funcao limpar_logs_antigos() contra uma pasta temporaria (nao mexe
em dados\\ de verdade), criando arquivos de log falsos.
"""
import importlib.util
import os
import shutil
import sys
import tempfile


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    destino = tempfile.mkdtemp(prefix="arena_teste_logs_")
    try:
        caminho_arena = os.path.join(RAIZ, "servidor", "arena.py")
        spec = importlib.util.spec_from_file_location("arena_teste_logs", caminho_arena)
        arena = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        spec.loader.exec_module(arena)

        arena.PASTA_DADOS = destino

        nomes_esperados_16 = []
        for i in range(16):
            nome = "retroarch__2026_09_22__%02d_00_00.log" % i
            with open(os.path.join(destino, nome), "w") as f:
                f.write("log falso")
            nomes_esperados_16.append(nome)
        # Um arquivo que NAO e log do RetroArch -- nao pode ser tocado.
        with open(os.path.join(destino, "config.json"), "w") as f:
            f.write("{}")

        print("Antes:", len(os.listdir(destino)), "arquivos")
        apagados = arena.limpar_logs_antigos()
        print("Apagados:", apagados)

        restantes = sorted(os.listdir(destino))
        logs_restantes = [n for n in restantes if n.startswith("retroarch__")]
        print("Depois:", len(restantes), "arquivos totais,", len(logs_restantes), "logs")
        print("Logs que sobraram:", logs_restantes)

        ok = (apagados == 16 - arena.LOGS_MANTIDOS
              and len(logs_restantes) == arena.LOGS_MANTIDOS
              and "config.json" in restantes
              and logs_restantes == sorted(nomes_esperados_16)[-arena.LOGS_MANTIDOS:])
        print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
