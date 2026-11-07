# -*- coding: utf-8 -*-
r"""
ARENA - a pasta de jogos do ARENA no cartao SD, e levar para ela os jogos da memoria do aparelho.

Pedido do Rafael (07/11/2026): "deve ter um recurso para criar uma pasta no cartao sd para o aluno sempre onde salvar
os jogos que baixou, e como o ARENA ja identifica [os jogos] em qualquer [lugar], se quiser ele move os jogos de onde
estiver no armazenamento interno [...] para a pasta de jogos criada pelo ARENA no SD".

O QUE FAZ:
  1. criar_no_cartao(): cria <cartao>\ARENA-jogos com uma pasta por console (a mesma arrumacao de jogos\pessoais) e a
     poe na lista de pastas de jogos do cartao (servidor\armazenamento.py), como "Jogos do ARENA no cartao". Ela passa a
     ser o destino dos jogos baixados ("Levar para o ARENA").
  2. jogos_na_memoria(): os jogos de "Meus jogos" e "Da turma" que moram na memoria do aparelho, com o tamanho.
  3. Mudanca: leva os jogos escolhidos para o cartao, um por vez, numa thread a parte. Cada arquivo e' COPIADO com
     outro nome, CONFERIDO pelo tamanho e so entao trocado para o nome certo; o original so e' apagado depois que o
     jogo inteiro chegou. Se faltar espaco, o cartao sair ou der erro, o original fica onde estava.

O JOGO INTEIRO VAI JUNTO: jogo numa pasta so dele (PS1\Crash\...) leva a pasta; jogo solto na pasta do console leva os
arquivos com o mesmo nome (Crash.cue + Crash.bin, Zelda.sfc + Zelda.srm) e as trilhas que o .cue/.gdi/.m3u citam.
Os saves ficam no lugar deles (retroarch\saves): o RetroArch os acha pelo nome do arquivo, que nao muda.

So biblioteca padrao; nunca levanta para a tela (devolve o que fazer, em portugues).
"""
import os
import re
import threading
import time

import armazenamento

NOME_DA_PASTA = "ARENA-jogos"
NOME_NA_LISTA = "Jogos do ARENA no cartão"
LEIA = ("Pasta de jogos do ARENA neste cartao de memoria.\n\n"
        "Ponha cada jogo na pasta do console dele (Super Nintendo, PS1, Dreamcast...). O ARENA do celular le esta\n"
        "pasta sozinho e guarda aqui os jogos que voce baixa. Nao renomeie as pastas dos consoles.\n")
ORIGENS_DA_MEMORIA = ("pessoais", "turma")        # "livres" vem com o ARENA: fica onde esta
BLOCO = 4 * 1024 * 1024
FOLGA_MB = 64                                     # nunca encher o cartao ate o ultimo byte
RE_TRILHA_DO_CUE = re.compile(r'^\s*FILE\s+"?(.+?)"?\s+\S+\s*$', re.I | re.M)


class NaoPode(Exception):
    """Algo que a pessoa precisa resolver (a mensagem diz o que fazer)."""


# ---------------------------------------------------------------------------
# A pasta no cartao
# ---------------------------------------------------------------------------

def pasta_no_cartao(dados=None):
    """O caminho da pasta ARENA-jogos que esta na lista e no aparelho agora, ou None."""
    dados = armazenamento.ler() if dados is None else dados
    for extra in dados["jogos_extras"]:
        if os.path.basename(os.path.normpath(extra["caminho"])) == NOME_DA_PASTA and os.path.isdir(extra["caminho"]):
            return extra["caminho"]
    return None


