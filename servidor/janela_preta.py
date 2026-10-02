# -*- coding: utf-8 -*-
r"""A janela preta do ARENA e o que fazer quando o servidor cai.

Achado de 02/10/2026. O Rafael: "algumas vezes sem motivo nenhum o servidor
do ARENA para de funcionar e tem que fechar e abrir tudo". O registro de
aplicativos do Windows mostrou o Python do ARENA caindo duas vezes em 26/09,
com jogo aberto, por falha de acesso a memoria (codigo 0xC0000005, dentro
do ntdll.dll). Esse tipo de queda fecha o programa NA HORA, sem mensagem
nenhuma -- e a tela fica la, parada, sem ninguem do outro lado.

Tres protecoes moram aqui (a quarta, reabrir o servidor, e' do ARENA.bat):

1. REGISTRO DA QUEDA. O faulthandler (biblioteca padrao do Python) escreve
   em dados\logs\queda-do-servidor.txt, no instante da queda, EM QUE LINHA
   de qual arquivo cada parte do servidor estava. E' a diferenca entre
   "caiu" e "caiu por causa disto". Custa nada: o arquivo so recebe uma
   linha ao abrir o ARENA, e o resto so se ele cair.

2. EDICAO RAPIDA DESLIGADA. No console antigo do Windows (o normal no
   Windows 10), um clique dentro da janela preta comeca uma selecao de
   texto, e enquanto ela dura QUALQUER texto que o programa tente escrever
   fica parado esperando alguem apertar uma tecla. O servidor escreve na
   janela quando abre e fecha jogo: um clique sem querer na janela deixava
   o "Abrindo..." preso para sempre. E' um ajuste so desta janela; nao
   muda nada no Windows.

3. SAIDA QUE NAO TRAVA. Mesmo assim (selecao pelo menu da janela, console
   lento), quem escreve na janela e' uma linha de execucao separada, que
   pega o texto de uma fila. O servidor so poe o texto na fila e segue:
   nunca mais espera pela janela.

Analogia: o servidor e' o cozinheiro e a janela preta e' o mural de
recados. Antes, se alguem segurasse o giz, o cozinheiro parava de cozinhar
ate devolverem o giz. Agora ele deixa o recado numa caixinha e volta para o
fogao; outra pessoa passa os recados para o mural quando der.
"""
import atexit
import faulthandler
import os
import queue
import sys
import threading
from datetime import datetime

NOME_DO_REGISTRO = "queda-do-servidor.txt"
# Passou disto, o registro antigo vira "...anterior.txt" e comeca um novo:
# o arquivo nunca cresce sem limite (pen drive e cartao SD).
LIMITE_DO_REGISTRO = 128 * 1024
# Recados esperando a janela. Se a janela ficar travada por muito tempo, os
# mais novos sao descartados (e contados) em vez de a memoria crescer.
LIMITE_DA_FILA = 2000

_registro_aberto = []   # o arquivo PRECISA continuar aberto: e' nele que o faulthandler escreve


