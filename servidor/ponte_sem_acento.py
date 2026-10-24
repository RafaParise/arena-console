# -*- coding: utf-8 -*-
r"""
ARENA - a ponte sem acento: para o nucleo que nao abre arquivo de pasta com
acento.

Achados de 14 e 15/10/2026: o Hatari (o nucleo do Atari ST), o AppleWin (o do
Apple II), o atari800 (o do Atari 8-bit) e o FreeJ2ME-Plus (o do Java ME) so
abrem caminho SEM acento. O ARENA do Rafael mora em
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

Outro caso, mais leve (rodada final de 15/10/2026): o nucleo que ABRE o jogo
com acento, mas GRAVA na pasta system pelo caminho em ANSI, o jeito antigo
do Windows, em que o "ó" vira "Ã³". Para ele nao precisa de copia: basta
dizer a pasta system pelo caminho relativo (pasta_sistema_relativa).

No Linux (item 13, 17/10/2026), o nome do arquivo e' uma sequencia de bytes
em UTF-8, sem o "jeito ANSI" do Windows, e quase todo nucleo abre e grava
caminho com acento (conferido com o Hatari no conteiner Linux,
testes\teste_linux.py): o jogo abre direto, como no pen drive sem acento. A
excecao e' o Java ME (20/10/2026): o FreeJ2ME-Plus abre o Java com
"-Dfile.encoding=ISO_8859_1" e manda o caminho do jogo por um cano, que o
Java le em Latin-1. O "ó" (dois bytes em UTF-8) vira "Ã³", o Java procura um
arquivo que nao existe e a tela fica preta, com qualquer lingua do sistema
(conferido no conteiner com C, POSIX e C.UTF-8). Ele vai pela ponte tambem
fora do Windows (PONTE_EM_TODO_SISTEMA).
"""
import hashlib
import os
import re
import shutil
import stat
import tempfile
import time
import unicodedata

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
    # Java ME (15/10/2026): com acento, o FreeJ2ME-Plus dizia "freej2me-lr.jar
    # does not exist in the system dir" e nem abria o Java. A metade Java
    # dele mora na system e abre com a system como pasta de trabalho.
    "freej2me_libretro.dll": ["freej2me-lr.jar"],
    # PocketStation (24/10/2026): o Pokket abre o pocketstation.bin com fopen em ANSI; com acento na pasta, o
    # conteudo "falha ao carregar" (provado: com a system em C:/pasta-sem-acento ele roda com o mesmo BIOS).
    "pokket_libretro.dll": ["pocketstation.bin"],
}
PREFIXO = "ARENA-sem-acento-"
# No Windows, todo nucleo da lista vai pela ponte (ver o topo).
PRECISA_DA_PONTE = os.name == "nt"
# No Linux e no Android, so o que le o caminho em Latin-1: o Java ME.
PONTE_EM_TODO_SISTEMA = ("freej2me_libretro.dll",)

# Os nucleos que abrem o jogo com acento, mas gravam na pasta system pelo
# caminho em ANSI (rodada final de 15/10/2026): o N64 (mupen64plus-next)
# gravou o cache de shaders, o de texturas e o mupen64plus.ini numa pasta de
# nome estragado, fora do ARENA ("...\Criador De Apps PedagÃ³gicos\..."), e
# o VICE (os Commodore) criou ali a pasta vice dele. Com a pasta system dita
# pelo caminho relativo ("system", a partir da pasta do RetroArch), o texto
# fica sem acento e o Windows completa o resto pela pasta de trabalho, que
# ele guarda certo: o cache foi para retroarch\system (conferido em 16/10/2026).
GRAVAM_EM_ANSI = ("mupen64plus_next_libretro.dll", "vice_")

# O que o Windows nao aceita num nome de arquivo. O nome do jogo nao tem
# nada disso, mas o NFKD (abaixo) pode criar: a barra de largura dupla "＼"
# vira "\", e o "：" vira ":". Revisao de seguranca de 16/10/2026: sem esta
# troca, um jogo chamado "＼..＼..＼x.st" fazia a copia sair da pasta da
# ponte e ir para C:\x.st, por cima do que estivesse la.
PROIBIDOS_NO_NOME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Os nomes que o Windows reserva para aparelhos: "CON.st" e' a tela, nao um
# arquivo (e o "ＣＯＮ" de largura dupla vira "CON").
RESERVADOS = re.compile(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])$", re.IGNORECASE)


def sem_acento(caminho):
    """So letras e simbolos do ASCII (sem acento, sem cedilha)?"""
    return str(caminho).isascii()


def nome_sem_acento(nome):
    """O nome do arquivo sem acento, para a copia na ponte: "Ação.st" vira
    "Acao.st". O RetroArch da ao estado (F2) o nome do jogo: com um nome so
    para todos ("jogo.st", ate 15/10/2026), os jogos que passavam pela ponte
    gravavam o estado um por cima do outro. O nome sem nenhuma letra do
    ASCII (todo em japones, por exemplo) vira "jogo". Barra, dois-pontos e
    os outros sinais que o Windows nao aceita viram "_": a copia nunca sai
    da pasta da ponte."""
    base, extensao = os.path.splitext(nome)
    # NFKD separa a letra do acento ("ç" vira "c" + cedilha); o ASCII fica so
    # com a letra.
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = PROIBIDOS_NO_NOME.sub("_", base).strip(" .")
    if not base or RESERVADOS.match(base):
        base = "jogo"
    return base + (extensao.lower() if sem_acento(extensao) and not PROIBIDOS_NO_NOME.search(extensao) else "")


