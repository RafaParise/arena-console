"""Fase 1 da auditoria: varredura de codigo morto e problemas conhecidos.

So le codigo, nao muda nada (a lista de remocao so e aplicada depois que
o Rafael aprovar). Usa so a biblioteca padrao (regra 5 do PLANO-AUDITORIA.md).

Gera pistas, nao veredito: cada candidato encontrado aqui ainda precisa de
conferencia manual antes de entrar na lista de remocao (regra 3 -- prova de
verdade, nao suposicao de regex).

Uso:
    servidor\\python\\python.exe testes\\varredura_fase1.py
"""
import ast
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVIDOR = os.path.join(RAIZ, "servidor")
LAUNCHER = os.path.join(RAIZ, "launcher")

ARQUIVOS_PY = []
for raiz, subpastas, arquivos in os.walk(SERVIDOR):
    if os.path.basename(raiz) in ("python", "tests", "__pycache__"):
        subpastas[:] = []
        continue
    for nome in arquivos:
        if nome.endswith(".py"):
            ARQUIVOS_PY.append(os.path.join(raiz, nome))

ARQUIVOS_JS = [os.path.join(LAUNCHER, n) for n in os.listdir(LAUNCHER) if n.endswith(".js")]


def ler(caminho):
    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


TEXTO_PY = {c: ler(c) for c in ARQUIVOS_PY}
TEXTO_JS = {c: ler(c) for c in ARQUIVOS_JS}
TEXTO_TUDO = "\n".join(TEXTO_PY.values()) + "\n" + "\n".join(TEXTO_JS.values())


def funcoes_definidas():
    """Nome de toda funcao/metodo de topo ou de classe, por arquivo."""
    resultado = []
    for caminho, texto in TEXTO_PY.items():
        try:
            arvore = ast.parse(texto, filename=caminho)
        except SyntaxError as falha:
            resultado.append(("ERRO_SINTAXE", caminho, str(falha)))
            continue
        for no in ast.walk(arvore):
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                resultado.append((no.name, caminho, no.lineno))
    return resultado


def contar_uso(nome):
    """Conta quantas vezes 'nome(' aparece em todo o codigo (inclui a definicao)."""
    padrao = re.compile(r"\b" + re.escape(nome) + r"\s*\(")
    return len(padrao.findall(TEXTO_TUDO))


DUNDER = {"__init__", "__str__", "__repr__", "__enter__", "__exit__", "__eq__", "__lt__", "__call__"}


def candidatos_funcao_morta():
    candidatos = []
    for nome, caminho, linha in funcoes_definidas():
        if nome == "ERRO_SINTAXE":
            continue
        if nome.startswith("test_") or nome in ("setUp", "tearDown"):
            continue
        if nome in DUNDER:
            continue
        usos = contar_uso(nome)
        if usos <= 1:
            candidatos.append({"funcao": nome, "arquivo": os.path.relpath(caminho, RAIZ), "linha": linha, "ocorrencias": usos})
    return candidatos


def chaves_config_padrao():
    caminho = os.path.join(SERVIDOR, "arena.py")
    texto = TEXTO_PY[caminho]
    m = re.search(r"def config_padrao\(\):(.*?)\n\ndef ", texto, re.S)
    if not m:
        return []
    bloco = m.group(1)
    chaves = re.findall(r'"([a-z_]+)":', bloco)
    return sorted(set(chaves))


def uso_de_chave(chave):
    padrao = re.compile(r'["\']' + re.escape(chave) + r'["\']')
    return len(padrao.findall(TEXTO_TUDO))


def excecoes_silenciosas():
    achados = []
    for caminho, texto in TEXTO_PY.items():
        linhas = texto.splitlines()
        for i, linha in enumerate(linhas):
            if re.match(r"\s*except\s*:\s*$", linha) or re.match(r"\s*except\s+\w+(\.\w+)*\s*:\s*$", linha):
                seguinte = linhas[i + 1].strip() if i + 1 < len(linhas) else ""
                if seguinte in ("pass", "continue", "..."):
                    achados.append({"arquivo": os.path.relpath(caminho, RAIZ), "linha": i + 1, "trecho": linha.strip() + " " + seguinte})
    return achados


