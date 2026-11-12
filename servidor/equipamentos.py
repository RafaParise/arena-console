# -*- coding: utf-8 -*-
r"""Equipamentos do ARENA: tudo o que o ARENA tem, o que falta e o botao que resolve (13/11/2026).

Pedido do Rafael (13/11/2026): o ARENA tem de fazer sozinho o que antes pedia
varios passos -- achar o MFG Super Motion e o Lossless Scaling, baixar o que
e' gratis, levar a loja o que e' pago, baixar as versoes para PC (recomps) --
e mostrar num lugar so o que esta "equipado". Para quem nao entende nada de
computador nem de videogame, e para quem tem laudo (dificuldade de
aprendizagem, TEA, TDAH): uma linha por recurso, frase curta, uma palavra de
estado (com icone, nao so com cor) e UM botao.

O que o ARENA baixa sozinho, sempre da pagina oficial de quem fez, com a
marca SHA-256 conferida, para dentro da propria pasta (portatil, sem
instalar nada no Windows):
  - o MFG Super Motion (gratis; licenca PolyForm Strict 1.0.0: o ARENA nao o
    leva no pacote nem no GitHub, quem usa e' que baixa do autor). O autor
    publica .rar; o tar.exe que vem no Windows 10 e 11 abre (servidor\recomps.py,
    tar_do_sistema);
  - as versoes para PC (recomps) dos jogos que a pessoa tem (servidor\recomps.py).
O Lossless Scaling e' pago: o botao abre a pagina dele na Steam. Sem ele, o
MFG faz o mesmo papel, de graca.

O que NAO faz: baixar jogo comercial (a copia e' sempre de quem usa), instalar
driver, WSL ou Wine (pedem administrador), mexer no registro.
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time

import baixar
import lossless
import mfg
import plataforma as plataforma_do_sistema
import recomps
import waydroid

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

REPO_MFG = "NODIX-TECH/MFG-SUPER-MOTION"
# A marca do arquivo que o ARENA ja conferiu (13/11/2026, igual a publicada no GitHub). Versao nova do autor vale
# pela marca que o GitHub publica; sem nenhuma das duas, nao instala.
MARCAS_MFG = {"Mfg.Super.Motion1.0.5.rar": "0d4291ab9a372644cc1c02182262182e5e0b9dccff37a397ec1a856ab15a4791"}
MARCA_MFG = "arena-mfg.json"
LICENCA_MFG = "PolyForm Strict 1.0.0: grátis para uso pessoal e na escola; não pode ser repassado"

PAGINA_LOSSLESS = "https://store.steampowered.com/app/%s/" % lossless.NUMERO_NA_STEAM
LOJA_LOSSLESS = "steam://store/%s" % lossless.NUMERO_NA_STEAM

# O andamento de cada coisa que esta sendo baixada: {id: {"estado", "mensagem", "feito", "total"}}.
ANDAMENTO = {}
_TRAVA = threading.Lock()
_FILA = []
_TRABALHANDO = {"ativo": False}
_CACHE_WSL = {}


# ---------------------------------------------------------------------------
# Andamento
# ---------------------------------------------------------------------------
def _anotar(item_id, **campos):
    with _TRAVA:
        atual = ANDAMENTO.setdefault(item_id, {"estado": "esperando", "mensagem": "", "feito": 0, "total": 0})
        atual.update(campos)


def andamento(item_id):
    """O andamento do item (o dos recomps vem do proprio recomps.PROGRESSO)."""
    if item_id.startswith("recomp:"):
        de_la = recomps.progresso(item_id.split(":", 1)[1])
        if de_la:
            return de_la
    with _TRAVA:
        return dict(ANDAMENTO.get(item_id) or {})


def trabalhando():
    with _TRAVA:
        return _TRABALHANDO["ativo"] or bool(_FILA)


# ---------------------------------------------------------------------------
# O MFG Super Motion, baixado do autor
# ---------------------------------------------------------------------------
def pasta_do_mfg(raiz=RAIZ):
    """Onde o ARENA poe o MFG: o primeiro lugar que o mfg.achar procura (emuladores\\MFG SUPER MOTION)."""
    return os.path.join(raiz, "emuladores", mfg.PASTA_DO_PROGRAMA)


def instalar_mfg(raiz=RAIZ, release=None):
    """Baixa o MFG da release oficial, confere a marca e descompacta em emuladores\\MFG SUPER MOTION. Devolve a
    pasta. Lanca recomps.NaoDaParaInstalar com a frase para a tela; o andamento fica em ANDAMENTO["mfg"]."""
    if os.name != "nt":
        raise recomps.NaoDaParaInstalar("O MFG Super Motion só existe para Windows.")
    if not recomps.tar_do_sistema():
        raise recomps.NaoDaParaInstalar("Este Windows não tem o programa que abre o arquivo do MFG (o tar, que vem "
                                        "no Windows 10 e 11). Atualize o Windows e tente de novo.")
    _anotar("mfg", estado="rodando", mensagem="Procurando a versão mais nova no site do autor...", feito=0, total=0)
    rel = release or recomps.release(REPO_MFG, "")
    arquivo = next((a for a in rel["arquivos"] if a["nome"].lower().endswith(".rar")), None)
    if not arquivo:
        raise recomps.NaoDaParaInstalar("O autor não publicou o MFG para Windows nesta versão (%s)." % rel["tag"])
    if not arquivo["url"].lower().startswith("https://"):
        raise recomps.NaoDaParaInstalar("O arquivo do MFG não vem por https; o ARENA não baixa assim.")
    esperadas = [m.lower() for m in (MARCAS_MFG.get(arquivo["nome"], ""), arquivo.get("sha256", "")) if m]
    if not esperadas:
        raise recomps.NaoDaParaInstalar("O site do autor não mostra a marca de conferência desta versão do MFG. "
                                        "Por segurança, nada foi baixado.")
    pasta = pasta_do_mfg(raiz)
    baixando = os.path.join(raiz, "emuladores", ".baixando")
    os.makedirs(baixando, exist_ok=True)
    caminho = os.path.join(baixando, re.sub(r"[^A-Za-z0-9._-]", "_", arquivo["nome"]))
    _anotar("mfg", mensagem="Baixando o MFG Super Motion (%s)..." % recomps._legivel(arquivo["tamanho"]),
            total=arquivo["tamanho"])
    try:
        codigo, _ = baixar.rodar(arquivo["url"], recomps.SEGUNDOS_DOWNLOAD, destino=caminho)
        if codigo != 0 or not os.path.isfile(caminho):
            raise recomps.NaoDaParaInstalar("O download do MFG não terminou (código %s). Confira a internet e "
                                            "toque de novo." % codigo)
        _anotar("mfg", mensagem="Conferindo se o arquivo chegou inteiro...", feito=arquivo["tamanho"])
        marca = recomps._sha256(caminho)
        if any(marca != m for m in esperadas):
            raise recomps.NaoDaParaInstalar("O arquivo do MFG chegou diferente do publicado pelo autor. Nada foi "
                                            "instalado; toque de novo.")
        _anotar("mfg", mensagem="Abrindo o arquivo na pasta do ARENA...")
        nova = pasta + ".nova"
        if os.path.isdir(nova):
            shutil.rmtree(nova)
        recomps.descompactar(caminho, nova)
        if not os.path.isfile(os.path.join(nova, mfg.MOTOR)):
            shutil.rmtree(nova, ignore_errors=True)
            raise recomps.NaoDaParaInstalar("O arquivo do MFG não trouxe o motor (Engine\\nvngx.dll). Nada foi "
                                            "instalado.")
        with open(os.path.join(nova, MARCA_MFG), "w", encoding="utf-8") as saida:
            json.dump({"tag": rel["tag"], "arquivo": arquivo["nome"], "sha256": marca, "licenca": LICENCA_MFG,
                       "repo": REPO_MFG, "instalado_em": time.strftime("%Y-%m-%d %H:%M")},
                      saida, ensure_ascii=False, indent=1)
        if os.path.isdir(pasta):
            velha = pasta + ".velha"
            if os.path.isdir(velha):
                shutil.rmtree(velha)
            os.replace(pasta, velha)
            os.replace(nova, pasta)
            shutil.rmtree(velha, ignore_errors=True)
        else:
            os.replace(nova, pasta)
        _anotar("mfg", estado="pronto", mensagem="MFG Super Motion pronto.")
        return pasta
    except recomps.NaoDaParaInstalar as falha:
        _anotar("mfg", estado="erro", mensagem=str(falha))
        raise
    except OSError as falha:
        _anotar("mfg", estado="erro", mensagem="Não deu para instalar o MFG (%s). Toque de novo." % falha)
        raise recomps.NaoDaParaInstalar("Não deu para instalar o MFG (%s)." % falha)
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# A fila do "Equipar": um de cada vez, em segundo plano
# ---------------------------------------------------------------------------
def _trabalhar(depois=None):
    while True:
        with _TRAVA:
            if not _FILA:
                _TRABALHANDO["ativo"] = False
                break
            item_id = _FILA.pop(0)
            _TRABALHANDO["ativo"] = True
        try:
            if item_id == "mfg":
                instalar_mfg()
            elif item_id == "wine":
                instalar_wine()
            elif item_id == "linux":
                preparar_linux()
            elif item_id == "waydroid":
                atualizar_android_do_linux()
            elif item_id.startswith("recomp:"):
                recomps.instalar(item_id.split(":", 1)[1])
            if depois:
                depois(item_id)
        except recomps.NaoDaParaInstalar as falha:
            print("[ARENA] Equipar %s: %s" % (item_id, falha))
        except Exception as falha:       # nunca derruba a fila: o proximo item ainda tenta
            _anotar(item_id, estado="erro", mensagem="Não deu certo (%s). Toque de novo." % falha)
            print("[ARENA] Equipar %s: %s" % (item_id, falha))


def equipar(ids, depois=None):
    """Poe os itens na fila e comeca, se ninguem estiver trabalhando. Devolve os que entraram."""
    entraram = []
    with _TRAVA:
        for item_id in ids:
            if item_id in _FILA or (ANDAMENTO.get(item_id) or {}).get("estado") == "rodando":
                continue
            _FILA.append(item_id)
            ANDAMENTO[item_id] = {"estado": "esperando", "mensagem": "Na fila...", "feito": 0, "total": 0}
            entraram.append(item_id)
        comecar = entraram and not _TRABALHANDO["ativo"]
        if comecar:
            _TRABALHANDO["ativo"] = True
    if comecar:
        threading.Thread(target=_trabalhar, args=(depois,), daemon=True).start()
    return entraram


# ---------------------------------------------------------------------------
# A lista que a tela mostra
# ---------------------------------------------------------------------------
def _item(item_id, icone, nome, para_que, estado, detalhe="", acao=None, itens=None):
    """Um recurso. 'estado': pronto | falta | opcional | pago. A tela escreve a palavra e o icone (nunca so a cor)."""
    andando = andamento(item_id) if acao and acao.get("tipo") in ("baixar", "admin") else {}
    return {"id": item_id, "icone": icone, "nome": nome, "para_que": para_que, "estado": estado,
            "detalhe": detalhe, "acao": acao or {"tipo": "nenhuma"}, "andamento": andando, "itens": itens or []}


def recomps_da_biblioteca(jogos):
    """Os recomps dos jogos que a pessoa TEM (um por jogo, o melhor do catalogo), com o titulo do jogo."""
    vistos, lista = set(), []
    for jogo in jogos:
        for r in recomps.para_o_titulo(jogo.get("titulo", ""), jogo.get("plataforma", ""))[:1]:
            if r["id"] in vistos:
                continue
            vistos.add(r["id"])
            resumo = recomps.resumo_para_a_tela(r)
            resumo["jogo"] = jogo.get("titulo", "")
            lista.append(resumo)
    return sorted(lista, key=lambda r: r["jogo"].lower())


def listar(raiz, plataformas, jogos, achar_externo, nucleos_prontos=0, retroarch_ok=True, android=None):
    """Os recursos do ARENA, na ordem em que importam para quem chega: jogar, imagem, quadros a mais, versoes para
    PC e o resto. 'achar_externo(plataforma) -> caminho ou None' vem do graficos (a mesma conta do Jogar)."""
    android = plataforma_do_sistema.ANDROID if android is None else android
    lista = []
    lista.append(_item(
        "consoles", "🎮", "Consoles clássicos", "Abre os jogos de Super Nintendo, Mega Drive, PS1 e muitos outros.",
        "pronto" if retroarch_ok and nucleos_prontos else "falta",
        "%d consoles prontos para jogar." % nucleos_prontos if nucleos_prontos else
        "Falta a pasta retroarch. Baixe o pacote completo do ARENA de novo."))
    if android:
        lista.append(_item("jogos_android", "📱", "Jogos do celular",
                           "Os jogos instalados neste celular aparecem na lista do ARENA.", "pronto",
                           "O ARENA pergunta ao Android quais apps são jogos."))
    else:
        # Um emulador de fora por linha (o Dolphin abre o GameCube E o Wii: uma linha so, com os dois nomes).
        por_emulador = {}
        for plataforma in plataformas:
            externo = plataforma.get("externo") or {}
            if not externo.get("nome") or plataforma.get("nativo"):
                continue
            por_emulador.setdefault(externo["nome"], []).append(plataforma)
        for nome_externo, consoles in por_emulador.items():
            nomes = " e ".join(p.get("nome", p["id"]) for p in consoles)
            achado = any(achar_externo(p) for p in consoles)
            lista.append(_item(
                "emulador:" + consoles[0]["id"], "💿", "%s (%s)" % (nomes, nome_externo),
                "Abre os jogos de %s." % nomes, "pronto" if achado else "falta",
                "Pronto." if achado else "Vem no pacote completo do ARENA (o zip grande da página de downloads)."))
    lista.append(_item("imagem", "🖼️", "Imagem mais bonita", "Deixa o jogo antigo nítido na tela grande (FSR, SGSR).",
                       "pronto", "Já vem no ARENA. Escolha em Ajustes, Escala da tela."))
    lista.append(_item("internet", "🌐", "Partidas pela internet",
                       "Confere se a sua internet deixa jogar com quem está em outra casa.", "opcional",
                       "Toque em Conferir: o ARENA olha o caminho até a internet e o roteador, sozinho.",
                       {"tipo": "conferir", "rotulo": "Conferir minha internet"}))
    if android:
        return lista

    # Quadros a mais (so no Windows): o MFG (gratis, o ARENA baixa) e o Lossless Scaling (pago, a pessoa compra).
    if os.name == "nt":
        lista.extend(_quadros_a_mais(raiz))

    # As versoes para PC dos jogos que a pessoa tem (Windows e Linux).
    da_biblioteca = recomps_da_biblioteca(jogos)
    if da_biblioteca:
        prontos = sum(1 for r in da_biblioteca if r["instalado"])
        itens = [{"id": "recomp:" + r["id"], "nome": r["nome"], "jogo": r["jogo"], "tamanho": r.get("tamanho", ""),
                  "licenca": r.get("licenca", ""), "instalado": r["instalado"], "em_uso": r.get("em_uso", False),
                  "andamento": andamento("recomp:" + r["id"])} for r in da_biblioteca]
        lista.append(_item("recomps", "🕹️", "Versões para PC dos seus jogos",
                           "Alguns jogos de console têm uma versão feita para computador: roda sem emulador, com "
                           "imagem melhor. Usa o jogo que você já tem.",
                           "pronto" if prontos == len(itens) else "opcional",
                           "%d de %d prontas." % (prontos, len(itens)),
                           {"tipo": "lista", "rotulo": "Ver os jogos"}, itens))
    if plataforma_do_sistema.WINDOWS:
        lista.append(_item_do_wsl())
    elif os.name != "nt":
        lista.append(_item_do_wine(raiz))
        lista.append(_item_do_waydroid(raiz))
    return lista


def _item_do_wsl():
    """Jogos de Linux no Windows: ligar o WSL (administrador), depois o Linux do ARENA (sem administrador)."""
    situacao = situacao_do_wsl()
    nome, icone = "Jogos de Linux no Windows", "🐧"
    para_que = "Só para quem tem jogo de computador feito para Linux. Não é preciso para jogar o resto."
    if not situacao["ativo"]:
        return _item("wsl", icone, nome, para_que, "opcional",
                     "Precisa ligar o WSL, da Microsoft. É a única coisa do ARENA que pede permissão de administrador.",
                     {"tipo": "admin", "rotulo": "Instalar (pede permissão de administrador)",
                      "aviso": "Para ligar o WSL, o Windows vai pedir a permissão de administrador (a senha de quem "
                               "cuida do computador). Pode pedir para reiniciar no fim. Na escola, sem a senha, não dá. "
                               "Continuar?"})
    if not situacao["do_arena"]:
        return _item("linux", icone, nome, para_que, "opcional",
                     "O WSL está ligado. Falta o Linux do ARENA: o ARENA baixa o Ubuntu oficial (uns 350 MB) e guarda "
                     "em emuladores\\Linux, sem pedir permissão.",
                     {"tipo": "baixar", "rotulo": "Preparar o Linux do ARENA"})
    return _item("wsl", icone, nome, para_que, "pronto", "Pronto: o Linux do ARENA fica em emuladores\\Linux.")


def _item_do_wine(raiz):
    """Jogos de Windows no Linux: o Wine (o do sistema, o do Proton ou o portatil que o ARENA baixa)."""
    import jogos_pc
    camada = jogos_pc.wine()
    nome, icone = "Jogos de Windows no Linux", "🍷"
    para_que = "Só para quem tem jogo de computador feito para Windows. Não é preciso para jogar o resto."
    if camada:
        de_onde = "o do ARENA" if camada[0].startswith(pasta_do_wine(raiz)) else (
            "o Proton da Steam" if "proton" in camada[0].lower() else "o deste Linux")
        return _item("wine", icone, nome, para_que, "pronto", "Pronto: o Wine é %s." % de_onde)
    return _item("wine", icone, nome, para_que, "opcional",
                 "O ARENA baixa o Wine portátil (uns 100 MB) e guarda em emuladores/Wine, sem pedir permissão.",
                 {"tipo": "baixar", "rotulo": "Baixar o Wine"})


def _quadros_a_mais(raiz):
    """As duas linhas dos quadros a mais (Windows): o MFG e o Lossless Scaling."""
    lista = []
    achado_mfg = mfg.achar(raiz)
    if achado_mfg:
        lista.append(_item("mfg", "✨", "Movimento mais liso (MFG Super Motion)",
                           "Cria quadros a mais: o jogo parece mais suave.", "pronto",
                           "Versão %s. O ARENA liga sozinho quando a placa de vídeo aguenta."
                           % (achado_mfg.get("versao") or "instalada")))
    else:
        lista.append(_item("mfg", "✨", "Movimento mais liso (MFG Super Motion)",
                           "Cria quadros a mais: o jogo parece mais suave. É grátis.", "falta",
                           "O ARENA baixa do site do autor (cerca de 100 MB) e guarda na pasta dele. Licença: %s."
                           % LICENCA_MFG, {"tipo": "baixar", "rotulo": "Baixar e instalar"}))
    achado_ls = lossless.achar(raiz)
    if achado_ls and achado_ls.get("licenca"):
        lista.append(_item("lossless", "🚀", "Lossless Scaling", "Outro jeito de criar quadros a mais.", "pronto",
                           "Comprado na Steam. O ARENA escolhe sozinho entre ele e o MFG."))
    else:
        lista.append(_item("lossless", "🚀", "Lossless Scaling",
                           "Outro jeito de criar quadros a mais. É pago e não é obrigatório: o MFG faz o mesmo de graça.",
                           "pago", "Achado, mas sem a compra na Steam desta conta." if achado_ls else
                           "Não está neste computador.", {"tipo": "loja", "rotulo": "Ver na Steam"}))
    return lista


def ids_para_equipar_tudo(lista):
    """O que o "Equipar tudo" baixa: o que e' gratis e falta (o MFG e as versoes para PC dos seus jogos)."""
    ids = []
    for item in lista:
        if item["acao"].get("tipo") == "baixar" and item["estado"] == "falta":
            ids.append(item["id"])
        for sub in item.get("itens") or []:
            if not sub.get("instalado"):
                ids.append(sub["id"])
    return ids


