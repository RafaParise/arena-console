# -*- coding: utf-8 -*-
r"""
ARENA - a ponte sem acento: para o nucleo que nao abre arquivo de pasta com
acento.

Achado de 14/10/2026: o Hatari (o nucleo do Atari ST) so abre caminho SEM
acento. O ARENA do Rafael mora em "...\Criador De Apps Pedagógicos\...": com
o "ó" no caminho, o Hatari nao achava a BIOS ("System BIOS (tos.img) is
missing") nem o disquete do jogo, e a tela ficava preta. O mesmo aconteceria
com o ARENA numa "Área de Trabalho" do OneDrive. O nome curto do Windows
(8.3) nao resolve: ele vem desligado em muitos computadores (neste tambem).

A saida: antes de abrir o jogo, o ARENA copia a BIOS e o disquete para uma
pasta SEM acento (a pasta temporaria do Windows, ou C:\Users\Public quando
ate ela tem acento) e manda o nucleo abrir de la. Quando o jogo fecha, o
disquete volta para o lugar dele, se o jogo gravou nele (recorde, jogo
salvo). Com o ARENA numa pasta sem acento (um pen drive E:\ARENA, por
exemplo), nada disso acontece: o jogo abre direto, como sempre.
"""
import hashlib
import os
import shutil
import tempfile

# Os nucleos que nao abrem caminho com acento e o que cada um precisa da
# pasta system (conferido abrindo o jogo de verdade: testes\teste_consoles_livres.py).
NUCLEOS = {
    "hatari_libretro.dll": ["tos.img"],
}
NOME_DA_PONTE = "ARENA-sem-acento"


def sem_acento(caminho):
    """So letras e simbolos do ASCII (sem acento, sem cedilha)?"""
    return str(caminho).isascii()


def precisa(nucleo, pasta_sistema, caminho_jogo):
    """Este jogo precisa da ponte: o nucleo e' um dos que nao aceitam acento
    e a pasta da BIOS ou o jogo tem acento?"""
    nucleo = os.path.basename(str(nucleo or "")).lower()
    return nucleo in NUCLEOS and not (sem_acento(pasta_sistema) and sem_acento(caminho_jogo))


def pasta_da_ponte():
    """A pasta sem acento onde a ponte trabalha, ou None se nao houver."""
    for base in (tempfile.gettempdir(), os.environ.get("PUBLIC", "")):
        if base and sem_acento(base) and os.path.isdir(base):
            return os.path.join(base, NOME_DA_PONTE)
    return None


def _marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 16), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _copiar(origem, destino):
    """Copia trocando de uma vez (os.replace): ninguem le meio arquivo."""
    temporario = "%s.%d.copiando" % (destino, os.getpid())
    shutil.copyfile(origem, temporario)
    os.replace(temporario, destino)


def preparar(nucleo, pasta_sistema, caminho_jogo):
    """Poe a BIOS e o jogo na pasta sem acento. Devolve (caminho do jogo para
    o nucleo, opcoes do RetroArch para esta partida, devolver), em que
    devolver() leva de volta o disquete, se o jogo gravou nele. OSError se
    nao houver pasta sem acento ou a copia falhar."""
    ponte = pasta_da_ponte()
    if not ponte:
        raise OSError("nenhuma pasta sem acento para abrir o jogo (nem a temporaria, nem C:\\Users\\Public)")
    sistema = os.path.join(ponte, "system")
    os.makedirs(sistema, exist_ok=True)
    for nome in NUCLEOS[os.path.basename(nucleo).lower()]:
        origem = os.path.join(pasta_sistema, nome)
        destino = os.path.join(sistema, nome)
        if os.path.isfile(origem) and not (os.path.isfile(destino) and _marca(destino) == _marca(origem)):
            _copiar(origem, destino)
    if sem_acento(caminho_jogo):
        return caminho_jogo, {"system_directory": sistema}, lambda: False
    extensao = os.path.splitext(caminho_jogo)[1].lower()
    copia = os.path.join(ponte, "jogo" + (extensao if sem_acento(extensao) else ""))
    _copiar(caminho_jogo, copia)
    marca = _marca(copia)

    def devolver():
        """Leva o disquete de volta se o jogo gravou nele. True se levou."""
        if not os.path.isfile(copia) or _marca(copia) == marca:
            return False
        _copiar(copia, caminho_jogo)
        return True

    return copia, {"system_directory": sistema}, devolver