def criar_no_cartao(raiz_do_cartao, consoles, raizes=None, proprias=None):
    """Cria <cartao>/ARENA-jogos (com uma pasta por console) e poe na lista. Devolve o caminho.
    Se ja existe, so completa as pastas que faltam e confere que esta na lista."""
    if not raiz_do_cartao or not os.path.isdir(raiz_do_cartao):
        raise NaoPode("O cartão de memória não está no aparelho agora. Encaixe o cartão e tente de novo.")
    pasta = os.path.join(raiz_do_cartao, NOME_DA_PASTA)
    try:
        os.makedirs(pasta, exist_ok=True)
        for nome in consoles:
            os.makedirs(os.path.join(pasta, nome), exist_ok=True)
        leia = os.path.join(pasta, "LEIA.txt")
        if not os.path.isfile(leia):
            with open(leia, "w", encoding="utf-8") as arquivo:
                arquivo.write(LEIA)
    except OSError as falha:
        raise NaoPode("O cartão não deixou criar a pasta (%s). Confira se ele não está travado contra gravação e se "
                      "o ARENA tem a permissão de arquivos." % (falha.strerror or falha))
    if not any(os.path.realpath(e["caminho"]) == os.path.realpath(pasta) for e in armazenamento.ler()["jogos_extras"]):
        minusculos = {c.replace("\\", "/").split("/")[-1].lower() for c in consoles}
        _dados, erro = armazenamento.adicionar(pasta, raizes=raizes, nome=NOME_NA_LISTA, consoles=minusculos,
                                               proprias=proprias)
        if erro:
            raise NaoPode(erro)
    return os.path.realpath(pasta)


def pastas_dos_consoles(arquivo_de_consoles=None):
    """Os nomes das pastas de console como o ARENA as cria em jogos/pessoais ("Super Nintendo", "PS1"...), do
    consoles.json. A lista do armazenamento.nomes_de_pastas_de_console vem em minusculas: serve para comparar, nao
    para criar pasta."""
    import json
    try:
        with open(arquivo_de_consoles or armazenamento.ARQUIVO_DE_CONSOLES, encoding="utf-8") as arquivo:
            plataformas = json.load(arquivo).get("plataformas", [])
    except (OSError, ValueError):
        return []
    nomes = []
    for plataforma in plataformas:
        pasta = str(plataforma.get("pasta") or "").replace("\\", "/").strip("/")
        if pasta and ".." not in pasta.split("/") and pasta not in nomes:
            nomes.append(pasta)
    return nomes


# ---------------------------------------------------------------------------
# Que arquivos sao do jogo
# ---------------------------------------------------------------------------

def _citados(indice):
    """As trilhas que um .cue/.gdi/.m3u cita (so o nome, na mesma pasta)."""
    try:
        with open(indice, "rb") as arquivo:
            texto = arquivo.read(65536).decode("utf-8", "replace")
    except OSError:
        return []
    extensao = os.path.splitext(indice)[1].lower()
    if extensao == ".cue":
        nomes = RE_TRILHA_DO_CUE.findall(texto)
    elif extensao == ".m3u":
        nomes = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]
    elif extensao == ".gdi":
        nomes = []
        for linha in texto.splitlines()[1:]:
            partes = re.findall(r'"[^"]+"|\S+', linha)
            if len(partes) >= 5:
                nomes.append(partes[4].strip('"'))
    else:
        return []
    return [os.path.basename(n.replace("\\", "/")) for n in nomes]


def arquivos_do_jogo(caminho_do_jogo, pasta_do_console):
    """(pasta_de_cima, [arquivos relativos a ela]) que formam o jogo. Jogo numa pasta so dele: a pasta inteira (a
    pasta_de_cima e' a do console e os arquivos vem com o nome da pasta do jogo na frente)."""
    caminho_do_jogo = os.path.abspath(caminho_do_jogo)
    pasta_do_console = os.path.abspath(pasta_do_console)
    pasta = os.path.dirname(caminho_do_jogo)
    if os.path.normcase(pasta) != os.path.normcase(pasta_do_console):
        # numa pasta so dele: leva a primeira pasta abaixo da do console, inteira
        relativo = os.path.relpath(caminho_do_jogo, pasta_do_console).replace("\\", "/").split("/")
        topo = os.path.join(pasta_do_console, relativo[0])
        lista = []
        for atual, _subpastas, arquivos in os.walk(topo):
            for nome in arquivos:
                lista.append(os.path.relpath(os.path.join(atual, nome), pasta_do_console))
        return pasta_do_console, sorted(lista)
    base = os.path.splitext(os.path.basename(caminho_do_jogo))[0].casefold()
    try:
        vizinhos = os.listdir(pasta)
    except OSError:
        vizinhos = []
    juntos = {os.path.basename(caminho_do_jogo)}
    juntos.update(n for n in vizinhos if os.path.splitext(n)[0].casefold() == base
                  and os.path.isfile(os.path.join(pasta, n)))
    for nome in list(juntos):
        if os.path.splitext(nome)[1].lower() in (".cue", ".gdi", ".m3u"):
            for citado in _citados(os.path.join(pasta, nome)):
                if citado in vizinhos:
                    juntos.add(citado)
    return pasta, sorted(juntos)


