# -*- coding: utf-8 -*-
r"""Multitap, Fase B: a regra de ouro.

"Jogando sozinho ou em dois, nada muda em relacao a hoje." Este teste prova
isso comparando o arquivo de configuracao da partida (o --appendconfig)
gerado pela versao do ARENA de ANTES do multitap (commit 97ffe03, lido do git) com o da
versao ATUAL, jogo por jogo, pela rota /api/jogar de verdade.

Como: monta duas copias temporarias (antes e agora), com os mesmos nomes de
jogos da pasta jogos\pessoais (arquivos vazios -- o conteudo nao importa
aqui) e o RetroArch trocado por um falso que:
  - nao abre nada, so fecha na hora;
  - imita o RetroArch de verdade gravando no retroarch.cfg, ao fechar, o que
    veio no arquivo da partida (ver testes\protege_cfg.py).

Confere:
  1. jogo de 1 ou 2 jogadores: arquivo da partida IGUAL ao de antes, nos 3
     modos (sozinho, hospedar, entrar);
  2. jogo de 3+ (Super Bomberman): o adaptador chega (p2 = 257), o limite de
     conexoes sobe (4) e o controle 3 em diante e' lido (input_max_users 5);
  3. depois de uma partida de 3+, o retroarch.cfg volta a ter nas portas o
     que tinha antes (nada vaza para o proximo jogo).

Nada disto toca no dados\ nem no retroarch\ de verdade.

Uso:
    servidor\python\python.exe testes\teste_multitap_regra_de_ouro.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = os.path.join(RAIZ, "servidor", "python", "python.exe")
MODOS = ("sozinho", "hospedar", "entrar")
CHAVES_PORTAS = ["input_libretro_device_p%d" % n for n in range(1, 6)] + ["input_max_users"]


# ---------------------------------------------------------------------------
# Montagem das duas copias
# ---------------------------------------------------------------------------

def arquivos_do_git(revisao, pastas):
    saida = subprocess.run(["git", "ls-tree", "-r", "--name-only", revisao] + pastas,
                           cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    return [l for l in saida.splitlines() if not l.startswith("servidor/python/")
            and "/tests/" not in l]


# A versao "de hoje" da regra de ouro e' SEMPRE a de antes de todo o trabalho
# do multitap (Fase A so pesquisou, nao mudou o funcionamento). Comparar com
# o ultimo commit deixaria uma mudanca se esconder de fase em fase.
REVISAO_ANTES = "97ffe03"

# Titulos que mudaram DE PROPOSITO depois da versao de antes (sem par, nao
# da para comparar):
#  - 25/09/2026: "disc.gdi" passou a ter o nome da pasta ("Disc" -> "Capcom
#    Vs SNK 2...");
#  - 03/10/2026: o KOF 2002 do professor virou o kof2k2fd.zip do FBNeo, e o
#    nome vem de nomes_arcade.NOMES_FORA_DO_BANCO (a versao de antes nao tem
#    nomes de fliperama e o chamaria pelo nome do arquivo).
TITULOS_NOVOS_DE_PROPOSITO = {"Capcom Vs SNK 2 Millionaire Fighting 2001",
                              "The King of Fighters 2002"}

# C64 (VICE) e Amiga (PUAE) passaram a recusar o Jogar Junto DE PROPOSITO
# (25/09/2026): o nucleo nao tem netplay, confirmado tentando hospedar.
# Antes o ARENA abria e o RetroArch falhava; agora o servidor responde 409.
JOGAR_JUNTO_RECUSADO_DE_PROPOSITO = {"Alien Breed Disk1", "Top Gear 2 Disk2",
                                     "INTKARAT", "Mule", "PRINCEOP",
                                     # Java ME (15/10/2026): o FreeJ2ME-Plus nao tem
                                     # netplay, confirmado tentando hospedar.
                                     "God of War Betrayal J2ME EN V0195"}


# Auditoria 3 (Fase 4, J2, e a revisao dela): chaves que o RetroArch desta
# pasta nao conhece. As de nome errado sao COMPARADAS pelo nome certo (a
# versao de antes passa pelo mapa) -- assim uma mudanca futura nelas nao se
# esconde; as que nao existem mais saem dos dois lados.
NOME_CERTO_DESDE_A_AUDITORIA_3 = {
    "savestate_slot": "state_slot",
    "menu_rgui_color_theme": "rgui_menu_color_theme",
    "rgui_full_width_layout": "menu_rgui_full_width_layout",
    "content_show_add": "content_show_add_entry",
    "input_bsv_record_toggle": "input_record_replay",
    "netplay_port": "netplay_ip_port",
}
TIRADAS_NA_AUDITORIA_3 = {"quick_menu_show_cheevos", "notification_show_recording",
                          "notification_show_streaming", "netplay_stateless_mode",
                          "menu_show_legacy_thumbnail_updater"}
# Novas de proposito (o atalho de repetir/parar a gravacao da partida, sem tecla).
NOVAS_NA_AUDITORIA_3 = {"input_play_replay", "input_halt_replay"}
# Valor que mudou de proposito junto com o nome: o tema pedia o 27 e nunca
# valeu (fica o 4, o que os alunos sempre viram); "Importar conteudo" escondido
# era "false" no nome velho e e' "0" no novo.
VALOR_NOVO_DE_PROPOSITO = {("rgui_menu_color_theme", "27"): "4", ("content_show_add_entry", "false"): "0",
                           # Fase 5 da auditoria 3: o perfil Qualidade nao liga mais
                           # sozinho o voltar no tempo e a resposta instantanea (o N64
                           # caia para 30 quadros/s; o PS1 gastava 5x o processador).
                           ("rewind_enable", "true"): "false", ("run_ahead_enabled", "true"): "false"}


def com_nomes_certos(chaves_override):
    """A versao de antes, falando a lingua de hoje (nomes certos e valores que
    mudaram de proposito, nada mais)."""
    traduzido = {}
    for chave, valor in chaves_override.items():
        if chave in TIRADAS_NA_AUDITORIA_3:
            continue
        chave = NOME_CERTO_DESDE_A_AUDITORIA_3.get(chave, chave)
        traduzido[chave] = VALOR_NOVO_DE_PROPOSITO.get((chave, valor), valor)
    return traduzido


def sem_mudanca_de_proposito(chaves_override):
    """Tira as mudancas que valem para TODO jogo, de proposito (teste
    com os controles na mao, 25/09/2026):
      - botao/eixo de controle nao definido pelo aluno vai "nul" (numero
        velho no retroarch.cfg punha o Start no R3);
      - input_remapping_directory aponta para o .rmp da partida (o RetroArch
        ignora o tipo de porta vindo do --appendconfig);
      - o teclado de todos os jogadores vai escrito (o teclado e' o primeiro
        jogador sem controle; pedido do Rafael, 25/09/2026), e as direcoes
        dele movem tambem o analogico esquerdo (pedido de 14/10/2026);
      - as chaves novas da auditoria 3 (NOVAS_NA_AUDITORIA_3); as renomeadas
        sao comparadas pelo nome certo (com_nomes_certos)."""
    teclado = r"^input_player\d+_(up|down|left|right|a|b|x|y|l|r|l2|r2|l3|r3|start|select|l_x_plus|l_x_minus|l_y_plus|l_y_minus)$"
    return {c: v for c, v in com_nomes_certos(chaves_override).items()
            if c != "input_remapping_directory"
            and c not in NOVAS_NA_AUDITORIA_3
            and not re.match(teclado, c)
            and not (v == "nul" and re.match(r"^input_player\d+_\w+_(btn|axis)$", c))}


def montar(destino, revisao):
    """revisao=None -> copia a pasta de trabalho de agora; senao, le do git."""
    if revisao:
        for caminho in arquivos_do_git(revisao, ["servidor", "launcher"]):
            alvo = os.path.join(destino, *caminho.split("/"))
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            conteudo = subprocess.run(["git", "show", "%s:%s" % (revisao, caminho)],
                                      cwd=RAIZ, capture_output=True, check=True).stdout
            open(alvo, "wb").write(conteudo)
    else:
        ignorar = shutil.ignore_patterns("python", "tests", "__pycache__")
        for pasta in ("servidor", "launcher"):
            shutil.copytree(os.path.join(RAIZ, pasta), os.path.join(destino, pasta), ignore=ignorar)

    os.makedirs(os.path.join(destino, "dados"))
    config = json.load(open(os.path.join(RAIZ, "dados", "config.json"), encoding="utf-8"))
    config["servidores"] = []           # nada de sincronizar pela rede no teste
    config["permitir_rede"] = False
    json.dump(config, open(os.path.join(destino, "dados", "config.json"), "w", encoding="utf-8"))

    ra = os.path.join(destino, "retroarch")
    os.makedirs(os.path.join(ra, "cores"))
    open(os.path.join(ra, "retroarch.exe"), "wb").close()
    shutil.copy2(os.path.join(RAIZ, "retroarch", "retroarch.cfg"), os.path.join(ra, "retroarch.cfg"))
    # O nome de cada nucleo (pasta do .rmp da partida) vem do .info.
    shutil.copytree(os.path.join(RAIZ, "retroarch", "info"), os.path.join(ra, "info"))
    for nome in os.listdir(os.path.join(RAIZ, "retroarch", "cores")):
        open(os.path.join(ra, "cores", nome), "wb").close()

    origem_jogos = os.path.join(RAIZ, "jogos", "pessoais")
    for pasta, _, arquivos in os.walk(origem_jogos):
        relativo = os.path.relpath(pasta, origem_jogos)
        for nome in arquivos:
            alvo = os.path.join(destino, "jogos", "pessoais", relativo, nome)
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            open(alvo, "wb").close()


# ---------------------------------------------------------------------------
# O que roda DENTRO de cada copia (processo separado: as duas versoes tem
# modulos com o mesmo nome)
# ---------------------------------------------------------------------------

def trabalhador(raiz, porta):
    sys.path.insert(0, os.path.join(raiz, "servidor"))
    import arena
    import graficos

    cfg_real = os.path.join(raiz, "retroarch", "retroarch.cfg")

    class RetroArchFalso:
        """Fecha na hora, e grava no retroarch.cfg o que veio no arquivo da
        partida -- como o RetroArch de verdade faz ao fechar."""
        def __init__(self, comando, **_):
            self.override = comando[comando.index("--appendconfig") + 1]

        def wait(self):
            novas = dict(re.findall(r'^(\S+) = "(.*)"$', open(self.override, encoding="utf-8").read(), re.M))
            linhas = [l for l in open(cfg_real, encoding="utf-8", errors="replace").read().splitlines()
                      if l.split("=", 1)[0].strip() not in novas]
            linhas += ['%s = "%s"' % item for item in sorted(novas.items())]
            open(cfg_real, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
            return 0

    arena.subprocess.Popen = RetroArchFalso
    arena.fazer_backup = lambda *a, **k: None
    arena.servidor_alcancavel = lambda *a, **k: False
    arena.limpar_logs_antigos = lambda *a, **k: None
    arena.VIGIA["online"] = False
    # Quem entra avisa o ARENA do anfitriao (14/10/2026); no teste nao ha
    # anfitriao de verdade, e nada pode bater num ARENA real da porta 8777.
    if hasattr(arena, "chegar_na_partida"):
        arena.chegar_na_partida = lambda *a, **k: False
    # O resultado nao pode depender de quantos controles estao plugados
    # nesta maquina na hora do teste (o teclado muda de jogador com isso).
    if hasattr(arena.controles, "contar_controles"):
        arena.controles.contar_controles = lambda: 0

    servidor = arena.Servidor(("127.0.0.1", porta), arena.Manipulador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    def pedir(caminho, corpo=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=dados,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    _, catalogo = pedir("/api/catalogo")
    jogos = catalogo.get("jogos", catalogo if isinstance(catalogo, list) else [])
    resultado = {}
    for jogo in sorted(jogos, key=lambda j: j["id"]):
        for modo in MODOS:
            corpo = {"jogo_id": jogo["id"], "id": jogo["id"]}
            if modo != "sozinho":
                corpo.update({"partida": modo, "endereco": "127.0.0.1", "jogador": 5})
            if os.path.exists(arena.ARQUIVO_OVERRIDE):
                os.remove(arena.ARQUIVO_OVERRIDE)
            cfg_antes = graficos_valores(cfg_real)
            status, resposta = pedir("/api/jogar", corpo)
            for _ in range(200):
                if not arena.JOGO_EM_ANDAMENTO["ativo"]:
                    break
                time.sleep(0.05)
            texto = open(arena.ARQUIVO_OVERRIDE, encoding="utf-8").read() if os.path.exists(arena.ARQUIVO_OVERRIDE) else ""
            texto = texto.replace(raiz, "<RAIZ>")
            nucleo = dict(re.findall(r'^core_options_path = "(.*)"$', texto, re.M) and
                          [("caminho", re.search(r'^core_options_path = "(.*)"$', texto, re.M).group(1))] or [])
            copia = os.path.join(raiz, "dados", "opcoes_nucleo_partida.cfg")
            extras_nucleo = {}
            if "opcoes_nucleo_partida" in nucleo.get("caminho", "") and os.path.exists(copia):
                extras_nucleo = dict(re.findall(r'^(\S*multitap\S*) = "(.*)"$', open(copia, encoding="utf-8").read(), re.M | re.I))
            resultado["%s | %s" % (jogo["titulo"], modo)] = {
                "plataforma": jogo["plataforma"], "status": status,
                "jogadores_max": jogo.get("jogadores_max"),
                "override": texto, "nucleo_multitap": extras_nucleo,
                "cfg_antes": cfg_antes, "cfg_depois": graficos_valores(cfg_real)}
    servidor.shutdown()
    print(json.dumps(resultado, ensure_ascii=False))


def graficos_valores(cfg):
    valores = dict.fromkeys(CHAVES_PORTAS)
    for linha in open(cfg, encoding="utf-8", errors="replace"):
        chave, _, valor = linha.partition("=")
        if chave.strip() in valores:
            valores[chave.strip()] = valor.strip().strip('"')
    return valores


# ---------------------------------------------------------------------------
# Comparacao
# ---------------------------------------------------------------------------

def chaves(texto):
    return dict(re.findall(r'^(\S+) = "(.*)"$', texto, re.M))


def principal():
    antes_dir = tempfile.mkdtemp(prefix="arena_regra_antes_")
    agora_dir = tempfile.mkdtemp(prefix="arena_regra_agora_")
    try:
        montar(antes_dir, REVISAO_ANTES)
        montar(agora_dir, None)
        saidas = {}
        for nome, pasta, porta in (("antes", antes_dir, 18791), ("agora", agora_dir, 18792)):
            r = subprocess.run([PYTHON, os.path.abspath(__file__), "--trabalhador", pasta, str(porta)],
                               capture_output=True, timeout=900)
            linhas = r.stdout.decode("utf-8", "replace").strip().splitlines()
            try:
                saidas[nome] = json.loads(linhas[-1])
            except (IndexError, ValueError):
                print("FALHOU: a copia '%s' nao respondeu.\n%s" % (
                    nome, (r.stdout + r.stderr).decode("utf-8", "replace")[-3000:]))
                return 1

        antes, agora = saidas["antes"], saidas["agora"]
        falhas, iguais, com_adaptador = [], 0, []
        for caso in sorted(agora):
            a, b = antes.get(caso), agora[caso]
            if a is None:
                # Titulo que mudou DE PROPOSITO depois da versao de antes
                # (25/09/2026: "disc.gdi" passou a ter o nome da pasta, "Disc"
                # -> "Capcom Vs SNK 2..."). Sem par, nao da para comparar.
                if caso.split(" | ")[0] in TITULOS_NOVOS_DE_PROPOSITO:
                    continue
                falhas.append("%s: nao existe na versao de antes" % caso)
                continue
            mais_de_dois = (b["jogadores_max"] or 2) > 2 and b["status"] == 200
            titulo, _, modo = caso.partition(" | ")
            if (b["status"] == 409 and modo in ("hospedar", "entrar")
                    and titulo in JOGAR_JUNTO_RECUSADO_DE_PROPOSITO):
                continue
            if a["status"] != 200 and b["status"] in (200, 409):
                # O jogo que antes nem abria e agora abre nao e' mudanca para
                # pior: a regra de ouro e' nao estragar o que ja funcionava. O
                # Java ME (16/10/2026): antes sem nucleo, o ARENA respondia 400;
                # desde 15/10 abre pelo FreeJ2ME-Plus (fc788dd).
                continue
            if not mais_de_dois:
                ca, cb =sem_mudanca_de_proposito(chaves(a["override"])), sem_mudanca_de_proposito(chaves(b["override"]))
                if (cb.get("system_directory", "").endswith("\\OpenBIOS")
                        and ca.get("system_directory", "").endswith("\\system")):
                    # O PS1 sem a BIOS da Sony (as copias deste teste vem do git,
                    # sem BIOS de empresa): desde 15/10/2026 liga pela OpenBIOS, a
                    # livre, numa pasta so dela (f50cdac).
                    ca.pop("system_directory")
                    cb.pop("system_directory")
                if a["status"] != b["status"] or ca != cb:
                    dif = sorted(set(ca.items()) ^ set(cb.items()))
                    falhas.append("%s: MUDOU (status %s -> %s) %s" % (caso, a["status"], b["status"], dif[:6]))
                else:
                    iguais += 1
                continue
            com_adaptador.append((caso, b))

        print("Jogos de 1 ou 2 jogadores: %d casos com o arquivo da partida IGUAL ao de antes." % iguais)
        for caso, b in com_adaptador:
            k = chaves(b["override"])
            # Portas 1 e 2 e input_max_users sao reescritos em TODA partida
            # (opcoes de controle), desde sempre: mudar ali nao e' vazamento.
            # Vazamento e' o que so a partida de 3+ escreve: portas 3 a 5.
            vazou = {c: (b["cfg_antes"][c], b["cfg_depois"][c]) for c in CHAVES_PORTAS[2:5]
                     if b["cfg_antes"][c] != b["cfg_depois"][c]}
            print("  %-55s p2=%s max_users=%s conexoes=%s nucleo=%s vazou=%s" % (
                caso[:55], k.get("input_libretro_device_p2"), k.get("input_max_users"),
                k.get("netplay_max_connections", "-"), b["nucleo_multitap"] or "-", vazou or "nada"))
            if vazou:
                falhas.append("%s: vazou para o retroarch.cfg %s" % (caso, vazou))
            if "Bomberman 4" in caso:
                if k.get("input_libretro_device_p2") != "257" or k.get("input_max_users") != "5":
                    falhas.append("%s: adaptador/controles nao chegaram" % caso)
                if not caso.endswith("sozinho") and k.get("netplay_max_connections") != "4":
                    falhas.append("%s: limite de conexoes nao subiu para 4" % caso)
        print("\n%s" % ("\n".join("FALHA: " + f for f in falhas) if falhas else "Nenhuma diferenca fora do esperado."))
        print("RESULTADO:", "PASSOU" if not falhas else "FALHOU")
        return 1 if falhas else 0
    finally:
        shutil.rmtree(antes_dir, ignore_errors=True)
        shutil.rmtree(agora_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--trabalhador":
        trabalhador(sys.argv[2], int(sys.argv[3]))
    else:
        sys.exit(principal())
