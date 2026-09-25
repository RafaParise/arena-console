# -*- coding: utf-8 -*-
"""
ARENA - Por que a partida a dois nao conecta
=============================================
Roda nos DOIS computadores e diz, em portugues, o que esta faltando.

Uso:
    python partida.py                  confere este computador
    python partida.py 192.168.137.1    confere tambem o do colega

Nao muda nada. So olha e conta.
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)
PORTA = 8777
PORTA_PARTIDA = 55435

problemas = []
avisos = []


def falar(texto=""):
    print(texto)


def certo(texto):
    falar("  [ok]      %s" % texto)


def torto(texto, conserto=""):
    problemas.append(texto)
    falar("  [PROBLEMA] %s" % texto)
    if conserto:
        falar("             -> %s" % conserto)


def olhar(texto):
    avisos.append(texto)
    falar("  [olhe]    %s" % texto)


def pedir(url, tempo=4, corpo=None):
    """GET normal; com `corpo`, manda POST em JSON (o servidor so aceita
    POST com Content-Type application/json)."""
    try:
        requisicao = urllib.request.Request(url)
        if corpo is not None:
            requisicao = urllib.request.Request(
                url, data=json.dumps(corpo).encode("utf-8"), method="POST",
                headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(requisicao, timeout=tempo) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except Exception:
        return None


def porta_aberta(endereco, porta, tempo=2.0):
    try:
        with socket.create_connection((endereco, porta), timeout=tempo):
            return True
    except OSError:
        return False


def categoria_de_rede():
    """Confere se o Windows marcou a rede atual como Publica -- so LER essa
    categoria nao pede administrador, mas o Firewall do Windows trata rede
    Publica de um jeito bem mais fechado, e um aluno comum (sem senha de
    admin) nao consegue aprovar a caixa "Permitir que este app se comunique"
    que aparece nesse caso. Achado real na auditoria: antes desta checagem,
    o ARENA so *chutava* firewall como possivel causa, sem confirmar nada.
    Devolve a categoria ("Public", "Private", "DomainAuthenticated") ou None
    se nao deu pra descobrir (comando indisponivel, por exemplo)."""
    import subprocess
    try:
        resultado = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-NetConnectionProfile | Select-Object -First 1 -ExpandProperty NetworkCategory)"],
            capture_output=True, text=True, timeout=5)
        saida = resultado.stdout.strip()
        return saida or None
    except Exception:
        return None


falar("=" * 62)
falar("  ARENA - diagnostico da partida a dois")
falar("=" * 62)

# ---------------------------------------------------------------- 1. versao
falar()
falar("1. Este ARENA")
falar("-" * 62)

meu = pedir("http://127.0.0.1:%d/api/estado" % PORTA)
if not meu:
    torto("O ARENA nao esta aberto neste computador.",
          "De dois cliques no ARENA.bat e rode isto de novo.")
    falar()
    falar("Sem o ARENA aberto nao da para conferir mais nada.")
    sys.exit(1)

versao = meu.get("versao", "(versao antiga, sem carimbo)")
certo("versao %s" % versao)
if not meu.get("versao"):
    torto("Esta versao e anterior as correcoes de partida a dois.",
          "Baixe o pacote novo e copie por cima. Veja o documento 6.")

certo("apelido: %s" % (meu["config"].get("apelido") or "(vazio)"))
certo("codigo deste aparelho: %s" % meu["config"]["dispositivo_id"])

# ---------------------------------------------------------------- 2. rede
falar()
falar("2. A rede deste computador")
falar("-" * 62)

if not meu["config"].get("permitir_rede"):
    torto("'Aceitar conexoes da rede' esta DESLIGADO.",
          "Ajustes > Amigos > ligue, e feche e abra o ARENA.")
else:
    certo("aceita conexoes da rede")

uteis = [e for e in meu.get("enderecos", []) if e["tipo"] != "virtual"]
virtuais = [e for e in meu.get("enderecos", []) if e["tipo"] == "virtual"]

if not uteis:
    torto("Nenhum endereco que sirva para o colega.",
          "Confira se voce esta mesmo numa rede: Wi-Fi, cabo ou ponto de acesso.")
else:
    falar("  Passe UM destes para o colega:")
    for e in uteis:
        falar("      %-22s %s" % (e["rotulo"], e["url"]))

if virtuais:
    olhar("Tem %d endereco virtual na lista (WSL, VirtualBox). "
          "NAO passe esses." % len(virtuais))
    for e in virtuais:
        falar("      (nao usar) %s" % e["url"])

# ---------------------------------------------------------------- 3. portas
falar()
falar("3. As duas portas")
falar("-" * 62)
falar("  O ARENA usa DUAS portas, e o Windows pergunta do firewall")
falar("  separado para cada uma:")
falar()

certo("porta %d (ARENA) esta escutando" % PORTA)

categoria = categoria_de_rede()
if categoria == "Public":
    torto(
        "O Windows marcou esta rede como PUBLICA.",
        "O Firewall do Windows fecha bem mais numa rede publica, e a caixa "
        "'Permitir que este app se comunique' pede senha de administrador -- "
        "um aluno comum nao consegue aprovar sozinho. Peca para o professor "
        "(com a senha de admin) trocar a rede para 'Privada' em "
        "Configuracoes > Rede e Internet > Wi-Fi > Propriedades, ou aprove "
        "a caixa do Firewall quando ela aparecer.")
elif categoria:
    certo("rede categorizada como %s (nao e publica)" % categoria)
else:
    olhar("nao consegui perguntar ao Windows a categoria da rede (comando "
         "indisponivel). Se a partida nao conectar, confira manualmente em "
         "Configuracoes > Rede e Internet.")

if porta_aberta("127.0.0.1", PORTA_PARTIDA, 1.0):
    certo("porta %d (partida) esta aberta - tem jogo em rede rodando"
          % PORTA_PARTIDA)
else:
    olhar("porta %d (partida) fechada agora. E normal: ela so abre "
          "enquanto uma partida esta acontecendo." % PORTA_PARTIDA)
    falar("             Quem hospeda precisa clicar em 'Eu abro a partida'")
    falar("             e o jogo tem que estar na tela ANTES do outro entrar.")

# ---------------------------------------------------------------- 4. colega
colega = sys.argv[1] if len(sys.argv) > 1 else ""
if colega:
    colega = colega.replace("http://", "").split(":")[0].strip("/")
    falar()
    falar("4. O computador do colega (%s)" % colega)
    falar("-" * 62)

    if not porta_aberta(colega, PORTA):
        torto("Nao alcanco o ARENA dele.",
              "Confira o endereco, se ele ligou 'Aceitar conexoes' e "
              "se voces estao na mesma rede.")
    else:
        certo("o ARENA dele responde")

        # /api/sinc/ola e' uma das rotas abertas a rede; /api/estado (que
        # era usada aqui) so responde ao proprio computador desde a Fase 3
        # da auditoria -- com ela, estas duas checagens sumiam em silencio.
        dele = pedir("http://%s:%d/api/sinc/ola" % (colega, PORTA), corpo={})
        if not dele:
            olhar("o ARENA dele respondeu, mas nao consegui ler a versao e o "
                  "codigo do aparelho dele.")
        else:
            if dele.get("versao") != meu.get("versao"):
                torto("Versoes diferentes: voce %s, ele %s."
                      % (versao, dele.get("versao", "antiga")),
                      "Os dois precisam ter a mesma versao do ARENA.")
            else:
                certo("mesma versao dos dois lados")

            if dele.get("servidor_id") == meu["config"]["dispositivo_id"]:
                torto("Voces dois tem o MESMO codigo de aparelho.",
                      "Um dos dois usa Ajustes > Perfil > Comecar do zero.")
            else:
                certo("codigos de aparelho diferentes")

        if porta_aberta(colega, PORTA_PARTIDA):
            certo("a partida dele esta aberta - pode entrar")
        else:
            olhar("a porta da partida dele esta fechada.")
            falar("             Ou ele ainda nao clicou em 'Eu abro a partida',")
            falar("             ou o firewall do Windows dele esta barrando o")
            falar("             retroarch.exe. Veja o documento 5.")

    # ---- o arquivo do jogo e o mesmo? ----
    meus_jogos = pedir("http://127.0.0.1:%d/api/catalogo" % PORTA, 8)
    if meus_jogos:
        falar()
        falar("5. Os arquivos de jogo batem?")
        falar("-" * 62)
        conferidos = iguais = 0
        for jogo in meus_jogos["jogos"][:40]:
            titulo = urllib.parse.quote(jogo["titulo"])
            minha = pedir("http://127.0.0.1:%d/api/jogo/impressao?titulo=%s"
                          % (PORTA, titulo), 3)
            dele = pedir("http://%s:%d/api/jogo/impressao?titulo=%s"
                         % (colega, PORTA, titulo), 3)
            if not minha or not dele:
                continue
            conferidos += 1
            if minha["marca"] == dele["marca"]:
                iguais += 1
            else:
                torto("'%s': arquivos DIFERENTES (regiao ou versao)."
                      % jogo["titulo"],
                      "Um dos dois copia o arquivo do outro.")
        if conferidos:
            certo("%d de %d jogos em comum com o arquivo igual"
                  % (iguais, conferidos))
        else:
            olhar("Nenhum jogo em comum entre os dois computadores.")
else:
    falar()
    falar("4. O computador do colega")
    falar("-" * 62)
    falar("  Nao informado. Para conferir tambem o dele, rode assim:")
    falar("      python partida.py 192.168.137.1")

# ---------------------------------------------------------------- resumo
falar()
falar("=" * 62)
falar("  RESUMO")
falar("=" * 62)
if problemas:
    falar("  %d problema(s) para resolver:" % len(problemas))
    for p in problemas:
        falar("   - %s" % p)
else:
    falar("  Nada errado por aqui.")
    if avisos:
        falar("  Confira os pontos marcados com [olhe] acima.")

falar()
falar("  A ordem certa, sempre:")
falar("   1. Os dois abrem o ARENA e ligam 'Aceitar conexoes da rede'.")
falar("   2. Quem hospeda clica em 'Eu abro a partida'.")
falar("   3. ESPERA o jogo aparecer na tela dele.")
falar("   4. So entao o outro clica em 'Entrar na partida do amigo'.")
falar("   5. Os dois precisam do MESMO arquivo de jogo.")
falar()