def _tamanho(pasta, nomes):
    total = 0
    for nome in nomes:
        try:
            total += os.path.getsize(os.path.join(pasta, nome))
        except OSError:
            pass
    return total


# ---------------------------------------------------------------------------
# Os jogos da memoria do aparelho
# ---------------------------------------------------------------------------

def jogos_na_memoria(jogos, raiz, pasta_dos_jogos, raizes=None):
    """[{id, titulo, console, bytes}] dos jogos de Meus jogos e Da turma que estao na memoria do aparelho (nao no
    cartao), com o tamanho do jogo inteiro. 'jogos': o catalogo (manifesto)."""
    saida = []
    for jogo in jogos:
        if jogo.get("origem") not in ORIGENS_DA_MEMORIA:
            continue
        caminho = os.path.join(raiz, jogo["arquivo"])
        indice = armazenamento.volume_da_pasta(caminho, raizes)
        if indice != 0:                        # ja esta num cartao (ou fora dos volumes conhecidos)
            continue
        console = _pasta_do_console(caminho, os.path.join(pasta_dos_jogos, jogo["origem"]))
        if not console:
            continue
        pasta, nomes = arquivos_do_jogo(caminho, console)
        saida.append({"id": jogo["id"], "titulo": jogo.get("titulo", ""), "console": os.path.basename(console),
                      "bytes": _tamanho(pasta, nomes)})
    return saida


def _pasta_do_console(caminho_do_jogo, pasta_da_origem):
    """A pasta do console (primeira abaixo da origem) do jogo, ou None se o jogo esta solto na origem."""
    relativo = os.path.relpath(os.path.abspath(caminho_do_jogo), os.path.abspath(pasta_da_origem)).replace("\\", "/")
    partes = relativo.split("/")
    if len(partes) < 2 or partes[0] in ("..", ""):
        return None
    return os.path.join(pasta_da_origem, partes[0])


# ---------------------------------------------------------------------------
# Levar um jogo (copiar, conferir, trocar o nome e so entao apagar o original)
# ---------------------------------------------------------------------------

def _copiar(origem, destino, progresso):
    parcial = destino + ".arena-parcial"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    try:
        with open(origem, "rb") as de, open(parcial, "wb") as para:
            while True:
                pedaco = de.read(BLOCO)
                if not pedaco:
                    break
                para.write(pedaco)
                progresso(len(pedaco))
            para.flush()
            os.fsync(para.fileno())
        if os.path.getsize(parcial) != os.path.getsize(origem):
            raise OSError("o tamanho da cópia não bate com o do original")
        os.replace(parcial, destino)
    except BaseException:
        try:
            os.remove(parcial)
        except OSError:
            pass
        raise


