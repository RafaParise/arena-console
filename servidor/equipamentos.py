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
    andando = andamento(item_id) if acao and acao.get("tipo") == "baixar" else {}
    return {"id": item_id, "icone": icone, "nome": nome, "para_que": para_que, "estado": estado,
            "detalhe": detalhe, "acao": acao or {"tipo": "nenhuma"}, "andamento": andando, "itens": itens or []}


def _wsl_em_cache():
    if "valor" not in _CACHE_WSL:
        import jogos_pc
        _CACHE_WSL["valor"] = bool(jogos_pc.wsl())
    return _CACHE_WSL["valor"]


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
        lista.append(_item("wsl", "🐧", "Jogos de Linux no Windows",
                           "Só para quem tem jogo de computador feito para Linux.",
                           "pronto" if _wsl_em_cache() else "opcional",
                           "Pronto (WSL)." if _wsl_em_cache() else
                           "Não é preciso para jogar. Quem cuida do computador pode instalar o WSL da Microsoft."))
    return lista


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