# ---------------------------------------------------------------------------
# Jogo de um sistema no outro (13/11/2026): o Wine no Linux e o WSL no Windows, por dentro do ARENA
# ---------------------------------------------------------------------------
# Jogo do Windows no Linux: o Wine portatil das compilacoes abertas do Kron4ek (LGPL; o "wow64" dispensa as
# bibliotecas de 32 bits), baixado para emuladores/Wine, sem administrador. O prefixo (o "C:" do Wine) fica em
# dados/wine, dentro do ARENA.
REPO_WINE = "Kron4ek/Wine-Builds"
# Jogo do Linux no Windows: o WSL. Liga-lo e' a UNICA coisa do ARENA que pede administrador (pedido do Rafael em
# 13/11/2026; o botao avisa antes e o proprio Windows pede a permissao). Ligado, o ARENA monta o Linux dele com a
# imagem oficial do Ubuntu para WSL, com o disco em emuladores\Linux (sem administrador).
DISTRO_DO_ARENA = "ARENA-Linux"
PAGINA_UBUNTU_WSL = "https://cloud-images.ubuntu.com/wsl/releases/noble/current/"
ARQUIVO_UBUNTU_WSL = "ubuntu-noble-wsl-amd64-wsl.rootfs.tar.gz"
# O que os jogos de Linux pedem para abrir janela, desenhar e tocar som (Ubuntu 24.04).
PACOTES_DOS_JOGOS = ("libgl1 libegl1 libgles2 libvulkan1 mesa-vulkan-drivers libsdl2-2.0-0 libpulse0 libasound2t64 "
                     "libx11-6 libxext6 libxrandr2 libxi6 libxcursor1 libxinerama1 libxkbcommon0 libwayland-client0 "
                     "libopenal1 libfreetype6 libfontconfig1 ca-certificates")
