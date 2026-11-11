# -*- coding: utf-8 -*-
r"""Os 60 quadros de verdade no GameCube e no Wii: os codigos "60fps" que o proprio Dolphin traz.

O irmao do servidor\quadros_ps2.py (11/11/2026). O Dolphin desta pasta traz,
em Sys\GameSettings\<ID>.ini, codigos da comunidade para cada jogo, e 25
deles tem um codigo de 60 quadros ("$60fps", "$60 FPS [Nerdzilla]"...).
Sao quadros de verdade, do proprio jogo: nada copiado, nada adivinhado.

Como o Dolphin liga um codigo so para um jogo (o formato dos proprios .ini
do Sys, conferido em 11/11/2026): o arquivo do usuario
User\GameSettings\<ID>.ini com
    [Core]
    EnableCheats = True
    [Gecko_Enabled]        (ou [ActionReplay_Enabled], ou [OnFrame_Enabled],
    $60fps                  conforme a secao em que o codigo esta)
As trapacas ficam ligadas SO nesse jogo: o Dolphin.ini geral nao muda.

O ID do jogo (6 letras: GM4P01) esta no comeco do disco: no .iso/.gcm no
byte 0; no .wbfs no byte 0x200; no .rvz/.wia no byte 0x58 (o cabecalho do
disco copiado no arquivo, docs/WiaAndRvz.md do Dolphin). Conferido nos 8
discos do PC do Rafael. A revisao do disco (byte 7) escolhe o <ID>r<N>.ini
quando ele existe.

O ARENA so mexe nas linhas que ele mesmo pos (dados\dolphin_codigos_do_arena.json).
"""
import json
import os
import re

ARQUIVO_DO_ARENA = "dolphin_codigos_do_arena.json"
SECOES_DE_CODIGO = ("Gecko", "ActionReplay", "OnFrame")
_SESSENTA = re.compile(r"^\s*\$\s*60\s*fps\b", re.I)


# ---------------------------------------------------------------------------
# O ID do jogo
# ---------------------------------------------------------------------------
def ler_id(caminho):
    """(id de 6 letras, revisao) do disco, ou None."""
    try:
        with open(caminho, "rb") as arquivo:
            cabeca = arquivo.read(0x60)
            if cabeca[:3] in (b"RVZ", b"WIA") and len(cabeca) >= 0x60:
                bruto = cabeca[0x58:0x60]
            elif cabeca[:4] == b"WBFS":
                arquivo.seek(0x200)
                bruto = arquivo.read(8)
            else:
                bruto = cabeca[:8]
    except OSError:
        return None
    jogo = bruto[:6].decode("ascii", "ignore")
    if not re.fullmatch(r"[A-Z0-9]{6}", jogo):
        return None
    return jogo, bruto[7] if len(bruto) > 7 else 0


# ---------------------------------------------------------------------------
# Os codigos do jogo
# ---------------------------------------------------------------------------
def _ler(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="replace") as arquivo:
            return arquivo.read()
    except OSError:
        return ""


def arquivos_do_jogo(pasta_dolphin, jogo, revisao=0):
    """Os .ini do Sys que valem para este jogo: <ID>r<rev>.ini (se existir) e <ID>.ini."""
    pasta = os.path.join(pasta_dolphin, "Sys", "GameSettings")
    candidatos = ["%sr%d.ini" % (jogo, revisao), "%s.ini" % jogo]
    return [os.path.join(pasta, nome) for nome in candidatos if os.path.isfile(os.path.join(pasta, nome))]


def codigos(texto):
    """{secao: [nomes dos codigos]} das secoes [Gecko], [ActionReplay] e [OnFrame] de um .ini do Dolphin."""
    achados = {}
    secao = None
    for linha in (texto or "").splitlines():
        limpa = linha.strip()
        if limpa.startswith("[") and limpa.endswith("]"):
            nome = limpa[1:-1]
            secao = nome if nome in SECOES_DE_CODIGO else None
        elif secao and limpa.startswith("$"):
            achados.setdefault(secao, []).append(limpa)
    return achados


