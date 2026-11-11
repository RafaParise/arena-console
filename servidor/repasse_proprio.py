# -*- coding: utf-8 -*-
r"""O repasse proprio do ARENA (10/11/2026): partida entre casas diferentes sem a lista publica da internet.

O problema
----------
Dois alunos em casas diferentes nao se enxergam: cada casa tem um roteador que nao deixa ninguem de fora entrar. O
RetroArch resolve isso com um REPASSE (no codigo dele, "tunnel server" ou "MITM"): os dois se ligam a um terceiro
computador na internet, e ele passa os dados de um para o outro. Os repasses do libretro sao gratis, mas o convidado so
acha a sala pela LISTA PUBLICA, que mostra na internet o apelido de quem abriu (aluno menor de idade), o jogo e o pais.

A solucao
---------
Este arquivo e' um repasse do proprio professor, que roda num aparelho sempre ligado (o Galaxy A12 da bancada, no
Termux) e fala o mesmo protocolo do RetroArch 1.22.2 (conferido no codigo dele, network/netplay/netplay_frontend.c).
Nao ha lista: quem abre a partida ganha um CODIGO de 6 numeros e passa ao amigo (na aula, no grupo da turma). Nenhum
nome passa por aqui, e nada fica gravado em disco.

Uma porta so (55440, TCP) atende as duas coisas, pelo comeco da conversa:
  - "GET " / "POST": um pedido HTTP curto do ARENA
      POST /sala           reserva um codigo para quem pede (vale 90 s, ate o RetroArch dele chegar)
      GET  /sala/<codigo>  o codigo da sessao do RetroArch, para o convidado entrar
      GET  /saude          se o repasse esta de pe (o ARENA testa antes de oferecer)
  - "RATS" / "RATL": o RetroArch (o protocolo do tunel, abaixo)

O protocolo do tunel (16 bytes = 4 de "assinatura" + 12 de codigo)
---------------------------------------------------------------------
  1. O anfitriao liga e manda RATS + 12 zeros; o repasse responde RATS + o codigo da sessao. Essa ligacao fica aberta
     (e' o "canal de controle").
  2. O convidado liga e manda RATS + o codigo da sessao (o ARENA passa no --mitm-session). Depois disso, o que vier
     e' a conversa normal do jogo.
  3. O repasse inventa um codigo de LIGACAO e avisa o anfitriao pelo canal de controle: RATL + codigo.
  4. O anfitriao pede o endereco do convidado: RATA + codigo; o repasse responde RATA + codigo + 16 bytes de endereco.
  5. O anfitriao abre uma ligacao nova com o repasse e manda RATL + codigo. O repasse emenda essa ligacao na do
     convidado, e dai em diante so passa os bytes de um lado para o outro.
  6. De vez em quando o repasse manda RATP (4 bytes) no canal de controle, e o anfitriao devolve RATP: e' o "ainda
     esta ai?", que tambem mantem a porta aberta no roteador de casa.

Como o codigo de 6 numeros encontra a sessao: o ARENA do anfitriao reserva o codigo (POST /sala) e, em seguida, o
RetroArch dele pede a sessao (RATS). Os dois saem do MESMO endereco de internet, entao o repasse liga um ao outro. So
pode haver uma reserva esperando por endereco (outra casa que divide a mesma internet espera alguns segundos), e um
RetroArch que chega sem reserva e' recusado: o repasse nao serve de repasse aberto para estranhos.

Risco aceito (revisoes de seguranca de 10/11/2026): 6 numeros sao 1 milhao de codigos. Com 30 consultas por minuto por
internet (o bloco /64 inteiro, no IPv6), 60 codigos errados a cada 10 minutos por vizinhanca de rede (/24 do IPv4, /48
do IPv6) e a sala fechando quando o jogo fecha, achar uma sala ao acaso de uma rede so levaria meses. Fica aceito o caso
de muitas redes diferentes tentando juntas: um bloqueio geral contra isso foi descartado porque qualquer um poderia
dispara-lo e travar todo mundo. A sala so e' do RetroArch que sai do MESMO endereco exato de quem reservou (o /64 conta
os limites, nao a posse). O pior caso e' um estranho entrar como jogador
numa partida: o RetroArch mostra na tela o apelido de quem entrou, e fechar o jogo fecha a sala. Nao ha conversa, voz,
nem dado do aluno no repasse.

Uso (no aparelho que fica ligado):
    python repasse_proprio.py --servir [--porta 55440]
So biblioteca padrao (roda no Termux, no Linux e no Windows)."""
import argparse
import asyncio
import base64
import http.client
import ipaddress
import json
import secrets
import socket
import time

