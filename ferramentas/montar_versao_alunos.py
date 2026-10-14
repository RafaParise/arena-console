# -*- coding: utf-8 -*-
r"""Monta a VERSAO DOS ALUNOS do ARENA: limpa, enxuta, so o que faz o ARENA
funcionar. Pedido do Rafael (01/10/2026).

Sai em <pasta do projeto>\ARENA-alunos (ao lado de ARENA-unificado). E' so
copiar essa pasta para o pen drive (exFAT) ou para o computador.

O QUE ENTRA (lista fechada -- o que nao esta aqui, nao vai):
  - os .bat de usar (ARENA, VERIFICAR, PARTIDA), os guias (LEIA-ME, 1 a 6)
    e o COLETAR.bat (o professor mede o notebook da escola com a propria
    versao dos alunos: ferramentas\coletar_maquina.py e medir_arena.py);
  - a licenca (LICENSE, GPL-3.0) e o TERCEIROS.md (a licenca e o
    codigo-fonte de cada programa de outros projetos que vai no pacote);
  - servidor\ (o ARENA e o Python embutido), sem testes;
  - launcher\ (a tela);
  - RetroArch: o programa, so os 48 nucleos que o ARENA usa (de 195), os
    perfis de controle, o menu rgui, os filtros de tela, os bancos de
    nomes de fliperama (FBNeo e MAME);
  - PCSX2, Dolphin, RPCS3 e Xenia: so o programa e a configuracao que o
    ARENA completa a cada jogo (sem os dados de quem usou);
  - pastas vazias com o LEIA.txt de cada uma (jogos, saves, estados...).

O QUE NAO ENTRA, e por que:
  - jogos, saves, estados, capas baixadas, cartoes de memoria, perfil,
    recordes, amigos, configuracao, registros: sao de quem usou;
  - BIOS dos consoles e firmware do PS3: sao da Sony/Sega/SNK. Quem decide
    se vai junto e' o professor (opcao --com-bios); sem elas o ARENA abre e
    avisa o que falta;
  - caches (Xenia 1,4 GB, RPCS3 1,7 GB, PS1 153 MB), jogos instalados do
    PS3 (5,8 GB), copias velhas (rpcs3_old), simbolos de depuracao,
    atualizadores, ferramentas de teste e relatorios de desenvolvimento;
  - a conta RPCN (rpcn.yml), sempre: e' dado pessoal.

Depois de montar, a versao e' testada numa COPIA temporaria: o servidor
dela abre, a lista de jogos sai (vazia), nenhum arquivo do teste fica na
versao, e nenhum caminho da maquina do professor sobra nela.

Uso:
    servidor\python\python.exe ferramentas\montar_versao_alunos.py [--com-bios] [--destino PASTA]
    servidor\python\python.exe ferramentas\montar_versao_alunos.py --atualizar [--destino PASTA]
    servidor\python\python.exe ferramentas\montar_versao_alunos.py --zip-atualizacao ARQUIVO.zip
(o ultimo monta o pacote de atualizacao do Release: so o programa, o mesmo
conjunto que o --atualizar troca.)

TRAVA (02/10/2026): montar APAGA a pasta de destino e faz de novo. Se ela ja
foi usada (jogos, dados, saves, recordes...), a montagem recusa -- o Rafael
estava jogando na ARENA-alunos, com 3,7 GB de jogos dele, quando a versao
precisou de conserto. Para esse caso existe o --atualizar: troca SO o
programa do ARENA (servidor, tela, guias, .bat e as ferramentas do COLETAR) e
nao encosta em jogos, dados, saves, estados, capas, cartoes de memoria nem
nos emuladores. Confere antes e depois que nada de quem usou mudou.
"""
import filecmp
import fnmatch
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJETO = os.path.dirname(RAIZ)
NOME_DESTINO = "ARENA-alunos"

ARQUIVOS_DA_RAIZ = ["ARENA.bat", "VERIFICAR.bat", "PARTIDA.bat", "COLETAR.bat", "LEIA-ME.md", "1-COMECAR.md",
                    "2-JOGOS.md", "3-IMAGEM-SOM-CONTROLE.md", "4-SAVES.md", "5-AMIGOS.md",
                    "6-RECURSOS-E-REPARO.md",
                    # A licenca do ARENA (GPL-3.0) e a de cada programa de
                    # outros projetos que vai junto, com o codigo-fonte: a GPL
                    # pede o texto da licenca junto do programa distribuido
                    # (Fase 8 da auditoria 3, o pacote do GitHub).
                    "LICENSE", "TERCEIROS.md"]
# Do ferramentas\, so o que o COLETAR.bat usa.
FERRAMENTAS = ["coletar_maquina.py", "medir_arena.py"]
# Jogo pequeno do proprio projeto para conferir que o RetroArch da versao
# abre e desenha (usado so na copia temporaria da conferencia).
JOGO_DE_PROVA = (os.path.join("jogos", "pessoais", "NES", "Contra (USA).nes"), "fceumm")
# Com BIOS: um jogo de PS1, que so liga com a BIOS (a da versao).
JOGO_PS1 = (os.path.join("jogos", "pessoais", "PS1", "Crash Bandicoot (USA).chd"), "swanstation")
LIXO_SEMPRE = ["__pycache__", "*.pyc", "*.pyo", "*.log", "*.tmp", "Thumbs.db", "desktop.ini", "*.bak",
               "*.antes-*", "*.antes_*"]

# Onde mora o que e' de quem USOU a versao (a montagem so poe LEIA.txt e,
# com --com-bios, o neogeo.zip). Achou outra coisa: a versao esta em uso.
PASTAS_DE_QUEM_USOU = ["dados", "jogos", "backup",
                       # A pasta BIOS (03/10/2026): o ARENA cria ao abrir, e o
                       # que vai dentro sao as BIOS de quem usa.
                       "BIOS",
                       os.path.join("retroarch", "saves"), os.path.join("retroarch", "states"),
                       os.path.join("retroarch", "screenshots"), os.path.join("retroarch", "thumbnails"),
                       os.path.join("retroarch", "remaps"),
                       # Correcoes de jogo de fliperama (o som do KOF 2002 convertido,
                       # 03/10/2026): parte de um jogo de quem usou.
                       os.path.join("retroarch", "system", "fbneo", "patched"),
                       os.path.join("emuladores", "PCSX2", "PCSX2", "memcards"),
                       os.path.join("emuladores", "PCSX2", "PCSX2", "sstates"),
                       os.path.join("emuladores", "Dolphin", "Dolphin-x64", "User"),
                       os.path.join("emuladores", "RPCS3", "RPCS3", "dev_hdd0"),
                       os.path.join("emuladores", "Xenia", "Xenia", "content")]

