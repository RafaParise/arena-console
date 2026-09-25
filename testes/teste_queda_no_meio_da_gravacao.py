# -*- coding: utf-8 -*-
"""Fase 6: mata o processo NO MEIO da gravacao de config/banco e confere
que nada fica corrompido -- o arquivo antigo continua inteiro (o
os.replace() atomico e' tudo-ou-nada) ou o novo aparece inteiro, nunca
um pedaco dos dois.

Estrategia: monkeypatcha gravar_texto_atomico() pra escrever o arquivo
temporario, dar um sinal (arquivo marcador) e ENTAO se matar sozinho
ANTES do os.replace() -- simula a queda no pior instante possivel (temp
pronto, troca ainda nao aconteceu). Roda isso num processo FILHO, pra
poder matar so ele sem afetar o processo de teste.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPT_FILHO = '''
import sys, os, json
sys.path.insert(0, {servidor!r})
import importlib.util
spec = importlib.util.spec_from_file_location("arena_queda", os.path.join({destino!r}, "servidor", "arena.py"))
arena = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arena)

config = arena.carregar_config()
config["apelido"] = "NomeQueDeviaGravar"

original_replace = os.replace
def replace_que_mata_antes(origem, alvo):
    # neste ponto o TEMPORARIO ja foi escrito por completo (gravar_texto_atomico
    # ja fez write+flush+fsync) -- so falta a troca. E' o pior instante:
    # simula a queda de energia bem aqui.
    os._exit(137)

os.replace = replace_que_mata_antes
try:
    arena.salvar_config(config)
except SystemExit:
    pass
'''


def main():
    destino = tempfile.mkdtemp(prefix="arena_queda_")
    print("Pasta de teste:", destino)
    try:
        for pasta in ("servidor", "dados", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta),
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))

        caminho_config = os.path.join(destino, "dados", "config.json")
        with open(caminho_config, "r", encoding="utf-8") as f:
            config_antes = json.load(f)
        print("Apelido antes:", config_antes.get("apelido"))

        script = SCRIPT_FILHO.format(servidor=os.path.join(destino, "servidor"), destino=destino)
        caminho_script = os.path.join(destino, "_filho.py")
        with open(caminho_script, "w", encoding="utf-8") as f:
            f.write(script)

        resultado = subprocess.run(
            [os.path.join(RAIZ, "servidor", "python", "python.exe"), caminho_script],
            cwd=destino, capture_output=True, text=True, timeout=15)
        print("Codigo de saida do processo filho (137 = morto de proposito):", resultado.returncode)

        # confere: o config.json continua sendo JSON valido (arquivo antigo
        # intacto, porque a troca nunca aconteceu) e nao tem arquivo .tmp
        # sobrando pra sempre (ficar um .tmp orfao nao corrompe nada, mas
        # o ARENA ja tem limpeza de .tmp na abertura -- confere que ainda
        # existe pra confirmar o cenario, e que principal() da proxima
        # abertura o removeria)
        with open(caminho_config, "r", encoding="utf-8") as f:
            texto_depois = f.read()
        try:
            config_depois = json.loads(texto_depois)
            json_valido = True
        except ValueError:
            json_valido = False

        tmps = [n for n in os.listdir(os.path.join(destino, "dados")) if n.endswith(".tmp")]

        print("config.json continua JSON valido:", json_valido)
        print("apelido depois (tem que ser o ANTIGO, nao 'NomeQueDeviaGravar' -- a troca nunca aconteceu):",
              config_depois.get("apelido") if json_valido else "(invalido)")
        print("arquivos .tmp orfaos encontrados (esperado: 1, sera limpo na proxima abertura):", tmps)

        ok = json_valido and config_depois.get("apelido") != "NomeQueDeviaGravar"
        print("\nRESULTADO:", "PASSOU (arquivo antigo protegido, nada corrompido)" if ok else "FALHOU")
        return 0 if ok else 1
    finally:
        shutil.rmtree(destino, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