_SEM_JANELA = {"creationflags": 0x08000000} if os.name == "nt" else {}
_CACHE_WSL_TEMPO = 30


def pasta_do_wine(raiz=RAIZ):
    return os.path.join(raiz, "emuladores", "Wine")


def instalar_wine(raiz=RAIZ, release=None):
    """Baixa o Wine portatil (o .tar.xz "amd64-wow64", sem staging) e abre em emuladores/Wine. So no Linux."""
    if os.name == "nt":
        raise recomps.NaoDaParaInstalar("No Windows o jogo do Windows abre direto: o Wine é para o Linux.")
    _anotar("wine", estado="rodando", mensagem="Procurando o Wine mais novo...", feito=0, total=0)
    try:
        rel = release or recomps.release(REPO_WINE, "")
        arquivo = next((a for a in rel["arquivos"] if re.fullmatch(r"wine-[\d.]+-amd64-wow64\.tar\.xz", a["nome"])),
                       None)
        if not arquivo:
            raise recomps.NaoDaParaInstalar("A versão %s do Wine não tem o arquivo para este computador." % rel["tag"])
        _baixar_conferido("wine", arquivo, [arquivo.get("sha256", "")], pasta_do_wine(raiz), raiz,
                          lambda nova: os.path.isfile(os.path.join(nova, "bin", "wine")))
        _anotar("wine", estado="pronto", mensagem="Wine pronto: os jogos do Windows abrem neste Linux.")
        return pasta_do_wine(raiz)
    except recomps.NaoDaParaInstalar as falha:
        _anotar("wine", estado="erro", mensagem=str(falha))
        raise


