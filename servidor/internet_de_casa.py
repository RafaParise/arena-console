# -*- coding: utf-8 -*-
r"""A internet de casa serve para partida entre casas? (13/11/2026, pedido do Rafael: o ARENA confere sozinho.)

Uma partida entre casas precisa que ALGUEM receba conexao de fora: o repasse da turma (servidor\repasse_proprio.py,
porta 55440) ou quem hospeda direto pelo RetroArch (porta 55435). Duas coisas impedem:
  - CGNAT: a operadora divide um endereco de internet entre varios clientes. Ai nada de fora chega, e nenhuma
    configuracao do roteador resolve (so o repasse de outra pessoa, ou um tunel como o Tailscale);
  - porta fechada no roteador (ou em DOIS roteadores, como o FortiGate atras da ONT da operadora).

O que o ARENA confere sozinho, sem senha de roteador nenhuma:
  1. o endereco de internet desta casa (o "IP publico"), perguntando a um site (api.ipify.org, so o endereco volta);
  2. os roteadores no caminho (os primeiros saltos ate a internet): dois roteadores de casa = "duplo NAT";
     um salto na faixa 100.64.0.0/10 (a reservada para CGNAT, RFC 6598) = CGNAT com certeza;
  3. o roteador pelo UPnP (o jeito padrao de um programa pedir porta ao roteador): o endereco de internet que o
     proprio roteador recebeu. Diferente do publico, ou de faixa privada = CGNAT com certeza. E, com o UPnP, o
     ARENA abre a porta sozinho (so quando a pessoa toca no botao, e por tempo limitado).
Quando nada disso decide, a tela orienta em 3 passos: abrir a pagina do roteador (o ARENA abre), achar "IP" na
parte de internet (WAN) e digitar; o ARENA compara.

So a biblioteca padrao. O UPnP so fala com endereco da rede de casa (privado); nada de UPnP com a internet.
"""
import ipaddress
import os
import re
import socket
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ElementTree

import baixar
import plataforma as plataforma_do_sistema

SITES_DO_IP = ("https://api.ipify.org", "https://icanhazip.com")
CGNAT = ipaddress.ip_network("100.64.0.0/10")
SSDP = ("239.255.255.250", 1900)
SERVICOS_WAN = ("urn:schemas-upnp-org:service:WANIPConnection:2", "urn:schemas-upnp-org:service:WANIPConnection:1",
                "urn:schemas-upnp-org:service:WANPPPConnection:1")
PORTAS_DA_PARTIDA = ((55435, "TCP", "partida a dois (RetroArch)"), (55440, "TCP", "repasse da turma"))
TEMPO_DA_PORTA = 4 * 3600        # a porta aberta pelo ARENA fecha sozinha em 4 h (o roteador apaga)
_SEM_JANELA = {"creationflags": 0x08000000} if os.name == "nt" else {}


def _ip(texto):
    try:
        return ipaddress.ip_address(str(texto).strip())
    except ValueError:
        return None


def de_casa(endereco):
    """Endereco que nao e' da internet: privado (192.168, 10, 172.16-31), da faixa do CGNAT ou de laco."""
    ip = _ip(endereco)
    return bool(ip) and (ip.is_private or ip in CGNAT or ip.is_loopback or ip.is_link_local)


# ---------------------------------------------------------------------------
# 1. O endereco de internet desta casa
# ---------------------------------------------------------------------------
def ip_publico(segundos=8):
    for site in SITES_DO_IP:
        try:
            codigo, saida = baixar.rodar(site, segundos)
        except OSError:
            continue
        ip = _ip(saida.decode("ascii", "replace")) if codigo == 0 else None
        if ip and not de_casa(ip):
            return str(ip)
    return None