PORTA_PADRAO = 55440
VERSAO = 1

SESSAO = b"RATS"
LIGACAO = b"RATL"
ENDERECO = b"RATA"
PING = b"RATP"
TAMANHO_ID = 16                    # 4 bytes de assinatura + 12 de codigo (mitm_id_t do RetroArch)

# Limites (o aparelho e' um celular na casa do professor: nada de deixar um estranho esgotar a memoria ou a internet).
MAX_SALAS = 32
MAX_LIGACOES_POR_SALA = 8          # o RetroArch guarda ate 8 ligacoes pendentes (NETPLAY_MITM_MAX_PENDING)
MAX_CONEXOES_POR_ENDERECO = 24
MAX_CONEXOES = 256
RESERVA_VALE = 90.0                # segundos para o RetroArch do anfitriao chegar depois do POST /sala
ESPERA_DO_ANFITRIAO = 15.0         # o RetroArch desiste da ligacao pendente em 15 s
ESPERA_DO_COMECO = 10.0            # quem liga e nao diz nada em 10 s e' desligado
SILENCIO_MAXIMO = 300.0            # ligacao emendada sem nenhum byte por 5 min cai (jogo de verdade fala sem parar)
INTERVALO_DO_PING = 30.0
LIMITE_RESERVAS = (10, 600.0)      # ate 10 reservas a cada 10 min por endereco
LIMITE_CONSULTAS = (30, 60.0)      # ate 30 consultas de codigo por minuto por endereco (6 numeros nao se adivinham)
# Revisao de seguranca (10/11/2026): codigos ERRADOS contam tambem pela vizinhanca de rede (o /24 do IPv4, o /48 do
# IPv6), para quem troca de endereco dentro da mesma rede. Um bloqueio geral do repasse foi descartado: qualquer um
# poderia dispara-lo de proposito e travar todo mundo.
LIMITE_ERROS_DA_VIZINHANCA = (60, 600.0)
MAX_SALAS_POR_ENDERECO = 2         # salas abertas (esperando ou jogando) de uma mesma internet
VIDA_MAXIMA_DA_SALA = 6 * 3600.0   # uma sala nao fica aberta mais de 6 horas


def endereco_de_16_bytes(ip):
    """O endereco no formato do RetroArch (netplay_address_t): IPv6, com o IPv4 como ::ffff:a.b.c.d."""
    try:
        endereco = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return bytes(16)
    if endereco.version == 4:
        return bytes(10) + b"\xff\xff" + endereco.packed
    return endereco.packed


def chave_do_endereco(ip):
    """O endereco de quem ligou, sem o "::ffff:" (o mesmo IPv4 pode chegar pelos dois jeitos). No IPv6, a casa inteira
    recebe um bloco /64 (milhoes de enderecos): os limites contam o bloco, senao quem tem IPv6 trocaria de endereco a
    cada pedido e escaparia deles."""
    try:
        endereco = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return ip
    if endereco.version == 6 and endereco.ipv4_mapped:
        return str(endereco.ipv4_mapped)
    if endereco.version == 6:
        return str(ipaddress.ip_network("%s/64" % endereco, strict=False))
    return str(endereco)


def vizinhanca(ip):
    """A rede em volta de quem ligou: o /24 do IPv4 e o /48 do IPv6 (para contar codigos errados)."""
    try:
        endereco = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        return ip
    if endereco.version == 6 and endereco.ipv4_mapped:
        endereco = endereco.ipv4_mapped
    tamanho = 24 if endereco.version == 4 else 48
    return str(ipaddress.ip_network("%s/%d" % (endereco, tamanho), strict=False))


class Limitador:
    """Conta pedidos por endereco numa janela de tempo."""

    def __init__(self, maximo, janela):
        self.maximo, self.janela = maximo, janela
        self.vezes = {}

    def pode(self, chave, agora=None):
        agora = time.monotonic() if agora is None else agora
        recentes = [t for t in self.vezes.get(chave, []) if agora - t < self.janela]
        if len(recentes) >= self.maximo:
            self.vezes[chave] = recentes
            return False
        recentes.append(agora)
        self.vezes[chave] = recentes
        return True

    def cheio(self, chave, agora=None):
        """Ja chegou ao maximo na janela (sem contar mais uma vez)?"""
        agora = time.monotonic() if agora is None else agora
        return sum(1 for t in self.vezes.get(chave, []) if agora - t < self.janela) >= self.maximo

    def limpar(self, agora=None):
        agora = time.monotonic() if agora is None else agora
        for chave in list(self.vezes):
            if not any(agora - t < self.janela for t in self.vezes[chave]):
                del self.vezes[chave]


