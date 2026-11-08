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


class TrilhaFaltando(Exception):
    """O .cue/.gdi/.m3u cita um arquivo que nao esta ao lado dele: levar so parte do jogo o quebraria."""


def _do_jogo_na_pasta(caminho_do_jogo):
    """Os nomes, na pasta do jogo, que formam o jogo: o mesmo nome (Crash.cue + Crash.bin, Zelda.sfc + Zelda.srm) e
    tudo o que o .cue/.gdi/.m3u cita, seguindo a corrente (.m3u -> .cue -> trilhas). A trilha e' achada sem
    diferenca de maiusculas (o .cue diz "Track 1.BIN" e o arquivo e' "Track 1.bin"; no Android isso importa).
    Auditoria 6 (DAD6-03): antes, a trilha com maiuscula diferente e as trilhas dos .cue de um .m3u ficavam para
    tras, e o jogo quebrava nos dois lugares. Levanta TrilhaFaltando se algo citado nao existe."""
    pasta = os.path.dirname(caminho_do_jogo)
    try:
        vizinhos = [n for n in os.listdir(pasta) if os.path.isfile(os.path.join(pasta, n))]
    except OSError:
        vizinhos = []
    pelo_nome = {}
    for nome in vizinhos:
        pelo_nome.setdefault(nome.casefold(), nome)
    base = os.path.splitext(os.path.basename(caminho_do_jogo))[0].casefold()
    juntos = {os.path.basename(caminho_do_jogo)}
    juntos.update(n for n in vizinhos if os.path.splitext(n)[0].casefold() == base)
    olhar = list(juntos)
    while olhar:
        nome = olhar.pop()
        if os.path.splitext(nome)[1].lower() not in (".cue", ".gdi", ".m3u"):
            continue
        for citado in _citados(os.path.join(pasta, nome)):
            achado = pelo_nome.get(citado.casefold())
            if achado is None:
                raise TrilhaFaltando(citado)
            if achado not in juntos:
                juntos.add(achado)
                olhar.append(achado)
    return juntos


def arquivos_do_jogo(caminho_do_jogo, pasta_do_console):
    """(pasta_de_cima, [arquivos relativos a ela]) que formam o jogo. Jogo numa pasta so dele: a pasta inteira (a
    pasta_de_cima e' a do console e os arquivos vem com o nome da pasta do jogo na frente). Pasta com OUTROS jogos
    (PS1\\Coletanea\\A.cue e B.cue): so os arquivos deste jogo, com o caminho dentro da pasta (auditoria 6, DAD6-06:
    marcar um levava a pasta inteira, com os outros jogos). Levanta TrilhaFaltando (ver _do_jogo_na_pasta)."""
    caminho_do_jogo = os.path.abspath(caminho_do_jogo)
    pasta_do_console = os.path.abspath(pasta_do_console)
    pasta = os.path.dirname(caminho_do_jogo)
    proprios = _do_jogo_na_pasta(caminho_do_jogo)
    if os.path.normcase(pasta) == os.path.normcase(pasta_do_console):
        return pasta, sorted(proprios)
    relativo = os.path.relpath(caminho_do_jogo, pasta_do_console).replace("\\", "/").split("/")
    topo = os.path.join(pasta_do_console, relativo[0])
    extensao = os.path.splitext(caminho_do_jogo)[1].casefold()
    lista, outro_jogo = [], False
    for atual, _subpastas, arquivos in os.walk(topo):
        for nome in arquivos:
            caminho = os.path.join(atual, nome)
            lista.append(os.path.relpath(caminho, pasta_do_console))
            mesmo_lugar = os.path.normcase(atual) == os.path.normcase(pasta)
            if os.path.splitext(nome)[1].casefold() == extensao and not (mesmo_lugar and nome in proprios):
                outro_jogo = True               # outro arquivo do mesmo tipo do jogo: outro jogo na mesma pasta
    if not outro_jogo:
        return pasta_do_console, sorted(lista)   # a pasta e' so dele: vai inteira (com extras, capas, leia-me)
    dentro = os.path.relpath(pasta, pasta_do_console)
    return pasta_do_console, sorted(os.path.join(dentro, nome) for nome in proprios)


def _iguais(um, outro):
    """Os dois arquivos tem o mesmo conteudo (bloco por bloco)."""
    if os.path.getsize(um) != os.path.getsize(outro):
        return False
    with open(um, "rb") as a, open(outro, "rb") as b:
        while True:
            x, y = a.read(BLOCO), b.read(BLOCO)
            if x != y:
                return False
            if not x:
                return True