def levar_jogo(caminho_do_jogo, pasta_do_console, destino_do_console, progresso=lambda n: None):
    """Leva o jogo (todos os arquivos dele) para destino_do_console. Devolve o novo caminho do arquivo do jogo.
    Arquivo com o mesmo nome e o mesmo tamanho ja no destino conta como ja copiado (uma mudanca interrompida
    continua); com outro tamanho, para sem mexer em nada."""
    pasta, nomes = arquivos_do_jogo(caminho_do_jogo, pasta_do_console)
    for nome in nomes:
        alvo = os.path.join(destino_do_console, nome)
        if os.path.exists(alvo) and os.path.getsize(alvo) != os.path.getsize(os.path.join(pasta, nome)):
            raise NaoPode("Já existe no cartão um arquivo %s diferente deste. Apague ou renomeie o de lá e tente de "
                          "novo." % nome)
    copiados = []
    for nome in nomes:
        alvo = os.path.join(destino_do_console, nome)
        if not os.path.exists(alvo):
            _copiar(os.path.join(pasta, nome), alvo, progresso)
        else:
            progresso(os.path.getsize(alvo))
        copiados.append(nome)
    # tudo chegou e conferido: agora sim o original sai
    for nome in nomes:
        try:
            os.remove(os.path.join(pasta, nome))
        except OSError:
            pass
    # a pasta so do jogo que ficou vazia sai tambem (nunca a do console)
    if os.path.normcase(pasta) == os.path.normcase(os.path.abspath(pasta_do_console)):
        primeiras = {n.replace("\\", "/").split("/")[0] for n in nomes if "/" in n.replace("\\", "/")}
        for topo in primeiras:
            for atual, _subpastas, _arquivos in sorted(os.walk(os.path.join(pasta, topo)), reverse=True):
                try:
                    os.rmdir(atual)
                except OSError:
                    pass
    relativo = os.path.relpath(os.path.abspath(caminho_do_jogo), os.path.abspath(pasta_do_console))
    return os.path.join(destino_do_console, relativo)


class Mudanca:
    """Leva uma lista de jogos para o cartao numa thread a parte; a tela pergunta o andamento (estado())."""

    def __init__(self):
        self.trava = threading.Lock()
        self._estado = {"rodando": False, "total": 0, "feitos": 0, "bytes_total": 0, "bytes_feitos": 0,
                        "atual": "", "erros": [], "terminou_em": None}

    def estado(self):
        with self.trava:
            return dict(self._estado, erros=list(self._estado["erros"]))

    def comecar(self, itens, depois=None):
        """'itens': [{titulo, caminho, pasta_do_console, destino_do_console, bytes}]. 'depois()': roda no fim (refazer
        a lista de jogos). False se ja ha uma mudanca andando."""
        with self.trava:
            if self._estado["rodando"]:
                return False
            self._estado = {"rodando": True, "total": len(itens), "feitos": 0, "bytes_feitos": 0, "atual": "",
                            "bytes_total": sum(int(i.get("bytes") or 0) for i in itens), "erros": [],
                            "terminou_em": None}
        threading.Thread(target=self._rodar, args=(itens, depois), daemon=True, name="arena-mudanca").start()
        return True

    def _somar(self, quantos):
        with self.trava:
            self._estado["bytes_feitos"] += quantos

    def _rodar(self, itens, depois):
        try:
            for item in itens:
                with self.trava:
                    self._estado["atual"] = item["titulo"]
                try:
                    livre = _livre_mb(item["destino_do_console"])
                    if livre is not None and livre * 1048576 < int(item.get("bytes") or 0) + FOLGA_MB * 1048576:
                        raise NaoPode("O cartão não tem espaço para %s (%d MB livres)." % (item["titulo"], livre))
                    levar_jogo(item["caminho"], item["pasta_do_console"], item["destino_do_console"], self._somar)
                except (NaoPode, OSError) as falha:
                    texto = str(falha) if isinstance(falha, NaoPode) else (getattr(falha, "strerror", None) or str(falha))
                    with self.trava:
                        self._estado["erros"].append("%s: %s" % (item["titulo"], texto))
                with self.trava:
                    self._estado["feitos"] += 1
        finally:
            try:
                if depois:
                    depois()
            finally:
                with self.trava:
                    self._estado.update(rodando=False, atual="", terminou_em=time.time())


def _livre_mb(pasta):
    alvo = pasta
    while alvo and not os.path.isdir(alvo):
        alvo = os.path.dirname(alvo)
    try:
        uso = os.statvfs(alvo)
        return int(uso.f_bavail * uso.f_frsize / 1048576)
    except (OSError, AttributeError):
        try:
            import shutil
            return int(shutil.disk_usage(alvo).free / 1048576)
        except OSError:
            return None