class Sala:
    def __init__(self, codigo, chave, ip=None):
        self.codigo = codigo
        self.chave = chave                 # a internet de quem reservou (o /64 no IPv6): conta os limites
        self.ip = ip or chave              # o endereco EXATO de quem reservou: so o RetroArch dele pega a sala
        self.criada = time.monotonic()
        self.sessao = None                 # 12 bytes, quando o RetroArch do anfitriao chega
        self.controle = None               # o escritor do canal de controle
        self.pendentes = {}                # codigo de ligacao -> (futuro com a ligacao do anfitriao, endereco do convidado)


def _sem_atraso(escritor):
    """Liga o TCP_NODELAY: cada pacote de controle sai na hora (sem juntar pedacos), o que importa num jogo."""
    sock = escritor.get_extra_info("socket")
    if sock is not None:
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass


async def _fechar(escritor):
    try:
        escritor.close()
        await asyncio.wait_for(escritor.wait_closed(), 2)
    except Exception:      # noqa: BLE001  (fechar nunca derruba o repasse)
        pass


class Repasse:
    def __init__(self, porta_publica=PORTA_PADRAO):
        self.porta_publica = porta_publica
        self.salas = {}                    # codigo de 6 numeros -> Sala
        self.por_sessao = {}               # 12 bytes -> Sala
        self.conexoes = {}                 # endereco -> quantas abertas
        self.total = 0
        self.reservas = Limitador(*LIMITE_RESERVAS)
        self.consultas = Limitador(*LIMITE_CONSULTAS)
        self.erros = Limitador(*LIMITE_ERROS_DA_VIZINHANCA)

    # --- Salas -----------------------------------------------------------------------------------------------
    def _limpar_reservas_vencidas(self):
        agora = time.monotonic()
        for codigo, sala in list(self.salas.items()):
            if sala.sessao is None and agora - sala.criada > RESERVA_VALE:
                del self.salas[codigo]
            elif agora - sala.criada > VIDA_MAXIMA_DA_SALA:
                self._fechar_sala(sala)
                if sala.controle is not None:
                    sala.controle.close()          # o anfitriao sai do repasse; o canal de controle termina sozinho
        self.reservas.limpar(agora)
        self.consultas.limpar(agora)
        self.erros.limpar(agora)

    def reservar(self, chave, ip=None):
        """(status HTTP, resposta) para o POST /sala."""
        self._limpar_reservas_vencidas()
        if any(s.chave == chave and s.sessao is None for s in self.salas.values()):
            return 409, {"erro": "Outra sala desta mesma internet está abrindo agora. Tente de novo em alguns segundos."}
        if sum(1 for s in self.salas.values() if s.chave == chave) >= MAX_SALAS_POR_ENDERECO:
            return 429, {"erro": "Já há salas demais abertas desta internet. Feche uma antes de abrir outra."}
        if len(self.salas) >= MAX_SALAS:
            return 503, {"erro": "O repasse está cheio agora. Tente mais tarde."}
        if not self.reservas.pode(chave):
            return 429, {"erro": "Muitas salas abertas em pouco tempo. Espere alguns minutos."}
        while True:
            codigo = "%06d" % secrets.randbelow(1000000)
            if codigo not in self.salas:
                break
        self.salas[codigo] = Sala(codigo, chave, ip)
        return 200, {"codigo": codigo, "vale": int(RESERVA_VALE)}

    def consultar(self, chave, codigo, perto=None):
        """(status HTTP, resposta) para o GET /sala/<codigo>."""
        if not self.consultas.pode(chave):
            return 429, {"erro": "Muitas tentativas. Espere um minuto e confira o código."}
        perto = perto or chave
        if self.erros.cheio(perto):
            # Codigos errados demais vindos desta vizinhanca de rede: so ela espera.
            return 429, {"erro": "Muitos códigos errados desta rede. Espere alguns minutos e confira o código."}
        sala = self.salas.get(codigo)
        if sala is None:
            self.erros.pode(perto)             # conta o erro
            return 404, {"erro": "Não há sala com esse código (confira os 6 números, ou a sala já fechou)."}
        if sala.sessao is None:
            return 202, {"aberta": False, "erro": "A sala ainda está abrindo. Tente de novo em alguns segundos."}
        return 200, {"aberta": True, "sessao": base64.b64encode(sala.sessao).decode("ascii"),
                     "porta": self.porta_publica}

    def saude(self):
        return 200, {"ok": True, "versao": VERSAO, "salas": sum(1 for s in self.salas.values() if s.sessao)}

    def _fechar_sala(self, sala):
        if self.salas.get(sala.codigo) is sala:
            del self.salas[sala.codigo]
        if sala.sessao is not None and self.por_sessao.get(sala.sessao) is sala:
            del self.por_sessao[sala.sessao]
        for futuro, _endereco in sala.pendentes.values():
            if not futuro.done():
                futuro.cancel()
        sala.pendentes.clear()

    # --- Conexoes --------------------------------------------------------------------------------------------
    async def atender(self, leitor, escritor):
        par = escritor.get_extra_info("peername") or ("?", 0)
        chave = chave_do_endereco(par[0])
        exato = str(par[0]).split("%")[0]
        if exato.startswith("::ffff:"):
            exato = exato[len("::ffff:"):]
        if self.total >= MAX_CONEXOES or self.conexoes.get(chave, 0) >= MAX_CONEXOES_POR_ENDERECO:
            await _fechar(escritor)
            return
        self.total += 1
        self.conexoes[chave] = self.conexoes.get(chave, 0) + 1
        _sem_atraso(escritor)
        try:
            comeco = await asyncio.wait_for(leitor.readexactly(4), ESPERA_DO_COMECO)
            if comeco in (b"GET ", b"POST", b"HEAD"):
                await self._http(comeco, leitor, escritor, chave)
            elif comeco == SESSAO:
                resto = await asyncio.wait_for(leitor.readexactly(TAMANHO_ID - 4), ESPERA_DO_COMECO)
                if resto == bytes(12):
                    await self._anfitriao(leitor, escritor, exato)
                else:
                    await self._convidado(resto, leitor, escritor, par[0])
            elif comeco == LIGACAO:
                resto = await asyncio.wait_for(leitor.readexactly(TAMANHO_ID - 4), ESPERA_DO_COMECO)
                await self._ligacao_do_anfitriao(resto, leitor, escritor)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError, OSError):
            pass
        finally:
            self.total -= 1
            self.conexoes[chave] -= 1
            if self.conexoes[chave] <= 0:
                del self.conexoes[chave]
            await _fechar(escritor)

    async def _http(self, comeco, leitor, escritor, chave):
        cabecalho = comeco + await asyncio.wait_for(leitor.readuntil(b"\r\n\r\n"), ESPERA_DO_COMECO)
        if len(cabecalho) > 4096:
            return
        linha = cabecalho.split(b"\r\n", 1)[0].decode("ascii", "replace").split()
        metodo, caminho = (linha + ["", ""])[:2]
        ip = str((escritor.get_extra_info("peername") or ("",))[0]).split("%")[0]
        exato = ip[len("::ffff:"):] if ip.startswith("::ffff:") else ip
        if metodo == "POST" and caminho == "/sala":
            status, corpo = self.reservar(chave, exato)
        elif metodo in ("GET", "HEAD") and caminho.startswith("/sala/"):
            codigo = caminho[len("/sala/"):]
            status, corpo = (self.consultar(chave, codigo, vizinhanca(ip)) if len(codigo) == 6 and codigo.isdigit()
                             else (404, {"erro": "O código da sala tem 6 números."}))
        elif metodo in ("GET", "HEAD") and caminho == "/saude":
            status, corpo = self.saude()
        else:
            status, corpo = 404, {"erro": "Pedido desconhecido."}
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        frases = {200: "OK", 202: "Accepted", 404: "Not Found", 409: "Conflict", 429: "Too Many Requests",
                  503: "Service Unavailable"}
        escritor.write(("HTTP/1.1 %d %s\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: %d\r\n"
                        "Cache-Control: no-store\r\nConnection: close\r\n\r\n"
                        % (status, frases.get(status, "OK"), len(dados))).encode("ascii")
                       + (b"" if metodo == "HEAD" else dados))
        await escritor.drain()

    async def _anfitriao(self, leitor, escritor, exato):
        self._limpar_reservas_vencidas()
        sala = next((s for s in self.salas.values() if s.ip == exato and s.sessao is None), None)
        if sala is None:
            return                         # sem reserva: nao e' um ARENA (o repasse nao e' aberto a estranhos)
        while True:
            sessao = secrets.token_bytes(12)
            if sessao != bytes(12) and sessao not in self.por_sessao:
                break
        sala.sessao, sala.controle = sessao, escritor
        self.por_sessao[sessao] = sala
        escritor.write(SESSAO + sessao)
        await escritor.drain()
        ping = asyncio.ensure_future(self._pingar(escritor))
        try:
            while True:
                magia = await leitor.readexactly(4)
                if magia == PING:
                    continue                                   # resposta do "ainda esta ai?"
                if magia != ENDERECO:
                    return                                     # algo que o RetroArch nao manda: fecha
                ligacao = await leitor.readexactly(TAMANHO_ID - 4)
                pendente = sala.pendentes.get(ligacao)
                endereco = pendente[1] if pendente else bytes(16)
                escritor.write(ENDERECO + ligacao + endereco)
                await escritor.drain()
        finally:
            ping.cancel()
            self._fechar_sala(sala)

    async def _pingar(self, escritor):
        try:
            while True:
                await asyncio.sleep(INTERVALO_DO_PING)
                escritor.write(PING)
                await escritor.drain()
        except (asyncio.CancelledError, ConnectionError, OSError):
            pass

    async def _convidado(self, sessao, leitor, escritor, ip):
        sala = self.por_sessao.get(sessao)
        if sala is None or sala.controle is None or len(sala.pendentes) >= MAX_LIGACOES_POR_SALA:
            return
        ligacao = secrets.token_bytes(12)
        futuro = asyncio.get_running_loop().create_future()
        sala.pendentes[ligacao] = (futuro, endereco_de_16_bytes(ip))
        try:
            sala.controle.write(LIGACAO + ligacao)
            await sala.controle.drain()
            leitor_anfitriao, escritor_anfitriao = await asyncio.wait_for(futuro, ESPERA_DO_ANFITRIAO)
        except (asyncio.TimeoutError, asyncio.CancelledError, ConnectionError, OSError):
            return
        finally:
            sala.pendentes.pop(ligacao, None)
        try:
            await self._emendar(leitor, escritor, leitor_anfitriao, escritor_anfitriao)
        finally:
            await _fechar(escritor_anfitriao)

    async def _ligacao_do_anfitriao(self, ligacao, leitor, escritor):
        for sala in self.salas.values():
            pendente = sala.pendentes.get(ligacao)
            if pendente and not pendente[0].done():
                fim = asyncio.get_running_loop().create_future()
                pendente[0].set_result((leitor, _Escritor(escritor, fim)))
                await fim                      # quem cuida desta ligacao agora e' o convidado (_emendar)
                return

    async def _emendar(self, leitor_a, escritor_a, leitor_b, escritor_b):
        """Passa os bytes de um lado para o outro ate um dos dois desligar (ou ficar mudo por SILENCIO_MAXIMO)."""
        async def passar(leitor, escritor):
            try:
                while True:
                    dados = await asyncio.wait_for(leitor.read(65536), SILENCIO_MAXIMO)
                    if not dados:
                        return
                    escritor.write(dados)
                    await escritor.drain()
            except (asyncio.TimeoutError, ConnectionError, OSError):
                return

        tarefas = [asyncio.ensure_future(passar(leitor_a, escritor_b)), asyncio.ensure_future(passar(leitor_b, escritor_a))]
        await asyncio.wait(tarefas, return_when=asyncio.FIRST_COMPLETED)
        for tarefa in tarefas:
            tarefa.cancel()


