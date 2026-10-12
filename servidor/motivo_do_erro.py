# -*- coding: utf-8 -*-
"""
ARENA - por que o jogo nao abriu, nas palavras do proprio emulador.

Por que existe (Rafael, 02/10/2026): "o ARENA nao reconhece o motivo do
kof2002 nao rodar, porque para o ARENA esta tudo certo, mas nao roda". Ele
tentou 4 vezes; nas 4, o MAME escreveu no registro exatamente o que faltava
("265-c1.c1 NOT FOUND", "Required files are missing") e a tela do ARENA nao
disse nada -- o RetroArch so mostrava "Falha ao carregar o conteudo".

Antes de abrir, o ARENA nao tem como saber se um zip de fliperama confere:
os bancos do RetroArch (retroarch\\database\\rdb) trazem o nome e o CRC do
conjunto, nao a lista de arquivos de cada jogo. Quem sabe e' o emulador, na
hora de abrir. Entao, quando o jogo fecha, o ARENA le o registro daquela
partida (dados\\retroarch__<data>.log), procura as frases conhecidas e
monta uma explicacao em portugues:

  - MAME:  "<arquivo> NOT FOUND (tried in kof2002 neogeo)",
           "<arquivo> WRONG CHECKSUMS", "Required files are missing";
  - FBNeo: "ROM at index 3 with name 265-c2.c2 and CRC 0x... is required",
           "Romset is unknown";
  - qualquer nucleo: "Falha ao carregar o conteudo" / "Failed to load content".

E separa o que falta do JOGO do que falta da BIOS: se o arquivo que falta
esta dentro de uma BIOS da pasta com outro nome (neogeo.mame.zip, em vez de
neogeo.zip), a resposta e' "renomeie" -- o caso do Rafael.

So le: nao muda nenhum arquivo do jogo nem da BIOS.
"""

import os
import re
import zipfile

# Linhas do MAME (o prefixo "[libretro ERROR] " so aparece na primeira).
RE_MAME_FALTA = re.compile(r"^(?:\[libretro [A-Z]+\]\s*)?(\S+) NOT FOUND(?: \(tried in ([^)]*)\))?\s*$", re.M)
RE_MAME_ERRADO = re.compile(r"^(?:\[libretro [A-Z]+\]\s*)?(\S+) WRONG (?:CHECKSUMS|LENGTH)", re.M)
# Linha do FBNeo: o nome e o CRC que ele procura.
RE_FBNEO_FALTA = re.compile(r"ROM at index \d+ with name (\S+) and CRC 0x([0-9a-fA-F]{8}) is required")
RE_ERRO_DO_NUCLEO = re.compile(r"^\[libretro ERROR\]\s*(?:\[[^\]]+\]\s*)?(.+)$", re.M)

FALHOU_AO_CARREGAR = ("Falha ao carregar o conteúdo", "Failed to load content")
# BIOS de fliperama que mora na pasta do jogo (a mesma lista do indexador).
RE_BIOS = re.compile(
    r"^(neogeo|pgm|naomi|naomi2|naomigd|awbios|stvbios|skns|cpzn1|cpzn2|hng64|"
    r"nss|playch10|megatech|megaplay|decocass|konamigv|taitogn|isgsm|qsound)"
    r"([ ._-].*)?\.(zip|7z)$", re.I)
# Os arquivos da BIOS do Neo Geo (MAME e FBNeo): separa "falta a BIOS" de
# "falta parte do jogo" mesmo sem BIOS nenhuma na pasta.
RE_BIOS_NEOGEO = re.compile(
    r"^(000-lo\.lo|sfix\.sfix|sm1\.sm1|sp-[\w.-]+\.sp1|sp1[\w.-]*|uni-bios[\w.-]*\.rom|vs-bios\.rom|"
    r"japan-j3\.bin|asia-s3\.rom|sp-1v1_3db8c\.bin|sp-[\w-]+\.bin)$", re.I)
# Arquivo que nao e' parte do jogo (vem junto em muito zip).
RE_NAO_E_ROM = re.compile(r"\.(txt|html?|nfo|diz|url|jpg|png)$", re.I)

