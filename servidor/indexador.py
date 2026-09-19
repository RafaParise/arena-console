# -*- coding: utf-8 -*-
"""
ARENA - Indexador de jogos
===========================
Varre a pasta 'jogos', descobre a qual plataforma cada arquivo pertence
e grava o resultado em 'dados/manifesto.json'.

Otimizacao importante: antes de varrer, o indexador calcula uma assinatura
das pastas (caminho + data de modificacao). Se nada mudou desde a ultima vez,
ele reaproveita o catalogo salvo em vez de ler o disco de novo. Isso importa
muito quando o ARENA roda de pen drive, onde ler pasta e lento.

Modulo da turma do 2o ano:
  - manipulacao de strings: limpar e formatar o titulo do jogo
  - arquivos com open() e context manager: ler pastas e gravar JSON

So biblioteca padrao do Python. Nenhum 'pip install'.
"""

import hashlib
import json
import os
import re
import threading
import unicodedata
import urllib.parse

import identificador

# ---------------------------------------------------------------------------
# BLOCO 1 - Onde estamos no disco
# ---------------------------------------------------------------------------
# __file__ e o caminho deste proprio arquivo. Subindo um nivel chegamos na
# raiz do ARENA. Nada aqui depende da letra do drive (E:, G:, F:), que muda
# de computador para computador.

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTA_JOGOS = os.path.join(RAIZ, "jogos")
PASTA_DADOS = os.path.join(RAIZ, "dados")
ARQUIVO_CONSOLES = os.path.join(PASTA_SERVIDOR, "consoles.json")
ARQUIVO_MANIFESTO = os.path.join(PASTA_DADOS, "manifesto.json")
ARQUIVO_MANUAIS = os.path.join(PASTA_DADOS, "consoles_manuais.json")

# Subpastas de jogos e o rotulo que cada uma recebe na tela.
ORIGENS = {
    "livres": "Acervo livre",
    "turma": "Feito pela turma",
    "pessoais": "Meus jogos",
}

# O repositorio publico de thumbnails do Libretro usa estes nomes de pasta.
# O Arena apenas monta a URL da imagem; nao baixa nem redistribui o arquivo.
# Quando o console nao esta nesta tabela, a capa tipografica continua sendo
# usada normalmente.
PASTAS_THUMBNAILS = {
    "super nintendo": "Nintendo - Super Nintendo Entertainment System",
    "nintendo (nes)": "Nintendo - Nintendo Entertainment System",
    "nintendo 64": "Nintendo - Nintendo 64",
    "game boy": "Nintendo - Game Boy",
    "game boy advance": "Nintendo - Game Boy Advance",
    "game boy e game boy color": "Nintendo - Game Boy Color",
    "gamecube e wii": "Nintendo - GameCube",
    "playstation": "Sony - PlayStation",
    "playstation 2": "Sony - PlayStation 2",
    "mega drive, master system e game gear": "Sega - Mega Drive - Genesis",
    "atari 2600": "Atari - 2600",
}


def urls_de_capa(plataforma_nome, nomes):
    """Monta candidatos de capa sem fazer nenhuma requisicao de rede."""
    pasta = PASTAS_THUMBNAILS.get(str(plataforma_nome).lower())
    if not pasta:
        return []
    candidatos = []
    for nome in nomes:
        base = os.path.splitext(os.path.basename(nome))[0].strip()
        if not base:
            continue
        base = re.sub(r"[&*/:<>?\\|]", "_", base)
        variacoes = [base]
        sem_marcadores = RE_COLCHETES.sub("", RE_PARENTESES.sub("", base)).strip()
        if sem_marcadores and sem_marcadores != base:
            variacoes.append(sem_marcadores)
        sem_subtitulo = re.sub(r"\s*(?:-|–)\s*Hyper Fighting$", "",
                               sem_marcadores, flags=re.IGNORECASE).strip()
        if sem_subtitulo and sem_subtitulo != sem_marcadores:
            variacoes.append(sem_subtitulo)
        base_regiao = sem_subtitulo or sem_marcadores
        if not re.search(r"\([^)]*\)", base_regiao):
            variacoes.extend([base_regiao + " (USA)",
                              base_regiao + " (Europe)",
                              base_regiao + " (Japan)"])
        for variacao in variacoes:
            url = "https://thumbnails.libretro.com/%s/Named_Boxarts/%s.png" % (
                urllib.parse.quote(pasta, safe=""),
                urllib.parse.quote(variacao, safe="()'!.-_"),
            )
            if url not in candidatos:
                candidatos.append(url)
    return candidatos

