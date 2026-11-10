# -*- coding: utf-8 -*-
r""""Estamos em casas diferentes" pelo ARENA de verdade, com o repasse proprio (10/11/2026).

Abre o repasse do ARENA (servidor\repasse_proprio.py) neste computador e uma COPIA do ARENA (testes\copia_do_arena.py)
com o Super Bomberman 4 e o snes9x, com o repasse posto em Ajustes. Duas fases:
  1. O ARENA abre a partida pela internet: a resposta traz o codigo de 6 numeros; um RetroArch de fora acha a sala
     por esse codigo e entra como jogador 2.
  2. Um RetroArch de fora abre a sala (o teste reserva o codigo); o ARENA entra digitando o codigo.
E confere os erros que o aluno pode ver: sem repasse em Ajustes, e codigo que nao existe.

Uso:
    servidor\python\python.exe testes\teste_repasse_proprio_pelo_arena.py
"""
import os
import sys
import time
import urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_cenarios_sala import CORE, JOGO, graficos, ler_log, matar  # noqa: E402
from teste_repasse_proprio_retroarch import abrir_repasse, abrir_retroarch, rp  # noqa: E402

NUCLEO = os.path.basename(CORE)


def pedir_ou_erro(rota, corpo, espera=40):
    """A resposta do ARENA, ou {"erro": ...} quando ele responde com erro (HTTP 400)."""
    try:
        return c.pedir(rota, corpo, espera=espera)
    except urllib.error.HTTPError as falha:
        try:
            import json
            return json.loads(falha.read().decode("utf-8"))
        except ValueError:
            return {"erro": "HTTP %d" % falha.code}


def main():
    if not os.path.isfile(JOGO):
        print("Falta o jogo do teste: %s" % JOGO)
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d): feche-o antes." % c.PORTA)
        return 1
    porta, fechar_repasse = abrir_repasse()
    endereco = "127.0.0.1:%d" % porta
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    de_fora = []
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    def log_da_copia():
        candidatos = sorted(n for n in os.listdir(os.path.join(copia, "dados")) if n.startswith("retroarch__"))
        if not candidatos:
            return ""
        with open(os.path.join(copia, "dados", candidatos[-1]), encoding="utf-8", errors="ignore") as arquivo:
            return arquivo.read()

    def esperar_texto(funcao, texto, limite=40):
        fim = time.monotonic() + limite
        while time.monotonic() < fim:
            if texto in funcao().lower():
                return True
            time.sleep(2)
        return False

    try:
        print("Copiando o ARENA para %s ..." % copia, flush=True)
        c.montar(copia, [NUCLEO], {"Super Nintendo": [JOGO]})
        servidor = c.subir_servidor(copia, os.path.join(trabalho, "servidor.log"))
        c.pedir("/api/indexar", {}, espera=90)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "snes"), 60)
        confere("o jogo aparece no Super Nintendo", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]
        c.pedir("/api/config", {"apelido": "Teste"})

        print("0. Sem repasse em Ajustes", flush=True)
        resposta = pedir_ou_erro("/api/jogar", {"jogo_id": jogo_id, "apelido": "Teste", "partida": "hospedar",
                                                "pela_internet": True})
        confere("o ARENA explica que falta o repasse", "repasse da turma" in str(resposta.get("erro", "")),
                resposta.get("erro"))
        guardado = c.pedir("/api/config", {"repasse_proprio": endereco})
        confere("o endereco do repasse ficou guardado", (guardado.get("config") or {}).get("repasse_proprio") == endereco)
        teste = pedir_ou_erro("/api/repasse/testar", {"endereco": endereco})
        confere("o Testar de Ajustes acha o repasse", bool(teste.get("ok")), teste.get("mensagem") or teste.get("erro"))

        print("1. O ARENA abre a partida pela internet", flush=True)
        resposta = pedir_ou_erro("/api/jogar", {"jogo_id": jogo_id, "apelido": "Teste", "partida": "hospedar",
                                                "pela_internet": True, "esperar": True})
        codigo = str(resposta.get("codigo_sala", ""))
        confere("a resposta traz o codigo da sala", len(codigo) == 6 and codigo.isdigit(), resposta.get("erro") or codigo)
        if codigo:
            achado, erro = rp.procurar_sala(endereco, codigo, tentativas=20, intervalo=1.0)
            confere("a sala abriu no repasse", bool(achado), erro)
            if achado:
                opcoes = graficos.opcoes_de_partida("Convidado", False, pela_internet=True, jogador=2)
                opcoes.update({"netplay_ip_port": str(porta), "netplay_use_mitm_server": "false",
                               "netplay_nat_traversal": "false"})
                de_fora.append(abrir_retroarch(os.path.join(trabalho, "conv"), opcoes,
                                               ["--connect", "127.0.0.1", "--port", str(porta),
                                                "--mitm-session=" + achado[0]]))
                confere("o convidado de fora entrou como jogador 2",
                        esperar_texto(log_da_copia, "se juntou como o jogador 2"))
                confere("pelo tunel", "tunnel link connection completed" in log_da_copia().lower())
        for processo, log in de_fora:
            matar(processo, log)
        de_fora.clear()
        c.fechar_pela_janela(retroarch, 30)
        c.esperar(lambda: not c.processos("retroarch", retroarch), 20)
        time.sleep(3)

        print("2. O ARENA entra pelo codigo", flush=True)
        resposta = pedir_ou_erro("/api/jogar", {"jogo_id": jogo_id, "apelido": "Teste", "partida": "entrar",
                                                "pela_internet": True, "codigo_sala": "000000"})
        confere("codigo que nao existe: o ARENA explica", "Nao ha sala" in str(resposta.get("erro", "")),
                resposta.get("erro"))
        codigo, erro = rp.reservar_sala(endereco)
        opcoes = graficos.opcoes_de_partida("Anfitriao", True, pela_internet=True, jogador=1)
        opcoes.update({"netplay_use_mitm_server": "true", "netplay_mitm_server": "custom",
                       "netplay_custom_mitm_server": rp.para_o_retroarch(endereco), "netplay_nat_traversal": "false",
                       "netplay_public_announce": "false"})
        pasta_host = os.path.join(trabalho, "host")
        de_fora.append(abrir_retroarch(pasta_host, opcoes, ["--host"]))
        resposta = pedir_ou_erro("/api/jogar", {"jogo_id": jogo_id, "apelido": "Teste", "partida": "entrar",
                                                "pela_internet": True, "codigo_sala": codigo}, espera=60)
        confere("o ARENA aceitou o codigo", bool(resposta.get("ok")), resposta.get("erro"))
        entrou = esperar_texto(lambda: ler_log(pasta_host), "se juntou como o jogador 2")
        confere("o ARENA entrou como jogador 2 na sala de fora", entrou)
        if not entrou:
            for linha in [l for l in log_da_copia().splitlines() if "netplay" in l.lower() or "argument" in l.lower()
                          or "connect" in l.lower()][-12:]:
                print("    " + linha[:180])
    finally:
        for processo, log in de_fora:
            matar(processo, log)
        for pid in c.processos("retroarch", retroarch):
            c.subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        if servidor is not None:
            c.derrubar(copia)
        fechar_repasse()
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        print("FALHOU: %d de %s" % (len(falhas), ", ".join(falhas)))
        return 1
    print("Casas diferentes pelo ARENA, com o repasse proprio: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