NOME_DO_NUCLEO = {"mame": "MAME", "fbneo": "FBNeo", "genesis_plus_gx": "O emulador do Sega CD",
                  "mednafen_saturn": "O emulador do Saturn", "flycast": "O emulador do Dreamcast",
                  "snes9x": "O emulador do Super Nintendo", "swanstation": "O emulador do PlayStation",
                  "pcsx_rearmed": "O emulador do PlayStation"}

# BIOS que falta, nas palavras de cada emulador (registros de 03/10/2026):
#   Genesis Plus GX: Unable to open CD BIOS: "...\retroarch\system\bios_CD_E.bin".
#   Beetle Saturn:   Cannot open BIOS file "...\retroarch\system\mpr-17933.bin".
#   Flycast:         Erro: Nao foi possivel carregar a Bios da naomi.zip
RE_BIOS_FALTA = re.compile(r'(?:Unable to open CD BIOS|Cannot open BIOS file|Could not (?:open|load) BIOS'
                           r'(?: file)?|Failed to (?:open|load) BIOS(?: file)?)\W*"?([^"\r\n]+?)"?\.?\s*$',
                           re.I | re.M)
RE_BIOS_FLYCAST = re.compile(r"(?:carregar a Bios da|load (?:the )?BIOS (?:from )?)\s*(\S+\.zip)", re.I)
REGIAO_DA_BIOS = {"bios_cd_e.bin": " (a do Sega CD da Europa)", "bios_cd_u.bin": " (a do Sega CD dos EUA)",
                  "bios_cd_j.bin": " (a do Sega CD do Japão)", "mpr-17933.bin": " (a do Saturn dos EUA e da Europa)",
                  "sega_101.bin": " (a do Saturn do Japão)"}


def _dica_da_bios(nome_arquivo):
    """Onde por a BIOS: a prateleira dela na pasta BIOS do ARENA (servidor\\bios.py)."""
    import bios
    return bios.como_colocar_a_bios(bios.prateleira_da_bios(nome_arquivo))


def motivo_da_bios(texto, caminho_jogo, quem):
    """A explicacao quando o que faltou foi a BIOS, ou None."""
    achado = RE_BIOS_FALTA.search(texto)
    if achado:
        caminho = achado.group(1).strip().strip('"')
        nome = os.path.basename(caminho.replace("\\", "/"))
        return ("%s não abriu este jogo: falta a BIOS %s%s. %s"
                % (quem, nome, REGIAO_DA_BIOS.get(nome.lower(), ""), _dica_da_bios(nome)))
    achado = RE_BIOS_FLYCAST.search(texto)
    if achado:
        # BIOS de placa de fliperama (naomi.zip...): nao tem prateleira; vai
        # onde o Flycast procura.
        return ("%s não abriu este jogo: ele é de fliperama (Naomi ou Atomiswave) e precisa da BIOS %s, "
                "dentro da pasta retroarch\\system\\dc (o .zip inteiro, sem descompactar)."
                % (quem, achado.group(1)))
    nome = os.path.basename(caminho_jogo or "")
    if "ROM loading failed" in texto and (nome.startswith("BS ") or nome.lower().endswith(".bs")):
        return ("%s não abriu este jogo de Satellaview (o \"BS\" do nome): ele precisa da BIOS BS-X.bin "
                "(o cartucho \"BS-X - Sore wa Namae o Nusumareta Machi no Monogatari\"). %s"
                % (quem, _dica_da_bios("BS-X.bin")))
    return None
MOSTRAR = 3   # quantos nomes de arquivo cabem numa frase sem virar lista


def registro_da_partida(pasta_dados, desde):
    """O registro do RetroArch DESTA partida: o mais novo de pasta_dados que
    nasceu depois de 'desde' (time.time() de quando o jogo foi aberto). Cada
    abertura cria um arquivo novo (log_to_file_timestamp). None se nao ha."""
    melhor = None
    try:
        nomes = os.listdir(pasta_dados)
    except OSError:
        return None
    for nome in nomes:
        if not (nome.startswith("retroarch__") and nome.endswith(".log")):
            continue
        caminho = os.path.join(pasta_dados, nome)
        try:
            info = os.stat(caminho)
        except OSError:
            continue
        # Quando o arquivo NASCEU (no Windows, st_ctime tambem e' isso, mas o
        # Python novo prefere st_birthtime).
        nasceu = getattr(info, "st_birthtime", None) or info.st_ctime
        if nasceu >= desde - 5 and (melhor is None or nasceu > melhor[0]):
            melhor = (nasceu, caminho)
    return melhor[1] if melhor else None