# Arquivos que nunca sao jogos, mesmo com extensao parecida.
IGNORAR = {"leia.txt", "leia-me.txt", "_console.txt", "readme.txt", "licenca.txt",
           "license.txt", "thumbs.db", "desktop.ini", ".gitkeep"}


# ---------------------------------------------------------------------------
# BLOCO 2 - Tratamento de strings
# ---------------------------------------------------------------------------

# Expressoes compiladas uma vez so. Compilar dentro do laco deixaria a
# varredura varias vezes mais lenta em pastas grandes.
RE_PARENTESES = re.compile(r"\([^)]*\)")
RE_COLCHETES = re.compile(r"\[[^\]]*\]")
RE_ESPACOS = re.compile(r"\s+")

LIGACOES = {"de", "da", "do", "dos", "das", "e", "the", "of", "in", "a", "o"}


def limpar_titulo(nome_arquivo):
    """Transforma o nome cru do arquivo em um titulo legivel.

    Exemplo:
        'super_jogo_(Brazil)_[!].sfc'  ->  'Super Jogo'

    Passo a passo:
      1. separa o nome da extensao
      2. remove o que estiver entre parenteses ou colchetes
      3. troca '_', '.' e '-' por espaco
      4. junta espacos repetidos e limpa as pontas
      5. coloca a inicial de cada palavra em maiuscula
    """
    titulo = os.path.splitext(nome_arquivo)[0]

    titulo = RE_PARENTESES.sub(" ", titulo)
    titulo = RE_COLCHETES.sub(" ", titulo)
    titulo = titulo.replace("_", " ").replace(".", " ").replace("-", " ")
    titulo = RE_ESPACOS.sub(" ", titulo).strip()

    if not titulo:
        return "Sem titulo"

    palavras = []
    for posicao, palavra in enumerate(titulo.split(" ")):
        if posicao > 0 and palavra.lower() in LIGACOES:
            palavras.append(palavra.lower())
        else:
            palavras.append(palavra[:1].upper() + palavra[1:])
    return " ".join(palavras)


