# -*- coding: utf-8 -*-
r"""
ARENA - os jogos repetidos (pedido do Rafael, 13/11/2026: "o ARENA deve ser capaz de identificar roms ou jogos
repetidos e poder excluir os mesmos repetidos para facilitar e liberar espaco").

Dois tipos de repetido:
  - IGUAIS: o mesmo arquivo em dois lugares (mesmo tamanho e mesmo conteudo). Um deles basta: o ARENA ja deixa
    marcados para apagar todos menos um (fica o favorito, o jogado por ultimo, ou o do caminho mais curto).
  - MESMO JOGO: o mesmo titulo no mesmo console, com arquivos diferentes (outra regiao, outro formato, outra
    versao). Pode ser de proposito, entao nada vem marcado: quem decide e' a pessoa.

Como compara sem ler o jogo inteiro (um ISO de 4 GB levaria minutos no pen drive do notebook da escola): so os
arquivos de TAMANHO IGUAL sao lidos, e em duas etapas -- primeiro o comeco (64 KB); os que ainda batem, o meio e o
fim. Dois arquivos diferentes praticamente nunca batem no tamanho e nos tres pedacos.

O que NUNCA entra: jogo instalado por loja (Steam...), app do Android, recomp, e o que nao esta numa das pastas de
jogos (jogos\pessoais, jogos\turma, jogos\livres e as pastas do cartao). O que entra mas NAO se apaga por aqui
(aparece com o motivo): jogo numa pasta inteira so dele (PC, PS3), lista de discos (.m3u) e jogo de varios discos.
Jogo de indice (.cue, .gdi) leva as trilhas junto, mas so as que nenhum outro jogo usa.

Apagar: so o que esta na ultima procura, so o que tem uma copia que fica, e nunca todas as copias de um grupo. No
Windows o arquivo vai para a Lixeira (da para desfazer); no pen drive e no cartao o Windows nao tem Lixeira e apaga
de vez, e no Linux e no Android tambem e' de vez -- a tela avisa antes. So biblioteca padrao.
"""
import errno
import hashlib
import os
import re
import shutil
import sys
import threading
import time

PEDACO = 65536
ORIGENS_DE_PASTA = ("pessoais", "turma", "livres")
PREFIXO_DO_CARTAO = "cartao-"
SO_A_LISTA = (".m3u",)                       # lista de discos: os discos sao outros jogos da lista
INDICES = (".cue", ".gdi")
RE_TRILHA_CUE = re.compile(r'^\s*FILE\s+"?(.+?)"?\s+\S+\s*$', re.I | re.M)
RE_TRILHA_GDI = re.compile(r'^\s*\d+\s+\d+\s+\d+\s+\d+\s+("[^"]+"|\S+)')
NOME_DA_LIXEIRA = ".ARENA-lixeira"           # com ponto: a procura de pastas de jogos do cartao pula

# As etiquetas dos conjuntos de ROMs (GoodTools e No-Intro), entre colchetes no nome do arquivo:
#   [!] dump conferido; [b] dump ruim; [o] overdump; [a] dump alternativo; [h] hack; [t1] trainer; [f] consertado;
#   [p] pirata; [T+Por] / [T-Por] traducao (o +/- e' versao nova/velha da traducao).
# Uma copia com etiqueta "ruim" so vem marcada se o grupo tem uma copia LIMPA da mesma regiao (sem etiqueta ruim e
# sem traducao). Traducao e outra regiao nunca vem marcadas; traducao em portugues nunca sai sem a pessoa pedir.
RE_COLCHETE = re.compile(r"\[([^\]]*)\]")
RE_PARENTESE = re.compile(r"\(([^)]*)\)")
RE_RUIM = re.compile(r"^(b|o|a|h|t|f|p)\d*([^+\-].*)?$", re.I)
RE_TRADUCAO = re.compile(r"^T[+\-]\s*([A-Za-z]{2,3})", re.I)
PORTUGUES = ("por", "pt", "bra", "br")