def open_sem_with():
    achados = []
    for caminho, texto in TEXTO_PY.items():
        for i, linha in enumerate(texto.splitlines()):
            if re.search(r"(?<!with )(?<!\.)\bopen\(", linha) and " as " not in linha:
                # ignora linhas obviamente dentro de "with" multiline ou comentarios
                trecho = linha.strip()
                if trecho.startswith("#"):
                    continue
                if "with open(" in trecho or "with codecs.open(" in trecho:
                    continue
                achados.append({"arquivo": os.path.relpath(caminho, RAIZ), "linha": i + 1, "trecho": trecho[:120]})
    return achados


def caminhos_absolutos():
    achados = []
    padrao = re.compile(r'["\'][A-Za-z]:\\\\?[^"\']*["\']')
    for caminho, texto in TEXTO_PY.items():
        for i, linha in enumerate(texto.splitlines()):
            if padrao.search(linha) and "NAVEGADORES" not in linha:
                trecho = linha.strip()
                if trecho.startswith("#"):
                    continue
                achados.append({"arquivo": os.path.relpath(caminho, RAIZ), "linha": i + 1, "trecho": trecho[:160]})
    return achados


def termos_removidos():
    termos = ["duckstation", "scroll lock", "scroll_lock", "transmiss", "gravar_video", "gravacao_video",
              "so assistir", "só assistir", "somente assistir", "livestream", "streaming ao vivo"]
    achados = {}
    for termo in termos:
        ocorrencias = []
        for caminho, texto in list(TEXTO_PY.items()) + list(TEXTO_JS.items()):
            for i, linha in enumerate(texto.splitlines()):
                if termo.lower() in linha.lower():
                    ocorrencias.append({"arquivo": os.path.relpath(caminho, RAIZ), "linha": i + 1, "trecho": linha.strip()[:160]})
        if ocorrencias:
            achados[termo] = ocorrencias
    return achados


def main():
    resultado = {}
    print("1/6 - Funcoes candidatas a mortas (definidas, usadas <=1 vez)...")
    resultado["funcoes_candidatas"] = candidatos_funcao_morta()
    print("    ", len(resultado["funcoes_candidatas"]), "candidatas")

    print("2/6 - Chaves de config.json e uso no codigo...")
    chaves = chaves_config_padrao()
    resultado["chaves_config"] = {c: uso_de_chave(c) for c in chaves}
    print("    ", len(chaves), "chaves,", sum(1 for v in resultado['chaves_config'].values() if v <= 1), "com <=1 ocorrencia (soma inclui a propria definicao)")

    print("3/6 - Excecoes engolidas em silencio (except: / except X: seguido de pass)...")
    resultado["excecoes_silenciosas"] = excecoes_silenciosas()
    print("    ", len(resultado["excecoes_silenciosas"]), "achados")

    print("4/6 - open() sem 'with' (pista, nao veredito -- pode estar coberto por try/finally)...")
    resultado["open_sem_with"] = open_sem_with()
    print("    ", len(resultado["open_sem_with"]), "achados")

    print("5/6 - Caminhos absolutos hardcoded (fora de NAVEGADORES)...")
    resultado["caminhos_absolutos"] = caminhos_absolutos()
    print("    ", len(resultado["caminhos_absolutos"]), "achados")

    print("6/6 - Termos de funcoes ja removidas (video, DuckStation, Scroll Lock, streaming)...")
    resultado["termos_removidos"] = termos_removidos()
    for termo, ocs in resultado["termos_removidos"].items():
        print("    '%s': %d ocorrencia(s)" % (termo, len(ocs)))

    destino = os.path.join(RAIZ, "docs", "varredura_fase1_bruta.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print("\nResultado bruto salvo em", destino)


if __name__ == "__main__":
    main()