# ---------------------------------------------------------------------------
# 2. Os roteadores no caminho
# ---------------------------------------------------------------------------
def saltos(alvo="1.1.1.1", quantos=5):
    """Os primeiros saltos ate a internet (so os enderecos; '*' quando o salto nao responde)."""
    if plataforma_do_sistema.ANDROID:
        return []
    if os.name == "nt":
        comando = ["tracert", "-d", "-h", str(quantos), "-w", "700", alvo]
    else:
        programa = shutil_which("traceroute") or shutil_which("tracepath")
        if not programa:
            return []
        comando = [programa, "-n", "-m", str(quantos), "-w", "1", alvo] if programa.endswith("traceroute") \
            else [programa, "-n", "-m", str(quantos), alvo]
    try:
        saida = subprocess.run(comando, capture_output=True, timeout=40, **_SEM_JANELA).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    lista = []
    for linha in saida.decode("utf-8", "replace").splitlines():
        achado = re.match(r"\s*(\d+)\s+(.*)$", linha)
        if not achado:
            continue
        ips = re.findall(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", achado.group(2))
        ips = [i for i in ips if i != alvo or int(achado.group(1)) >= quantos]
        lista.append(ips[-1] if ips else "*")
    return lista[:quantos]


def shutil_which(nome):
    import shutil
    return shutil.which(nome)


def ler_saltos(lista):
    """O que os saltos dizem: quantos roteadores de casa ha antes da internet e se algum e' da faixa do CGNAT."""
    roteadores, cgnat, operadora_privada = [], False, False
    for i, endereco in enumerate(lista):
        ip = _ip(endereco)
        if not ip:
            continue
        if ip in CGNAT:
            cgnat = True
            break
        if not de_casa(ip):
            break
        # Os primeiros saltos privados sao os roteadores de casa; um privado de outra faixa logo depois deles
        # costuma ser a rede da propria operadora (pode ser CGNAT; so a pagina do roteador confirma).
        if roteadores and ip.is_private and not _mesma_faixa(ip, roteadores):
            operadora_privada = True
            break
        roteadores.append(str(ip))
    return {"roteadores": roteadores, "cgnat": cgnat, "operadora_privada": operadora_privada}


def _mesma_faixa(ip, vistos):
    """Roteador de casa costuma estar em 192.168.x.x ou 10.x; a rede da operadora, em 172.16-31 ou outra faixa."""
    if ip in ipaddress.ip_network("172.16.0.0/12"):
        return False
    return True


# ---------------------------------------------------------------------------
# 3. O roteador pelo UPnP (sem senha)
# ---------------------------------------------------------------------------
def _so_da_rede_de_casa(url):
    """O UPnP so vale para endereco da rede de casa: o roteador nunca manda o ARENA para fora."""
    achado = re.match(r"http://([^/:]+)(?::\d+)?/", url or "")
    return bool(achado) and de_casa(achado.group(1)) and not _ip(achado.group(1)).is_loopback


def achar_roteador_upnp(espera=2.5):
    """{"controle": url do servico WAN, "servico": tipo} do roteador que responde ao UPnP, ou None."""
    pedido = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 2\r\n"
              "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n\r\n").encode()
    lugares = []
    soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        soquete.settimeout(0.5)
        soquete.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        soquete.sendto(pedido, SSDP)
        fim = time.monotonic() + espera
        while time.monotonic() < fim:
            try:
                dados, _de = soquete.recvfrom(4096)
            except socket.timeout:
                continue
            achado = re.search(rb"(?im)^location:\s*(\S+)", dados)
            if achado:
                url = achado.group(1).decode("ascii", "replace")
                if _so_da_rede_de_casa(url) and url not in lugares:
                    lugares.append(url)
    except OSError:
        return None
    finally:
        soquete.close()
    for url in lugares:
        servico = _servico_wan(url)
        if servico:
            return servico
    return None


