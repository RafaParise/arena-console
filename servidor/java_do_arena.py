# -*- coding: utf-8 -*-
r"""
ARENA - o Java que vem junto, para o emulador do Java ME (celular antigo).

Achado de 15/10/2026: o emulador do Java ME (FreeJ2ME-Plus) tem duas
metades. A metade do RetroArch (retroarch\cores\freej2me_libretro.dll) abre a
metade Java (freej2me-lr.jar, que fica na pasta system) chamando "javaw": o
Java do computador, procurado no PATH. Sem Java instalado, o jogo nao abre.

Para ninguem precisar instalar nada (o ARENA roda sem administrador, de um
pen drive), o pacote leva um Java pequeno em emuladores\Java: so as partes
que o FreeJ2ME usa (java.base, java.desktop e java.rmi), uns 47 MB, montado
com o jlink a partir do Eclipse Temurin 21 (ferramentas\preparar_java.py).

Ao abrir um jogo de Java ME, o ARENA poe a pasta bin desse Java NA FRENTE do
PATH, so para o RetroArch daquela partida. Nada muda no Windows, e o "javaw"
que o nucleo acha e' o do ARENA, mesmo num computador com outro Java.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_JAVA = os.path.join(RAIZ, "emuladores", "Java")


def javaw(pasta=PASTA_JAVA):
    """O caminho do javaw.exe do ARENA, ou None se ele nao estiver la."""
    caminho = os.path.join(pasta, "bin", "javaw.exe")
    return caminho if os.path.isfile(caminho) else None


def ambiente(base=None, pasta=PASTA_JAVA):
    """As variaveis de ambiente para abrir o RetroArch com o Java do ARENA na
    frente do PATH. Sem o Java do ARENA, devolve o ambiente como esta: o
    nucleo ainda acha o Java do computador, se houver um."""
    variaveis = dict(os.environ if base is None else base)
    if not javaw(pasta):
        return variaveis
    # No Windows o nome da variavel pode vir como "Path" ou "PATH".
    chave = next((nome for nome in variaveis if nome.upper() == "PATH"), "PATH")
    caminhos = [c for c in variaveis.get(chave, "").split(os.pathsep) if c]
    variaveis[chave] = os.pathsep.join([os.path.join(pasta, "bin")] + caminhos)
    return variaveis
