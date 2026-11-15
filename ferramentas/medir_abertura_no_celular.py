# -*- coding: utf-8 -*-
r"""Mede a abertura do ARENA num celular de verdade e confere o servidor nativo (14/11/2026).

A ideia veio do "test_adb_tvbox.sh" dos blueprints (docs\arena-blueprints\scripts), reescrita para o ARENA de
verdade: o pacote, a atividade e o servidor (libarenanativo.so) daqui. É a medida que o docs\DESEMPENHO-SERVIDOR.md
descreve feita à mão no Galaxy A12, agora automática.

Com o celular no cabo (depuração USB ligada) e o ARENA já instalado:
  1. N vezes (padrão 3): fecha o app, abre a tela do ARENA e espera no registro do Android (logcat, sem apagar nada) a
     linha que o launcher\app.js escreve quando a lista aparece ("[ARENA] lista na tela", etiqueta ARENA, que o
     ArenaActivity.java copia do console da página). O tempo da abertura vai da linha START do ActivityTaskManager
     até essa linha, pelos dois horários do próprio registro. Também guarda os ms que a própria linha diz
     (performance.now(), contado desde que a página começou a carregar);
  2. confere o servidor nativo: o processo libarenanativo.so vivo e se o ARENA escuta só no 127.0.0.1;
  3. confere o serviço em primeiro plano do ARENA (isForeground) e o registro de falhas (logcat -b crash);
  4. tira uma foto da tela, se a pessoa pedir (--foto CAMINHO);
  5. no fim, o resumo: mediana e pior tempo, nativo sim/não, escuta só local sim/não e as falhas (--json CAMINHO grava).

O que ele NUNCA faz no aparelho: tocar na tela ou mandar tecla (nem ligar/desligar a tela), mudar configuração,
instalar ou desinstalar. Só fecha e abre o próprio ARENA e lê.

Reaproveita o ferramentas\auditoria_celular.py (achar o adb e o celular, rodar o adb, o endereço do 127.0.0.1 no
/proc/net/tcp) e o servidor\adb_aparelho.py (por trás dele).

Uso:
    servidor\python\python.exe ferramentas\medir_abertura_no_celular.py [--vezes 3] [--foto tela.png] [--json saida.json]
"""
import argparse
import datetime
import json
import os
import re
import statistics
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import auditoria_celular as aud  # noqa: E402  (acha o adb e o celular; põe o servidor\ no caminho do Python)

PACOTE = aud.PACOTE                       # io.github.rafaparise.arena
TELA_DO_ARENA = aud.TELA_DO_ARENA         # io.github.rafaparise.arena/io.github.rafaparise.arena.ArenaActivity
LOOPBACK = aud.LOOPBACK                   # o 127.0.0.1 como o /proc/net/tcp e o tcp6 escrevem
NOME_DO_NATIVO = "libarenanativo.so"      # o servidor em Rust (ArenaServico.java o abre)
MARCA_DA_LISTA = "[ARENA] lista na tela"  # a linha do launcher\app.js
PORTA_DO_SERVIDOR = 8777

# Uma linha do logcat no formato threadtime: "11-14 13:45:06.858 27746 27746 I ARENA   : texto".
LINHA_THREADTIME = re.compile(
    r"^(?P<data>\d\d-\d\d) (?P<hora>\d\d:\d\d:\d\d\.\d{3})\s+(?P<pid>\d+)\s+(?P<tid>\d+)\s+"
    r"(?P<nivel>[VDIWEFA])\s+(?P<etiqueta>[^:]*?)\s*: (?P<texto>.*)$")


# ---------------------------------------------------------------------------
# Leitura dos textos (funções puras: o teste as confere com exemplos, sem celular)
# ---------------------------------------------------------------------------

def horario_do_logcat(data, hora):
    """'11-14' e '13:45:06.858' viram um datetime. O logcat não escreve o ano: uso 2000 (bissexto, aceita 29/02)."""
    return datetime.datetime.strptime("2000-%s %s" % (data, hora), "%Y-%m-%d %H:%M:%S.%f")


def ler_linha(linha):
    """Uma linha do logcat em threadtime vira um dicionário (horario, pid, etiqueta, texto), ou None se não é dessas."""
    achou = LINHA_THREADTIME.match(linha.rstrip("\r\n"))
    if not achou:
        return None
    return {"horario": horario_do_logcat(achou.group("data"), achou.group("hora")),
            "pid": int(achou.group("pid")), "etiqueta": achou.group("etiqueta").strip(), "texto": achou.group("texto")}