def _baixar_conferido(item_id, arquivo, marcas, pasta, raiz, tem_o_programa):
    """Baixa 'arquivo' (da release), confere com 'marcas' (as que houver; sem nenhuma, nao instala), abre numa pasta
    nova e troca a velha. tem_o_programa(pasta_nova) diz se veio o que importa."""
    if not arquivo["url"].lower().startswith("https://"):
        raise recomps.NaoDaParaInstalar("O arquivo não vem por https; o ARENA não baixa assim.")
    esperadas = [m.lower() for m in marcas if m]
    if not esperadas:
        raise recomps.NaoDaParaInstalar("O site não mostra a marca de conferência deste arquivo. Por segurança, "
                                        "nada foi baixado.")
    baixando = os.path.join(raiz, "emuladores", ".baixando")
    os.makedirs(baixando, exist_ok=True)
    caminho = os.path.join(baixando, re.sub(r"[^A-Za-z0-9._-]", "_", arquivo["nome"]))
    _anotar(item_id, mensagem="Baixando (%s)..." % recomps._legivel(arquivo.get("tamanho", 0)),
            total=arquivo.get("tamanho", 0))
    try:
        codigo, _ = baixar.rodar(arquivo["url"], recomps.SEGUNDOS_DOWNLOAD, destino=caminho)
        if codigo != 0 or not os.path.isfile(caminho):
            raise recomps.NaoDaParaInstalar("O download não terminou (código %s). Confira a internet e toque de novo."
                                            % codigo)
        _anotar(item_id, mensagem="Conferindo se o arquivo chegou inteiro...", feito=arquivo.get("tamanho", 0))
        if any(recomps._sha256(caminho) != m for m in esperadas):
            raise recomps.NaoDaParaInstalar("O arquivo chegou diferente do publicado. Nada foi instalado; toque de "
                                            "novo.")
        _anotar(item_id, mensagem="Abrindo o arquivo na pasta do ARENA...")
        nova = pasta + ".nova"
        if os.path.isdir(nova):
            shutil.rmtree(nova)
        try:
            recomps.descompactar(caminho, nova)
        except OSError as falha:
            raise recomps.NaoDaParaInstalar("Não deu para abrir o arquivo (%s). Toque de novo." % falha)
        if not tem_o_programa(nova):
            shutil.rmtree(nova, ignore_errors=True)
            raise recomps.NaoDaParaInstalar("O arquivo não trouxe o programa esperado. Nada foi instalado.")
        if os.path.isdir(pasta):
            velha = pasta + ".velha"
            if os.path.isdir(velha):
                shutil.rmtree(velha)
            os.replace(pasta, velha)
            os.replace(nova, pasta)
            shutil.rmtree(velha, ignore_errors=True)
        else:
            os.replace(nova, pasta)
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