def ligar_registro_de_queda(pasta_logs, versao=""):
    """Liga o registro de queda em pasta_logs\\queda-do-servidor.txt.

    Escreve uma linha com a hora de abertura (para cada queda ter data) e
    devolve o caminho do arquivo, ou None se nao deu para abrir."""
    try:
        os.makedirs(pasta_logs, exist_ok=True)
        caminho = os.path.join(pasta_logs, NOME_DO_REGISTRO)
        try:
            if os.path.getsize(caminho) > LIMITE_DO_REGISTRO:
                os.replace(caminho, caminho[:-4] + ".anterior.txt")
        except OSError:
            pass
        arquivo = open(caminho, "a", encoding="utf-8", errors="replace")
        arquivo.write("\n--- ARENA %s aberto em %s ---\n"
                      % (versao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        arquivo.flush()
        faulthandler.enable(file=arquivo, all_threads=True)
        _registro_aberto[:] = [arquivo]
        return caminho
    except OSError:
        return None


def desligar_edicao_rapida():
    """Desliga a "Edicao Rapida" SO desta janela preta (o clique que congela
    o programa). Devolve True se mudou alguma coisa. Fora do Windows, ou
    sem janela (saida redirecionada, testes), nao faz nada."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetStdHandle.argtypes = [wintypes.DWORD]
        k.GetStdHandle.restype = wintypes.HANDLE
        k.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetConsoleMode.restype = wintypes.BOOL
        k.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.SetConsoleMode.restype = wintypes.BOOL
        ENTRADA_PADRAO = 0xFFFFFFF6          # STD_INPUT_HANDLE, ou seja, (DWORD)-10
        EDICAO_RAPIDA, OPCOES_EXTRAS = 0x0040, 0x0080
        entrada = k.GetStdHandle(ENTRADA_PADRAO)
        modo = wintypes.DWORD(0)
        if not entrada or not k.GetConsoleMode(entrada, ctypes.byref(modo)):
            return False                     # a entrada nao e' uma janela de console
        # A Microsoft documenta: para a Edicao Rapida valer (ou deixar de
        # valer), o bit de opcoes extras precisa estar ligado junto.
        novo = (modo.value | OPCOES_EXTRAS) & ~EDICAO_RAPIDA
        if novo == modo.value:
            return False
        return bool(k.SetConsoleMode(entrada, novo))
    except (AttributeError, OSError, ValueError):
        return False


class _Recados:
    """A fila unica entre o servidor e a janela (stdout e stderr juntos,
    para a ordem dos recados nao trocar)."""

    def __init__(self):
        self.fila = queue.Queue(maxsize=LIMITE_DA_FILA)
        self.perdidos = 0
        self.esvaziou = threading.Condition()
        self.pendentes = 0
        threading.Thread(target=self._passar_para_a_janela, name="janela-preta",
                         daemon=True).start()

    def guardar(self, destino, texto):
        with self.esvaziou:
            try:
                self.fila.put_nowait((destino, texto))
                self.pendentes += 1
            except queue.Full:
                self.perdidos += 1

    def _passar_para_a_janela(self):
        while True:
            destino, texto = self.fila.get()
            with self.esvaziou:
                aviso, self.perdidos = self.perdidos, 0
            if aviso:
                self._escrever(destino, "[ARENA] (%d recado(s) nao couberam enquanto a "
                                        "janela estava travada)\n" % aviso)
            self._escrever(destino, texto)
            with self.esvaziou:
                self.pendentes -= 1
                if not self.pendentes:
                    self.esvaziou.notify_all()

    @staticmethod
    def _escrever(destino, texto):
        try:
            destino.write(texto)
            destino.flush()
        except (OSError, ValueError, UnicodeError):
            pass                             # janela fechada ou letra que nao cabe: o servidor segue

    def esperar(self, segundos):
        """Espera os recados chegarem na janela, no maximo `segundos`.
        Devolve False se a janela continua travada (quem chamou segue)."""
        with self.esvaziou:
            return self.esvaziou.wait_for(lambda: not self.pendentes, timeout=segundos)


class SaidaSemTravar:
    """Faz o papel do sys.stdout/sys.stderr: o texto vai para a fila e o
    servidor segue sem esperar a janela."""

    def __init__(self, original, recados):
        self._original = original
        self._recados = recados

    def write(self, texto):
        if texto:
            self._recados.guardar(self._original, texto)
        return len(texto)

    def flush(self):
        # Espera um pouco (o "Pressione Enter" precisa aparecer antes da
        # pergunta), mas nunca para sempre.
        self._recados.esperar(1.0)

    def __getattr__(self, nome):
        # encoding, errors, fileno... continuam sendo os da janela de verdade.
        return getattr(self._original, nome)


def sem_janela_de_erro_do_windows():
    """Se o Python cair, o Windows as vezes mostra "python.exe parou de
    funcionar" e ESPERA alguem clicar -- e o ARENA.bat so consegue reabrir
    o servidor depois do clique. Isto pede ao Windows para nao mostrar essa
    janela (so para este programa e os emuladores que ele abrir; o registro
    de aplicativos do Windows continua anotando a queda)."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.WinDLL("kernel32")
        k.GetErrorMode.restype = ctypes.c_uint
        k.SetErrorMode.argtypes = [ctypes.c_uint]
        k.SetErrorMode.restype = ctypes.c_uint
        SEM_JANELA_DE_FALHA = 0x0002            # SEM_NOGPFAULTERRORBOX
        k.SetErrorMode(k.GetErrorMode() | SEM_JANELA_DE_FALHA)
    except (AttributeError, OSError):
        pass


def preparar(pasta_logs, versao=""):
    """Tudo junto, chamado uma vez quando o ARENA abre. Devolve o caminho do
    registro de queda (ou None)."""
    caminho = ligar_registro_de_queda(pasta_logs, versao)
    desligar_edicao_rapida()
    sem_janela_de_erro_do_windows()
    if not isinstance(sys.stdout, SaidaSemTravar):
        recados = _Recados()
        erro_original = sys.stderr
        sys.stdout = SaidaSemTravar(sys.stdout, recados)
        sys.stderr = SaidaSemTravar(sys.stderr, recados)

        def erro_sem_fila(tipo, valor, rastro):
            # Erro que derruba o programa: o motivo precisa aparecer na
            # janela ANTES de ela fechar -- por isso vai direto, sem fila,
            # e tambem para o registro de queda.
            import traceback
            recados.esperar(2.0)
            texto = "".join(traceback.format_exception(tipo, valor, rastro))
            for destino in [erro_original] + _registro_aberto:
                try:
                    destino.write(texto)
                    destino.flush()
                except (OSError, ValueError):
                    pass

        sys.excepthook = erro_sem_fila
        # Ao fechar do jeito normal, os ultimos recados chegam na janela.
        atexit.register(recados.esperar, 2.0)
    return caminho