def eh_start_do_arena(linha):
    """A linha START do ActivityTaskManager que abre a tela do ARENA (e não a de outro app)."""
    if linha["etiqueta"] != "ActivityTaskManager" or not linha["texto"].startswith("START u"):
        return False
    componente = re.search(r"cmp=([\w.]+)/([\w.$]+)", linha["texto"])
    if not componente or componente.group(1) != PACOTE:
        return False
    atividade = componente.group(2)
    return atividade in (".ArenaActivity", PACOTE + ".ArenaActivity")


def medir_no_logcat(texto):
    """Do registro de UMA abertura, o tempo da linha START até a "[ARENA] lista na tela".
    Devolve {"ms": ..., "ms_da_pagina": ..., "guardada_pelo_nativo": ...}, ou None se falta uma das duas linhas.
    Se o registro tem mais de um START do ARENA, vale o último antes da lista."""
    inicio = None
    for bruta in texto.splitlines():
        linha = ler_linha(bruta)
        if not linha:
            continue
        if eh_start_do_arena(linha):
            inicio = linha["horario"]
        elif linha["etiqueta"] == "ARENA" and MARCA_DA_LISTA in linha["texto"] and inicio is not None:
            diferenca = linha["horario"] - inicio
            if diferenca.total_seconds() < 0:          # virou o ano (31/12 para 01/01): o logcat não diz o ano
                diferenca += datetime.timedelta(days=366)
            pagina = re.search(r", (\d+) ms depois", linha["texto"])
            return {"ms": int(round(diferenca.total_seconds() * 1000)),
                    "ms_da_pagina": int(pagina.group(1)) if pagina else None,
                    "guardada_pelo_nativo": "guardada pelo nativo" in linha["texto"]}
    return None


def ler_ps(texto):
    """A saída do 'ps -A' (toybox do Android) vira uma lista de {"usuario", "pid", "ppid", "nome"}.
    O nome é a última coluna; a primeira linha (USER PID PPID ...) é o cabeçalho."""
    processos = []
    for linha in texto.splitlines():
        campos = linha.split()
        if len(campos) < 4 or not campos[1].isdigit() or not campos[2].isdigit():
            continue                                    # o cabeçalho e as linhas quebradas
        processos.append({"usuario": campos[0], "pid": int(campos[1]), "ppid": int(campos[2]), "nome": campos[-1]})
    return processos


def uid_do_usuario(usuario):
    """'u0_a337' (o nome que o ps mostra para um app) vira o número 10337, o mesmo do /proc/net/tcp.
    Regra do Android: uid = usuário * 100000 + 10000 + número do app. None se o nome não é desse formato."""
    achou = re.fullmatch(r"u(\d+)_a(\d+)", usuario or "")
    if not achou:
        return int(usuario) if (usuario or "").isdigit() else None
    return int(achou.group(1)) * 100000 + 10000 + int(achou.group(2))


def processos_do_arena(processos):
    """Do 'ps -A', só os processos do ARENA: o da tela (PACOTE:tela) e os filhos dele (o nativo e o Python)."""
    tela = [p for p in processos if p["nome"].startswith(PACOTE)]
    pids = {p["pid"] for p in tela}
    filhos = [p for p in processos if p["ppid"] in pids]
    netos = [p for p in processos if p["ppid"] in {f["pid"] for f in filhos}]
    return tela + filhos + netos


def escutas(texto_proc_net, uid):
    """As portas TCP que o uid ESCUTA (estado 0A = LISTEN) no texto do /proc/net/tcp e/ou tcp6.
    Cada uma vira {"porta", "endereco", "so_do_aparelho"}. Mesma leitura do soquetes_do_app() do
    ferramentas\\auditoria_celular.py, separada aqui para o teste conferir sem celular."""
    portas = []
    for linha in texto_proc_net.splitlines():
        campos = linha.split()
        if len(campos) < 10 or ":" not in campos[1] or campos[7] != str(uid) or campos[3] != "0A":
            continue
        endereco, porta = campos[1].split(":")
        portas.append({"porta": int(porta, 16), "endereco": endereco, "so_do_aparelho": endereco in LOOPBACK})
    return portas


def servico_em_primeiro_plano(texto_dumpsys):
    """No 'dumpsys activity services PACOTE', o ArenaServico está em primeiro plano (isForeground=true)?
    True/False, ou None se o serviço nem aparece (o ARENA está fechado). Os outros serviços do pacote (o
    SandboxedProcessService do WebView) não contam."""
    blocos = re.split(r"\n\s*\* ServiceRecord\{", "\n" + texto_dumpsys)
    for bloco in blocos[1:]:
        cabecalho = bloco.split("\n", 1)[0]
        if "ArenaServico" in cabecalho:
            achou = re.search(r"isForeground=(true|false)", bloco)
            return achou is not None and achou.group(1) == "true"
    return None