def _item_do_waydroid(raiz):
    """Jogos de Android no Linux: o Waydroid (instalar pede administrador, avisado antes; o resto, nao)."""
    nome, icone = "Jogos de Android no Linux", "🤖"
    para_que = "Os jogos de celular (Android) abrem numa janela deste Linux. Não é preciso para jogar o resto."
    situacao = waydroid.situacao()
    andando = andamento("waydroid")
    if andando.get("estado") == "rodando" and not situacao["preparado"]:
        return _item("waydroid", icone, nome, para_que, "opcional", "⏳ " + andando.get("mensagem", ""))
    if not situacao["preparado"]:
        falta = "" if situacao["binder"] else (" Atenção: este Linux não tem o \"binder\" do Android no núcleo; sem "
                                               "ele o Waydroid não liga (veja docs.waydro.id).")
        return _item("waydroid", icone, nome, para_que, "opcional",
                     "Precisa do Waydroid, um Android que roda dentro do Linux. Instalar pede a senha de "
                     "administrador e baixa uns 800 MB." + falta,
                     {"tipo": "admin", "rotulo": "Instalar (pede permissão de administrador)",
                      "aviso": "Para instalar o Waydroid, o Linux vai pedir a senha de administrador (de quem cuida "
                               "do computador). Ele baixa o Android oficial do Waydroid, uns 800 MB, e pode demorar. "
                               "Continuar?"})
    if not situacao["binder"]:
        return _item("waydroid", icone, nome, para_que, "falta",
                     "O Waydroid está instalado, mas este Linux não tem o \"binder\" no núcleo. Peça a quem cuida do "
                     "computador (docs.waydro.id, Troubleshooting).")
    jogos = waydroid.jogos(raiz)
    aviso = "" if waydroid.tem_wayland() else (" Para abrir, entre no Linux pela sessão Wayland (na tela de entrada, "
                                                "a engrenagem).")
    return _item("waydroid", icone, nome, para_que, "pronto",
                 "Pronto: %d jogos de Android. Ponha APKs em jogos/pessoais/Android e clique em Atualizar.%s"
                 % (len(jogos), aviso),
                 {"tipo": "baixar", "rotulo": "Atualizar os jogos de Android"})