def etiquetas(nome):
    """{"verificado", "ruim", "traducao", "portugues", "regiao"} de um nome de arquivo de ROM."""
    base = os.path.basename(str(nome))
    colchetes = [c.strip() for c in RE_COLCHETE.findall(base)]
    traducoes = [m.group(1).lower() for c in colchetes for m in [RE_TRADUCAO.match(c)] if m]
    ruim = any(RE_RUIM.match(c) and not RE_TRADUCAO.match(c) for c in colchetes if c != "!")
    parenteses = RE_PARENTESE.findall(base)
    return {"verificado": "!" in colchetes, "ruim": ruim, "traducao": bool(traducoes),
            "portugues": any(t.startswith(PORTUGUES) for t in traducoes),
            "regiao": parenteses[0].strip().lower() if parenteses else ""}


def marcar_variantes(itens):
    """No grupo do mesmo jogo: marca as variantes ruins que tem uma copia limpa da mesma regiao, e diz qual fica.
    Devolve quantas marcou."""
    limpas = {}
    for item in itens:
        e = item["_etiquetas"]
        if not e["ruim"] and not e["traducao"]:
            atual = limpas.get(e["regiao"])
            if atual is None or (e["verificado"] and not atual["_etiquetas"]["verificado"]):
                limpas[e["regiao"]] = item
    for item in limpas.values():
        item["fica"] = True
    marcados = 0
    for item in itens:
        e = item["_etiquetas"]
        if item["apagavel"] and e["ruim"] and not e["portugues"] and e["regiao"] in limpas:
            item["marcado"] = True
            marcados += 1
    return marcados


def origem_de_pasta(origem):
    origem = str(origem or "")
    return origem in ORIGENS_DE_PASTA or origem.startswith(PREFIXO_DO_CARTAO)


# ---------------------------------------------------------------------------
# Os arquivos de cada jogo
# ---------------------------------------------------------------------------

def trilhas(caminho):
    """Os arquivos que um .cue ou .gdi cita, ao lado dele (caminhos absolutos). Arquivo citado que falta, fica fora."""
    extensao = os.path.splitext(caminho)[1].lower()
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            texto = arquivo.read(65536)
    except OSError:
        return []
    nomes = []
    if extensao == ".cue":
        nomes = [m.group(1) for m in RE_TRILHA_CUE.finditer(texto)]
    elif extensao == ".gdi":
        for linha in texto.splitlines()[1:]:
            achado = RE_TRILHA_GDI.match(linha)
            if achado:
                nomes.append(achado.group(1).strip('"'))
    pasta = os.path.dirname(caminho)
    saida = []
    for nome in nomes:
        alvo = os.path.join(pasta, os.path.basename(nome.replace("\\", "/")))
        if os.path.isfile(alvo) and alvo not in saida:
            saida.append(alvo)
    return saida


def arquivos_do_jogo(jogo, raiz):
    """(arquivos absolutos do jogo, motivo de nao poder apagar ou ""). O primeiro e' o arquivo da lista."""
    caminho = os.path.normpath(os.path.join(raiz, jogo.get("arquivo") or ""))
    extensao = os.path.splitext(caminho)[1].lower()
    if os.path.isdir(caminho):
        return [], "jogo numa pasta inteira: apague a pasta à mão, se quiser"
    if not os.path.isfile(caminho):
        return [], "o arquivo não está mais lá (atualize a lista)"
    if jogo.get("discos") and len(jogo["discos"]) > 1:
        return [caminho], "jogo de vários discos: apague à mão, se quiser"
    if extensao in SO_A_LISTA:
        return [caminho], "lista de discos (.m3u): apague à mão, se quiser"
    arquivos = [caminho]
    if extensao in INDICES:
        arquivos += [t for t in trilhas(caminho) if os.path.normcase(t) != os.path.normcase(caminho)]
    return arquivos, ""


def _tamanho(arquivos):
    total = 0
    for caminho in arquivos:
        try:
            total += os.path.getsize(caminho)
        except OSError:
            pass
    return total