def falhas_do_crash(texto):
    """No 'logcat -b crash -d', as quedas do ARENA (as de outros apps só se contam, por nome do processo)."""
    do_arena, de_outros = [], {}
    linhas = texto.splitlines()
    for numero, linha in enumerate(linhas):
        if "FATAL EXCEPTION" in linha or "Fatal signal" in linha:
            junto = " ".join(linhas[numero:numero + 3])
            achou = re.search(r"Process: ([\w.:]+)", junto) or re.search(r"\(([\w.:]+)\), pid", junto)
            processo = achou.group(1) if achou else "?"
            if processo.startswith(PACOTE) or "arena" in processo.lower():
                do_arena.append(linha.strip()[:200])
            else:
                de_outros[processo] = de_outros.get(processo, 0) + 1
    return {"do_arena": do_arena[:20], "de_outros_apps": de_outros}


def resumo_dos_tempos(tempos):
    """Mediana e pior tempo (ms) das aberturas que deram certo; None quando nenhuma deu."""
    if not tempos:
        return {"mediana_ms": None, "pior_ms": None}
    return {"mediana_ms": int(round(statistics.median(tempos))), "pior_ms": max(tempos)}


# ---------------------------------------------------------------------------
# No aparelho
# ---------------------------------------------------------------------------

def horario_do_aparelho():
    """O relogio do celular em segundos desde 1970 ("1794677180.000"), no formato que o 'logcat -T' aceita."""
    segundos = aud.shell("date +%s").strip()
    return (segundos if segundos.isdigit() else "0") + ".000"


def abrir_uma_vez(espera):
    """Fecha o ARENA, abre a tela e espera a linha da lista (até 'espera' segundos). O registro do Android não é
    apagado (ele é do aparelho inteiro): lê só o que veio depois do horário em que esta abertura começou."""
    aud.shell("am force-stop " + PACOTE)
    time.sleep(2)                                       # deixa o Android terminar de fechar os processos
    desde = horario_do_aparelho()
    aud.shell("am start -n " + TELA_DO_ARENA)
    limite = time.monotonic() + espera
    while time.monotonic() < limite:
        time.sleep(0.5)
        registro = aud.texto("logcat", "-d", "-T", desde, "-v", "threadtime", "-s", "ActivityTaskManager:I",
                             "ARENA:I", segundos=30)
        medida = medir_no_logcat(registro)
        if medida:
            return medida
    return None


def conferir_servidor():
    """O nativo vivo e o que o ARENA escuta (todos os processos dele usam o mesmo uid do app)."""
    processos = processos_do_arena(ler_ps(aud.shell("ps -A")))
    nativo = [p for p in processos if NOME_DO_NATIVO in p["nome"]]
    uid = next((uid_do_usuario(p["usuario"]) for p in processos if uid_do_usuario(p["usuario"])), None)
    portas = escutas(aud.shell("cat /proc/net/tcp") + "\n" + aud.shell("cat /proc/net/tcp6"), uid) if uid else []
    return {"processos": [p["nome"] for p in processos], "nativo_rodando": bool(nativo),
            "pid_do_nativo": nativo[0]["pid"] if nativo else None, "uid": uid, "escutas": portas,
            "escuta_a_porta_do_servidor": any(p["porta"] == PORTA_DO_SERVIDOR for p in portas),
            "escuta_so_local": bool(portas) and all(p["so_do_aparelho"] for p in portas)}