def ler(caminho, limite=2 * 1024 * 1024):
    """O texto do registro (no maximo os ultimos 2 MB)."""
    try:
        with open(caminho, "rb") as arquivo:
            arquivo.seek(0, os.SEEK_END)
            tamanho = arquivo.tell()
            arquivo.seek(max(0, tamanho - limite))
            return arquivo.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def _nomes_no_zip(caminho):
    """Nomes (sem pasta) dos arquivos de um zip; [] se nao abre."""
    try:
        with zipfile.ZipFile(caminho) as z:
            return [os.path.basename(i.filename) for i in z.infolist() if not i.is_dir()]
    except (OSError, zipfile.BadZipFile, ValueError):
        return []


def _lista(nomes):
    """'a, b, c e mais 9' com no maximo MOSTRAR nomes."""
    nomes = list(nomes)
    texto = ", ".join(nomes[:MOSTRAR])
    return texto + (" e mais %d" % (len(nomes) - MOSTRAR) if len(nomes) > MOSTRAR else "")


def _plural(n, um, varios):
    return "%d %s" % (n, um if n == 1 else varios)


# Jogar Junto: o que o RetroArch escreve quando NAO deu para entrar na partida
# de um colega. Sao TRES casos diferentes (textos do retroarch.exe; o menu do
# ARENA e' em portugues, o ingles fica por garantia):
#  - o anfitriao disse que esta cheio;
CHEIA = ("Host de netplay cheio", "Netplay host full")
#  - a conexao abriu, mas a entrada falhou (o sexto jogador de uma partida de
#    5 recebe esta: o anfitriao fecha a porta na cara dele);
ENTRADA_RECUSADA = ("Falha ao conectar ao host.", "Failed to connect to host.")
#  - nem chegou a conectar: ninguem atendeu no endereco (o jogo do anfitriao
#    ainda nao tinha aberto, ou o Firewall/o Wi-Fi barrou). Revisao da Fase 4:
#    antes este caso tambem dizia "pode estar cheia" -- impossivel ali.
NAO_ALCANCOU = re.compile(r"Failed to connect to host \S+ on port \S+")


def motivo_da_partida(texto, jogadores_max=None):
    """Por que nao deu para ENTRAR na partida de um colega, ou None.

    Achado da auditoria 3 (08/10/2026, testes\\teste_netplay_sexto_jogador.py):
    o sexto jogador numa partida de 5 recebe do RetroArch so "Falha ao
    conectar ao host" -- e acha que e' a rede. Cada caso tem a sua frase, com
    o que fazer."""
    limite = ("este jogo aceita até %d jogadores. " % int(jogadores_max)) if jogadores_max else ""
    if NAO_ALCANCOU.search(texto):
        return ("Não deu para entrar: o computador de quem abriu a partida não respondeu. "
                "Confira se o jogo dele já está aberto na tela e tente de novo. Se continuar, a rede "
                "pode estar barrando (Firewall numa rede Pública, ou Wi-Fi que isola os aparelhos): "
                "rode o PARTIDA.bat nos dois computadores.")
    if any(f in texto for f in CHEIA):
        return ("Não deu para entrar: a partida está cheia (%s). Espere alguém sair, ou abram "
                "outra partida." % (limite.rstrip(". ") or "não cabe mais ninguém"))
    if any(f in texto for f in ENTRADA_RECUSADA):
        return ("Não deu para entrar na partida. Ela pode estar cheia" + (": " + limite if limite else ". ")
                + "Pergunte a quem hospeda quantos já entraram; se ainda tem vaga, rode o PARTIDA.bat "
                  "nos dois computadores para ver o que a rede está barrando.")
    return None