def bytes_do_jogo(caminho_do_jogo, pasta_do_console):
    """O tamanho do jogo inteiro, ou 0 se ele cita um arquivo que falta (quem leva avisa o motivo)."""
    try:
        pasta, nomes = arquivos_do_jogo(caminho_do_jogo, pasta_do_console)
    except TrilhaFaltando:
        return 0
    return _tamanho(pasta, nomes)


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
        saida.append({"id": jogo["id"], "titulo": jogo.get("titulo", ""), "console": os.path.basename(console),
                      "bytes": bytes_do_jogo(caminho, console)})
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
    Arquivo que ja esta no destino so conta como ja copiado (uma mudanca interrompida continua) se for IGUAL ao
    original, byte por byte; diferente, para sem mexer em nada. Auditoria 6 (DAD6-01): antes bastava o mesmo nome e o
    mesmo tamanho, e um Zelda.srm de outro progresso no cartao fazia o do aluno ser apagado."""
    try:
        pasta, nomes = arquivos_do_jogo(caminho_do_jogo, pasta_do_console)
    except TrilhaFaltando as falta:
        raise NaoPode("O jogo cita o arquivo %s, que não está ao lado dele: nada foi levado." % falta)
    for nome in nomes:
        original, alvo = os.path.join(pasta, nome), os.path.join(destino_do_console, nome)
        if not os.path.exists(alvo):
            continue
        if os.path.samefile(original, alvo):
            raise NaoPode("O arquivo %s já é o mesmo do cartão: nada foi levado." % nome)
        if not _iguais(original, alvo):
            raise NaoPode("Já existe no cartão um arquivo %s diferente deste. Apague ou renomeie o de lá e tente de "
                          "novo." % nome)
    for nome in nomes:
        alvo = os.path.join(destino_do_console, nome)
        if not os.path.exists(alvo):
            _copiar(os.path.join(pasta, nome), alvo, progresso)
        else:
            progresso(os.path.getsize(alvo))
    # Tudo chegou: confere de novo cada copia (o cartao pode ter saido no meio) e so entao o original sai. Auditoria 6
    # (DAD6-02): antes nada era reconferido e o erro ao apagar era engolido.
    for nome in nomes:
        alvo = os.path.join(destino_do_console, nome)
        if not os.path.isfile(alvo) or os.path.getsize(alvo) != os.path.getsize(os.path.join(pasta, nome)):
            raise NaoPode("A cópia de %s no cartão não confere (o cartão saiu?): o original ficou onde estava." % nome)
    nao_apagados = []
    for nome in nomes:
        try:
            os.remove(os.path.join(pasta, nome))
        except OSError:
            nao_apagados.append(nome)
    if nao_apagados:
        raise NaoPode("O jogo chegou inteiro ao cartão, mas não consegui apagar da memória: %s. Ele aparece duas "
                      "vezes até ser apagado à mão." % ", ".join(nao_apagados))
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
        self._levados = []

    def levados(self):
        """[(caminho antigo, caminho novo)] do arquivo de cada jogo levado na ultima mudanca: o ARENA troca o id do
        jogo nos favoritos, nos recentes, no placar e no tempo de jogo (auditoria 6, DAD6-04)."""
        with self.trava:
            return list(self._levados)

    def rodando(self):
        with self.trava:
            return bool(self._estado["rodando"])

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
            self._levados = []
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
                    _apagar_parciais(item["destino_do_console"])
                    novo = levar_jogo(item["caminho"], item["pasta_do_console"], item["destino_do_console"],
                                      self._somar)
                    with self.trava:
                        self._levados.append((item["caminho"], novo))
                except Exception as falha:          # qualquer erro vira recado do item (auditoria 6, DAD6-08)
                    if isinstance(falha, NaoPode):
                        texto = str(falha)
                    elif isinstance(falha, OSError):
                        texto = getattr(falha, "strerror", None) or str(falha)
                    else:
                        texto = "erro inesperado (%s); o original ficou onde estava" % type(falha).__name__
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


def _apagar_parciais(pasta):
    """Tira os .arena-parcial que sobraram de uma mudanca cortada no meio (o app fechado a forca): ocupavam o cartao
    sem aparecer em lista nenhuma (auditoria 6, DAD6-08). So na pasta do console de destino."""
    for atual, _subpastas, arquivos in os.walk(pasta) if os.path.isdir(pasta) else ():
        for nome in arquivos:
            if nome.endswith(".arena-parcial"):
                try:
                    os.remove(os.path.join(atual, nome))
                except OSError:
                    pass


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