def _pedaco(caminho, onde, tamanho):
    with open(caminho, "rb") as arquivo:
        if onde == "comeco":
            return arquivo.read(PEDACO)
        if onde == "meio":
            arquivo.seek(max(0, tamanho // 2 - PEDACO // 2))
            return arquivo.read(PEDACO)
        arquivo.seek(max(0, tamanho - PEDACO))
        return arquivo.read(PEDACO)


def marca(arquivos, etapa):
    """Marca do conteudo do jogo: etapa 1 = o comeco de cada arquivo; etapa 2 = o meio e o fim. None se nao leu."""
    resumo = hashlib.sha1()
    try:
        for caminho in sorted(arquivos, key=lambda c: os.path.getsize(c), reverse=True):
            tamanho = os.path.getsize(caminho)
            resumo.update(str(tamanho).encode())
            partes = ("comeco",) if etapa == 1 else ("meio", "fim")
            for onde in partes:
                resumo.update(_pedaco(caminho, onde, tamanho))
    except OSError:
        return None
    return resumo.hexdigest()


# ---------------------------------------------------------------------------
# A procura
# ---------------------------------------------------------------------------

def _caminho_curto(raiz, caminho):
    try:
        return os.path.relpath(caminho, raiz)
    except ValueError:              # outra unidade no Windows
        return caminho


def _quem_fica(itens, favoritos, recentes):
    """O que fica num grupo de iguais: o favorito, o jogado por ultimo, depois o caminho mais curto (o que esta direto
    na pasta do console, em vez de uma subpasta de downloads)."""
    def chave(item):
        recente = recentes.index(item["id"]) if item["id"] in recentes else len(recentes)
        return (0 if item["id"] in favoritos else 1, recente, item["arquivo"].count(os.sep) + item["arquivo"].count("/"),
                len(item["arquivo"]), item["arquivo"].lower())
    return min(itens, key=chave)


def procurar(jogos, raiz, favoritos=(), recentes=(), progresso=lambda feitos, total: None, parar=lambda: False):
    """{"iguais": [grupo], "mesmo_jogo": [grupo], "livra_bytes": n}. Grupo: {"titulo", "plataforma_nome",
    "livra_bytes", "itens": [{id, titulo, arquivo, plataforma_nome, origem_rotulo, bytes, apagavel, motivo, marcado,
    fica}]}. 'jogos': o catalogo (manifesto)."""
    favoritos, recentes = set(favoritos or ()), list(recentes or ())
    candidatos = []
    for jogo in jogos:
        if not origem_de_pasta(jogo.get("origem")):
            continue
        arquivos, motivo = arquivos_do_jogo(jogo, raiz)
        if not arquivos:
            continue
        # O que se compara: num .cue/.gdi, so as trilhas (o indice cita o nome delas, e duas copias do mesmo jogo
        # com nomes diferentes teriam o indice diferente).
        indice = len(arquivos) > 1 and os.path.splitext(arquivos[0])[1].lower() in INDICES
        conteudo = arquivos[1:] if indice else arquivos
        candidatos.append({"jogo": jogo, "arquivos": arquivos, "conteudo": conteudo, "motivo": motivo,
                           "bytes": _tamanho(arquivos), "bytes_conteudo": _tamanho(conteudo)})

    # IGUAIS: tamanho igual -> comeco igual -> meio e fim iguais
    por_tamanho = {}
    for c in candidatos:
        if c["bytes_conteudo"] > 0:
            por_tamanho.setdefault(c["bytes_conteudo"], []).append(c)
    suspeitos = [lista for lista in por_tamanho.values() if len(lista) > 1]
    total = sum(len(lista) for lista in suspeitos)
    feitos = 0
    grupos_iguais = []
    for lista in suspeitos:
        por_comeco = {}
        for c in lista:
            if parar():
                return None
            m = marca(c["conteudo"], 1)
            feitos += 1
            progresso(feitos, total)
            if m:
                por_comeco.setdefault(m, []).append(c)
        for mesmos in por_comeco.values():
            if len(mesmos) < 2:
                continue
            por_resto = {}
            for c in mesmos:
                m = marca(c["conteudo"], 2)
                if m:
                    por_resto.setdefault(m, []).append(c)
            grupos_iguais += [g for g in por_resto.values() if len(g) > 1]

    def item(c, grupo_iguais):
        jogo = c["jogo"]
        return {"id": jogo["id"], "titulo": jogo.get("titulo", ""), "arquivo": _caminho_curto(raiz, c["arquivos"][0]),
                "plataforma_nome": jogo.get("plataforma_nome", ""), "origem_rotulo": jogo.get("origem_rotulo", ""),
                "bytes": c["bytes"], "arquivos": len(c["arquivos"]), "apagavel": not c["motivo"],
                "motivo": c["motivo"], "marcado": False, "fica": False, "_iguais": grupo_iguais,
                "_etiquetas": etiquetas(c["arquivos"][0])}

    saida_iguais, ja_em_iguais = [], set()
    for grupo in grupos_iguais:
        itens = [item(c, True) for c in grupo]
        fica = _quem_fica(itens, favoritos, recentes)
        for i in itens:
            i["fica"] = i is fica
            i["marcado"] = i["apagavel"] and i is not fica
            ja_em_iguais.add(i["id"])
        saida_iguais.append({"tipo": "iguais", "titulo": fica["titulo"], "plataforma_nome": fica["plataforma_nome"],
                             "livra_bytes": sum(i["bytes"] for i in itens if i["marcado"]), "itens": itens})

    # MESMO JOGO: mesmo titulo no mesmo console, arquivos diferentes. So as variantes ruins com copia limpa da mesma
    # regiao vem marcadas (marcar_variantes); o resto, quem decide e' a pessoa.
    por_titulo = {}
    for c in candidatos:
        jogo = c["jogo"]
        chave = (jogo.get("plataforma"), jogo.get("ordenacao") or str(jogo.get("titulo", "")).lower())
        por_titulo.setdefault(chave, []).append(c)
    saida_mesmo = []
    for lista in por_titulo.values():
        diferentes = [c for c in lista if c["jogo"]["id"] not in ja_em_iguais]
        if len(lista) < 2 or len(diferentes) < 2:
            continue
        itens = [item(c, False) for c in lista]
        marcar_variantes(itens)
        saida_mesmo.append({"tipo": "mesmo_jogo", "titulo": itens[0]["titulo"],
                            "plataforma_nome": itens[0]["plataforma_nome"],
                            "livra_bytes": sum(i["bytes"] for i in itens if i["marcado"]), "itens": itens})

    for grupo in saida_iguais + saida_mesmo:
        for i in grupo["itens"]:
            i.pop("_iguais", None)
            i.pop("_etiquetas", None)
    saida_iguais.sort(key=lambda g: -g["livra_bytes"])
    saida_mesmo.sort(key=lambda g: (g["plataforma_nome"], g["titulo"].lower()))
    return {"iguais": saida_iguais, "mesmo_jogo": saida_mesmo,
            "livra_bytes": sum(g["livra_bytes"] for g in saida_iguais + saida_mesmo)}


# ---------------------------------------------------------------------------
# Apagar
# ---------------------------------------------------------------------------

def _unidade_removivel(caminho):
    """No Windows: o arquivo esta num pen drive ou cartao (sem Lixeira)?"""
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        unidade = os.path.splitdrive(os.path.abspath(caminho))[0] + "\\"
        return ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(unidade)) == 2   # DRIVE_REMOVABLE
    except (AttributeError, OSError):
        return False


def vai_para_a_lixeira(caminho):
    return sys.platform.startswith("win") and not _unidade_removivel(caminho)


def _para_a_lixeira(caminhos):
    """Windows: manda para a Lixeira pelo SHFileOperationW (o mesmo do Explorador, sem janela). True se foi."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", ctypes.c_uint), ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

    FO_DELETE, FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 3, 0x4, 0x10, 0x40, 0x400
    lista = "\0".join(os.path.abspath(c) for c in caminhos) + "\0\0"
    operacao = SHFILEOPSTRUCTW(None, FO_DELETE, lista, None,
                               FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI, False, None, None)
    funcao = ctypes.windll.shell32.SHFileOperationW
    funcao.argtypes = [ctypes.POINTER(SHFILEOPSTRUCTW)]
    funcao.restype = ctypes.c_int
    return funcao(ctypes.byref(operacao)) == 0 and not operacao.fAnyOperationsAborted


def pasta_da_lixeira(origem_real):
    """A Lixeira do ARENA de uma pasta de jogos: ao lado dela, no mesmo disco ou cartao (mover e' so renomear)."""
    return os.path.join(os.path.dirname(origem_real), NOME_DA_LIXEIRA, os.path.basename(origem_real))


def _mover(de, para):
    os.makedirs(os.path.dirname(para), exist_ok=True)
    base, extensao = os.path.splitext(para)
    n = 2
    while os.path.exists(para):
        para = "%s (%d)%s" % (base, n, extensao)
        n += 1
    try:
        os.replace(de, para)
    except OSError as falha:
        if falha.errno != errno.EXDEV:
            raise
        shutil.move(de, para)          # outro disco (raro: o atalho da origem aponta para outro lugar)
    return para


def para_a_lixeira_do_arena(arquivos, origem_real):
    """Move os arquivos do jogo para a Lixeira do ARENA, guardando o caminho dentro da pasta de jogos (o Devolver
    poe cada um de volta no lugar)."""
    lixeira = pasta_da_lixeira(origem_real)
    for caminho in arquivos:
        real = os.path.realpath(caminho)
        relativo = os.path.relpath(real, origem_real)
        if relativo.startswith(".."):
            relativo = os.path.basename(real)
        _mover(real, os.path.join(lixeira, relativo))


def lixeiras(pasta_dos_jogos, origens):
    """[{pasta, arquivos, bytes}] das Lixeiras do ARENA que tem alguma coisa, uma por pasta de jogos."""
    saida, vistas = [], set()
    for origem in origens:
        real = os.path.realpath(os.path.join(pasta_dos_jogos, origem))
        pasta = pasta_da_lixeira(real)
        if pasta in vistas or not os.path.isdir(pasta):
            continue
        vistas.add(pasta)
        arquivos, total = 0, 0
        for atual, _subpastas, nomes in os.walk(pasta):
            for nome in nomes:
                arquivos += 1
                try:
                    total += os.path.getsize(os.path.join(atual, nome))
                except OSError:
                    pass
        if arquivos:
            saida.append({"pasta": pasta, "origem_real": real, "arquivos": arquivos, "bytes": total})
    return saida


def devolver_da_lixeira(lixeira):
    """Poe cada arquivo da Lixeira do ARENA de volta no lugar. Devolve (devolvidos, erros)."""
    devolvidos, erros = 0, []
    for atual, _subpastas, nomes in os.walk(lixeira["pasta"]):
        for nome in nomes:
            de = os.path.join(atual, nome)
            para = os.path.join(lixeira["origem_real"], os.path.relpath(de, lixeira["pasta"]))
            try:
                _mover(de, para)
                devolvidos += 1
            except OSError as falha:
                erros.append("%s: %s" % (nome, getattr(falha, "strerror", None) or falha))
    _tirar_pastas_vazias(lixeira["pasta"])
    return devolvidos, erros


def esvaziar_lixeira(lixeira):
    """Apaga de vez o que esta na Lixeira do ARENA. Devolve (bytes, erros)."""
    total, erros = 0, []
    for atual, _subpastas, nomes in os.walk(lixeira["pasta"]):
        for nome in nomes:
            caminho = os.path.join(atual, nome)
            try:
                tamanho = os.path.getsize(caminho)
                os.remove(caminho)
                total += tamanho
            except OSError as falha:
                erros.append("%s: %s" % (nome, getattr(falha, "strerror", None) or falha))
    _tirar_pastas_vazias(lixeira["pasta"])
    return total, erros


def _tirar_pastas_vazias(pasta):
    for atual, _subpastas, _nomes in sorted(os.walk(pasta), reverse=True):
        try:
            os.rmdir(atual)
        except OSError:
            pass
    try:
        os.rmdir(os.path.dirname(pasta))      # a .ARENA-lixeira, se ficou vazia
    except OSError:
        pass


def apagar(pedidos, resultado, jogos, raiz, apagar_arquivo=None, pasta_dos_jogos=None):
    """Apaga os jogos pedidos (ids) que estao na ultima procura ('resultado'), so os apagaveis e nunca todas as copias
    de um grupo. No Windows (disco interno) vai para a Lixeira dele; no resto (celular, Linux, pen drive), para a
    Lixeira do ARENA (pasta_da_lixeira), que a pessoa esvazia ou devolve depois. Devolve {"apagados": [titulo],
    "erros": [texto], "bytes": n, "lixeira": "windows" | "arena" | ""}.
    'apagar_arquivo(caminhos)' troca o jeito de apagar (os testes usam)."""
    pasta_dos_jogos = pasta_dos_jogos or os.path.join(raiz, "jogos")
    pedidos = {str(p) for p in pedidos or ()}
    por_id = {j["id"]: j for j in jogos}
    permitidos = set()
    for grupo in (resultado or {}).get("iguais", []) + (resultado or {}).get("mesmo_jogo", []):
        ids = [i["id"] for i in grupo["itens"]]
        escolhidos = [i for i in grupo["itens"] if i["id"] in pedidos and i["apagavel"]]
        if escolhidos and len([i for i in ids if i not in {e["id"] for e in escolhidos}]) == 0:
            # todas as copias marcadas: a que ficaria pela regra fica
            fica = next((i for i in grupo["itens"] if i["fica"]), grupo["itens"][0])
            escolhidos = [e for e in escolhidos if e["id"] != fica["id"]]
        permitidos.update(e["id"] for e in escolhidos)

    apagados, erros, total, lixeira = [], [], 0, None
    usados_por_outros = set()
    for jogo in jogos:          # trilha que outro jogo (que fica) tambem usa nao sai
        if jogo["id"] in permitidos or not origem_de_pasta(jogo.get("origem")):
            continue
        arquivos, _motivo = arquivos_do_jogo(jogo, raiz)
        usados_por_outros.update(os.path.normcase(a) for a in arquivos)
    for identificador in sorted(permitidos):
        jogo = por_id.get(identificador)
        if not jogo:
            continue
        arquivos, motivo = arquivos_do_jogo(jogo, raiz)
        if motivo or not arquivos:
            erros.append("%s: %s" % (jogo.get("titulo", ""), motivo or "não achei o arquivo"))
            continue
        arquivos = [a for a in arquivos if os.path.normcase(a) not in usados_por_outros]
        tamanho = _tamanho(arquivos)
        try:
            if apagar_arquivo:
                apagar_arquivo(arquivos)
                lixeira = lixeira or ""
            elif vai_para_a_lixeira(arquivos[0]):
                if not _para_a_lixeira(arquivos):
                    raise OSError("o Windows não deixou mandar para a Lixeira")
                lixeira = lixeira or "windows"
            else:
                para_a_lixeira_do_arena(arquivos, os.path.realpath(os.path.join(pasta_dos_jogos, jogo["origem"])))
                lixeira = lixeira or "arena"
            apagados.append(jogo.get("titulo", ""))
            total += tamanho
        except OSError as falha:
            erros.append("%s: %s" % (jogo.get("titulo", ""), getattr(falha, "strerror", None) or str(falha)))
    return {"apagados": apagados, "erros": erros, "bytes": total, "lixeira": lixeira or ""}


# ---------------------------------------------------------------------------
# A procura em segundo plano (a tela pergunta o andamento)
# ---------------------------------------------------------------------------

class Procura:
    def __init__(self):
        self.trava = threading.Lock()
        self._estado = {"rodando": False, "feitos": 0, "total": 0, "resultado": None, "erro": "", "feita_em": None}

    def estado(self):
        with self.trava:
            return dict(self._estado)

    def resultado(self):
        with self.trava:
            return self._estado["resultado"]

    def esquecer(self):
        with self.trava:
            if not self._estado["rodando"]:
                self._estado["resultado"] = None

    def comecar(self, jogos, raiz, favoritos=(), recentes=()):
        with self.trava:
            if self._estado["rodando"]:
                return False
            self._estado = {"rodando": True, "feitos": 0, "total": 0, "resultado": None, "erro": "", "feita_em": None}
        threading.Thread(target=self._rodar, args=(list(jogos), raiz, list(favoritos), list(recentes)),
                         daemon=True, name="arena-repetidos").start()
        return True

    def _progresso(self, feitos, total):
        with self.trava:
            self._estado["feitos"], self._estado["total"] = feitos, total

    def _rodar(self, jogos, raiz, favoritos, recentes):
        resultado, erro = None, ""
        try:
            resultado = procurar(jogos, raiz, favoritos, recentes, self._progresso)
        except Exception as falha:          # noqa: BLE001 -- vira recado na tela, nunca derruba o servidor
            erro = "Não consegui terminar a procura (%s). Tente de novo." % type(falha).__name__
        with self.trava:
            self._estado.update(rodando=False, resultado=resultado, erro=erro, feita_em=time.time())