def atualizar_android_do_linux(raiz=RAIZ):
    """Liga o Android do Waydroid, instala os APKs novos da pasta e le a lista de jogos de novo."""
    _anotar("waydroid", estado="rodando", mensagem="Ligando o Android (uns 30 segundos)...", feito=0, total=0)
    if not waydroid.ligar_sessao():
        _anotar("waydroid", estado="erro", mensagem="O Android não ligou. Reinicie o computador e tente de novo.")
        return
    _anotar("waydroid", mensagem="Instalando os APKs da pasta jogos/pessoais/Android...")
    novos = waydroid.instalar_apks(raiz)
    lista = waydroid.jogos(raiz)
    _anotar("waydroid", estado="pronto", mensagem="Pronto: %d jogos (%d novos)." % (len(lista), novos))


def instalar_waydroid_com_administrador(raiz=RAIZ):
    """Roda o roteiro de instalacao do Waydroid com o pkexec (a janela da senha e' do proprio Linux), em segundo
    plano, e guarda o que ele escreveu em dados/waydroid-instalacao.log. Devolve a frase para a tela."""
    if os.name == "nt" or plataforma_do_sistema.ANDROID:
        raise recomps.NaoDaParaInstalar("O Waydroid é do Linux.")
    if (andamento("waydroid") or {}).get("estado") == "rodando":
        return "A instalação do Waydroid já está andando. Espere terminar."
    roteiro, motivo = waydroid.roteiro_de_instalacao()
    if not roteiro:
        raise recomps.NaoDaParaInstalar(motivo)
    comando = waydroid.comando_com_administrador(roteiro)
    if not comando:
        raise recomps.NaoDaParaInstalar("Este Linux não tem o pkexec, que pede a senha de administrador. Peça a quem "
                                        "cuida do computador para instalar o Waydroid (docs.waydro.id).")
    os.makedirs(os.path.join(raiz, "dados"), exist_ok=True)
    caminho_log = os.path.join(raiz, "dados", "waydroid-instalacao.log")
    _anotar("waydroid", estado="rodando", mensagem="Instalando o Waydroid (pode levar uns 15 minutos)...")

    def instalar():
        texto = ""
        try:
            with open(caminho_log, "wb") as log:
                codigo = subprocess.run(comando, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                        timeout=3600).returncode
        except (OSError, subprocess.SubprocessError) as falha:
            codigo, texto = 1, str(falha)
        waydroid.esquecer()
        if codigo in (126, 127):
            _anotar("waydroid", estado="erro", mensagem="A senha de administrador não foi dada, então nada mudou.")
        elif codigo != 0:
            _anotar("waydroid", estado="erro", mensagem="A instalação parou (código %d%s). O que aconteceu está em "
                    "dados/waydroid-instalacao.log." % (codigo, (": " + texto) if texto else ""))
        else:
            _anotar("waydroid", estado="pronto", mensagem="Waydroid instalado. Clique em Atualizar os jogos.")
    threading.Thread(target=instalar, daemon=True).start()
    return ("O Linux vai pedir a senha de administrador numa janela à parte. Depois o ARENA instala o Waydroid e baixa "
            "o Android sozinho: acompanhe aqui, na linha Jogos de Android no Linux.")