class _Escritor:
    """O escritor da ligacao do anfitriao, que avisa a conexao dona dele quando a emenda termina."""

    def __init__(self, escritor, fim):
        self._escritor, self._fim = escritor, fim

    def __getattr__(self, nome):
        return getattr(self._escritor, nome)

    def close(self):
        self._escritor.close()
        if not self._fim.done():
            self._fim.set_result(None)


async def servir(porta=PORTA_PADRAO, endereco=None, porta_publica=None, pronto=None):
    """Abre o repasse e atende para sempre (ou ate a tarefa ser cancelada). 'pronto' recebe o servidor aberto."""
    repasse = Repasse(porta_publica or porta)
    servidor = await asyncio.start_server(repasse.atender, host=endereco, port=porta, reuse_address=True)
    if pronto is not None:
        pronto(servidor, repasse)
    async with servidor:
        await servidor.serve_forever()


# --- O lado do ARENA (quem joga) ------------------------------------------------------------------------------------
def separar_endereco(texto, porta_padrao=PORTA_PADRAO):
    """'host', 'host:porta' ou '[ipv6]:porta' -> (host, porta). Devolve None se nao der para entender."""
    texto = (texto or "").strip()
    if not texto or any(c.isspace() for c in texto) or "/" in texto:
        return None
    if texto.startswith("["):
        fim = texto.find("]")
        if fim < 0:
            return None
        host, resto = texto[1:fim], texto[fim + 1:]
        porta = resto[1:] if resto.startswith(":") else ""
    elif texto.count(":") == 1:
        host, porta = texto.split(":")
    else:
        host, porta = texto, ""
    if not host:
        return None
    if porta:
        if not porta.isdigit() or not 0 < int(porta) < 65536:
            return None
        return host, int(porta)
    return host, porta_padrao


