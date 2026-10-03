# -*- coding: utf-8 -*-
r"""
ARENA - o arquivo do jogo no lugar certo, com um clique ("Arrumar").

Pedido do Rafael (03/10/2026): "O ARENA deve saber como cada jogo deve ser
posicionado, por exemplo o Killer Instinct que deve ter uma pasta com o
mesmo nome da rom com o arquivo .chd, o ARENA deve ser capaz de saber como
configurar e posicionar todos os arquivos sejam bios ou jogos, e assim deve
tambem saber e criar essas subpastas necessarias para guiar um usuario leigo
como configurar".

O indexador AVISA o que esta fora do lugar (servidor\indexador.py). Aqui
fica o CONSERTO de cada caso em que so existe um jeito certo. O cartao do
jogo mostra o botao "Arrumar" e, no clique -- quem manda e' a pessoa: o
ARENA nunca move arquivo de jogo sozinho (decisao antiga, ver "A pasta
manda" no CLAUDE.md) --, este modulo confere de novo e faz:

  zip_na_pasta_do_disco  Arcade\kinst\kinst.zip (junto do kinst.chd)
                         -> Arcade\kinst.zip: o MAME procura o zip na pasta
                         de cima e o disco na pasta com o nome do zip
                         (provado em 02/10/2026: assim, "unknown option: kinst")
  disco_solto            Arcade\kinst.chd ao lado do kinst.zip
                         -> Arcade\kinst\kinst.chd (cria a pasta)
  disco_em_outra_pasta   Arcade\Killer Instinct\kinst.chd, com o Arcade\kinst.zip
                         -> Arcade\kinst\kinst.chd
  bios_neogeo_nome       neogeo.mame.zip na pasta do jogo
                         -> neogeo.zip (o unico nome que o emulador procura)
  bios_neogeo            jogo de Neo Geo no MAME sem o neogeo.zip na pasta dele
                         -> uma copia do neogeo.zip (da pasta BIOS do ARENA)
  pasta_dentro_do_zip    o zip com tudo dentro de uma pasta ("king\...")
                         -> o zip refeito sem a pasta; o original vai para
                         backup\originais
  descompactar           jogo de CD dentro de .zip (PS1\Crash.zip com o .cue e
                         os .bin): o emulador nao abre CD de dentro de zip
                         -> descompactado numa pasta com o nome do jogo, em
                         segundo plano (pode levar minutos); o .zip fica
  extrair_disco          o disco de fliperama dentro de outro zip
                         (kinst-chd.zip) -> Arcade\kinst\kinst.chd

E pasta_do_disco(): quando o MAME diz que falta o disco ("kinst.chd NOT
FOUND"), cria a pasta onde ele vai, com um LEIA dizendo o que por la.

Nunca apaga nem passa por cima: se o destino ja existe, para e explica.
Tudo dentro da pasta de jogos.
"""
import os
import re
import shutil
import threading
import time
import uuid
import zipfile

# Leia-me, imagem e atalho que vem junto no zip nao sao parte do jogo.
_NAO_E_DO_JOGO = re.compile(r"\.(txt|html?|nfo|diz|url|jpe?g|png|gif|pdf|doc)$", re.I)
# Os arquivos de uma BIOS de Neo Geo (o neogeo.zip do MAME e o do FBNeo).
_RE_NEOGEO_COM_OUTRO_NOME = re.compile(r"^neogeo[ ._-].+\.zip$", re.I)


class NaoDa(Exception):
    """O conserto nao pode ser feito agora; a mensagem diz por que."""


def _rotulo(acao, **dados):
    textos = {
        "zip_na_pasta_do_disco": "Arrumar: tirar o %(zip)s da pasta %(pasta)s",
        "disco_solto": "Arrumar: pôr o %(disco)s na pasta %(pasta)s",
        "disco_em_outra_pasta": "Arrumar: pôr o %(disco)s na pasta %(pasta)s",
        "bios_neogeo_nome": "Arrumar: renomear %(atual)s para neogeo.zip",
        "bios_neogeo": "Arrumar: pôr o neogeo.zip nesta pasta",
        "pasta_dentro_do_zip": "Arrumar: refazer o %(zip)s sem a pasta de dentro",
        "descompactar": "Arrumar: descompactar o %(zip)s",
        "extrair_disco": "Arrumar: tirar o %(disco)s de dentro do %(zip)s",
    }
    return textos[acao] % dados