def codigo_de_60(pasta_dolphin, jogo, revisao=0):
    """(secao, "$60fps") do codigo de 60 quadros deste jogo, ou None."""
    for arquivo in arquivos_do_jogo(pasta_dolphin, jogo, revisao):
        for secao, nomes in codigos(_ler(arquivo)).items():
            for nome in nomes:
                if _SESSENTA.match(nome):
                    return secao, nome
    return None


# ---------------------------------------------------------------------------
# O .ini do usuario (User\GameSettings\<ID>.ini)
# ---------------------------------------------------------------------------
def _secoes(texto):
    """[(nome ou None, [linhas])] na ordem do arquivo."""
    blocos, atual = [], (None, [])
    for linha in (texto or "").splitlines():
        limpa = linha.strip()
        if limpa.startswith("[") and limpa.endswith("]"):
            blocos.append(atual)
            atual = (limpa[1:-1], [])
        else:
            atual[1].append(linha)
    blocos.append(atual)
    return blocos


def _montar(blocos):
    saida = []
    for nome, linhas in blocos:
        if nome is not None:
            saida.append("[%s]" % nome)
        saida.extend(linhas)
    texto = "\n".join(saida).strip("\n")
    return texto + "\n" if texto else ""


def _por_na_secao(blocos, nome, linha):
    for secao, linhas in blocos:
        if secao == nome:
            if not any(l.strip().lower() == linha.lower() for l in linhas):
                linhas.append(linha)
            return blocos
    blocos.append((nome, [linha]))
    return blocos


def _tirar_da_secao(blocos, nome, linha):
    novos = []
    for secao, linhas in blocos:
        if secao == nome:
            linhas = [l for l in linhas if l.strip().lower() != linha.lower()]
            if not any(l.strip() for l in linhas):
                continue
        novos.append((secao, linhas))
    return novos


def _gravar(caminho, texto):
    """Gravacao atomica, com a espera do os.replace quando outra thread esta lendo (como quadros_ps2._gravar)."""
    import time
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    temporario = "%s.%d.tmp" % (caminho, os.getpid())
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
    for tentativa in range(20):
        try:
            os.replace(temporario, caminho)
            return
        except PermissionError:
            if tentativa == 19:
                try:
                    os.remove(temporario)
                except OSError:
                    pass
                raise
            time.sleep(0.05)


def _ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def aplicar(pasta_dolphin, jogo, revisao, ligar, pasta_dados):
    """Liga (ou tira) o codigo de 60 quadros deste jogo. Devolve o nome do codigo ligado, ou ""."""
    arquivo = os.path.join(pasta_dolphin, "User", "GameSettings", jogo + ".ini")
    registro_arquivo = os.path.join(pasta_dados, ARQUIVO_DO_ARENA)
    registro = _ler_json(registro_arquivo)
    feito = registro.get(jogo) or {}
    if not isinstance(feito, dict):
        feito = {}
    texto = _ler(arquivo)
    existia = os.path.isfile(arquivo)
    achado = codigo_de_60(pasta_dolphin, jogo, revisao) if ligar else None
    if ligar and achado:
        secao, nome = achado
        blocos = _secoes(texto)
        blocos = _por_na_secao(blocos, "Core", "EnableCheats = True")
        blocos = _por_na_secao(blocos, secao + "_Enabled", nome)
        novo = _montar(blocos)
        if novo != texto:
            _gravar(arquivo, novo)
            registro[jogo] = {"secao": secao, "codigo": nome, "criou_o_arquivo": feito.get("criou_o_arquivo", not existia),
                              # So o ARENA ligou as trapacas? Entao e' ele quem desliga.
                              "ligou_as_trapacas": feito.get("ligou_as_trapacas",
                                                             "enablecheats" not in texto.lower())}
            _gravar(registro_arquivo, json.dumps(registro, ensure_ascii=False, indent=1))
        return nome
    if feito.get("codigo") and existia:
        blocos = _tirar_da_secao(_secoes(texto), feito.get("secao", "Gecko") + "_Enabled", feito["codigo"])
        if feito.get("ligou_as_trapacas"):
            blocos = _tirar_da_secao(blocos, "Core", "EnableCheats = True")
        novo = _montar(blocos)
        if feito.get("criou_o_arquivo") and not novo.strip():
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