def analisar(texto, caminho_jogo, nucleo=""):
    """Le o registro de uma partida e diz por que o jogo nao abriu.

    Devolve None (abriu, ou nao ha o que dizer) ou um dicionario:
      texto    - a explicacao para o aluno/professor, em portugues;
      faltando - nomes que o emulador procurou e nao achou;
      renomear - (nome_atual, nome_certo) quando a BIOS so esta com o nome errado.
    """
    nucleo = (nucleo or "").lower()
    quem = next((v for k, v in NOME_DO_NUCLEO.items() if k in nucleo), "O emulador")
    faltando, onde = [], ""
    for m in RE_MAME_FALTA.finditer(texto):
        if m.group(1) not in faltando:
            faltando.append(m.group(1))
        onde = onde or (m.group(2) or "")
    crcs = {}
    for m in RE_FBNEO_FALTA.finditer(texto):
        if m.group(1) not in faltando:
            faltando.append(m.group(1))
        crcs[m.group(1).lower()] = m.group(2).lower()
    errados = []
    for m in RE_MAME_ERRADO.finditer(texto):
        if m.group(1) not in errados:
            errados.append(m.group(1))
    # So fala quando o jogo NAO abriu. Arquivo que falta mas e' opcional, ou
    # "WRONG CHECKSUMS" com o MAME rodando assim mesmo ("might not run
    # correctly"), nao e' "nao abriu" -- o zip danificado ja tem o aviso do
    # integridade.py.
    falhou = (any(f in texto for f in FALHOU_AO_CARREGAR) or "Required files are missing" in texto
              or bool(crcs))
    desconhecido = "Romset is unknown" in texto
    if not (falhou or desconhecido):
        return None
    # Faltou a BIOS (Sega CD, Saturn, Dreamcast/Naomi, Satellaview...): e' a
    # causa, e o emulador diz qual arquivo (03/10/2026).
    texto_bios = motivo_da_bios(texto, caminho_jogo, quem)
    if texto_bios:
        return {"texto": texto_bios, "faltando": [], "renomear": None, "discos": []}

    pasta = os.path.dirname(caminho_jogo or "")
    nome_zip = os.path.basename(caminho_jogo or "")
    # "tried in kof2002 neogeo": o segundo nome e' o conjunto da BIOS.
    conjuntos = onde.split()
    bios_certa = (conjuntos[1] + ".zip") if len(conjuntos) > 1 else ""

    # O que falta e' da BIOS? Procura nas BIOS desta pasta (com qualquer nome).
    bios_da_pasta = {}
    try:
        for nome in os.listdir(pasta) if pasta else []:
            if RE_BIOS.match(nome) and nome.lower() != nome_zip.lower():
                bios_da_pasta[nome] = {n.lower() for n in _nomes_no_zip(os.path.join(pasta, nome))}
    except OSError:
        pass
    da_bios, sem_zip, renomear = [], [], None
    for nome in faltando:
        achou = False
        for zip_da_bios, conteudo in bios_da_pasta.items():
            if nome.lower() in conteudo:
                da_bios.append(nome)
                achou = True
                certo = bios_certa or (re.split(r"[ ._-]", zip_da_bios, 1)[0].lower() + ".zip")
                if zip_da_bios.lower() != certo.lower() and not renomear \
                        and not os.path.exists(os.path.join(pasta, certo)):
                    renomear = (zip_da_bios, certo)
                break
        # Nao esta em BIOS nenhuma da pasta, mas e' nome da BIOS do Neo Geo.
        if not achou and bios_certa in ("", "neogeo.zip") and RE_BIOS_NEOGEO.match(nome):
            sem_zip.append(nome)
    # O disco (.chd) que falta nao fica DENTRO do zip: fica numa pasta com o
    # nome do zip, ao lado dele ("kinst.chd NOT FOUND (tried in kinst)").
    discos = [n for n in faltando if n.lower().endswith(".chd")]
    do_jogo = [n for n in faltando if n not in da_bios and n not in sem_zip and n not in discos]
    bios_nome = bios_certa or "neogeo.zip"

    partes = []
    if discos:
        romset_do_zip = os.path.splitext(nome_zip)[0]
        partes.append("Falta o disco deste jogo (%s): ele fica na pasta %s, ao lado do %s. Ponha o "
                      "arquivo lá e abra de novo."
                      % (_lista(discos), os.path.join(os.path.basename(pasta), romset_do_zip), nome_zip))
    if renomear:
        partes.append("A BIOS está na pasta, mas com o nome errado: renomeie %s para %s "
                      "(o emulador só procura por esse nome)." % renomear)
    elif da_bios or (sem_zip and os.path.exists(os.path.join(pasta, bios_nome))):
        partes.append("A BIOS %s desta pasta é de outra versão (o emulador não achou nela: %s)."
                      % (bios_nome, _lista(da_bios or sem_zip)))
    elif sem_zip:
        partes.append("Falta a BIOS %s: ela vai na mesma pasta do jogo (e não aparece na lista)."
                      % bios_nome)
    if do_jogo:
        dentro = [n for n in _nomes_no_zip(caminho_jogo) if not RE_NAO_E_ROM.search(n)]
        frase = "Faltam %s do jogo dentro do %s (%s)." % (
            _plural(len(do_jogo), "arquivo", "arquivos"), nome_zip or "arquivo do jogo", _lista(do_jogo))
        if dentro and not any(n.lower() in {d.lower() for d in dentro} for n in do_jogo):
            frase += (" Este zip é de outra versão ou feito para outro emulador: dentro dele há %s. "
                      "Troque por um %s feito para o %s desta versão do ARENA (guia 2-JOGOS.md, "
                      "\"Fliperama: Neo Geo e Arcade\")." % (_lista(dentro), nome_zip or "romset", quem))
        # BIOS de outro sistema (o MAME diz qual: "tried in jogo pgm") que
        # nao esta na pasta: nao da para separar os arquivos dela dos do jogo.
        if bios_certa and bios_certa != "neogeo.zip" and not bios_da_pasta \
                and not os.path.exists(os.path.join(pasta, bios_certa)):
            frase += " E falta a BIOS %s, que vai na mesma pasta do jogo." % bios_certa
        partes.append(frase)
    if errados:
        partes.append("%s com o conteúdo diferente do esperado (%s): o zip está danificado ou é "
                      "de outra versão." % (_plural(len(errados), "arquivo está", "arquivos estão"),
                                           _lista(errados)))
    if desconhecido and not partes:
        # "O FBNeo", "O MAME"; quem ja vem com o artigo ("O emulador do ...") fica como esta.
        sujeito = quem if quem.startswith("O ") else "O " + quem
        partes.append("%s não conhece este jogo (%s): ou o nome do zip não é o do romset (no "
                      "fliperama, o nome curto, ex.: kof2002.zip, sem espaços), ou este emulador "
                      "não tem esse jogo -- aí, ponha o zip na pasta Arcade (MAME)."
                      % (sujeito, nome_zip))
    # O zip dentro da pasta de mesmo nome (Arcade\kinst\kinst.zip, junto do
    # disco): o MAME so diz "unknown option: kinst" (provado em 02/10/2026).
    romset = os.path.splitext(nome_zip)[0].lower()
    if not partes and "unknown option" in texto and romset and os.path.basename(pasta).lower() == romset:
        partes.append("O %s está dentro da pasta %s, e assim o emulador não abre. Tire o %s dessa "
                      "pasta e ponha na pasta de cima: dentro da pasta %s fica só o disco (%s.chd)."
                      % (nome_zip, romset, nome_zip, romset, romset))
    if not partes:
        ultimo = RE_ERRO_DO_NUCLEO.findall(texto)
        frase = "O arquivo pode estar danificado, ser de outra versão ou de outro console."
        if ultimo:
            frase += " (O emulador disse: “%s”.)" % ultimo[-1].strip()[:140]
        partes.append(frase)

    abertura = "%s não abriu este jogo." % quem
    return {"texto": abertura + " " + " ".join(partes), "faltando": faltando,
            "renomear": renomear, "discos": discos}