def para_o_retroarch(endereco):
    """O endereco no formato da chave netplay_custom_mitm_server: "host|porta" (netplay_decode_hostname do RetroArch
    1.22.2 separa pela barra vertical; "host:porta" da "Failed to resolve host")."""
    partes = separar_endereco(endereco)
    return None if partes is None else "%s|%d" % partes


def _pedir(endereco, metodo, caminho, espera=6.0):
    """(status, resposta em dict) de um pedido ao repasse; (None, {"erro": ...}) se nao alcancar."""
    partes = separar_endereco(endereco)
    if partes is None:
        return None, {"erro": "Endereço do repasse inválido."}
    conexao = http.client.HTTPConnection(partes[0], partes[1], timeout=espera)
    try:
        conexao.request(metodo, caminho, headers={"Content-Length": "0"} if metodo == "POST" else {})
        resposta = conexao.getresponse()
        corpo = resposta.read(8192)
        try:
            dados = json.loads(corpo.decode("utf-8"))
        except ValueError:
            dados = {"erro": "O repasse respondeu algo estranho."}
        return resposta.status, dados if isinstance(dados, dict) else {"erro": "O repasse respondeu algo estranho."}
    except (OSError, http.client.HTTPException) as falha:
        return None, {"erro": "Não consegui falar com o repasse (%s)." % falha.__class__.__name__}
    finally:
        conexao.close()