def chave_ordenacao(texto):
    """Versao sem acento e em minusculas, usada so para ordenar a lista.

    'Acido' e 'Ácido' precisam ficar lado a lado na tela.
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.lower()


# ---------------------------------------------------------------------------
# BLOCO 3 - Leitura do catalogo de plataformas
# ---------------------------------------------------------------------------

def carregar_plataformas():
    """Le o catalogo de consoles e devolve dois dicionarios prontos para uso.

    - por_id:       id da plataforma -> dados completos
    - por_extensao: '.sfc' -> lista de ids que aceitam essa extensao
    """
    # 'with' fecha o arquivo sozinho, mesmo se der erro no meio da leitura.
    with open(ARQUIVO_CONSOLES, "r", encoding="utf-8") as arquivo:
        catalogo = json.load(arquivo)

    por_id = {}
    por_extensao = {}

    for plataforma in catalogo["plataformas"]:
        por_id[plataforma["id"]] = plataforma
        for extensao in plataforma["extensoes"]:
            por_extensao.setdefault(extensao, []).append(plataforma["id"])

    # Ordem de preferencia para extensao que serve a varias plataformas.
    # Sem isso valia a ordem do catalogo, e como o Sega CD vinha primeiro,
    # TODO arquivo .iso, .chd e .cue virava Sega CD - inclusive jogo de
    # PlayStation 2 de 3 GB.
    preferencia = catalogo.get("preferencia", {})
    for extensao, ordem in preferencia.items():
        if extensao not in por_extensao:
            continue
        atuais = por_extensao[extensao]
        por_extensao[extensao] = ([p for p in ordem if p in atuais] +
                                  [p for p in atuais if p not in ordem])

    return por_id, por_extensao


# ---------------------------------------------------------------------------
# BLOCO 4 - Assinatura das pastas (evita varredura desnecessaria)
# ---------------------------------------------------------------------------

def assinatura_das_pastas():
    """Resume o estado atual das pastas de jogos em um texto curto.

    Se nenhuma pasta foi criada, apagada ou teve arquivo alterado, a
    assinatura continua a mesma e a varredura inteira pode ser pulada.
    """
    partes = []
    for origem in ORIGENS:
        caminho = os.path.join(PASTA_JOGOS, origem)
        if not os.path.isdir(caminho):
            continue
        for pasta_atual, subpastas, _arquivos in os.walk(caminho):
            subpastas.sort()
            try:
                partes.append("%s|%d" % (pasta_atual, os.path.getmtime(pasta_atual)))
            except OSError:
                continue
    texto = "\n".join(sorted(partes))
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def ler_manifesto_salvo():
    try:
        with open(ARQUIVO_MANIFESTO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# BLOCO 5 - Varredura
# ---------------------------------------------------------------------------

ARQUIVO_MARCACAO = "_console.txt"


def ler_manuais():
    """Consoles que o aluno corrigiu na tela, jogo por jogo.

    Tem prioridade sobre tudo: se voce disse que aquele arquivo e PSP, e
    PSP, e o ARENA nao discute mais. Fica guardado, entao vale para sempre
    e viaja junto com a pasta.
    """
    try:
        with open(ARQUIVO_MANUAIS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_manual(jogo_id, plataforma):
    """Guarda (ou apaga, com plataforma vazia) a correcao de um jogo."""
    manuais = ler_manuais()
    if plataforma:
        manuais[jogo_id] = plataforma
    else:
        manuais.pop(jogo_id, None)
    os.makedirs(PASTA_DADOS, exist_ok=True)
    gravar_atomico(ARQUIVO_MANUAIS,
                   json.dumps(manuais, ensure_ascii=False, indent=1))
    return manuais


def ler_marcacao(pasta, por_id):
    """Le o arquivo _console.txt, se existir na pasta.

    E a palavra final: se o aluno escreveu 'ps2' nesse arquivo, tudo o que
    estiver na pasta e PlayStation 2, sem discussao. Serve para o caso raro
    em que os outros sinais erram.
    """
    try:
        caminho = os.path.join(pasta, ARQUIVO_MARCACAO)
        with open(caminho, "r", encoding="utf-8", errors="replace") as arquivo:
            escrito = arquivo.read().strip().lower()
    except OSError:
        return None
    return escrito if escrito in por_id else None


def plataforma_pelo_nome(texto, por_id, candidatos):
    """Procura o apelido de alguma plataforma dentro do nome da pasta.

    Compara apelido por apelido, do mais longo para o mais curto, para
    'playstation 2' vencer 'playstation' quando os dois servem.
    """
    texto = texto.lower()
    melhor, tamanho = None, 0
    for identificador in candidatos:
        for apelido in por_id[identificador].get("apelidos", [identificador]):
            if apelido in texto and len(apelido) > tamanho:
                melhor, tamanho = identificador, len(apelido)
    return melhor


SEM_PASTA = "indefinido"


def escolher_plataforma(candidatos, por_id, nome_pasta, marcado, tamanho_mb,
                        caminho_absoluto=None):
    """Decide de qual console e o arquivo. A PASTA manda.

    Quando a extensao serve a um console so (.nes, .sfc, .gba...), nao ha
    o que decidir. Quando serve a varios (.iso, .chd, .cue, .zip), quem
    decide e a pasta em que o arquivo esta - do mesmo jeito que o
    RetroArch faz.

    Por que parei de adivinhar: o Half-Life de PlayStation 2 foi lancado
    em CD, com a mesma estrutura de um jogo de PlayStation 1. Nenhuma
    pista de tamanho ou de cabecalho separa os dois. Chutar so gerava jogo
    abrindo no emulador errado, e o aluno sem entender por que.

    Sem pasta que diga o console, o jogo fica marcado como indefinido e
    aparece no topo da lista, esperando um clique.
    """
    if len(candidatos) == 1:
        return candidatos[0], None

    if marcado and marcado in candidatos:
        return marcado, None

    # A pasta manda, e manda mesmo. Se o arquivo esta dentro da pasta de
    # um console, e daquele console - ainda que aquela extensao nao esteja
    # cadastrada nele. Voce colocou ali de proposito.
    pela_pasta = plataforma_pelo_nome(nome_pasta, por_id, candidatos)
    if not pela_pasta:
        pela_pasta = plataforma_pelo_nome(nome_pasta, por_id, list(por_id))
    if pela_pasta:
        return pela_pasta, None

    # Sem pasta: nao decide. Mas deixa uma sugestao pronta, para o aluno
    # so confirmar em vez de escolher entre 47 consoles.
    sugestao = None
    if caminho_absoluto:
        try:
            sugestao = identificador.identificar(caminho_absoluto, candidatos)
        except Exception:
            sugestao = None
    if not sugestao and tamanho_mb:
        cabem = [c for c in candidatos
                 if tamanho_mb <= por_id[c].get("tamanho_max_mb", 10 ** 6)]
        sugestao = (cabem or candidatos)[0]

    return SEM_PASTA, sugestao


def varrer_pasta(caminho_pasta, origem, por_extensao, por_id, manuais=None):
    """Percorre uma pasta e devolve a lista de jogos encontrados.

    os.walk entra tambem nas subpastas, entao o aluno pode organizar os
    arquivos em pastas por console que continua funcionando.
    """
    encontrados = []

    if not os.path.isdir(caminho_pasta):
        return encontrados

    for pasta_atual, subpastas, arquivos in os.walk(caminho_pasta):
        subpastas.sort()
        # O caminho inteiro conta, nao so a ultima pasta: quem organiza em
        # 'Sony\PlayStation 2\Corrida' tambem e atendido.
        caminho_relativo_pasta = os.path.relpath(pasta_atual, caminho_pasta)
        marcado = ler_marcacao(pasta_atual, por_id)

        for nome_arquivo in arquivos:

            if nome_arquivo.lower() in IGNORAR:
                continue

            extensao = os.path.splitext(nome_arquivo)[1].lower()
            candidatos = por_extensao.get(extensao)
            if not candidatos:
                continue

            caminho_absoluto = os.path.join(pasta_atual, nome_arquivo)
            try:
                tamanho = os.path.getsize(caminho_absoluto)
            except OSError:
                continue
            tamanho_mb = tamanho / (1024.0 * 1024.0)

            caminho_relativo = os.path.relpath(caminho_absoluto, RAIZ)
            identificacao = caminho_relativo.replace("\\", "/").lower()

            # Correcao feita na tela vence tudo.
            sugestao = None
            corrigido = (manuais or {}).get(identificacao)
            if corrigido in por_id:
                id_plataforma = corrigido
                incerto = False
            else:
                id_plataforma, sugestao = escolher_plataforma(
                    candidatos, por_id, caminho_relativo_pasta, marcado,
                    tamanho_mb, caminho_absoluto)
                incerto = (id_plataforma == SEM_PASTA)
            if id_plataforma == SEM_PASTA:
                plataforma = {"nome": "Precisa escolher o console",
                              "pede_placar": False}
            else:
                plataforma = por_id[id_plataforma]
            titulo = limpar_titulo(nome_arquivo)

            encontrados.append({
                "id": identificacao,
                "titulo": titulo,
                "ordenacao": chave_ordenacao(titulo),
                "plataforma": id_plataforma,
                "plataforma_nome": plataforma["nome"],
                "arquivo": caminho_relativo,
                "origem": origem,
                "origem_rotulo": ORIGENS.get(origem, origem),
                "pede_placar": plataforma.get("pede_placar", False),
                "tamanho_mb": round(tamanho_mb, 1),
                "capa_urls": urls_de_capa(plataforma["nome"],
                                           [nome_arquivo, titulo]),
                # Quando houve desempate, a tela oferece a correcao.
                "ambiguo": incerto,
                "corrigido": bool(corrigido),
                # Console que o ARENA acha provavel. Serve so para deixar
                # a lista ja marcada na opcao mais util - quem decide e voce.
                "sugestao": sugestao,
            })

    return encontrados


# ---------------------------------------------------------------------------
# BLOCO 6 - Montar e gravar o manifesto
# ---------------------------------------------------------------------------

_TRAVA = threading.Lock()


def gravar_atomico(caminho, texto):
    """Grava sem deixar arquivo pela metade.

    Escreve num temporario com nome unico por thread e so entao renomeia.
    Se o pen drive for retirado no meio da gravacao, o catalogo antigo
    continua inteiro em vez de virar um arquivo cortado ao meio.
    """
    temporario = "%s.%d.tmp" % (caminho, threading.get_ident())
    with _TRAVA:
        try:
            with open(temporario, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                try:
                    os.remove(temporario)
                except OSError:
                    pass


def indexar(forcar=False):
    """Funcao principal. Devolve o manifesto e grava em disco.

    Com forcar=False, reaproveita o catalogo salvo se nada mudou nas pastas.
    """
    assinatura = assinatura_das_pastas()

    if not forcar:
        salvo = ler_manifesto_salvo()
        if salvo and salvo.get("assinatura") == assinatura:
            # Migra manifestos antigos: adicionar uma nova propriedade visual
            # nao deve exigir que o aluno altere ou recopie os jogos.
            alterado = False
            for jogo in salvo.get("jogos", []):
                novas_urls = urls_de_capa(
                    jogo.get("plataforma_nome", ""),
                    [jogo.get("arquivo", ""), jogo.get("titulo", "")],
                )
                if jogo.get("capa_urls") != novas_urls:
                    jogo["capa_urls"] = novas_urls
                    alterado = True
            if alterado:
                gravar_atomico(
                    ARQUIVO_MANIFESTO,
                    json.dumps(salvo, ensure_ascii=False, separators=(",", ":")),
                )
            salvo["reaproveitado"] = True
            return salvo

    por_id, por_extensao = carregar_plataformas()

    manuais = ler_manuais()
    jogos = []
    for origem in ORIGENS:
        jogos.extend(
            varrer_pasta(os.path.join(PASTA_JOGOS, origem), origem,
                         por_extensao, por_id, manuais)
        )

    # Ordena por plataforma e depois por titulo, sem acento atrapalhar.
    jogos.sort(key=lambda j: (j["plataforma_nome"], j["ordenacao"]))

    manifesto = {
        "assinatura": assinatura,
        "total": len(jogos),
        "jogos": jogos,
        "reaproveitado": False,
    }

    os.makedirs(PASTA_DADOS, exist_ok=True)
    # separators sem espaco extra deixa o arquivo menor e a leitura mais rapida.
    texto = json.dumps(manifesto, ensure_ascii=False, separators=(",", ":"))
    gravar_atomico(ARQUIVO_MANIFESTO, texto)

    return manifesto


# Executado direto pelo terminal: roda a varredura e mostra um resumo.
if __name__ == "__main__":
    resultado = indexar(forcar=True)
    print("Jogos encontrados: %d" % resultado["total"])

    contagem = {}
    for jogo in resultado["jogos"]:
        nome = jogo["plataforma_nome"]
        contagem[nome] = contagem.get(nome, 0) + 1

    for nome in sorted(contagem):
        print("  %-45s %d" % (nome, contagem[nome]))

    if resultado["total"] == 0:
        print("")
        print("Nenhum jogo na pasta 'jogos'.")
        print("Coloque seus arquivos em jogos\\pessoais e rode de novo.")
