# -*- coding: utf-8 -*-
r"""Os 60 quadros de verdade no PS2: os patches "60 FPS" que o proprio PCSX2 traz.

Pedido de 11/11/2026: juntar o melhor do Lossless Scaling e do MFG Super
Motion dentro do ARENA. Os dois criam quadros "de mentira" a partir da
imagem pronta (copiam a tela e adivinham o meio do movimento): custa a placa
de video, atrasa um pouco o controle e erra nas bordas do que se move. No
PS2 da para fazer melhor: muitos jogos rodam a 30 quadros por escolha de
quem os fez, e a comunidade do PCSX2 escreveu patches que fazem o PROPRIO
jogo rodar a 60. O PCSX2 2.8.2 desta pasta ja traz 627 deles, dentro do
resources\patches.zip. Sao quadros de verdade: nada copiado, nada adivinhado.

Como o PCSX2 liga um patch (conferido no registro dele, emulog.txt, em
11/11/2026, com o Black: "Enabled patch: 60 FPS"):
  - cada jogo tem o seu arquivo de ajuste, gamesettings\SERIAL_CRC.ini;
  - ali, na secao [Patches], uma linha "Enable = <nome do patch>".
O SERIAL vem do SYSTEM.CNF do disco (BOOT2 = cdrom0:\SLUS_213.76;1 da
SLUS-21376) e o CRC e' o "ou exclusivo" de todas as palavras de 32 bits do
programa do jogo (o ELF). Conferido nos 5 ISOs de PS2 do PC do Rafael: os
5 batem com o nome de um .pnach do patches.zip.

Disco comprimido (CHD, CSO) o ARENA nao abre sem biblioteca de fora. Ali
ele aprende na primeira partida: o PCSX2 escreve o serial e o CRC no
registro dele, e da segunda vez em diante o patch ja vale.

O ARENA so mexe na linha que ele mesmo pos (guarda quais em
dados\ps2_patches_do_arena.json): o ajuste que a pessoa fez no PCSX2 fica.
"""
import json
import os
import re
import struct
import zipfile

import identificador

ARQUIVO_DO_ARENA = "ps2_patches_do_arena.json"
ARQUIVO_DOS_JOGOS = "ps2_jogos_aprendidos.json"
# O nome do patch de 60 quadros varia de jogo para jogo ("60 FPS", "60 fps", "50/60 FPS",
# "60 fps & No Interlacing"): vale o que comeca pelo numero.
_SESSENTA = re.compile(r"^\s*(?:50\s*/\s*)?60\s*fps\b", re.I)
_MAIOR_ELF = 64 * 1024 * 1024