def tirar_foto(caminho):
    """A foto da tela (screencap) num arquivo PNG. Devolve o caminho, ou o motivo de não ter dado."""
    feito = aud.adb("exec-out", "screencap", "-p", segundos=60)
    if feito.returncode != 0 or not feito.stdout.startswith(b"\x89PNG"):
        return {"erro": "o celular não mandou a foto da tela; confira se ele está desbloqueado e tente de novo"}
    pasta = os.path.dirname(os.path.abspath(caminho))
    os.makedirs(pasta, exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(feito.stdout)
    return {"arquivo": caminho, "bytes": len(feito.stdout)}


def sim_nao(valor):
    return "sim" if valor else ("não" if valor is not None else "não sei")


def main(argumentos=None):
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")   # acento certo no terminal e no arquivo
        except (AttributeError, ValueError):
            pass
    leitor = argparse.ArgumentParser(
        add_help=False, description="Mede a abertura do ARENA no celular (cabo USB) e confere o servidor nativo.",
        epilog="Nunca toca na tela, nunca muda configuração e nunca instala nada no aparelho.")
    leitor._optionals.title = "opções"
    leitor.add_argument("-h", "--ajuda", action="help", help="mostra esta ajuda e sai")
    leitor.add_argument("--vezes", type=int, default=3, help="quantas aberturas medir (padrão: 3)")
    leitor.add_argument("--espera", type=int, default=40,
                        help="segundos de espera pela lista na tela em cada abertura (padrão: 40)")
    leitor.add_argument("--foto", metavar="CAMINHO", help="grava uma foto da tela (PNG) neste arquivo no fim")
    leitor.add_argument("--json", metavar="CAMINHO", help="grava o resultado inteiro neste arquivo JSON")
    opcoes = leitor.parse_args(argumentos)
    if opcoes.vezes < 1 or opcoes.espera < 5:
        leitor.error("use --vezes 1 ou mais e --espera 5 ou mais")

    aud.ADB = aud.achar_adb()                           # sai com o recado de como instalar, se não achar
    aud.SERIE = aud.escolher_o_celular()                # sai com o recado de ligar a depuração USB
    instalado = aud.shell("pm path " + PACOTE).strip()
    if not instalado.startswith("package:"):
        raise SystemExit("O ARENA não está instalado neste celular. Instale antes com "
                         "servidor\\python\\python.exe ferramentas\\instalar_no_celular.py e rode de novo.")

    aberturas = []
    comeco = horario_do_aparelho()                      # as quedas contadas no fim são só as desta medida
    for vez in range(1, opcoes.vezes + 1):
        medida = abrir_uma_vez(opcoes.espera)
        aberturas.append(medida)
        if medida:
            print("Abertura %d: %d ms (a página diz %s ms%s)" % (
                vez, medida["ms"], medida["ms_da_pagina"], ", com a lista guardada pelo nativo"
                if medida["guardada_pelo_nativo"] else ""))
        else:
            print("Abertura %d: a lista não apareceu em %d s (confira se o celular está desbloqueado e "
                  "rode de novo com --espera maior)" % (vez, opcoes.espera))
    time.sleep(3)                                       # o servidor termina de abrir depois da lista

    servidor = conferir_servidor()
    primeiro_plano = servico_em_primeiro_plano(aud.shell("dumpsys activity services " + PACOTE))
    falhas = falhas_do_crash(aud.texto("logcat", "-b", "crash", "-d", "-T", comeco, "-v", "threadtime",
                                         segundos=60))
    foto = tirar_foto(opcoes.foto) if opcoes.foto else None

    tempos = [m["ms"] for m in aberturas if m]
    resultado = {"quando": datetime.datetime.now().isoformat(timespec="seconds"),
                 "aparelho": aud.shell("getprop ro.product.model").strip(),
                 "android": aud.shell("getprop ro.build.version.release").strip(),
                 "aberturas": aberturas, **resumo_dos_tempos(tempos),
                 "servidor": servidor, "servico_em_primeiro_plano": primeiro_plano, "falhas": falhas, "foto": foto}

    print()
    print("Resumo (%s, Android %s):" % (resultado["aparelho"], resultado["android"]))
    print("  aberturas medidas: %d de %d" % (len(tempos), opcoes.vezes))
    if tempos:
        print("  mediana: %d ms; pior: %d ms" % (resultado["mediana_ms"], resultado["pior_ms"]))
    print("  servidor nativo (%s) rodando: %s" % (NOME_DO_NATIVO, sim_nao(servidor["nativo_rodando"])))
    print("  escuta só no 127.0.0.1: %s (%s)" % (sim_nao(servidor["escuta_so_local"]), ", ".join(
        "%s:%d" % ("127.0.0.1" if p["so_do_aparelho"] else p["endereco"], p["porta"]) for p in servidor["escutas"])
        or "nenhuma porta"))
    if any(not p["so_do_aparelho"] for p in servidor["escutas"]):
        print("    (o 0.0.0.0 é a rede inteira: é o que a chave \"Liberar a rede\" dos Ajustes do ARENA faz; se ela"
              " não foi ligada de propósito, desligue-a lá)")
    print("  serviço em primeiro plano: %s" % sim_nao(primeiro_plano))
    print("  quedas do ARENA no registro: %d%s" % (len(falhas["do_arena"]), "".join(
        "\n    " + linha for linha in falhas["do_arena"])))
    if foto:
        print("  foto da tela: %s" % (foto.get("arquivo") or foto.get("erro")))
    if opcoes.json:
        pasta = os.path.dirname(os.path.abspath(opcoes.json))
        os.makedirs(pasta, exist_ok=True)
        with open(opcoes.json, "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
        print("  resultado gravado em %s" % opcoes.json)
    tudo_certo = (len(tempos) == opcoes.vezes and servidor["nativo_rodando"] and servidor["escuta_so_local"]
                  and primeiro_plano and not falhas["do_arena"])
    return 0 if tudo_certo else 1


if __name__ == "__main__":
    sys.exit(main())