def conserto(acao, **dados):
    return {"acao": acao, "rotulo": _rotulo(acao, **dados)}


# ---------------------------------------------------------------------------
# O que da para arrumar (o indexador chama ao montar o cartao)
# ---------------------------------------------------------------------------

def _chds(pasta):
    try:
        return sorted(n for n in os.listdir(pasta) if n.lower().endswith(".chd"))
    except OSError:
        return []


def zip_na_pasta_do_disco(caminho):
    """Arcade\\kinst\\kinst.zip junto do disco: (destino) ou None."""
    pasta = os.path.dirname(caminho)
    romset = os.path.splitext(os.path.basename(caminho))[0].lower()
    if os.path.basename(pasta).lower() != romset or not _chds(pasta):
        return None
    return os.path.join(os.path.dirname(pasta), os.path.basename(caminho))


def disco_solto(caminho):
    """Arcade\\kinst.chd ao lado do kinst.zip: (disco, pasta de destino) ou None."""
    pasta = os.path.dirname(caminho)
    romset = os.path.splitext(os.path.basename(caminho))[0]
    disco = next((n for n in _chds(pasta) if os.path.splitext(n)[0].lower() == romset.lower()), None)
    if not disco or os.path.basename(pasta).lower() == romset.lower():
        return None
    return os.path.join(pasta, disco), os.path.join(pasta, romset)


def disco_em_outra_pasta(caminho_disco):
    """Arcade\\Killer Instinct\\kinst.chd com o Arcade\\kinst.zip: (zip, pasta
    de destino) ou None. So quando o zip de mesmo nome esta na pasta de cima."""
    pasta = os.path.dirname(caminho_disco)
    pai = os.path.dirname(pasta)
    base = os.path.splitext(os.path.basename(caminho_disco))[0]
    if os.path.basename(pasta).lower() == base.lower():
        return None
    try:
        nomes = os.listdir(pai)
    except OSError:
        return None
    zip_irmao = next((n for n in nomes if n.lower() == base.lower() + ".zip"), None)
    if not zip_irmao:
        return None
    return os.path.join(pai, zip_irmao), os.path.join(pai, os.path.splitext(zip_irmao)[0])


def bios_neogeo(caminho, bios_do_arena):
    """Jogo de Neo Geo no MAME: o que fazer pelo neogeo.zip da pasta dele.
    ("bios_neogeo_nome", atual) | ("bios_neogeo", origem) | None."""
    pasta = os.path.dirname(caminho)
    try:
        nomes = sorted(os.listdir(pasta))
    except OSError:
        return None
    if any(n.lower() == "neogeo.zip" for n in nomes):
        return None
    errado = next((n for n in nomes if _RE_NEOGEO_COM_OUTRO_NOME.match(n)), None)
    if errado:
        return "bios_neogeo_nome", errado
    if bios_do_arena and os.path.isfile(bios_do_arena):
        return "bios_neogeo", bios_do_arena
    return None


def pasta_dentro_do_zip(caminho):
    """O zip com tudo dentro de UMA pasta (o emulador procura na raiz): o nome
    da pasta, ou None."""
    try:
        with zipfile.ZipFile(caminho) as z:
            nomes = [n.replace("\\", "/") for n in z.namelist() if not n.endswith("/")]
    except (OSError, zipfile.BadZipFile, ValueError):
        return None
    soltos = [n for n in nomes if "/" not in n and not _NAO_E_DO_JOGO.search(n)]
    pastas = {n.split("/", 1)[0] for n in nomes if "/" in n}
    if nomes and not soltos and len(pastas) == 1:
        return next(iter(pastas))
    return None


def conserto_do_disco(caminho_disco):
    """O conserto do .chd fora do lugar, ou None."""
    achado = disco_em_outra_pasta(caminho_disco)
    if not achado:
        return None
    return conserto("disco_em_outra_pasta", disco=os.path.basename(caminho_disco),
                     pasta=os.path.basename(achado[1]))


# ---------------------------------------------------------------------------
# Fazer (a rota /api/jogo/arrumar chama, depois do clique)
# ---------------------------------------------------------------------------