# ---------------------------------------------------------------------------
# Serial e CRC
# ---------------------------------------------------------------------------
def crc_do_elf(dados):
    """O CRC do PCSX2: o "ou exclusivo" de todas as palavras de 32 bits do ELF."""
    crc = 0
    for (palavra,) in struct.iter_unpack("<I", dados[:len(dados) // 4 * 4]):
        crc ^= palavra
    return crc


def serial_do_elf(nome_do_elf):
    """SLUS_213.76 -> SLUS-21376."""
    nome = nome_do_elf.upper().split(";")[0].replace("_", "-").replace(".", "")
    return nome if re.match(r"^[A-Z]{4}-\d{5}$", nome) else ""


def ler_do_iso(caminho):
    """(serial, crc) de um ISO de PS2, ou None (outro formato, ou o programa fora da raiz do disco)."""
    try:
        with open(caminho, "rb") as arquivo:
            descritor = identificador._descritor_primario(arquivo)
            if not descritor:
                return None
            achados = identificador._procurar_no_raiz(arquivo, descritor, ["SYSTEM.CNF"])
            if "SYSTEM.CNF" not in achados:
                return None
            setor, tamanho = achados["SYSTEM.CNF"]
            arquivo.seek(setor * identificador.SETOR)
            cnf = arquivo.read(min(tamanho, 4096)).decode("latin-1", "replace")
            achou = re.search(r"BOOT2\s*=\s*cdrom0:\\+([^;\s]+)", cnf, re.I)
            if not achou:
                return None
            elf = achou.group(1).upper()
            serial = serial_do_elf(elf)
            lugar = identificador._procurar_no_raiz(arquivo, descritor, [elf])
            if not serial or elf not in lugar or not 0 < lugar[elf][1] <= _MAIOR_ELF:
                return None
            arquivo.seek(lugar[elf][0] * identificador.SETOR)
            dados = arquivo.read(lugar[elf][1])
    except OSError:
        return None
    return serial, "%08X" % crc_do_elf(dados)


def ler_do_registro(texto):
    """(serial, crc) das linhas "Serial: ..." e "CRC: ..." do emulog.txt do PCSX2, ou None."""
    serial = re.findall(r"^\s*(?:\[[^\]]*\]\s*)?Serial:\s*([A-Z]{4}-\d{5})\s*$", texto or "", re.M)
    crc = re.findall(r"^\s*(?:\[[^\]]*\]\s*)?CRC:\s*([0-9A-Fa-f]{8})\s*$", texto or "", re.M)
    if serial and crc and crc[-1] != "00000000":
        return serial[-1], crc[-1].upper()
    return None


def _chave_do_arquivo(caminho):
    """O jogo, sem caminho absoluto (o pen drive troca de letra): nome e tamanho."""
    try:
        return "%s|%d" % (os.path.basename(caminho), os.path.getsize(caminho))
    except OSError:
        return os.path.basename(caminho)


def _ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def _gravar(caminho, texto):
    """Gravacao atomica: temporario ao lado e troca (o pen drive pode sair no meio)."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = "%s.%d.tmp" % (caminho, os.getpid())
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
    os.replace(temporario, caminho)


def identificar(caminho, pasta_dados):
    """(serial, crc) do jogo: do ISO, ou do que o ARENA aprendeu numa partida anterior. None se nao sabe."""
    if caminho.lower().endswith(".iso"):
        lido = ler_do_iso(caminho)
        if lido:
            return lido
    aprendido = _ler_json(os.path.join(pasta_dados, ARQUIVO_DOS_JOGOS)).get(_chave_do_arquivo(caminho))
    if isinstance(aprendido, list) and len(aprendido) == 2:
        return aprendido[0], aprendido[1]
    return None


def aprender_do_registro(pasta_pcsx2, caminho, pasta_dados):
    """Depois da partida: guarda o serial e o CRC que o PCSX2 escreveu no registro. Devolve (serial, crc) ou None."""
    try:
        with open(os.path.join(pasta_pcsx2, "logs", "emulog.txt"), encoding="utf-8", errors="replace") as arquivo:
            lido = ler_do_registro(arquivo.read())
    except OSError:
        return None
    if not lido:
        return None
    arquivo_dos_jogos = os.path.join(pasta_dados, ARQUIVO_DOS_JOGOS)
    jogos = _ler_json(arquivo_dos_jogos)
    chave = _chave_do_arquivo(caminho)
    if jogos.get(chave) != list(lido):
        jogos[chave] = list(lido)
        _gravar(arquivo_dos_jogos, json.dumps(jogos, ensure_ascii=False, indent=1))
    return lido


# ---------------------------------------------------------------------------
# Os patches do jogo
# ---------------------------------------------------------------------------
def nomes_dos_patches(texto):
    """Os nomes dos patches de um .pnach (as linhas [Nome])."""
    return [nome.strip() for nome in re.findall(r"^\s*\[([^\]\r\n]+)\]\s*$", texto or "", re.M)]


def patches_do_jogo(pasta_pcsx2, serial, crc):
    """Os nomes dos patches que o PCSX2 tem para este jogo (o patches.zip dele e a pasta patches)."""
    nome = "%s_%s.pnach" % (serial, crc)
    textos = []
    try:
        with zipfile.ZipFile(os.path.join(pasta_pcsx2, "resources", "patches.zip")) as pacote:
            if nome in pacote.namelist():
                textos.append(pacote.read(nome).decode("utf-8", "replace"))
    except (OSError, zipfile.BadZipFile):
        pass
    solto = os.path.join(pasta_pcsx2, "patches", nome)
    if os.path.isfile(solto):
        try:
            with open(solto, encoding="utf-8", errors="replace") as arquivo:
                textos.append(arquivo.read())
        except OSError:
            pass
    vistos = []
    for texto in textos:
        for patch in nomes_dos_patches(texto):
            if patch not in vistos:
                vistos.append(patch)
    return vistos


def patch_de_60(nomes):
    """O patch de 60 quadros da lista, ou "". Prefere o que e' so isso ("60 FPS") ao que junta outra coisa."""
    candidatos = [n for n in nomes if _SESSENTA.match(n)]
    if not candidatos:
        return ""
    sozinhos = [n for n in candidatos if re.fullmatch(r"\s*(?:50\s*/\s*)?60\s*fps\s*", n, re.I)]
    return (sozinhos or candidatos)[0]


# ---------------------------------------------------------------------------
# O arquivo do jogo no PCSX2 (gamesettings\SERIAL_CRC.ini)
# ---------------------------------------------------------------------------
def _trocar_na_secao(texto, nome, ligar):
    """O texto do .ini com (ligar) ou sem a linha "Enable = nome" na secao [Patches]. O resto fica igual."""
    linhas = texto.splitlines()
    inicio = next((i for i, l in enumerate(linhas) if l.strip().lower() == "[patches]"), None)
    if inicio is None:
        if not ligar:
            return texto
        if linhas and linhas[-1].strip():
            linhas.append("")
        linhas += ["[Patches]", "Enable = %s" % nome]
        return "\n".join(linhas) + "\n"
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].strip().startswith("[")), len(linhas))
    padrao = re.compile(r"^\s*Enable\s*=\s*%s\s*$" % re.escape(nome), re.I)
    tem = any(padrao.match(l) for l in linhas[inicio + 1:fim])
    if ligar and not tem:
        linhas.insert(inicio + 1, "Enable = %s" % nome)
    elif not ligar and tem:
        linhas = linhas[:inicio + 1] + [l for l in linhas[inicio + 1:fim] if not padrao.match(l)] + linhas[fim:]
    return "\n".join(linhas) + "\n"


