# -*- coding: utf-8 -*-
r"""
ARENA - o celular como controle PELO CABO USB (o caminho de menor atraso).

Pedido do Rafael (25/10/2026): "tente implementar de alguma forma a conexao usb para otimizar ao maximo esses comandos
e que funcione muito bem sem fio tambem". O controle pelo Wi-Fi (controle_remoto.py) continua sendo o jeito de todo dia;
este e' o jeito de quem quer o menor atraso e a conexao que nao oscila.

COMO: o ADB oficial do Google (o mesmo que o painel "Celular ligado no cabo" usa: adb_aparelho.py). O comando
`adb reverse tcp:PORTA tcp:PORTA` faz o 127.0.0.1:PORTA DO CELULAR chegar no 127.0.0.1:PORTA DESTE computador, dentro do
cabo. Depois o ARENA manda o celular abrir no navegador dele a pagina do controle (http://127.0.0.1:PORTA/), ja com o
codigo no endereco depois do "#" (que o navegador nao manda para servidor nenhum). A pagina e o WebSocket vao e voltam
pelo cabo.

POR QUE E' MELHOR:
  * sem Wi-Fi no meio: a conta nao depende de roteador, de sinal, nem de o firewall do Windows deixar a porta 8780 entrar
    (no Windows, a rede "Publica" barra isso; o cabo chega por dentro do proprio computador);
  * sem a oscilacao do Wi-Fi (o roteador junta pacotes para poupar bateria do celular: o atraso vai de 3 ms a 100 ms);
  * o endereco 127.0.0.1 e' "contexto seguro" para o navegador do celular: so por ele a pagina pode ler o
    giroscopio e o acelerometro (inclinar o celular) e manter a tela acesa. Pelo Wi-Fi (http de rede) o Chrome nao deixa;
  * o celular carrega durante o jogo.

O QUE FICA: o celular precisa de Depuracao USB ligada e o computador, do ADB (nao vai no pacote: e' do Google). O ARENA
so LE e abre uma pagina: nada e' instalado no celular. Cada leitura que falha diz o que fazer, em portugues, nunca levanta.
"""
import re

import adb_aparelho as adb

PADRAO_DO_CODIGO = re.compile(r"^[0-9]{4,12}$")
_ligamos_o_servidor = False        # o servidor do adb (que guarda o `adb reverse`) foi ligado por este programa?


def _lista(adb_caminho):
    return adb.interpretar_lista(adb.executar(adb_caminho, ["devices", "-l"], tempo=adb.TEMPO_DO_ADB)[1])