def _servico_wan(url_descricao):
    try:
        with urllib.request.urlopen(url_descricao, timeout=4) as resposta:
            xml = resposta.read(256 * 1024)
        # Sem DOCTYPE nem ENTITY: a descricao de um roteador nunca precisa, e assim nenhum aparelho da rede consegue
        # mandar um XML que exploda a memoria ou leia arquivo (o Python 3.13 ja nao segue entidade externa).
        if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
            return None
        raiz = ElementTree.fromstring(xml)
    except (OSError, ElementTree.ParseError, ValueError):
        return None
    base = re.match(r"(http://[^/]+)", url_descricao).group(1)
    for servico in raiz.iter():
        if not servico.tag.endswith("service"):
            continue
        campos = {filho.tag.split("}")[-1]: (filho.text or "").strip() for filho in servico}
        if campos.get("serviceType") in SERVICOS_WAN and campos.get("controlURL"):
            controle = campos["controlURL"]
            controle = controle if controle.startswith("http") else base + "/" + controle.lstrip("/")
            if _so_da_rede_de_casa(controle):
                return {"controle": controle, "servico": campos["serviceType"]}
    return None


def _soap(roteador, acao, argumentos=""):
    corpo = ('<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
             's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:%s xmlns:u="%s">%s</u:%s>'
             '</s:Body></s:Envelope>' % (acao, roteador["servico"], argumentos, acao)).encode()
    pedido = urllib.request.Request(roteador["controle"], data=corpo, headers={
        "Content-Type": 'text/xml; charset="utf-8"', "SOAPAction": '"%s#%s"' % (roteador["servico"], acao)})
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        return resposta.read(64 * 1024).decode("utf-8", "replace")


def ip_do_roteador(roteador):
    """O endereco de internet que o roteador recebeu da operadora (pelo UPnP), ou None."""
    try:
        texto = _soap(roteador, "GetExternalIPAddress")
    except OSError:
        return None
    achado = re.search(r"<NewExternalIPAddress>([^<]*)<", texto)
    return str(_ip(achado.group(1))) if achado and _ip(achado.group(1)) else None


def meu_ip_na_rede(roteador_url):
    """O endereco deste computador na rede do roteador (o que o roteador deve mandar a conexao de fora)."""
    host = re.match(r"http://([^/:]+)", roteador_url).group(1)
    soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        soquete.connect((host, 1900))
        return soquete.getsockname()[0]
    finally:
        soquete.close()


def abrir_portas(roteador=None, portas=PORTAS_DA_PARTIDA):
    """Pede ao roteador (UPnP) para mandar as portas da partida a este computador, por TEMPO_DA_PORTA. Devolve a lista
    das que abriram. So quando a pessoa toca no botao."""
    roteador = roteador or achar_roteador_upnp()
    if not roteador:
        return []
    meu = meu_ip_na_rede(roteador["controle"])
    abertas = []
    for porta, protocolo, descricao in portas:
        argumentos = ("<NewRemoteHost></NewRemoteHost><NewExternalPort>%d</NewExternalPort><NewProtocol>%s</NewProtocol>"
                      "<NewInternalPort>%d</NewInternalPort><NewInternalClient>%s</NewInternalClient>"
                      "<NewEnabled>1</NewEnabled><NewPortMappingDescription>ARENA %s</NewPortMappingDescription>"
                      "<NewLeaseDuration>%d</NewLeaseDuration>" % (porta, protocolo, porta, meu, descricao, TEMPO_DA_PORTA))
        try:
            _soap(roteador, "AddPortMapping", argumentos)
            abertas.append(porta)
        except OSError:
            continue
    return abertas


