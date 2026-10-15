# -*- coding: utf-8 -*-
r"""
ARENA - a ponte sem acento: para o nucleo que nao abre arquivo de pasta com
acento.

Achados de 14 e 15/10/2026: o Hatari (o nucleo do Atari ST), o AppleWin (o do
Apple II) e o atari800 (o do Atari 8-bit) so abrem caminho SEM acento. O ARENA do Rafael mora em
"...\Criador De Apps Pedagógicos\...": com o "ó" no caminho, o Hatari nao
achava a BIOS ("System BIOS (tos.img) is missing") nem o disquete do jogo, e
o AppleWin nao abria o disco ("Falha ao carregar o conteudo"). O mesmo aconteceria
com o ARENA numa "Área de Trabalho" do OneDrive. O nome curto do Windows
(8.3) nao resolve: ele vem desligado em muitos computadores (neste tambem).

A saida: antes de abrir o jogo, o ARENA copia a BIOS e o disquete para uma
pasta SEM acento e manda o nucleo abrir de la. Quando o jogo fecha, o
disquete volta para o lugar dele, se o jogo gravou nele (recorde, jogo
salvo), e a pasta e' apagada. Com o ARENA numa pasta sem acento (um pen
drive E:\ARENA, por exemplo), nada disso acontece: o jogo abre direto.

Seguranca (revisao de 14/10/2026): a pasta e' NOVA a cada jogo, com nome
sorteado, e so em lugar que e' de quem esta usando o computador: a pasta
temporaria dele ou, quando ate ela tem acento (um usuario "João"), a
C:\ProgramData, onde o Windows deixa so quem criou a pasta mexer no que esta
dentro. Nunca a pasta Public do Windows, que e' de todos: la outro usuario
poderia trocar o disquete no meio do jogo, e o ARENA levaria a troca de volta
para a pasta do aluno.
"""
import hashlib
import os
import shutil
import stat
import tempfile
import time

# Os nucleos que nao abrem caminho com acento e o que cada um precisa da
# pasta system (conferido abrindo o jogo de verdade: testes\teste_consoles_livres.py).
# Lista vazia: o nucleo nao usa a pasta system (so o jogo vai pela ponte).
NUCLEOS = {
    "hatari_libretro.dll": ["tos.img"],          # Atari ST
    "applewin_libretro.dll": [],                 # Apple II ("Falha ao carregar o conteudo", 14/10/2026)
    # Atari 8-bit: com acento, o atari800 ficava na tela do AltirraOS, sem o
    # jogo (15/10/2026). Leva as ROMs originais da lista do .info, quando a
    # pessoa tiver posto alguma; sem elas, ele liga pelo AltirraOS embutido.
    "atari800_libretro.dll": ["ATARIXL.ROM", "ATARIBAS.ROM", "ATARIOSA.ROM", "ATARIOSB.ROM",
                              "5200.rom", "BB01R4_OS.ROM", "XEGAME.ROM"],
}
PREFIXO = "ARENA-sem-acento-"


def sem_acento(caminho):
    """So letras e simbolos do ASCII (sem acento, sem cedilha)?"""
    return str(caminho).isascii()


def precisa(nucleo, pasta_sistema, caminho_jogo):
    """Este jogo precisa da ponte: o nucleo e' um dos que nao aceitam acento
    e o jogo tem acento -- ou a pasta da BIOS, quando ele usa uma?"""
    nucleo = os.path.basename(str(nucleo or "")).lower()
    if nucleo not in NUCLEOS:
        return False
    return not sem_acento(caminho_jogo) or (bool(NUCLEOS[nucleo]) and not sem_acento(pasta_sistema))


def pasta_da_ponte():
    """Onde a ponte cria a pasta dela: a temporaria de quem esta usando o
    computador ou a ProgramData, a primeira sem acento. None se nenhuma."""
    for base in (tempfile.gettempdir(), os.environ.get("ProgramData", "")):
        if base and sem_acento(base) and os.path.isdir(base):
            return base
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


def _apagar(pasta):
    """Apaga a pasta da ponte, ate arquivo somente leitura (o disquete
    protegido contra gravacao). O que nao sair fica para a proxima limpeza."""
    def tirar_protecao(funcao, alvo, _erro):
        try:
            os.chmod(alvo, stat.S_IWRITE)
            funcao(alvo)
        except OSError:
            pass
    try:
        shutil.rmtree(pasta, onexc=tirar_protecao)
    except OSError:
        pass


def limpar_sobras(base, idade=12 * 3600):
    """Apaga as pastas de pontes velhas (de um jogo que nao fechou direito).
    So as de mais de 12 horas: nunca a de um jogo que ainda esta aberto."""
    try:
        nomes = os.listdir(base)
    except OSError:
        return
    agora = time.time()
    for nome in nomes:
        caminho = os.path.join(base, nome)
        try:
            velha = agora - os.path.getmtime(caminho) > idade
        except OSError:
            continue
        if nome.startswith(PREFIXO) and velha and os.path.isdir(caminho):
            _apagar(caminho)


def preparar(nucleo, pasta_sistema, caminho_jogo):
    """Poe a BIOS e o jogo numa pasta nova, sem acento. Devolve (caminho do
    jogo para o nucleo, opcoes do RetroArch para esta partida, devolver), em
    que devolver() -- chamado UMA vez, quando o jogo fecha -- leva de volta o
    disquete, se o jogo gravou nele, e apaga a pasta. OSError se nao houver
    lugar sem acento ou a copia falhar."""
    base = pasta_da_ponte()
    if not base:
        raise OSError("nenhuma pasta sem acento para abrir o jogo (nem a temporária do Windows, nem a ProgramData)")
    limpar_sobras(base)
    ponte = tempfile.mkdtemp(prefix=PREFIXO, dir=base)
    necessarios = NUCLEOS[os.path.basename(nucleo).lower()]
    try:
        sistema = os.path.join(ponte, "system")
        os.makedirs(sistema)
        for nome in necessarios:
            origem = os.path.join(pasta_sistema, nome)
            if os.path.isfile(origem):
                _copiar(origem, os.path.join(sistema, nome))
        copia = caminho_jogo
        if not sem_acento(caminho_jogo):
            extensao = os.path.splitext(caminho_jogo)[1].lower()
            copia = os.path.join(ponte, "jogo" + (extensao if sem_acento(extensao) else ""))
            _copiar(caminho_jogo, copia)
        marca = _marca(copia)
    except OSError:
        _apagar(ponte)
        raise

    def devolver():
        """Leva o disquete de volta se o jogo gravou nele (True se levou) e
        apaga a pasta da ponte."""
        try:
            if copia == caminho_jogo or not os.path.isfile(copia) or _marca(copia) == marca:
                return False
            _copiar(copia, caminho_jogo)
            return True
        finally:
            _apagar(ponte)

    # O nucleo que nao usa a pasta system continua com a do ARENA.
    return copia, ({"system_directory": sistema} if necessarios else {}), devolver
