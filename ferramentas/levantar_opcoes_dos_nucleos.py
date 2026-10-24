# -*- coding: utf-8 -*-
"""Pergunta aos nucleos libretro do ARENA quais opcoes e quais tipos de controle eles oferecem.

Para que serve: o catalogo de acessorios (servidor\\acessorios.json) so pode citar uma chave de opcao que o nucleo
REALMENTE tem, com valores que o nucleo REALMENTE aceita. Procurar o texto no binario diz que a chave existe, mas nao
diz os valores; ler a documentacao pode estar desatualizado. O jeito certo e perguntar ao proprio nucleo, do mesmo
jeito que o RetroArch pergunta: carregar a DLL e chamar `retro_set_environment` com um "ambiente" de mentira que
anota o que o nucleo declara (RETRO_ENVIRONMENT_SET_CORE_OPTIONS*, SET_VARIABLES e SET_CONTROLLER_INFO).

Como usar (Windows, com o Python embutido):
    servidor\\python\\python.exe ferramentas\\levantar_opcoes_dos_nucleos.py [--saida arquivo.json] [nucleo ...]
Sem nome de nucleo, olha todos os *_libretro.dll de retroarch\\cores. Cada nucleo roda num processo separado (um que
trave ou caia nao derruba os outros). So le: nao abre jogo, nao grava nada fora do arquivo de saida.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_NUCLEOS = os.path.join(RAIZ, "retroarch", "cores")

# Numeros do ambiente libretro (libretro.h).
GET_VARIABLE = 15
SET_VARIABLES = 16
GET_VARIABLE_UPDATE = 17
SET_SUPPORT_NO_GAME = 18
GET_LOG_INTERFACE = 27
SET_CONTROLLER_INFO = 35
GET_CORE_OPTIONS_VERSION = 52
SET_CORE_OPTIONS = 53
SET_CORE_OPTIONS_INTL = 54
SET_CORE_OPTIONS_V2 = 67
SET_CORE_OPTIONS_V2_INTL = 68
ESCONDIDOS = 0x30000          # EXPERIMENTAL e PRIVATE: o RetroArch tira esses bits antes de comparar

MAXIMO_DE_VALORES = 128       # RETRO_NUM_CORE_OPTION_VALUES_MAX


class Valor(ctypes.Structure):
    _fields_ = [("valor", ctypes.c_char_p), ("rotulo", ctypes.c_char_p)]


class DefinicaoV1(ctypes.Structure):
    _fields_ = [("chave", ctypes.c_char_p), ("descricao", ctypes.c_char_p), ("info", ctypes.c_char_p),
                ("valores", Valor * MAXIMO_DE_VALORES), ("padrao", ctypes.c_char_p)]


class DefinicaoV2(ctypes.Structure):
    _fields_ = [("chave", ctypes.c_char_p), ("descricao", ctypes.c_char_p), ("descricao_categoria", ctypes.c_char_p),
                ("info", ctypes.c_char_p), ("info_categoria", ctypes.c_char_p), ("categoria", ctypes.c_char_p),
                ("valores", Valor * MAXIMO_DE_VALORES), ("padrao", ctypes.c_char_p)]


class Categoria(ctypes.Structure):
    _fields_ = [("chave", ctypes.c_char_p), ("descricao", ctypes.c_char_p), ("info", ctypes.c_char_p)]


class OpcoesV2(ctypes.Structure):
    _fields_ = [("categorias", ctypes.POINTER(Categoria)), ("definicoes", ctypes.POINTER(DefinicaoV2))]


class OpcoesV2Intl(ctypes.Structure):
    _fields_ = [("us", ctypes.POINTER(OpcoesV2)), ("local", ctypes.POINTER(OpcoesV2))]


class OpcoesV1Intl(ctypes.Structure):
    _fields_ = [("us", ctypes.POINTER(DefinicaoV1)), ("local", ctypes.POINTER(DefinicaoV1))]


class Variavel(ctypes.Structure):
    _fields_ = [("chave", ctypes.c_char_p), ("valor", ctypes.c_char_p)]


class DescricaoDeControle(ctypes.Structure):
    _fields_ = [("descricao", ctypes.c_char_p), ("id", ctypes.c_uint)]


class InfoDeControle(ctypes.Structure):
    _fields_ = [("tipos", ctypes.POINTER(DescricaoDeControle)), ("quantos", ctypes.c_uint)]


def texto(valor):
    return valor.decode("utf-8", "replace") if valor else ""


def ler_valores(definicao):
    valores = []
    for item in definicao.valores:
        if not item.valor:
            break
        valores.append({"valor": texto(item.valor), "rotulo": texto(item.rotulo)})
    return valores


def anotar_definicoes(opcoes, definicoes, versao):
    indice = 0
    while indice < 4000:
        d = definicoes[indice]
        if not d.chave:
            break
        item = {"chave": texto(d.chave), "descricao": texto(d.descricao), "info": texto(d.info)[:300],
                "valores": ler_valores(d), "padrao": texto(d.padrao)}
        if versao == 2:
            item["categoria"] = texto(d.categoria)
        opcoes[item["chave"]] = item
        indice += 1


def perguntar_ao_nucleo(caminho):
    """Carrega o nucleo e devolve {"opcoes": {...}, "controles": [...], "info": {...}} ou {"erro": "..."}."""
    achado = {"opcoes": {}, "controles": []}
    os.add_dll_directory(os.path.dirname(caminho))
    nucleo = ctypes.WinDLL(caminho)
    chamada = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)

    def ambiente(comando, dado):
        comando &= ~ESCONDIDOS
        achado.setdefault("comandos", [])
        if comando not in achado["comandos"] and len(achado["comandos"]) < 80:
            achado["comandos"].append(comando)
        try:
            if comando == GET_CORE_OPTIONS_VERSION:
                ctypes.cast(dado, ctypes.POINTER(ctypes.c_uint))[0] = 2
                return True
            if comando == SET_CORE_OPTIONS_V2:
                opcoes = ctypes.cast(dado, ctypes.POINTER(OpcoesV2))[0]
                anotar_definicoes(achado["opcoes"], opcoes.definicoes, 2)
                return True
            if comando == SET_CORE_OPTIONS_V2_INTL:
                opcoes = ctypes.cast(dado, ctypes.POINTER(OpcoesV2Intl))[0].us[0]
                anotar_definicoes(achado["opcoes"], opcoes.definicoes, 2)
                return True
            if comando == SET_CORE_OPTIONS:
                anotar_definicoes(achado["opcoes"], ctypes.cast(dado, ctypes.POINTER(DefinicaoV1)), 1)
                return True
            if comando == SET_CORE_OPTIONS_INTL:
                anotar_definicoes(achado["opcoes"], ctypes.cast(dado, ctypes.POINTER(OpcoesV1Intl))[0].us, 1)
                return True
            if comando == SET_VARIABLES:
                variaveis = ctypes.cast(dado, ctypes.POINTER(Variavel))
                for indice in range(4000):
                    v = variaveis[indice]
                    if not v.chave:
                        break
                    descricao, _, resto = texto(v.valor).partition(";")
                    valores = [{"valor": x.strip(), "rotulo": x.strip()} for x in resto.split("|") if x.strip()]
                    achado["opcoes"][texto(v.chave)] = {
                        "chave": texto(v.chave), "descricao": descricao.strip(), "info": "", "valores": valores,
                        "padrao": valores[0]["valor"] if valores else ""}
                return True
            if comando == SET_CONTROLLER_INFO:
                portas = ctypes.cast(dado, ctypes.POINTER(InfoDeControle))
                achado["controles"] = []
                for porta in range(32):
                    info = portas[porta]
                    if not info.tipos:
                        break
                    achado["controles"].append([
                        {"descricao": texto(info.tipos[i].descricao), "id": info.tipos[i].id}
                        for i in range(info.quantos)])
                return True
            if comando in (GET_VARIABLE, GET_LOG_INTERFACE):
                return False
            if comando == GET_VARIABLE_UPDATE:
                ctypes.cast(dado, ctypes.POINTER(ctypes.c_bool))[0] = False
                return True
            if comando == SET_SUPPORT_NO_GAME:
                return True
        except Exception as erro:                     # um ambiente de mentira nao pode derrubar a leitura
            achado.setdefault("avisos", []).append("%s: %s" % (comando, erro))
        return False

    gancho = chamada(ambiente)                         # fica vivo ate o fim da funcao
    nucleo.retro_set_environment.argtypes = [chamada]
    nucleo.retro_set_environment(gancho)
    if not achado["opcoes"]:
        # Alguns nucleos so declaram as opcoes depois do retro_init.
        try:
            nucleo.retro_init()
        except OSError as erro:
            achado.setdefault("avisos", []).append("retro_init: %s" % erro)
    # Os tipos de controle de alguns nucleos so aparecem no retro_init; os de outros, so com jogo carregado.
    return achado


def um_nucleo(caminho):
    inicio = time.time()
    try:
        achado = perguntar_ao_nucleo(caminho)
        achado["segundos"] = round(time.time() - inicio, 1)
    except Exception as erro:
        achado = {"erro": "%s: %s" % (type(erro).__name__, erro)}
    sys.stdout.write("\n@@RESULTADO@@" + json.dumps(achado, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    os._exit(0)                                        # sem descarregar o nucleo (alguns travam ao sair)


def todos(nomes, saida, segundos):
    if not nomes:
        nomes = sorted(n for n in os.listdir(PASTA_NUCLEOS) if n.endswith("_libretro.dll"))
    resultado = {"gerado_em": time.strftime("%Y-%m-%d %H:%M"), "nucleos": {}}
    for nome in nomes:
        caminho = os.path.join(PASTA_NUCLEOS, nome)
        try:
            feito = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--um", caminho],
                                   capture_output=True, timeout=segundos, cwd=PASTA_NUCLEOS)
            bruto = feito.stdout.decode("utf-8", "replace")
            marca = bruto.rfind("@@RESULTADO@@")
            # Um nucleo pode escrever mais coisa na saida depois da resposta: vale so a linha da marca.
            achado = json.loads(bruto[marca + len("@@RESULTADO@@"):].split("\n", 1)[0]) if marca >= 0 else {
                "erro": "sem resposta (codigo %s)" % feito.returncode}
        except subprocess.TimeoutExpired:
            achado = {"erro": "demorou mais de %d s" % segundos}
        except ValueError as erro:
            achado = {"erro": "resposta ilegivel: %s" % erro}
        resultado["nucleos"][nome] = achado
        print("%-40s %s" % (nome, ("%d opcoes, %d portas" % (len(achado.get("opcoes", {})), len(achado.get("controles", [])))
                                   if "erro" not in achado else "ERRO " + achado["erro"][:80])))
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1, sort_keys=True)
    print("gravado em", saida)


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    argumentos.add_argument("nucleos", nargs="*", help="nomes de arquivo, como flycast_libretro.dll")
    argumentos.add_argument("--saida", default="opcoes_dos_nucleos.json")
    argumentos.add_argument("--segundos", type=int, default=60, help="tempo maximo por nucleo")
    argumentos.add_argument("--um", help="(uso interno) caminho de UM nucleo; imprime o resultado")
    dados = argumentos.parse_args()
    # O console do Windows (cp1252) nao imprime todo caractere que um nucleo escreve na mensagem de erro.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if dados.um:
        um_nucleo(dados.um)
    else:
        todos(dados.nucleos, dados.saida, dados.segundos)