# BIOS que o ARENA conhece (retroarch\system): o resto da pasta e' apoio.
PADROES_BIOS = ["*.bin", "*.BIN", "*.rom", "*.ROM*", "*.MEC", "*.NVM", "*.EROM", "neogeo*.zip", "*.sfx", "*.sp1",
                "*.sm1", "*.lo", "dc", "bios*", "*.chd"]


def ignorar(padroes):
    def regra(_pasta, nomes):
        return {n for n in nomes for p in padroes if fnmatch.fnmatch(n, p)}
    return regra


def copiar_arvore(origem, destino, extra=()):
    shutil.copytree(origem, destino, ignore=ignorar(LIXO_SEMPRE + list(extra)), dirs_exist_ok=True)


def copiar_arquivo(origem, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.copy2(origem, destino)


def copiar_leia(rel, destino_raiz):
    """O LEIA.txt de uma pasta (a pasta vai vazia, so com ele)."""
    origem = os.path.join(RAIZ, rel, "LEIA.txt")
    os.makedirs(os.path.join(destino_raiz, rel), exist_ok=True)
    if os.path.isfile(origem):
        copiar_arquivo(origem, os.path.join(destino_raiz, rel, "LEIA.txt"))


def coisas_de_quem_usou(destino):
    """Arquivos que a montagem NAO poe e que sao de quem usou a versao."""
    achados = []
    for rel in PASTAS_DE_QUEM_USOU:
        for atual, _sub, arquivos in os.walk(os.path.join(destino, rel)):
            for nome in arquivos:
                if nome == "LEIA.txt" or fnmatch.fnmatch(nome.lower(), "neogeo*.zip"):
                    continue
                achados.append(os.path.relpath(os.path.join(atual, nome), destino))
    return sorted(achados)


def retrato(destino, arquivos):
    """Nome -> (tamanho, data) de cada arquivo: para provar que nada mudou."""
    marcas = {}
    for rel in arquivos:
        try:
            info = os.stat(os.path.join(destino, rel))
            marcas[rel] = (info.st_size, info.st_mtime_ns)
        except OSError:
            marcas[rel] = None
    return marcas


def mudou(origem, alvo):
    """O arquivo do programa e' diferente do que esta na versao (ou falta)?"""
    return not os.path.isfile(alvo) or not filecmp.cmp(origem, alvo, shallow=False)


def espelhar(origem, destino, extra=()):
    """Deixa 'destino' igual a 'origem' (com as mesmas regras de lixo da
    montagem): copia o que mudou e tira o que nao existe mais no programa.
    So para pasta de PROGRAMA (servidor, launcher): nelas nao mora dado de
    quem usa. Devolve (copiados, tirados)."""
    padroes = LIXO_SEMPRE + list(extra)
    lixo = lambda nome: any(fnmatch.fnmatch(nome, p) for p in padroes)  # noqa: E731
    queridos, pastas, copiados, tirados = set(), set(), [], []
    for atual, subpastas, arquivos in os.walk(origem):
        subpastas[:] = [s for s in subpastas if not lixo(s)]
        pastas.add(os.path.normcase(os.path.relpath(atual, origem)))
        for nome in arquivos:
            if lixo(nome):
                continue
            rel = os.path.relpath(os.path.join(atual, nome), origem)
            queridos.add(os.path.normcase(rel))
            alvo = os.path.join(destino, rel)
            if mudou(os.path.join(atual, nome), alvo):
                copiar_arquivo(os.path.join(atual, nome), alvo)
                copiados.append(rel)
    for atual, subpastas, arquivos in os.walk(destino, topdown=False):
        for nome in arquivos:
            rel = os.path.relpath(os.path.join(atual, nome), destino)
            if os.path.normcase(rel) not in queridos:
                os.remove(os.path.join(atual, nome))
                tirados.append(rel)
        # Pasta vazia que o programa nao tem mais sai; a que ele tem, fica.
        if atual != destino and not os.listdir(atual) \
                and os.path.normcase(os.path.relpath(atual, destino)) not in pastas:
            os.rmdir(atual)
    return copiados, tirados


def atualizar(destino):
    """Troca so o programa do ARENA numa versao que ja esta em uso.
    Devolve (copiados, tirados, quantos arquivos de quem usou, problemas)."""
    de_quem_usou = coisas_de_quem_usou(destino)
    antes = retrato(destino, de_quem_usou)
    copiados, tirados = [], []
    for nome in ARQUIVOS_DA_RAIZ:
        origem, alvo = os.path.join(RAIZ, nome), os.path.join(destino, nome)
        if mudou(origem, alvo):
            copiar_arquivo(origem, alvo)
            copiados.append(nome)
    for pasta, extra in (("servidor", ["tests"]), ("launcher", [])):
        c, r = espelhar(os.path.join(RAIZ, pasta), os.path.join(destino, pasta), extra)
        copiados += [os.path.join(pasta, x) for x in c]
        tirados += [os.path.join(pasta, x) for x in r]
    for nome in FERRAMENTAS:
        origem, alvo = os.path.join(RAIZ, "ferramentas", nome), os.path.join(destino, "ferramentas", nome)
        if mudou(origem, alvo):
            copiar_arquivo(origem, alvo)
            copiados.append(os.path.join("ferramentas", nome))
    problemas = []
    depois = retrato(destino, de_quem_usou)
    if depois != antes or coisas_de_quem_usou(destino) != de_quem_usou:
        problemas.append("algo de quem usou mudou durante a atualizacao (nao devia)")
    return copiados, tirados, len(de_quem_usou), problemas


def prova_do_programa(destino):
    """O servidor da versao atualizada abre e diz a versao certa -- numa copia
    temporaria SO do programa (dados vazios): os dados de quem usa ficam
    intocados."""
    if not porta_livre():
        return ["nao deu para conferir: o ARENA de verdade esta aberto (porta 8777)"]
    copia = os.path.join(tempfile.mkdtemp(prefix="arena_atualizacao_"), "ARENA")
    for pasta in ("servidor", "launcher"):
        shutil.copytree(os.path.join(destino, pasta), os.path.join(copia, pasta))
    for nome in ARQUIVOS_DA_RAIZ:
        shutil.copy2(os.path.join(destino, nome), os.path.join(copia, nome))
    os.makedirs(os.path.join(copia, "dados"))
    servidor = subprocess.Popen([os.path.join(copia, "servidor", "python", "python.exe"),
                                 os.path.join(copia, "servidor", "arena.py")], cwd=copia,
                                env=dict(os.environ, ARENA_SEM_JANELA="1"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    problemas, estado = [], None
    try:
        for _ in range(300):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=2) as r:
                    estado = json.loads(r.read())
                break
            except OSError:
                time.sleep(0.2)
    finally:
        servidor.kill()
        servidor.wait()
        time.sleep(0.5)
    with open(os.path.join(RAIZ, "servidor", "arena.py"), encoding="utf-8") as arquivo:
        versao = re.search(r'^VERSAO = "([^"]+)"', arquivo.read(), re.M)
    if not estado:
        problemas.append("o servidor atualizado nao respondeu")
    elif versao and estado.get("versao") != versao.group(1):
        problemas.append("o servidor atualizado diz a versao %s (devia ser %s)"
                         % (estado.get("versao"), versao.group(1)))
    else:
        print("  servidor atualizado abriu: versao %s" % estado.get("versao"), flush=True)
    if not apagar_pasta(os.path.dirname(copia)):
        print("  (aviso: a copia temporaria nao saiu toda do Temp: %s)" % os.path.dirname(copia))
    return problemas


def tamanho(pasta):
    total = 0
    for atual, _sub, arquivos in os.walk(pasta):
        for n in arquivos:
            try:
                total += os.path.getsize(os.path.join(atual, n))
            except OSError:
                pass
    return total


# ---------------------------------------------------------------------------

def nucleos_usados():
    dados = json.load(open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8"))
    usados = set()
    for p in dados["plataformas"]:
        for chave in ("core", "core_netplay"):
            if p.get(chave):
                usados.add(p[chave].lower())
    return usados, [p["pasta"] for p in dados["plataformas"] if p.get("pasta")]


def limpar_retroarch_cfg(origem, destino):
    """Copia o retroarch.cfg sem nada de quem usou: apelido de rede,
    enderecos, senhas e o caminho da maquina do professor (o ARENA corrige
    os caminhos sozinho na primeira abertura -- corrigir_caminhos_retroarch_cfg)."""
    pessoais = {"netplay_nickname", "netplay_ip_address", "netplay_password", "netplay_spectate_password",
                "cheevos_username", "cheevos_password", "cheevos_token", "discord_app_id",
                "netplay_mitm_server_custom", "rgui_browser_directory", "last_start_directory"}
    raiz_barra = RAIZ.replace("/", "\\")
    saida, vistas = [], set()
    for linha in open(origem, encoding="utf-8", errors="replace"):
        chave = linha.split("=", 1)[0].strip()
        if "=" in linha and chave in vistas:
            continue          # chave repetida (o cache_directory chegou a 5): fica a primeira
        vistas.add(chave)
        if chave in pessoais:
            linha = '%s = ""\n' % chave
        elif raiz_barra.lower() in linha.lower():
            # O caminho de quem montou nao vai junto: vira um neutro, que o
            # ARENA troca pelo certo ao abrir (reconhece dados, retroarch...).
            linha = re.sub(re.escape(raiz_barra), lambda _m: r"C:\ARENA", linha, flags=re.I)
        saida.append(linha)
    with open(destino, "w", encoding="utf-8") as f:
        f.writelines(saida)


def limpar_pcsx2_ini(origem, destino):
    """PCSX2.ini sem a BIOS escolhida (com [Filenames] BIOS vazio, o PCSX2
    acha sozinho uma que sirva -- ver graficos.escrever_config_pcsx2)."""
    saida, bloco = [], ""
    for linha in open(origem, encoding="utf-8", errors="replace"):
        limpo = linha.strip()
        if limpo.startswith("[") and limpo.endswith("]"):
            bloco = limpo
        if bloco == "[Filenames]" and limpo.split("=", 1)[0].strip() == "BIOS":
            linha = "BIOS = \n"
        saida.append(linha)
    with open(destino, "w", encoding="utf-8") as f:
        f.writelines(saida)


def montar(destino, com_bios=False):
    """Monta a versao. Devolve o resumo (texto)."""
    if os.path.basename(os.path.normpath(destino)) != NOME_DESTINO:
        raise SystemExit("Por seguranca, o destino tem que se chamar %s." % NOME_DESTINO)
    if os.path.isdir(destino):
        de_quem_usou = coisas_de_quem_usou(destino)
        if de_quem_usou:
            raise SystemExit(
                "A pasta %s ja esta em uso: tem %d arquivo(s) de quem usou (jogos, dados, saves...),\n"
                "por exemplo %s. Montar de novo APAGARIA tudo isso. Nada foi mexido.\n"
                "  - Para so trocar o programa, mantendo tudo:  --atualizar\n"
                "  - Para montar do zero em outro lugar:        --destino <outra pasta>\\%s"
                % (destino, len(de_quem_usou), de_quem_usou[0], NOME_DESTINO))
        shutil.rmtree(destino)        # e' a saida desta ferramenta, sempre refeita
    os.makedirs(destino)
    usados, pastas_de_console = nucleos_usados()
    RA, RA_D = os.path.join(RAIZ, "retroarch"), os.path.join(destino, "retroarch")

    # 1. Raiz, servidor, tela.
    for nome in ARQUIVOS_DA_RAIZ:
        copiar_arquivo(os.path.join(RAIZ, nome), os.path.join(destino, nome))
    copiar_arvore(os.path.join(RAIZ, "servidor"), os.path.join(destino, "servidor"), extra=["tests"])
    copiar_arvore(os.path.join(RAIZ, "launcher"), os.path.join(destino, "launcher"))
    for nome in FERRAMENTAS:
        copiar_arquivo(os.path.join(RAIZ, "ferramentas", nome), os.path.join(destino, "ferramentas", nome))

    # 2. Pastas do aluno: vazias, com o LEIA.txt.
    for rel in ("dados", os.path.join("jogos", "pessoais"), os.path.join("jogos", "turma"),
                os.path.join("jogos", "livres"), "backup"):
        copiar_leia(rel, destino)
    for pasta in sorted(set(pastas_de_console)):
        os.makedirs(os.path.join(destino, "jogos", "pessoais", pasta), exist_ok=True)

    # 3. RetroArch.
    os.makedirs(RA_D)
    for nome in os.listdir(RA):
        caminho = os.path.join(RA, nome)
        if not os.path.isfile(caminho):
            continue
        minusculo = nome.lower()
        if minusculo.endswith(".dll") or minusculo in ("retroarch.exe", "qt.conf", "retroarch.default.cfg"):
            copiar_arquivo(caminho, os.path.join(RA_D, nome))
    limpar_retroarch_cfg(os.path.join(RA, "retroarch.cfg"), os.path.join(RA_D, "retroarch.cfg"))
    os.makedirs(os.path.join(RA_D, "cores"))
    os.makedirs(os.path.join(RA_D, "info"), exist_ok=True)
    for nome in os.listdir(os.path.join(RA, "cores")):
        if nome.lower() in usados:
            copiar_arquivo(os.path.join(RA, "cores", nome), os.path.join(RA_D, "cores", nome))
            info = os.path.join(RA, "info", nome[:-4] + ".info")
            if os.path.isfile(info):
                copiar_arquivo(info, os.path.join(RA_D, "info", os.path.basename(info)))
    copiar_leia(os.path.join("retroarch", "cores"), destino)
    for pasta in ("autoconfig", "platforms", os.path.join("shaders", "shaders_slang")):
        if os.path.isdir(os.path.join(RA, pasta)):
            copiar_arvore(os.path.join(RA, pasta), os.path.join(RA_D, pasta))
    for pasta in ("rgui", "pkg", "sounds"):               # menu rgui: o resto e' de outros menus
        if os.path.isdir(os.path.join(RA, "assets", pasta)):
            copiar_arvore(os.path.join(RA, "assets", pasta), os.path.join(RA_D, "assets", pasta))
    for rdb in ("FBNeo - Arcade Games.rdb", "MAME.rdb"):  # nomes de fliperama (nomes_arcade.py)
        origem = os.path.join(RA, "database", "rdb", rdb)
        if os.path.isfile(origem):
            copiar_arquivo(origem, os.path.join(RA_D, "database", "rdb", rdb))
    for rel in ("system", "saves", "states", "screenshots", "cheats", "remaps", "controles", "cache"):
        copiar_leia(os.path.join("retroarch", rel), destino)
    levadas = []          # o que foi de BIOS, para a folha de rosto
    if com_bios:
        # So os arquivos soltos de retroarch\system: as subpastas sao cache
        # (swanstation\vulkan_pipelines.bin, 171 MB), configuracao que o
        # nucleo cria (config\fbneo64.ini) ou SAVE (dc\vmu_save_*.bin).
        sistema = os.path.join(RA, "system")
        tem_neogeo = os.path.isfile(os.path.join(sistema, "neogeo.zip"))
        for nome in os.listdir(sistema):
            caminho = os.path.join(sistema, nome)
            if os.path.isfile(caminho) and any(fnmatch.fnmatch(nome, p) for p in PADROES_BIOS):
                # Copia da BIOS do Neo Geo com outro nome (neogeo.mame.zip): o
                # FBNeo usa o neogeo.zip daqui e o MAME nem procura nesta pasta.
                if tem_neogeo and nome.lower() != "neogeo.zip" and fnmatch.fnmatch(nome.lower(), "neogeo*.zip"):
                    continue
                copiar_arquivo(caminho, os.path.join(RA_D, "system", nome))
                levadas.append(nome)
        # Dreamcast: so a BIOS de dentro de system\dc (nunca os cartoes VMU).
        for nome in ("dc_boot.bin", "dc_flash.bin"):
            caminho = os.path.join(sistema, "dc", nome)
            if os.path.isfile(caminho):
                copiar_arquivo(caminho, os.path.join(RA_D, "system", "dc", nome))
                levadas.append(nome)
        # As do catalogo de BIOS (servidor\bios_catalogo.py) que os padroes
        # acima nao pegam: syscard3.pce, kick34005.A500, Mupen64plus\IPL.n64,
        # same_cdi\bios\cdimono1.zip, as pastas Machines e Databases do MSX.
        # A pasta BIOS (as prateleiras) o proprio ARENA monta ao abrir.
        if os.path.join(RAIZ, "servidor") not in sys.path:
            sys.path.insert(0, os.path.join(RAIZ, "servidor"))
        import bios_catalogo
        for entrada in bios_catalogo.CATALOGO:
            relativo = entrada.get("destino")
            if not relativo:
                continue
            origem = os.path.join(sistema, *relativo.split("/"))
            alvo = os.path.join(RA_D, "system", *relativo.split("/"))
            if os.path.exists(alvo):
                continue
            if os.path.isfile(origem):
                copiar_arquivo(origem, alvo)
                levadas.append(os.path.basename(relativo))
            elif os.path.isdir(origem) and entrada.get("e_pasta"):
                copiar_arvore(origem, alvo)
                levadas.append(relativo)
        # BIOS de fliperama que mora na pasta dos jogos (neogeo.zip ao lado
        # dos jogos do Neo Geo): a lista de jogos nao mostra.
        pessoais = os.path.join(RAIZ, "jogos", "pessoais")
        # Vai SEMPRE como neogeo.zip, o unico nome que o emulador procura (o
        # neogeo.mame.zip da pasta Arcade ia com esse nome e o MAME nao achava:
        # "000-lo.lo NOT FOUND", provado em 02/10/2026).
        for pasta in sorted(set(pastas_de_console)):
            origem = os.path.join(pessoais, pasta)
            nomes = sorted(os.listdir(origem)) if os.path.isdir(origem) else []
            bios = [n for n in nomes if fnmatch.fnmatch(n.lower(), "neogeo*.zip")]
            certa = next((n for n in bios if n.lower() == "neogeo.zip"), bios[0] if bios else None)
            if certa:
                copiar_arquivo(os.path.join(origem, certa),
                               os.path.join(destino, "jogos", "pessoais", pasta, "neogeo.zip"))
                levadas.append("%s\\neogeo.zip%s" % (pasta, "" if certa.lower() == "neogeo.zip"
                                                        else " (era %s)" % certa))

    # 4. Emuladores de fora: so o programa e a configuracao que o ARENA completa.
    E, E_D = os.path.join(RAIZ, "emuladores"), os.path.join(destino, "emuladores")
    copiar_leia("emuladores", destino)
    for emu in ("PCSX2", "Dolphin", "RPCS3", "Xenia"):
        copiar_leia(os.path.join("emuladores", emu), destino)

    def programa(pasta_rel, arquivos, pastas, fora=()):
        origem, alvo = os.path.join(E, pasta_rel), os.path.join(E_D, pasta_rel)
        if not os.path.isdir(origem):
            return
        os.makedirs(alvo, exist_ok=True)
        for nome in os.listdir(origem):
            caminho = os.path.join(origem, nome)
            if os.path.isfile(caminho) and any(fnmatch.fnmatch(nome.lower(), p.lower()) for p in arquivos) \
                    and not any(fnmatch.fnmatch(nome.lower(), p.lower()) for p in fora):
                copiar_arquivo(caminho, os.path.join(alvo, nome))
        for pasta in pastas:
            if os.path.isdir(os.path.join(origem, pasta)):
                copiar_arvore(os.path.join(origem, pasta), os.path.join(alvo, pasta))

    programa(os.path.join("PCSX2", "PCSX2"), ["*.exe", "*.dll", "qt.conf", "portable.txt"],
             ["D3D12", "QtPlugins", "resources", "translations", "docs"], fora=["updater.exe"])
    bios_ps2 = os.path.join(E, "PCSX2", "PCSX2", "bios")
    if com_bios and os.path.isdir(bios_ps2):
        copiar_arvore(bios_ps2, os.path.join(E_D, "PCSX2", "PCSX2", "bios"))
        levadas.append("PCSX2\\bios")
    ini = os.path.join(E, "PCSX2", "PCSX2", "inis", "PCSX2.ini")
    if os.path.isfile(ini):
        os.makedirs(os.path.join(E_D, "PCSX2", "PCSX2", "inis"), exist_ok=True)
        limpar_pcsx2_ini(ini, os.path.join(E_D, "PCSX2", "PCSX2", "inis", "PCSX2.ini"))
    programa(os.path.join("Dolphin", "Dolphin-x64"), ["Dolphin.exe", "*.dll", "qt.conf", "portable.txt",
                                                       "COPYING", "build_info.txt"],
             ["Sys", "QtPlugins", "Languages", "LICENSES"])
    programa(os.path.join("RPCS3", "RPCS3"), ["rpcs3.exe", "*.dll"], ["qt6", "Icons", "sounds", "fonts"])
    rpcs3 = os.path.join(E, "RPCS3", "RPCS3")
    if os.path.isdir(rpcs3):
        guis = os.path.join(rpcs3, "GuiConfigs")
        for nome in (os.listdir(guis) if os.path.isdir(guis) else []):
            if nome.lower().endswith(".qss"):                     # temas da tela (o .ini e' de quem usou)
                copiar_arquivo(os.path.join(guis, nome), os.path.join(E_D, "RPCS3", "RPCS3", "GuiConfigs", nome))
        cfg = os.path.join(rpcs3, "config", "config.yml")        # o ARENA completa este arquivo
        if os.path.isfile(cfg):
            copiar_arquivo(cfg, os.path.join(E_D, "RPCS3", "RPCS3", "config", "config.yml"))
        os.makedirs(os.path.join(E_D, "RPCS3", "RPCS3", "config", "input_configs", "global"), exist_ok=True)
        if com_bios and os.path.isdir(os.path.join(rpcs3, "dev_flash")):
            copiar_arvore(os.path.join(rpcs3, "dev_flash"), os.path.join(E_D, "RPCS3", "RPCS3", "dev_flash"))
            levadas.append("firmware do PS3")
    programa(os.path.join("Xenia", "Xenia"), ["xenia_canary.exe", "xenia_canary_netplay.exe", "LICENSE",
                                               "xenia-canary.config.toml", "xenia-canary-netplay.config.toml",
                                               "portable.txt"], [])
    # O Xenia Canary de hoje ja guarda tudo na propria pasta, mas a regra
    # escrita nele e' "portable.txt ao lado do .exe"; com ele, nenhuma versao
    # do Xenia grava em Documentos.
    xenia = os.path.join(E_D, "Xenia", "Xenia")
    if os.path.isdir(xenia) and not os.path.exists(os.path.join(xenia, "portable.txt")):
        with open(os.path.join(xenia, "portable.txt"), "w", encoding="utf-8") as f:
            f.write("Criado pelo ARENA: guarda tudo do Xenia nesta pasta.\n")

    # 5. Uma folha de rosto (UTF-8 com marca: o Bloco de Notas antigo
    # tambem mostra os acentos).
    with open(os.path.join(destino, "LEIA-PRIMEIRO.txt"), "w", encoding="utf-8-sig") as f:
        f.write(FOLHA_DE_ROSTO.format(bios=frase_das_bios(levadas) if com_bios else BIOS_FORA))
    return usados


BIOS_FORA = ("Esta versão NÃO vem com BIOS nem firmware das empresas (são da Sony, da Sega, da SNK...). "
             "Vêm só as BIOS livres, escritas por voluntários (servidor\\bios_livres: o C-BIOS do MSX).")


def frase_das_bios(levadas):
    """Quais consoles ja vem prontos, pelo que foi copiado de BIOS."""
    texto = " ".join(levadas).lower()
    consoles = []
    if "scph1001" in texto or "scph5501" in texto or "scph7001" in texto:
        consoles.append("PlayStation")
    if "pcsx2" in texto or "ps2" in texto or "scph-70004" in texto or "scph39001" in texto:
        consoles.append("PlayStation 2")
    if "firmware do ps3" in texto:
        consoles.append("PlayStation 3 (firmware já instalado)")
    if "neogeo" in texto:
        consoles.append("Neo Geo")
    if "bios_cd_" in texto:
        consoles.append("Sega CD")
    if "mpr-17933" in texto or "sega_101" in texto:
        consoles.append("Sega Saturn")
    if "dc_boot" in texto:
        consoles.append("Dreamcast")
    if "bs-x" in texto:
        consoles.append("Satellaview (os jogos \"BS\" do Super Nintendo)")
    if not consoles:
        return "Esta versão já vem com as BIOS que o professor tinha."
    return "Esta versão já vem com as BIOS de: %s." % ", ".join(consoles)
FOLHA_DE_ROSTO = """ARENA — versão para os alunos
=============================

1. Copie esta pasta inteira para o pen drive (formatado em exFAT) ou para o
   computador. Pode renomear a pasta para ARENA.
2. Abra o ARENA.bat. Na primeira vez, o Windows pode perguntar se deixa o
   Python usar a rede: só precisa para jogar com os colegas.
3. Coloque seus jogos em jogos\\pessoais\\<console> (as pastas já estão lá).
   O guia 2-JOGOS.md explica cada console.

{bios}
Console que ainda pedir BIOS mostra no cartão o que falta. Na primeira vez
que o ARENA abre, ele cria a pasta BIOS, uma pasta por console: ponha a BIOS
na pasta do console (com qualquer nome, ou o .zip em que ela veio) e clique
em Conferir, em Ajustes → Emuladores. O arquivo "LEIA - O QUE FALTA.txt" de
lá diz quantas e quais faltam (guia 2-JOGOS.md, "A BIOS").
PS3: o firmware vai pelo próprio RPCS3 (File > Install Firmware).

Não vem nada de quem preparou: nem jogos, nem saves, nem recordes, nem
amigos, nem configuração. Cada aluno começa do zero.

Problema? O VERIFICAR.bat confere e conserta. Dúvida? LEIA-ME.md.
"""


# ---------------------------------------------------------------------------
# Conferencia: a versao montada abre de verdade (numa copia temporaria)
# ---------------------------------------------------------------------------

def porta_livre(porta=8777):
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", porta)) != 0
    finally:
        s.close()


def marcas_de_quem_montou():
    """O que identifica quem monta, descoberto NA HORA (o nome de ninguem
    fica escrito neste arquivo, que e' publico no GitHub): o e-mail do git
    (a parte antes do @; no e-mail privado do GitHub, o nome depois do +) e
    o apelido do ARENA de quem monta (dados\\config.json)."""
    marcas = set()
    try:
        email = subprocess.run(["git", "-C", RAIZ, "config", "user.email"], capture_output=True,
                               text=True, timeout=10).stdout.strip().lower()
    except (OSError, subprocess.SubprocessError):
        email = ""
    nome = email.split("@", 1)[0]
    marcas.add(nome.split("+", 1)[-1])
    try:
        with open(os.path.join(RAIZ, "dados", "config.json"), encoding="utf-8") as arquivo:
            marcas.add(str(json.load(arquivo).get("apelido") or "").strip().lower())
    except (OSError, ValueError, AttributeError):
        pass
    # Curto demais pegaria palavra comum ("ana", "rafa"): so nome com 6 letras ou mais.
    return sorted(m for m in marcas if len(m) >= 6)


# O endereco publico do repositorio do ARENA leva o nome da conta do GitHub,
# que pode ser igual ao apelido de quem monta (em 12/10/2026, era): nos guias
# ele TEM que estar (e' de onde se baixa o ARENA). So ele sai do texto antes
# de procurar as marcas; o apelido em qualquer outro lugar continua barrado.
ENDERECO_DO_REPOSITORIO = re.compile(r"github\.com/[a-z0-9-]+/arena-console", re.I)


def texto_sem_enderecos_publicos(texto):
    return ENDERECO_DO_REPOSITORIO.sub("github.com/<repositorio>/arena-console", texto)


def conferir(destino, com_bios=False):
    problemas = []
    # Nada de caminho da maquina de quem montou, em arquivo de texto nenhum.
    alvo = RAIZ.lower().replace("/", "\\")
    # A pasta do usuario do Windows de quem montou (C:\Users\<nome>) tambem
    # nao pode aparecer: seria um caminho fora da pasta do ARENA.
    usuario = os.path.expanduser("~").lower().replace("/", "\\")
    marcas = [alvo, usuario + "\\"] + marcas_de_quem_montou()
    for atual, _sub, arquivos in os.walk(destino):
        if os.sep + "python" + os.sep in atual + os.sep:
            continue
        for n in arquivos:
            if n.lower().endswith((".cfg", ".ini", ".yml", ".toml", ".json", ".txt", ".md", ".bat", ".py")):
                texto = open(os.path.join(atual, n), encoding="utf-8", errors="replace").read().lower()
                texto = texto_sem_enderecos_publicos(texto)
                achado = next((m for m in marcas if m in texto), None)
                if achado:
                    problemas.append("dado de quem montou (%s) em %s" % (
                        "caminho" if "\\" in achado else "nome",
                        os.path.relpath(os.path.join(atual, n), destino)))
    for atual, _sub, arquivos in os.walk(os.path.join(destino, "jogos")):
        for n in arquivos:
            if fnmatch.fnmatch(n.lower(), "neogeo?*.zip"):
                problemas.append("BIOS do Neo Geo com nome que o emulador nao procura: %s"
                                 % os.path.relpath(os.path.join(atual, n), destino))
    for sobra in ("docs", "testes", "perfil", ".git", os.path.join("servidor", "tests")):
        if os.path.exists(os.path.join(destino, sobra)):
            problemas.append("pasta de desenvolvimento na versao: %s" % sobra)
    for proibido in ("rpcn.yml", "arena.db", "config.json", "controles.json", "manifesto.json", "jogadores.txt"):
        for atual, _sub, arquivos in os.walk(destino):
            if proibido in arquivos and not atual.endswith("servidor"):
                problemas.append("arquivo pessoal: %s" % os.path.relpath(os.path.join(atual, proibido), destino))
    # Abre numa copia temporaria (a versao fica intacta).
    if not porta_livre():
        problemas.append("nao deu para abrir: o ARENA de verdade esta aberto (porta 8777)")
        return problemas
    copia = os.path.join(tempfile.mkdtemp(prefix="arena_versao_alunos_"), "ARENA")
    shutil.copytree(destino, copia)
    servidor = subprocess.Popen([os.path.join(copia, "servidor", "python", "python.exe"),
                                 os.path.join(copia, "servidor", "arena.py")], cwd=copia,
                                env=dict(os.environ, ARENA_SEM_JANELA="1"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        estado = catalogo = None
        for _ in range(300):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8777/api/estado", timeout=2) as r:
                    estado = json.loads(r.read())
                with urllib.request.urlopen("http://127.0.0.1:8777/api/catalogo", timeout=10) as r:
                    catalogo = json.loads(r.read())
                break
            except OSError:
                time.sleep(0.2)
        if not estado:
            problemas.append("o servidor da versao nao respondeu")
        else:
            if catalogo.get("total", -1) != 0:
                problemas.append("a lista de jogos devia sair vazia (saiu %s)" % catalogo.get("total"))
            if not estado.get("retroarch_presente"):
                problemas.append("o ARENA da versao nao achou o RetroArch")
            plataformas = catalogo.get("plataformas", [])
            prontas = [p["id"] for p in plataformas if p.get("estado") == "pronta"]
            sem_nucleo = [p["id"] for p in plataformas if p.get("estado") == "sem_core"]
            print("  consoles prontos: %d de %d (os outros pedem BIOS ou programa de fora)"
                  % (len(prontas), len(plataformas)), flush=True)
            # So acusa o nucleo que existe aqui e nao foi junto (o do J2ME,
            # por exemplo, nao existe nem na pasta de desenvolvimento).
            dados = json.load(open(os.path.join(RAIZ, "servidor", "consoles.json"), encoding="utf-8"))
            core_de = {p["id"]: p.get("core") or "" for p in dados["plataformas"]}
            faltou = [i for i in sem_nucleo if core_de.get(i)
                      and os.path.isfile(os.path.join(RAIZ, "retroarch", "cores", core_de[i]))]
            if faltou:
                problemas.append("nucleo que existe aqui e nao foi para a versao: %s" % ", ".join(faltou))
            elif sem_nucleo:
                print("  (sem nucleo tambem aqui, nao e' falha da versao: %s)" % ", ".join(sem_nucleo))
            if len(prontas) < 30:
                problemas.append("so %d consoles prontos (faltou nucleo?)" % len(prontas))
            if com_bios:
                faltando = [p for p in ("ps1", "ps2", "ps3", "neogeo") if p not in prontas]
                if faltando:
                    problemas.append("com as BIOS, ainda nao ficaram prontos: %s" % ", ".join(faltando))
    finally:
        servidor.kill()
        servidor.wait()
        time.sleep(0.5)
    # O RetroArch DA VERSAO abre um jogo e desenha (o retroarch.cfg dela ja
    # foi corrigido para a pasta da copia pelo servidor, acima).
    problemas += prova_do_retroarch(copia, *JOGO_DE_PROVA)
    if com_bios:
        problemas += prova_do_retroarch(copia, *JOGO_PS1, quadros=900, nome="jogo de PS1", com_bios=True)
    if not apagar_pasta(os.path.dirname(copia)):
        print("  (aviso: a copia temporaria nao saiu toda do Temp: %s)" % os.path.dirname(copia))
    return problemas


def apagar_pasta(caminho):
    """rmtree que tambem apaga o que esta "somente leitura" (ver
    testes\\limpeza.py: com ignore_errors, sobrava a pasta no Temp)."""
    import stat

    def tirar_trava(funcao, alvo, _erro):
        try:
            os.chmod(alvo, stat.S_IWRITE)
            funcao(alvo)
        except OSError:
            pass
    shutil.rmtree(caminho, onexc=tirar_trava)
    return not os.path.exists(caminho)


def prova_do_retroarch(copia, relativo, nucleo, quadros=300, nome="jogo de prova", com_bios=False):
    """O RetroArch DA VERSAO abre um jogo daqui (sem copiar o jogo) e desenha.
    com_bios: o registro tem que mostrar a BIOS da versao sendo usada."""
    jogo = os.path.join(RAIZ, relativo)
    if not os.path.isfile(jogo):
        print("  (sem o %s %s: nao conferido)" % (nome, relativo))
        return []
    pasta = os.path.join(copia, "prova_" + nucleo)
    os.makedirs(pasta)
    foto, registro = os.path.join(pasta, "foto.png"), os.path.join(pasta, "ra.log")
    extra = os.path.join(pasta, "prova.cfg")
    with open(extra, "w", encoding="utf-8") as f:
        f.write('config_save_on_exit = "false"\naudio_enable = "false"\nvideo_fullscreen = "false"\n'
                'savefile_directory = "%s"\nsavestate_directory = "%s"\nscreenshot_directory = "%s"\n'
                % (pasta, pasta, pasta))
    retroarch = os.path.join(copia, "retroarch", "retroarch.exe")
    try:
        subprocess.run([retroarch, "-L", os.path.join(copia, "retroarch", "cores", nucleo + "_libretro.dll"),
                        "--appendconfig", extra, "--verbose", "--log-file", registro,
                        "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                       cwd=os.path.dirname(retroarch), timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return ["o RetroArch da versao travou abrindo o %s" % nome]
    texto = open(registro, encoding="utf-8", errors="replace").read() if os.path.isfile(registro) else ""
    idioma = "Carregando" in texto or "Redirecionando" in texto     # mensagens em portugues
    bios = os.path.join(copia, "retroarch", "system").lower() in texto.lower() and "bios" in texto.lower()
    tamanho_foto = os.path.getsize(foto) if os.path.isfile(foto) else 0
    print("  RetroArch da versao, %s: %s (foto de %d KB, em portugues: %s%s)"
          % (nome, "abriu e desenhou" if tamanho_foto > 2000 else "NAO desenhou", tamanho_foto // 1024,
             "sim" if idioma else "nao", (", BIOS da versao: %s" % ("sim" if bios else "NAO")) if com_bios else ""),
          flush=True)
    problemas = []
    if tamanho_foto <= 2000:
        problemas.append("o RetroArch da versao nao mostrou imagem do %s" % nome)
    if not idioma:
        problemas.append("o RetroArch da versao nao esta em portugues")
    if com_bios and not bios:
        problemas.append("o %s nao usou a BIOS da versao" % nome)
    return problemas


def parece_versao_dos_alunos(destino):
    """O --atualizar so mexe numa versao dos alunos: a pasta com o nome de
    sempre (ARENA-alunos) ou uma com a folha de rosto que o montador escreve
    (LEIA-PRIMEIRO.txt) -- em 10/10/2026 o Rafael passou a usar a versao dos
    alunos com o nome ARENA. Nunca esta pasta (a de desenvolvimento) nem
    pasta com .git (o repositorio)."""
    if not os.path.isdir(destino):
        return False
    if os.path.normcase(os.path.abspath(destino)) == os.path.normcase(os.path.abspath(RAIZ)):
        return False
    if os.path.exists(os.path.join(destino, ".git")):
        return False
    return (os.path.basename(os.path.normpath(destino)) == NOME_DESTINO
            or os.path.isfile(os.path.join(destino, "LEIA-PRIMEIRO.txt")))


def arquivos_do_programa():
    """(origem, caminho no pacote) de tudo o que o --atualizar troca: os
    arquivos da raiz, servidor\\ (com o Python embutido, sem os testes),
    launcher\\ e as ferramentas do COLETAR. Nada de jogos, dados, saves, BIOS,
    RetroArch nem emuladores."""
    lista = [(os.path.join(RAIZ, nome), nome) for nome in ARQUIVOS_DA_RAIZ]
    for pasta, extra in (("servidor", ["tests"]), ("launcher", [])):
        padroes = LIXO_SEMPRE + extra
        lixo = lambda nome: any(fnmatch.fnmatch(nome, p) for p in padroes)  # noqa: E731
        for atual, subpastas, nomes in os.walk(os.path.join(RAIZ, pasta)):
            subpastas[:] = sorted(s for s in subpastas if not lixo(s))
            for nome in sorted(nomes):
                if not lixo(nome):
                    origem = os.path.join(atual, nome)
                    lista.append((origem, os.path.relpath(origem, RAIZ)))
    lista += [(os.path.join(RAIZ, "ferramentas", nome), os.path.join("ferramentas", nome)) for nome in FERRAMENTAS]
    return lista


def zip_de_atualizacao(caminho_zip):
    """O pacote de ATUALIZACAO (Fase 8 da auditoria 3): so o programa, para
    copiar por cima de um ARENA em uso sem trocar a configuracao dos
    emuladores nem tocar em nada de quem usa (o guia 6 manda usar este, e
    nao o pacote completo, que traz o RetroArch e os emuladores ja
    configurados). Dentro do .zip tudo fica em ARENA\\, como no completo."""
    import zipfile
    temporario = caminho_zip + ".fazendo"
    with zipfile.ZipFile(temporario, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for origem, rel in arquivos_do_programa():
            z.write(origem, "ARENA/" + rel.replace("\\", "/"))
    os.replace(temporario, caminho_zip)
    with zipfile.ZipFile(caminho_zip) as z:
        if z.testzip() is not None:
            raise SystemExit("arquivo estragado no zip de atualizacao")
        return len(z.namelist())


def principal():
    com_bios = "--com-bios" in sys.argv
    destino = os.path.join(PROJETO, NOME_DESTINO)
    if "--destino" in sys.argv:
        destino = os.path.abspath(sys.argv[sys.argv.index("--destino") + 1])
    inicio = time.time()
    if "--zip-atualizacao" in sys.argv:
        caminho = os.path.abspath(sys.argv[sys.argv.index("--zip-atualizacao") + 1])
        quantos = zip_de_atualizacao(caminho)
        print("Pacote de atualizacao: %s (%d arquivos, %.1f MB)." % (caminho, quantos,
                                                                    os.path.getsize(caminho) / 1024 ** 2))
        return 0
    if "--atualizar" in sys.argv:
        if not parece_versao_dos_alunos(destino):
            print("Nao achei a versao dos alunos em %s (a pasta ARENA-alunos, ou uma com o "
                  "LEIA-PRIMEIRO.txt que o montador escreve)." % destino)
            return 1
        print("Atualizando so o programa da versao em %s (jogos, dados e saves ficam)..." % destino,
              flush=True)
        copiados, tirados, quantos, problemas = atualizar(destino)
        for rel in copiados:
            print("  trocado: %s" % rel)
        for rel in tirados:
            print("  tirado (nao existe mais no programa): %s" % rel)
        print("  %d arquivo(s) de quem usou: intocados" % quantos, flush=True)
        problemas += prova_do_programa(destino)
        if problemas:
            print("PROBLEMAS:")
            for p in problemas:
                print("  - " + p)
            return 1
        print("Atualizada em %.0f s: %d trocado(s), %d tirado(s)." % (time.time() - inicio, len(copiados),
                                                                     len(tirados)))
        return 0
    print("Montando a versao dos alunos em %s%s..." % (destino, " (com BIOS)" if com_bios else ""), flush=True)
    usados = montar(destino, com_bios)
    print("Conferindo (abre a versao numa copia temporaria)...", flush=True)
    problemas = conferir(destino, com_bios)
    total = tamanho(destino)
    print()
    print("Versao dos alunos: %.2f GB, %d nucleos, em %.0f s." % (total / 1024 ** 3, len(usados), time.time() - inicio))
    print("  (a pasta de desenvolvimento, sem jogos, tem %.2f GB)" % (
        (tamanho(os.path.join(RAIZ, "retroarch")) + tamanho(os.path.join(RAIZ, "emuladores"))
         + tamanho(os.path.join(RAIZ, "servidor"))) / 1024 ** 3))
    if problemas:
        print("PROBLEMAS:")
        for p in problemas:
            print("  - " + p)
        return 1
    print("Conferencia: abriu, lista vazia, RetroArch achado, nada de quem montou. Pronto para copiar.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