def _nome_do_nucleo(nucleo):
    """'C:\\...\\hatari_libretro.dll' ou '.../hatari_libretro.so' ->
    'hatari_libretro.dll' (o nome das listas acima)."""
    nome = os.path.basename(str(nucleo or "").replace("\\", "/")).lower()
    return nome[:-3] + ".dll" if nome.endswith(".so") else nome


def pasta_sistema_relativa(nucleo, pasta_sistema, pasta_trabalho):
    """A pasta system dita a partir da pasta de trabalho do RetroArch
    ("system"), para o nucleo que grava em ANSI, quando o caminho dela tem
    acento. None quando nao precisa: outro nucleo, caminho sem acento, ou a
    system fora da pasta de trabalho (o caminho relativo teria acento ou "..")."""
    nome = _nome_do_nucleo(nucleo)
    if not PRECISA_DA_PONTE or not nome.startswith(GRAVAM_EM_ANSI) or sem_acento(pasta_sistema):
        return None
    try:
        relativa = os.path.relpath(pasta_sistema, pasta_trabalho)
    except ValueError:              # outra unidade (a system no E:, o RetroArch no C:)
        return None
    if not sem_acento(relativa) or relativa == os.curdir or relativa.split(os.sep)[0] == os.pardir:
        return None
    return relativa


def precisa(nucleo, pasta_sistema, caminho_jogo):
    """Este jogo precisa da ponte: o nucleo e' um dos que nao aceitam acento
    e o jogo tem acento -- ou a pasta da BIOS, quando ele usa uma?"""
    nucleo = _nome_do_nucleo(nucleo)
    if nucleo not in NUCLEOS or not (PRECISA_DA_PONTE or nucleo in PONTE_EM_TODO_SISTEMA):
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


def _e_atalho(caminho):
    """Link simbolico (ou a juncao do Windows): aponta para outro lugar."""
    return os.path.islink(caminho) or os.path.isjunction(caminho)


def _apagar(pasta):
    """Apaga a pasta da ponte, ate arquivo somente leitura (o disquete
    protegido contra gravacao). O que nao sair fica para a proxima limpeza."""
    def tirar_protecao(funcao, alvo, _erro):
        # O chmod segue o atalho: num atalho, ele mudaria a permissao do
        # arquivo para onde ele aponta, fora da ponte (revisao de seguranca
        # de 20/10/2026). Atalho nunca e' desprotegido. E so vale tentar de
        # novo o que apaga: o rmtree do Linux tambem avisa do os.open, que
        # sem os argumentos dele dava TypeError e derrubava a limpeza.
        if _e_atalho(alvo) or funcao not in (os.unlink, os.remove, os.rmdir):
            return
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
    So as de mais de 12 horas: nunca a de um jogo que ainda esta aberto.
    So pasta de verdade e do proprio usuario: no Linux, a temporaria (/tmp)
    e' de todos, e outro usuario poderia deixar ali um atalho com o nome da
    ponte apontando para os arquivos do aluno (revisao de 20/10/2026)."""
    try:
        nomes = os.listdir(base)
    except OSError:
        return
    agora = time.time()
    for nome in nomes:
        if not nome.startswith(PREFIXO):
            continue
        caminho = os.path.join(base, nome)
        try:
            info = os.lstat(caminho)
        except OSError:
            continue
        if not stat.S_ISDIR(info.st_mode) or _e_atalho(caminho):
            continue
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            continue
        if agora - info.st_mtime > idade:
            _apagar(caminho)


def preparar(nucleo, pasta_sistema, caminho_jogo):
    """Poe a BIOS e o jogo numa pasta nova, sem acento. Devolve (caminho do
    jogo para o nucleo, opcoes do RetroArch para esta partida, devolver), em
    que devolver() -- chamado UMA vez, quando o jogo fecha -- leva de volta o
    disquete, se o jogo gravou nele, e apaga a pasta. OSError se nao houver
    lugar sem acento ou a copia falhar."""
    base = pasta_da_ponte()
    if not base:
        raise OSError("nenhuma pasta sem acento para abrir o jogo (nem a temporária do sistema, nem a ProgramData)")
    limpar_sobras(base)
    ponte = tempfile.mkdtemp(prefix=PREFIXO, dir=base)
    necessarios = NUCLEOS[_nome_do_nucleo(nucleo)]
    try:
        sistema = os.path.join(ponte, "system")
        os.makedirs(sistema)
        for nome in necessarios:
            origem = os.path.join(pasta_sistema, nome)
            if os.path.isfile(origem):
                _copiar(origem, os.path.join(sistema, nome))
        copia = caminho_jogo
        if not sem_acento(caminho_jogo):
            # Numa pasta so do jogo: um jogo chamado "system" nao bate na
            # pasta das BIOS.
            pasta_jogo = os.path.join(ponte, "jogo")
            os.makedirs(pasta_jogo)
            copia = os.path.join(pasta_jogo, nome_sem_acento(os.path.basename(caminho_jogo)))
            # Conferencia final: a copia fica DENTRO da pasta do jogo, sempre.
            if os.path.dirname(os.path.abspath(copia)) != os.path.abspath(pasta_jogo):
                raise OSError("nome de jogo que sairia da pasta da ponte: %s" % ascii(os.path.basename(caminho_jogo)))
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