def abrir_no_celular(porta, codigo, serial=None, jogador=None):
    """Liga o cabo a porta do controle e abre a pagina no celular. {ok, escolhido, aparelhos, dica, erro, como_baixar,
    pelo_cabo}: o que o professor precisa saber vai em "erro" ou "dica"; nunca levanta."""
    resposta = {"ok": False, "adb": None, "como_baixar": None, "aparelhos": [], "escolhido": None, "dica": None,
                "erro": None, "pelo_cabo": None}
    if not (isinstance(porta, int) and 1024 <= porta <= 65535) or not PADRAO_DO_CODIGO.match(str(codigo or "")):
        resposta["erro"] = "O controle do celular não está ligado. Ligue a chave e tente de novo."
        return resposta
    if serial is not None and not (isinstance(serial, str) and adb.PADRAO_DE_SERIAL.match(serial)):
        resposta["erro"] = "Celular inválido. Clique em Abrir de novo."
        return resposta
    numero = jogador if isinstance(jogador, int) and not isinstance(jogador, bool) and 1 <= jogador <= 8 else None
    caminho, origem = adb.achar_adb()
    if not caminho:
        resposta["como_baixar"] = adb.COMO_BAIXAR_O_ADB
        return resposta
    resposta["adb"] = origem
    try:
        global _ligamos_o_servidor
        with adb.TRAVA_ADB:
            # Sem adb.sessao(): ele derruba o servidor do adb ao sair, e o `adb reverse` vive nesse servidor (achado da
            # revisao de 26/10/2026). Quem derruba, depois do cabo, e' soltar(), se foi o ARENA que o ligou.
            if not adb.servidor_do_adb_de_pe():
                _ligamos_o_servidor = True
            aparelhos = _lista(caminho)
            resposta["aparelhos"] = aparelhos
            prontos = [a for a in aparelhos if a["pronto"]]
            alvo = None
            if serial is not None:
                alvo = next((a for a in aparelhos if a["serial"] == serial), None)
                if alvo is None:
                    resposta["erro"] = "Esse celular saiu do cabo. Clique em Abrir de novo."
            elif len(prontos) == 1:
                alvo = prontos[0]
            elif len(prontos) > 1:
                resposta["dica"] = "Há %d celulares no cabo. Escolha em qual abrir o controle." % len(prontos)
            elif aparelhos:
                resposta["dica"] = aparelhos[0]["estado_texto"]
            else:
                resposta["dica"] = "Nenhum celular encontrado no cabo. " + adb.COMO_LIGAR_O_CELULAR
            if alvo is not None and not alvo["pronto"]:
                resposta["dica"] = alvo["estado_texto"]
            elif alvo is not None:
                resposta["escolhido"] = alvo["serial"]
                resposta["pelo_cabo"] = not alvo["por_wifi"]
                feito, saida = adb.executar(caminho, ["-s", alvo["serial"], "reverse", "tcp:%d" % porta, "tcp:%d" % porta])
                if feito != 0:
                    resposta["erro"] = ("O celular não deixou ligar o cabo ao controle (%s). Destrave a tela, confira se a "
                                        "Depuração USB está ligada e tente de novo." % (saida.strip().splitlines() or ["sem resposta"])[0][:100])
                    return resposta
                # O "#" guarda o codigo so no celular: o navegador nao o manda para servidor nenhum, e a pagina o tira do endereco.
                endereco = "http://127.0.0.1:%d/#c=%s%s" % (porta, codigo, "&j=%d" % numero if numero else "")
                feito, saida = adb.executar(caminho, ["-s", alvo["serial"], "shell",
                                                      "am start -a android.intent.action.VIEW -d '%s'" % endereco])
                if feito != 0 or "Error" in saida:
                    resposta["erro"] = ("O cabo está ligado, mas o celular não abriu a página (%s). Abra o navegador do celular e "
                                        "digite http://127.0.0.1:%d/" % ((saida.strip().splitlines() or ["sem resposta"])[0][:100], porta))
                    return resposta
                resposta["ok"] = True
                if alvo["por_wifi"]:
                    resposta["dica"] = ("Este celular está ligado ao ADB pelo Wi-Fi, e não pelo cabo: o atraso é o do Wi-Fi. Para o "
                                        "menor atraso, ligue o cabo USB e conecte por ele.")
    except TimeoutError:
        resposta["erro"] = "O celular demorou demais para responder. Destrave a tela, confira o cabo e tente de novo."
    except OSError as falha:
        resposta["erro"] = "Não consegui abrir o adb (%s). Confira se o arquivo está inteiro." % (falha.strerror or falha)
    return resposta


def soltar(ligados, ultimo=True):
    """Desfaz o cabo de cada (serial, porta) de 'ligados': o celular deixa de alcancar a porta deste computador. Tudo
    sem levantar: se o celular ja saiu do cabo, nao ha o que desfazer. 'ultimo': nao sobrou cabo nenhum; se foi o ARENA
    que ligou o servidor do adb, ele o desliga (o ADB no pen drive nao pode ficar segurando a pasta)."""
    global _ligamos_o_servidor
    caminho, _origem = adb.achar_adb()
    if not caminho:
        return
    try:
        with adb.TRAVA_ADB:
            for serial, porta in ligados or ():
                try:
                    adb.executar(caminho, ["-s", serial, "reverse", "--remove", "tcp:%d" % porta], tempo=adb.TEMPO_DO_ADB)
                except (OSError, TimeoutError):
                    pass
            if ultimo and _ligamos_o_servidor and adb.servidor_do_adb_de_pe():
                try:
                    adb.executar(caminho, ["kill-server"], tempo=adb.TEMPO_DO_ADB)
                except (OSError, TimeoutError):
                    pass
            if ultimo:
                _ligamos_o_servidor = False
    except (OSError, TimeoutError):
        pass