def saude(endereco, espera=4.0):
    status, dados = _pedir(endereco, "GET", "/saude", espera)
    return status == 200 and bool(dados.get("ok"))


def reservar_sala(endereco):
    """O codigo de 6 numeros da sala nova, ou (None, mensagem)."""
    status, dados = _pedir(endereco, "POST", "/sala")
    if status == 200 and str(dados.get("codigo", "")).isdigit():
        return dados["codigo"], None
    return None, dados.get("erro") or "O repasse nao abriu a sala."


def procurar_sala(endereco, codigo, tentativas=8, intervalo=2.0):
    """(sessao em base64, porta) da sala, esperando um pouco se ela ainda estiver abrindo; ou (None, mensagem)."""
    codigo = "".join(c for c in str(codigo) if c.isdigit())
    if len(codigo) != 6:
        return None, "O código da sala tem 6 números."
    mensagem = "A sala nao abriu a tempo."
    for vez in range(max(1, tentativas)):
        status, dados = _pedir(endereco, "GET", "/sala/" + codigo)
        if status == 200 and dados.get("sessao"):
            return (dados["sessao"], int(dados.get("porta") or PORTA_PADRAO)), None
        mensagem = dados.get("erro") or mensagem
        if status != 202:
            break
        if vez + 1 < tentativas:
            time.sleep(intervalo)
    return None, mensagem


def main():
    argumentos = argparse.ArgumentParser(description="Repasse proprio do ARENA (partida entre casas, sem lista publica).")
    argumentos.add_argument("--servir", action="store_true", help="abre o repasse e fica atendendo")
    argumentos.add_argument("--porta", type=int, default=PORTA_PADRAO)
    argumentos.add_argument("--porta-publica", type=int, default=None,
                            help="a porta que o roteador abre para a internet, se for outra")
    argumentos.add_argument("--testar", metavar="ENDERECO", help="so confere se um repasse responde (host:porta)")
    opcoes = argumentos.parse_args()
    if opcoes.testar:
        print("respondeu" if saude(opcoes.testar) else "nao respondeu")
        return 0
    if not opcoes.servir:
        argumentos.print_help()
        return 0
    print("Repasse do ARENA na porta %d (Ctrl+C para parar)." % opcoes.porta, flush=True)
    try:
        asyncio.run(servir(opcoes.porta, porta_publica=opcoes.porta_publica))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