def _dentro(caminho, raiz):
    caminho, raiz = os.path.normcase(os.path.abspath(caminho)), os.path.normcase(os.path.abspath(raiz))
    return caminho == raiz or caminho.startswith(raiz + os.sep)


def _mover(origem, destino, pasta_jogos):
    if not (_dentro(origem, pasta_jogos) and _dentro(destino, pasta_jogos)):
        raise NaoDa("Só arrumo arquivos dentro da pasta de jogos.")
    if os.path.exists(destino):
        raise NaoDa("Já existe %s em %s: tire um dos dois de lá e tente de novo."
                    % (os.path.basename(destino), os.path.relpath(os.path.dirname(destino), pasta_jogos)))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.move(origem, destino)


def aplicar(acao, caminho, pasta_jogos, raiz, bios_do_arena=None):
    """Faz o conserto 'acao' no jogo 'caminho' (conferindo de novo se ainda
    vale). Devolve (mensagem, caminho novo do jogo ou None). NaoDa se nao
    der."""
    if not _dentro(caminho, pasta_jogos) or not os.path.exists(caminho):
        raise NaoDa("O arquivo do jogo não está mais no lugar. Clique em Atualizar lista.")
    nome = os.path.basename(caminho)
    if acao == "zip_na_pasta_do_disco":
        destino = zip_na_pasta_do_disco(caminho)
        if not destino:
            raise NaoDa("O %s já não está dentro da pasta do disco." % nome)
        _mover(caminho, destino, pasta_jogos)
        return ("Pronto: o %s foi para %s, e o disco ficou na pasta %s ao lado dele."
                % (nome, os.path.relpath(os.path.dirname(destino), pasta_jogos),
                   os.path.basename(os.path.dirname(caminho))), destino)
    if acao == "disco_solto":
        achado = disco_solto(caminho)
        if not achado:
            raise NaoDa("O disco já não está solto ao lado do %s." % nome)
        disco, pasta = achado
        _mover(disco, os.path.join(pasta, os.path.basename(disco)), pasta_jogos)
        return ("Pronto: o %s foi para a pasta %s, ao lado do %s."
                % (os.path.basename(disco), os.path.basename(pasta), nome), None)
    if acao == "disco_em_outra_pasta":
        achado = disco_em_outra_pasta(caminho)
        if not achado:
            raise NaoDa("O disco já está na pasta certa.")
        zip_irmao, pasta = achado
        destino = os.path.join(pasta, nome)
        _mover(caminho, destino, pasta_jogos)
        return ("Pronto: o %s foi para a pasta %s, ao lado do %s."
                % (nome, os.path.basename(pasta), os.path.basename(zip_irmao)), destino)
    if acao in ("bios_neogeo_nome", "bios_neogeo"):
        achado = bios_neogeo(caminho, bios_do_arena)
        if not achado or achado[0] != acao:
            raise NaoDa("A BIOS do Neo Geo já está certa nesta pasta.")
        pasta = os.path.dirname(caminho)
        if acao == "bios_neogeo_nome":
            _mover(os.path.join(pasta, achado[1]), os.path.join(pasta, "neogeo.zip"), pasta_jogos)
            return "Pronto: %s agora se chama neogeo.zip." % achado[1], None
        destino = os.path.join(pasta, "neogeo.zip")
        if not _dentro(destino, pasta_jogos) or os.path.exists(destino):
            raise NaoDa("Já existe um neogeo.zip nesta pasta.")
        shutil.copy2(achado[1], destino)
        return "Pronto: o neogeo.zip (a BIOS do Neo Geo) foi copiado para a pasta deste jogo.", None
    if acao == "pasta_dentro_do_zip":
        pasta_de_dentro = pasta_dentro_do_zip(caminho)
        if not pasta_de_dentro:
            raise NaoDa("Os arquivos do %s já estão na raiz do zip." % nome)
        guarda = os.path.join(raiz, "backup", "originais")
        os.makedirs(guarda, exist_ok=True)
        copia = os.path.join(guarda, "%s (%s)%s" % (os.path.splitext(nome)[0], time.strftime("%Y-%m-%d_%H%M%S"),
                                                    os.path.splitext(nome)[1]))
        novo = caminho + ".refazendo"
        prefixo = pasta_de_dentro + "/"
        try:
            with zipfile.ZipFile(caminho) as velho, zipfile.ZipFile(novo, "w", zipfile.ZIP_DEFLATED,
                                                                    compresslevel=1) as refeito:
                for item in velho.infolist():
                    caminho_dentro = item.filename.replace("\\", "/")
                    if item.is_dir() or not caminho_dentro.startswith(prefixo):
                        continue
                    resto = caminho_dentro[len(prefixo):]
                    if not resto or any(p in ("", ".", "..") or ":" in p for p in resto.split("/")):
                        continue
                    with velho.open(item) as de, refeito.open(resto, "w") as para:
                        shutil.copyfileobj(de, para)
            shutil.copy2(caminho, copia)
            os.replace(novo, caminho)
        except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as falha:
            if os.path.exists(novo):
                os.remove(novo)
            raise NaoDa("Não consegui refazer o %s (%s). Nada foi mudado." % (nome, falha))
        return ("Pronto: o %s foi refeito com os arquivos na raiz. O original está em %s."
                % (nome, os.path.relpath(copia, raiz)), None)
    raise NaoDa("Não sei arrumar isso.")


