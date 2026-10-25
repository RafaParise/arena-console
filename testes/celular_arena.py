# -*- coding: utf-8 -*-
r"""O ARENA que roda NO celular, pelo computador: abre o app, chama as rotas da API dele e abre jogos.

So funciona com o APK de teste (ferramentas\montar_android.py --teste): e' ele que deixa o WebView aceitar a depuracao
(o protocolo CDP), e e' por ela que o pedido leva o cookie do segredo do app. O APK de producao nao deixa (de proposito).

Uso:
    servidor\python\python.exe testes\celular_arena.py abrir
    servidor\python\python.exe testes\celular_arena.py api /api/estado [filtro]
    servidor\python\python.exe testes\celular_arena.py api /api/jogar '{"jogo_id": "jogos/livres/..."}'
    servidor\python\python.exe testes\celular_arena.py jogos [pedaco do nome do console ou do jogo]
    servidor\python\python.exe testes\celular_arena.py jogar <pedaco do titulo> [--console pedaco]
Tudo vai para o celular fisico (ou o aparelho da variavel ANDROID_SERIAL), nunca para o emulador.
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import celular_mao  # noqa: E402

os.environ.setdefault("ANDROID_SERIAL", celular_mao.escolher())
import teste_android as t  # noqa: E402  (a classe Pagina, que fala com o WebView pelo CDP)


def abrir(segundos=90):
    """Poe o ARENA na frente e espera a tela dele aceitar pedidos. Devolve a Pagina (feche com .fechar())."""
    if "ArenaActivity" not in t.tela_de_cima():
        t.adb("shell", "am", "start", "-n", t.TELA_DO_ARENA)
    pagina = t.Pagina(segundos=segundos)
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        resposta = pagina.pedir("/api/estado")
        if isinstance(resposta, dict) and "erro" not in resposta:
            return pagina
        time.sleep(2)          # o primeiro pedido depois de uma volta de jogo as vezes da "Failed to fetch"
    raise SystemExit("A tela do ARENA no celular nao respondeu a /api/estado em %d s." % segundos)


def pedir(pagina, rota, corpo=None, tentativas=4):
    for numero in range(tentativas):
        resposta = pagina.pedir(rota, corpo)
        if not (isinstance(resposta, dict) and str(resposta.get("erro", "")).startswith("TypeError: Failed to fetch")):
            return resposta
        time.sleep(2 + numero)
    return resposta


def catalogo(pagina):
    resposta = pedir(pagina, "/api/catalogo")
    return resposta.get("jogos", resposta) if isinstance(resposta, dict) else resposta


def achar_jogo(pagina, pedaco, console=None):
    pedaco = pedaco.lower()
    for jogo in catalogo(pagina):
        if pedaco in jogo.get("titulo", "").lower() and (not console or console.lower() in jogo.get("plataforma_nome", "").lower()):
            return jogo
    return None


def main(argv):
    for saida in (sys.stdout, sys.stderr):
        try:
            saida.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2:
        print(__doc__)
        return 2
    verbo, resto = argv[1], argv[2:]
    pagina = abrir()
    try:
        if verbo == "abrir":
            print("ARENA aberto no celular (%s)." % os.environ["ANDROID_SERIAL"])
        elif verbo == "api":
            corpo = json.loads(resto[1]) if len(resto) > 1 and resto[1].lstrip().startswith("{") else None
            filtro = resto[2].lower() if len(resto) > 2 else (resto[1].lower() if len(resto) > 1 and corpo is None else "")
            texto = json.dumps(pedir(pagina, resto[0], corpo), ensure_ascii=False, indent=1)
            if filtro:
                texto = "\n".join(linha for linha in texto.splitlines() if filtro in linha.lower())
            print(texto[:int(os.environ.get("MAX", "8000"))])
        elif verbo == "jogos":
            filtro = " ".join(resto).lower()
            for jogo in catalogo(pagina):
                if not filtro or filtro in jogo.get("titulo", "").lower() or filtro in jogo.get("plataforma_nome", "").lower():
                    print("%-34s %-40s jog=%s  %s" % (jogo.get("plataforma_nome", "")[:34], jogo.get("titulo", "")[:40],
                                                       jogo.get("jogadores_max"), jogo["id"]))
        elif verbo == "jogar":
            console = resto[resto.index("--console") + 1] if "--console" in resto else None
            jeito = resto[resto.index("--jeito") + 1] if "--jeito" in resto else None
            titulo = " ".join(r for r in resto if r not in ("--console", console, "--jeito", jeito))
            jogo = achar_jogo(pagina, titulo, console)
            if not jogo:
                print("Nao achei o jogo %r." % titulo)
                return 1
            corpo = {"jogo_id": jogo["id"]}
            if jeito:
                corpo["jeito"] = jeito          # original, livre ou externo (sem "lembrar": nao muda a escolha dele)
            print(json.dumps(pedir(pagina, "/api/jogar", corpo), ensure_ascii=False)[:600])
        else:
            print(__doc__)
            return 2
    finally:
        pagina.fechar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