def _wsl_exe():
    return shutil.which("wsl.exe") or shutil.which("wsl") if os.name == "nt" else None


def _rodar_wsl(argumentos, segundos=30):
    """(codigo, texto) de um wsl.exe; a saida dele vem em UTF-16 quando fala do proprio WSL."""
    programa = _wsl_exe()
    if not programa:
        return 1, ""
    try:
        saida = subprocess.run([programa] + argumentos, capture_output=True, timeout=segundos, **_SEM_JANELA)
    except (OSError, subprocess.SubprocessError) as falha:
        return 1, str(falha)
    bruto = saida.stdout + saida.stderr
    texto = bruto.decode("utf-16-le", "replace") if b"\x00" in bruto else bruto.decode("utf-8", "replace")
    return saida.returncode, texto.replace("\x00", "")


def situacao_do_wsl(forcar=False):
    """{"ativo": o WSL esta ligado neste Windows, "do_arena": o Linux do ARENA esta registrado, "outras": [...]}.
    Guardada por 30 s (o painel atualiza a cada 1,5 s enquanto baixa)."""
    agora = time.monotonic()
    guardada = _CACHE_WSL.get("situacao")
    if guardada and not forcar and agora - guardada[0] < _CACHE_WSL_TEMPO:
        return guardada[1]
    situacao = {"ativo": False, "do_arena": False, "outras": []}
    if _wsl_exe():
        codigo, _texto = _rodar_wsl(["--status"], 20)
        situacao["ativo"] = codigo == 0
        if situacao["ativo"]:
            codigo, texto = _rodar_wsl(["-l", "-q"], 20)
            nomes = [l.strip() for l in texto.splitlines() if l.strip()] if codigo == 0 else []
            situacao["do_arena"] = DISTRO_DO_ARENA in nomes
            situacao["outras"] = [n for n in nomes if n != DISTRO_DO_ARENA and "docker" not in n.lower()]
    _CACHE_WSL["situacao"] = (agora, situacao)
    return situacao


def ligar_o_wsl_com_administrador():
    """Pede ao Windows para rodar 'wsl --install --no-distribution' como administrador (a janela do UAC aparece).
    Devolve a frase para a tela. Lanca recomps.NaoDaParaInstalar se a pessoa negar ou o Windows nao deixar."""
    if os.name != "nt":
        raise recomps.NaoDaParaInstalar("O WSL é do Windows.")
    import ctypes
    from ctypes import wintypes
    executar = ctypes.windll.shell32.ShellExecuteW
    executar.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                         ctypes.c_int]
    executar.restype = ctypes.c_void_p
    resultado = executar(None, "runas", "wsl.exe", "--install --no-distribution", None, 1)
    codigo = int(resultado or 0)
    _CACHE_WSL.clear()
    if codigo <= 32:
        if codigo == 5:
            raise recomps.NaoDaParaInstalar("A permissão de administrador não foi dada, então nada mudou. Na escola, "
                                            "peça a quem cuida dos computadores.")
        raise recomps.NaoDaParaInstalar("O Windows não deixou ligar o WSL (código %d). Peça a quem cuida do computador."
                                        % codigo)
    return ("O Windows está ligando o WSL numa janela à parte. Quando ela terminar, se pedir, reinicie o computador; "
            "depois volte aqui e toque em Preparar o Linux do ARENA.")


def pasta_do_linux(raiz=RAIZ):
    return os.path.join(raiz, "emuladores", "Linux")


def preparar_linux(raiz=RAIZ):
    """Monta o Linux do ARENA no WSL (sem administrador): registra o disco que ja esta na pasta (o ARENA levado para
    outro computador) ou baixa a imagem oficial do Ubuntu para WSL, confere, importa e poe o que os jogos pedem."""
    situacao = situacao_do_wsl(forcar=True)
    if not situacao["ativo"]:
        raise recomps.NaoDaParaInstalar("O WSL ainda não está ligado neste Windows: toque antes em Instalar (pede "
                                        "permissão de administrador).")
    pasta = pasta_do_linux(raiz)
    disco = os.path.join(pasta, "ext4.vhdx")
    _anotar("linux", estado="rodando", mensagem="Preparando o Linux do ARENA...", feito=0, total=0)
    try:
        if not situacao["do_arena"]:
            if os.path.isfile(disco):
                _anotar("linux", mensagem="Achei o Linux do ARENA na pasta: registrando neste computador...")
                codigo, texto = _rodar_wsl(["--import-in-place", DISTRO_DO_ARENA, disco], 300)
                if codigo != 0:
                    raise recomps.NaoDaParaInstalar("O WSL não aceitou o disco da pasta emuladores\\Linux (%s). "
                                                    "Atualize o WSL e toque de novo." % texto.strip()[:160])
            else:
                _importar_ubuntu(raiz, pasta)
        _anotar("linux", mensagem="Instalando o que os jogos de Linux pedem (vídeo e som). Pode demorar...")
        codigo, texto = _rodar_wsl(["-d", DISTRO_DO_ARENA, "-u", "root", "--", "sh", "-c",
                                    "export DEBIAN_FRONTEND=noninteractive; apt-get update -q && "
                                    "apt-get install -y -q --no-install-recommends " + PACOTES_DOS_JOGOS], 2400)
        if codigo != 0:
            raise recomps.NaoDaParaInstalar("O Linux do ARENA foi montado, mas não baixou as peças de vídeo e som "
                                            "(%s). Confira a internet e toque de novo." % texto.strip()[-160:])
        _CACHE_WSL.clear()
        _anotar("linux", estado="pronto", mensagem="Linux do ARENA pronto: os jogos de Linux abrem neste Windows.")
        return pasta
    except recomps.NaoDaParaInstalar as falha:
        _anotar("linux", estado="erro", mensagem=str(falha))
        raise