# ---------------------------------------------------------------------------
# A pasta do disco que falta (depois que o MAME diz o nome)
# ---------------------------------------------------------------------------

def pasta_do_disco(caminho_zip, discos, pasta_jogos):
    """O MAME disse que falta o disco ("kinst.chd NOT FOUND"): cria a pasta
    onde ele vai (Arcade\\kinst, ao lado do kinst.zip) com um LEIA dizendo o
    que por la, para quem nao sabe ver onde. Devolve a pasta criada, ou None."""
    pasta = os.path.dirname(caminho_zip)
    romset = os.path.splitext(os.path.basename(caminho_zip))[0]
    if not discos or not _dentro(pasta, pasta_jogos) or os.path.basename(pasta).lower() == romset.lower():
        return None
    destino = os.path.join(pasta, romset)
    try:
        os.makedirs(destino, exist_ok=True)
        leia = os.path.join(destino, "LEIA.txt")
        texto = ("Ponha aqui o disco deste jogo: %s.\r\n"
                 "O jogo de fliperama abre pelo %s (na pasta de cima); o disco fica nesta\r\n"
                 "pasta, que tem o mesmo nome do zip. Depois, clique em Atualizar lista.\r\n"
                 % (", ".join(discos), os.path.basename(caminho_zip)))
        if not os.path.exists(leia):
            with open(leia, "w", encoding="utf-8-sig", newline="") as arquivo:
                arquivo.write(texto)
    except OSError:
        return None
    return destino


# ---------------------------------------------------------------------------
# Jogo de CD dentro de .zip: descompactar (demora: em segundo plano)
# ---------------------------------------------------------------------------

# O que e' disco (de CD, DVD ou GD-ROM) dentro de um zip.
EXTENSOES_DE_DISCO = (".cue", ".bin", ".img", ".iso", ".chd", ".gdi", ".cdi", ".ccd", ".sub", ".mds", ".mdf",
                      ".pbp", ".cso", ".ecm", ".m3u", ".toc", ".raw", ".rvz", ".wbfs", ".gcm", ".wia", ".nrg")
DEMORADAS = ("descompactar", "extrair_disco")
# Folga de espaco alem do tamanho descompactado (o pen drive nao pode encher).
FOLGA = 64 * 1024 * 1024

_trava_tarefas = threading.Lock()
_tarefas = {}        # id -> {"estado", "feito", "total", "mensagem", "jogo"}


def discos_do_zip(caminho):
    """Os itens de disco dentro do zip ([ZipInfo]), ou [] (nao abre, ou nao tem)."""
    try:
        with zipfile.ZipFile(caminho) as z:
            return [i for i in z.infolist() if not i.is_dir()
                    and os.path.splitext(i.filename)[1].lower() in EXTENSOES_DE_DISCO]
    except (OSError, zipfile.BadZipFile, ValueError):
        return []


def pasta_do_descompactado(caminho):
    """Onde o jogo de dentro do zip vai: uma pasta com o nome do zip, ao lado."""
    return os.path.splitext(caminho)[0]


def precisa_descompactar(caminho, tipo_do_console):
    """Jogo de CD num .zip, num console que nao abre zip de CD ('disco' ou
    'externo', do servidor\\como_colocar.py) e ainda nao descompactado."""
    if not caminho.lower().endswith(".zip") or tipo_do_console not in ("disco", "externo"):
        return False
    if os.path.isdir(pasta_do_descompactado(caminho)):
        return False
    return bool(discos_do_zip(caminho))