def aplicar(pasta_pcsx2, serial, crc, ligar, pasta_dados):
    """Liga (ou tira) o patch de 60 quadros deste jogo. Devolve o nome do patch ligado, ou "".

    So tira a linha que o ARENA pos; o arquivo que o ARENA criou e ficou
    vazio sai de novo."""
    jogo = "%s_%s" % (serial, crc)
    arquivo = os.path.join(pasta_pcsx2, "gamesettings", jogo + ".ini")
    registro_arquivo = os.path.join(pasta_dados, ARQUIVO_DO_ARENA)
    registro = _ler_json(registro_arquivo)
    feito = registro.get(jogo) or {}
    if not isinstance(feito, dict):
        feito = {}
    try:
        with open(arquivo, encoding="utf-8", errors="replace") as lido:
            texto = lido.read()
        existia = True
    except OSError:
        texto, existia = "", False
    nome = patch_de_60(patches_do_jogo(pasta_pcsx2, serial, crc)) if ligar else ""
    if ligar and not nome:
        ligar = False
    if ligar:
        novo = _trocar_na_secao(texto, nome, True)
        if novo != texto:
            _gravar(arquivo, novo)
            registro[jogo] = {"patch": nome, "criou_o_arquivo": feito.get("criou_o_arquivo", not existia)}
            _gravar(registro_arquivo, json.dumps(registro, ensure_ascii=False, indent=1))
        return nome
    if feito.get("patch") and existia:
        novo = _trocar_na_secao(texto, feito["patch"], False)
        if feito.get("criou_o_arquivo") and novo.strip().lower() in ("", "[patches]"):
            try:
                os.remove(arquivo)
            except OSError:
                pass
        elif novo != texto:
            _gravar(arquivo, novo)
    if jogo in registro:
        del registro[jogo]
        _gravar(registro_arquivo, json.dumps(registro, ensure_ascii=False, indent=1))
    return ""


def decidir(modo, nota, nota_gpu, degrau):
    """Liga os 60 quadros neste PS2? (ligar, motivo)

    O patch faz o jogo rodar o dobro: pesa o dobro no processador e na placa.
    - "desligado": nunca; "sempre": sempre que o jogo tiver o patch;
    - "automatico": processador forte (nota 4 ou mais) e placa DEDICADA forte
      ('nota_gpu' e' a nota dos emuladores de fora, que na integrada para no
      3: a integrada divide a memoria com o emulador, e o dobro de quadros
      podia deixar o jogo pior que os 30 lisos de antes -- regra do Rafael,
      11/11/2026: "nunca regresso de desempenho"), e o console nao ficou no
      limite antes (o "Desempenho que aprende" nao desceu degrau). No
      Celeron N5100 da rede fica desligado; quem quiser, escolhe "Sempre"."""
    if modo == "desligado":
        return False, "desligado nos Ajustes"
    if modo == "sempre":
        return True, "ligado sempre, nos Ajustes"
    if int(degrau or 0) > 0:
        return False, "o PS2 ficou no limite da maquina antes"
    if int(nota or 0) < 4 or int(nota_gpu or 0) < 4:
        return False, "o dobro de quadros pede processador e placa de video dedicada fortes"
    return True, "maquina forte"