def _importar_ubuntu(raiz, pasta):
    """Baixa a imagem oficial do Ubuntu 24.04 para WSL, confere pela lista de marcas do proprio site e importa."""
    baixando = os.path.join(raiz, "emuladores", ".baixando")
    os.makedirs(baixando, exist_ok=True)
    lista = os.path.join(baixando, "SHA256SUMS")
    imagem = os.path.join(baixando, ARQUIVO_UBUNTU_WSL)
    try:
        _anotar("linux", mensagem="Lendo a lista de conferência do Ubuntu...")
        codigo, _ = baixar.rodar(PAGINA_UBUNTU_WSL + "SHA256SUMS", 60, destino=lista)
        marca = ""
        if codigo == 0 and os.path.isfile(lista):
            with open(lista, encoding="utf-8", errors="replace") as arquivo:
                for linha in arquivo:
                    partes = linha.split()
                    if len(partes) == 2 and partes[1].lstrip("*") == ARQUIVO_UBUNTU_WSL:
                        marca = partes[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", marca):
            raise recomps.NaoDaParaInstalar("Não consegui ler a lista de conferência do Ubuntu. Confira a internet e "
                                            "toque de novo.")
        _anotar("linux", mensagem="Baixando o Ubuntu oficial para WSL (uns 350 MB)...")
        codigo, _ = baixar.rodar(PAGINA_UBUNTU_WSL + ARQUIVO_UBUNTU_WSL, recomps.SEGUNDOS_DOWNLOAD, destino=imagem)
        if codigo != 0 or not os.path.isfile(imagem):
            raise recomps.NaoDaParaInstalar("O download do Ubuntu não terminou (código %s). Confira a internet e toque "
                                            "de novo." % codigo)
        _anotar("linux", mensagem="Conferindo se o Ubuntu chegou inteiro...")
        if recomps._sha256(imagem) != marca:
            raise recomps.NaoDaParaInstalar("O Ubuntu chegou diferente do publicado. Nada foi instalado; toque de novo.")
        _anotar("linux", mensagem="Montando o Linux do ARENA em emuladores\\Linux...")
        os.makedirs(pasta, exist_ok=True)
        codigo, texto = _rodar_wsl(["--import", DISTRO_DO_ARENA, pasta, imagem, "--version", "2"], 900)
        if codigo != 0:
            raise recomps.NaoDaParaInstalar("O WSL não montou o Linux do ARENA (%s). Reinicie o computador e toque de "
                                            "novo." % texto.strip()[:160])
    finally:
        for arquivo in (lista, imagem):
            try:
                os.remove(arquivo)
            except OSError:
                pass


def abrir_loja_do_lossless():
    """Abre a pagina do Lossless Scaling: pela Steam, se houver; senao, no navegador. Endereco fixo (nada vem da
    tela). Devolve o endereco aberto."""
    endereco = LOJA_LOSSLESS if lossless.bibliotecas_da_steam() else PAGINA_LOSSLESS
    if os.name == "nt":
        subprocess.Popen([shutil.which("rundll32") or "rundll32", "url.dll,FileProtocolHandler", endereco],
                         creationflags=0x08000000)
    else:
        programa = shutil.which("xdg-open")
        if not programa:
            raise OSError("não achei como abrir o navegador")
        endereco = PAGINA_LOSSLESS
        subprocess.Popen([programa, endereco], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return endereco


def _megas(texto):
    """'104 MB' -> 104.0; '1,2 GB' -> 1228.8; o que nao der para ler, 0."""
    achado = re.match(r"\s*([\d.,]+)\s*(KB|MB|GB)", str(texto or ""), re.I)
    if not achado:
        return 0.0
    numero = float(achado.group(1).replace(",", "."))
    return numero * {"KB": 1 / 1024, "MB": 1, "GB": 1024}[achado.group(2).upper()]


def tamanho_aproximado(lista, ids):
    """Quanto o "Equipar tudo" baixa, por alto ('cerca de 2,3 GB'), para a tela avisar antes."""
    total = 0.0
    for item in lista:
        if item["id"] in ids and item["id"] == "mfg":
            total += 100
        for sub in item.get("itens") or []:
            if sub["id"] in ids:
                total += _megas(sub.get("tamanho"))
    if total >= 1024:
        return "cerca de %s GB" % ("%.1f" % (total / 1024)).replace(".", ",")
    return "cerca de %d MB" % max(1, round(total))