def _partes_seguras(nome):
    """As partes do caminho de um item do zip, ou None se ele tentar sair da
    pasta (../, C:, caminho absoluto)."""
    partes = [p for p in nome.replace("\\", "/").split("/") if p not in ("", ".")]
    if not partes or any(p == ".." or ":" in p for p in partes) or nome.startswith(("/", "\\")):
        return None
    return partes


def _nova_tarefa(jogo):
    numero = uuid.uuid4().hex[:12]
    with _trava_tarefas:
        _tarefas[numero] = {"estado": "rodando", "feito": 0, "total": 0, "mensagem": "", "jogo": jogo}
        # So guarda as 20 mais novas.
        for velha in list(_tarefas)[:-20]:
            if _tarefas[velha]["estado"] != "rodando":
                del _tarefas[velha]
    return numero


def _atualizar(numero, **campos):
    with _trava_tarefas:
        _tarefas[numero].update(campos)


def progresso(numero):
    with _trava_tarefas:
        tarefa = _tarefas.get(numero)
        return dict(tarefa) if tarefa else None


def _extrair(numero, caminho_zip, itens, pasta_final, tirar_prefixo):
    """Extrai os itens para pasta_final, por uma pasta temporaria ao lado (o
    jogo so aparece inteiro: puxar o pen drive no meio nao deixa meio jogo)."""
    temporaria = pasta_final + ".descompactando"
    try:
        if os.path.isdir(temporaria):
            shutil.rmtree(temporaria)
        os.makedirs(temporaria)
        with zipfile.ZipFile(caminho_zip) as z:
            for item in itens:
                partes = _partes_seguras(item.filename)
                if not partes:
                    continue
                if tirar_prefixo and partes[0] == tirar_prefixo and len(partes) > 1:
                    partes = partes[1:]
                destino = os.path.join(temporaria, *partes)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with z.open(item) as de, open(destino, "wb") as para:
                    while True:
                        bloco = de.read(1024 * 1024)
                        if not bloco:
                            break
                        para.write(bloco)
                        with _trava_tarefas:
                            _tarefas[numero]["feito"] += len(bloco)
        if os.path.exists(pasta_final):
            # Alguem criou a pasta enquanto descompactava: junta o que falta.
            for atual, _subpastas, arquivos in os.walk(temporaria):
                for nome in arquivos:
                    origem = os.path.join(atual, nome)
                    alvo = os.path.join(pasta_final, os.path.relpath(origem, temporaria))
                    if not os.path.exists(alvo):
                        os.makedirs(os.path.dirname(alvo), exist_ok=True)
                        os.replace(origem, alvo)
            shutil.rmtree(temporaria, ignore_errors=True)
        else:
            os.replace(temporaria, pasta_final)
        return True, ""
    except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as falha:
        shutil.rmtree(temporaria, ignore_errors=True)
        return False, str(falha)


def _conferir_espaco(pasta, total):
    try:
        livre = shutil.disk_usage(pasta).free
    except OSError:
        return
    if livre < total + FOLGA:
        raise NaoDa("Não cabe: descompactado, o jogo ocupa %.0f MB, e só há %.0f MB livres. Libere espaço "
                    "(ou apague o .zip depois de descompactar em outro computador)."
                    % (total / 1048576.0, livre / 1048576.0))


def iniciar(acao, caminho, pasta_jogos, aoterminar=None, disco_zipado=None):
    """Comeca uma das DEMORADAS em segundo plano. Devolve (numero da tarefa,
    mensagem). 'aoterminar': chamado no fim (o servidor refaz a lista).
    'disco_zipado': no extrair_disco, o zip que tem o .chd dentro."""
    if not _dentro(caminho, pasta_jogos) or not os.path.exists(caminho):
        raise NaoDa("O arquivo do jogo não está mais no lugar. Clique em Atualizar lista.")
    nome = os.path.basename(caminho)
    try:
        return _iniciar(acao, caminho, nome, pasta_jogos, aoterminar, disco_zipado)
    except (zipfile.BadZipFile, ValueError, RuntimeError):
        raise NaoDa("O .zip está danificado: não consegui ler o que tem dentro.")