# ---------------------------------------------------------------------------
# A conclusao, em palavras simples
# ---------------------------------------------------------------------------
def conferir():
    """Tudo o que da para saber sozinho. Devolve {"conclusao", "titulo", "explica", "passos", "publico",
    "roteadores", "upnp", "pagina_do_roteador"}."""
    publico = ip_publico()
    lidos = ler_saltos(saltos())
    roteador = achar_roteador_upnp()
    do_roteador = ip_do_roteador(roteador) if roteador else None
    pagina = "http://%s/" % lidos["roteadores"][-1] if lidos["roteadores"] else ""
    base = {"publico": publico, "roteadores": lidos["roteadores"], "upnp": bool(roteador),
            "ip_do_roteador": do_roteador, "pagina_do_roteador": pagina, "passos": []}
    if not publico:
        return dict(base, conclusao="sem_internet", titulo="Sem internet agora",
                    explica="O ARENA não conseguiu falar com a internet. Confira o cabo ou o Wi-Fi e toque de novo.")
    # CGNAT com certeza: um salto ou o endereco que o roteador recebeu na faixa 100.64/10, ou o roteador com endereco
    # de internet diferente do que a internet ve. (Endereco privado no roteador = roteador de dentro, como um
    # FortiGate atras da ONT: nao decide nada.)
    ip_rot = _ip(do_roteador) if do_roteador else None
    if lidos["cgnat"] or (ip_rot and (ip_rot in CGNAT or (not de_casa(ip_rot) and str(ip_rot) != publico))):
        return dict(base, conclusao="cgnat", titulo="A operadora divide a internet (CGNAT)",
                    explica="Ninguém de fora consegue chegar até esta casa, e nenhum ajuste do roteador muda isso. "
                            "Você ainda joga com outras casas pelo repasse de outra pessoa (Amigos, Partidas entre "
                            "casas). Para receber conexões aqui, peça à operadora um \"IP público\" (algumas fazem sem "
                            "custo).")
    if do_roteador and do_roteador == publico and len(lidos["roteadores"]) <= 1:
        return dict(base, conclusao="pronto", titulo="Sua internet serve para partidas",
                    explica="Esta casa tem endereço de internet próprio e o roteador aceita abrir portas sozinho. "
                            "Na hora de hospedar, o ARENA pede a porta ao roteador.")
    passos = ["Toque em Abrir a página do roteador (o ARENA abre %s)." % (pagina or "o endereço do seu roteador"),
              "Entre com o usuário e a senha que vêm na etiqueta embaixo do roteador e procure \"WAN\" ou \"Internet\".",
              "Copie o \"Endereço IP\" que aparece lá e cole aqui embaixo. O ARENA compara para você."]
    if len(lidos["roteadores"]) >= 2:
        return dict(base, conclusao="dois_roteadores", passos=passos,
                    titulo="Há dois roteadores no caminho" + (" e pode haver CGNAT" if lidos["operadora_privada"] else ""),
                    explica="A internet passa por %d roteadores (%s). Para receber partidas, cada um precisa mandar a "
                            "porta para o seguinte. Antes, confira se a operadora não divide a internet (3 passos):"
                            % (len(lidos["roteadores"]), ", ".join(lidos["roteadores"])))
    return dict(base, conclusao="conferir", passos=passos,
                titulo="Falta uma conferência" + (" (pode haver CGNAT)" if lidos["operadora_privada"] else ""),
                explica="O roteador não respondeu sozinho. Em 3 passos você confere se a operadora divide a internet:")


def comparar(ip_digitado, publico):
    """O passo 3: o endereco que a pessoa leu na pagina do roteador, comparado com o publico."""
    ip = _ip(ip_digitado)
    if not ip:
        return {"conclusao": "invalido", "titulo": "Isso não parece um endereço",
                "explica": "Copie de novo o número no formato 200.150.10.20 e cole aqui."}
    if de_casa(ip) or str(ip) != publico:
        return {"conclusao": "cgnat", "titulo": "A operadora divide a internet (CGNAT)",
                "explica": "O roteador recebeu %s, mas a internet vê esta casa como %s. Ninguém de fora chega aqui; "
                           "jogue pelo repasse de outra pessoa ou peça à operadora um \"IP público\"." % (ip, publico)}
    return {"conclusao": "sem_cgnat", "titulo": "Sem CGNAT: dá para receber partidas",
            "explica": "O endereço do roteador é o mesmo da internet (%s). Falta só mandar a porta 55440 (repasse) ou "
                       "55435 (partida direta) para este computador, na página do roteador (\"Encaminhamento de "
                       "porta\" ou \"Virtual Server\")." % ip}