def _iniciar(acao, caminho, nome, pasta_jogos, aoterminar, disco_zipado):
    if acao == "descompactar":
        itens_disco = discos_do_zip(caminho)
        if not itens_disco:
            raise NaoDa("Não achei jogo de CD dentro do %s." % nome)
        pasta_final = pasta_do_descompactado(caminho)
        if os.path.isdir(pasta_final):
            raise NaoDa("Já existe a pasta %s: o jogo já foi descompactado." % os.path.basename(pasta_final))
        with zipfile.ZipFile(caminho) as z:
            itens = [i for i in z.infolist() if not i.is_dir() and _partes_seguras(i.filename)]
        # Tudo dentro de UMA pasta no zip: sem pasta dentro de pasta.
        primeiras = {_partes_seguras(i.filename)[0] for i in itens}
        prefixo = next(iter(primeiras)) if len(primeiras) == 1 and all(
            len(_partes_seguras(i.filename)) > 1 for i in itens) else None
        origem_zip = caminho
    elif acao == "extrair_disco":
        if not disco_zipado or not _dentro(disco_zipado, pasta_jogos) or not os.path.isfile(disco_zipado):
            raise NaoDa("O zip com o disco não está mais na pasta.")
        romset = os.path.splitext(nome)[0]
        pasta_final = os.path.join(os.path.dirname(caminho), romset)
        with zipfile.ZipFile(disco_zipado) as z:
            itens = [i for i in z.infolist() if i.filename.lower().endswith(".chd") and _partes_seguras(i.filename)]
        if not itens:
            raise NaoDa("Não achei o disco (.chd) dentro do %s." % os.path.basename(disco_zipado))
        if any(os.path.exists(os.path.join(pasta_final, _partes_seguras(i.filename)[-1])) for i in itens):
            raise NaoDa("O disco já está na pasta %s." % romset)
        prefixo = None
        # O .chd fica direto na pasta do romset (sem a pasta que tiver no zip).
        itens_planos = [(item, _partes_seguras(item.filename)[-1]) for item in itens]
        origem_zip = disco_zipado
    else:
        raise NaoDa("Não sei arrumar isso.")
    total = sum(i.file_size for i in itens)
    _conferir_espaco(os.path.dirname(pasta_final), total)
    numero = _nova_tarefa(nome)
    _atualizar(numero, total=total)

    def trabalhar():
        if acao == "extrair_disco":
            ok, erro = True, ""
            try:
                os.makedirs(pasta_final, exist_ok=True)
                with zipfile.ZipFile(origem_zip) as z:
                    for item, nome_do_disco in itens_planos:
                        alvo = os.path.join(pasta_final, nome_do_disco)
                        with z.open(item) as de, open(alvo + ".descompactando", "wb") as para:
                            while True:
                                bloco = de.read(1024 * 1024)
                                if not bloco:
                                    break
                                para.write(bloco)
                                with _trava_tarefas:
                                    _tarefas[numero]["feito"] += len(bloco)
                        os.replace(alvo + ".descompactando", alvo)
            except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as falha:
                ok, erro = False, str(falha)
                for _item, nome_do_disco in itens_planos:      # nada pela metade fica
                    parcial = os.path.join(pasta_final, nome_do_disco) + ".descompactando"
                    if os.path.exists(parcial):
                        os.remove(parcial)
        else:
            ok, erro = _extrair(numero, origem_zip, itens, pasta_final, prefixo)
        if ok:
            _atualizar(numero, estado="pronto",
                       mensagem="Pronto: o jogo está na pasta %s. O %s pode ser apagado, se quiser "
                                "liberar espaço." % (os.path.relpath(pasta_final, pasta_jogos),
                                                     os.path.basename(origem_zip)))
        else:
            _atualizar(numero, estado="erro",
                       mensagem="Não consegui descompactar o %s (%s). Nada pela metade ficou na pasta."
                                % (os.path.basename(origem_zip), erro))
        if aoterminar:
            try:
                aoterminar()
            except Exception:    # noqa: BLE001 -- refazer a lista e' bonus
                pass

    threading.Thread(target=trabalhar, daemon=True).start()
    return numero, "Descompactando o %s... (pode levar alguns minutos)" % os.path.basename(origem_zip)
