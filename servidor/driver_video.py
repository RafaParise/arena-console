# -*- coding: utf-8 -*-
r"""O painel do driver da placa de video (AMD Software: Adrenalin Edition; o da Intel), lido pelo ARENA.

Pedido do Rafael (11/11/2026): "alinhe a configuracao do AMD Software para
extrair o maximo de desempenho e faca o ARENA saber detectar essas
configuracoes, tanto da AMD, que vai ter o exemplo real, como da Intel".

O que da e o que nao da para fazer, sem administrador:
  - As opcoes globais do driver ficam em HKLM (a chave da classe
    "Adaptadores de video", {4d36e968-...}\000N e a subchave UMD dela). LER
    qualquer um pode; GRAVAR so o administrador -- e o ARENA nunca grava no
    registro (restricao do projeto). O perfil por jogo do Adrenalin nao
    esta em lugar nenhum que o ARENA alcance (procurado em 11/11/2026: nem
    no registro, nem no gmdb.blb, que so guarda RSR, FreeSync e cor).
  - Entao o ARENA LE o painel, se ALINHA a ele (a frequencia que o "Mais
    quadros" segue, a escala que ele nao repete) e MOSTRA, em Ajustes ->
    Maquina, o que esta como esta e o que vale a pena mudar a mao.

Os valores e o que cada um significa foram lidos no PC do Rafael (Ryzen 5
5600G, Radeon integrada, AMD Software 26.5.2, driver 31.0.21925.1001):
  - UMD\VSyncControl (texto UTF-16 em REG_BINARY): "0" sempre desligado,
    "1" desligado salvo o que o jogo pedir, "2" ligado salvo o jogo, "3"
    sempre ligado  [Provavel: a tabela e' a do driver; neste PC esta "3"];
  - UMD\TFQ (qualidade da filtragem de textura): "0" alta, "1" padrao, "2"
    desempenho  [Provavel; aqui "2"];
  - UMD\Tessellation_OPTION: "0" otimizado pela AMD, "1" do jogo, "2"
    forcado no nivel de UMD\Tessellation  [Provavel; aqui "0"];
  - UMD\AnisoType "0" do jogo / "1" forcado; UMD\AntiAlias "1" do jogo, "2"
    melhora o do jogo, "3" forcado  [Provavel; aqui "0" e "1"];
  - UMD\TurboSync: o Enhanced Sync  [Provavel; aqui "0"];
  - UMD\ShaderCache: "0" desligado, "1" otimizado (ligado)  [Provavel; "1"];
  - KMD_DeLagEnabled (DWORD): o Anti-Lag  [Certo pelo nome; aqui 0];
  - KMD_USUEnable (DWORD): o Radeon Super Resolution (RSR), e
    KMD_USUSharpeningDegree a nitidez dele, um float nos 4 bytes  [Provavel;
    aqui 0 e 0,3];
  - KMD_FRTEnabled + KMD_MaxFrameRateRequested: o limite de quadros (Frame
    Rate Target Control)  [Certo pelo nome; aqui 1 e 60];
  - HKLM\SOFTWARE\AMD\CN: CNVersion e DriverVersion do painel;
  - HKCU\Software\AMD\DVR\DvrEnabled: a gravacao do Adrenalin (aqui 0).
Os valores brutos vao para a tela junto com a leitura, para quem conferir
no painel enxergar qualquer diferenca.

Intel: o ARENA reconhece a placa e a versao do driver e se o painel dela
(Intel Graphics Command Center ou Intel Arc Control, pacotes da Loja) esta
instalado; as opcoes do painel ele ainda NAO le -- nao houve maquina Intel
para conferir onde ficam. NVIDIA: idem, so a versao.
"""
import os
import struct

CLASSE_DE_VIDEO = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
PACOTES_APPX = (r"Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel"
                r"\Repository\Packages")
PAINEIS_INTEL = {"AppUp.IntelGraphicsExperience": "Intel Graphics Command Center",
                 "AppUp.IntelArcControl": "Intel Arc Control"}
_CACHE = {}


# ---------------------------------------------------------------------------
# Leitura crua do registro (so leitura, sem administrador)
# ---------------------------------------------------------------------------
def texto_utf16(valor):
    """Os valores da UMD sao textos UTF-16 guardados como bytes ("3\\x00"). Devolve o texto limpo."""
    if isinstance(valor, (bytes, bytearray)):
        try:
            return valor.decode("utf-16-le", "ignore").strip("\x00").strip()
        except Exception:
            return ""
    return str(valor).strip() if valor is not None else ""


def float_de_dword(valor):
    """Um float guardado nos 4 bytes de um DWORD (a nitidez do RSR: 1050253722 -> 0.3)."""
    try:
        return round(struct.unpack("<f", struct.pack("<I", int(valor) & 0xFFFFFFFF))[0], 2)
    except (struct.error, ValueError, TypeError):
        return None


def _ler_valores(raiz, caminho, nomes):
    """{nome: valor} dos nomes que existirem na chave; {} se a chave nao abrir."""
    if os.name != "nt":
        return {}
    import winreg
    lidos = {}
    try:
        chave = winreg.OpenKey(raiz, caminho)
    except OSError:
        return {}
    try:
        for nome in nomes:
            try:
                lidos[nome] = winreg.QueryValueEx(chave, nome)[0]
            except OSError:
                pass
    finally:
        winreg.CloseKey(chave)
    return lidos


def _subchaves(raiz, caminho):
    if os.name != "nt":
        return []
    import winreg
    nomes = []
    try:
        chave = winreg.OpenKey(raiz, caminho)
    except OSError:
        return []
    try:
        indice = 0
        while True:
            try:
                nomes.append(winreg.EnumKey(chave, indice))
            except OSError:
                break
            indice += 1
    finally:
        winreg.CloseKey(chave)
    return nomes


def versao_instalada(comeco_do_nome):
    """A DisplayVersion do programa cujo nome comeca assim, na lista de programas instalados do Windows."""
    if os.name != "nt":
        return ""
    import winreg
    for raiz in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
        for sub in _subchaves(winreg.HKEY_LOCAL_MACHINE, raiz):
            lidos = _ler_valores(winreg.HKEY_LOCAL_MACHINE, raiz + "\\" + sub, ("DisplayName", "DisplayVersion"))
            if str(lidos.get("DisplayName", "")).startswith(comeco_do_nome) and lidos.get("DisplayVersion"):
                return str(lidos["DisplayVersion"])
    return ""


def adaptadores():
    """[(indice "000N", DriverDesc, ProviderName, DriverVersion)] da classe de video, na ordem do registro."""
    if os.name != "nt":
        return []
    import winreg
    lista = []
    for indice in range(16):
        sub = "%s\\%04d" % (CLASSE_DE_VIDEO, indice)
        lidos = _ler_valores(winreg.HKEY_LOCAL_MACHINE, sub, ("DriverDesc", "ProviderName", "DriverVersion"))
        if lidos.get("DriverDesc"):
            lista.append(("%04d" % indice, str(lidos["DriverDesc"]), str(lidos.get("ProviderName", "")),
                          str(lidos.get("DriverVersion", ""))))
    return lista


def fabricante_do_provedor(provedor):
    p = (provedor or "").lower()
    if "advanced micro" in p or p.startswith("amd") or "ati " in p:
        return "amd"
    if "intel" in p:
        return "intel"
    if "nvidia" in p:
        return "nvidia"
    return ""


def adaptador_da_placa(nome_da_placa):
    """O adaptador (indice, nome, provedor, versao) da placa da tela principal, pelo nome; senao o primeiro que
    nao seja virtual (os "Remote Display", "Virtual Display", "Basic")."""
    lista = adaptadores()
    limpo = " ".join((nome_da_placa or "").split()).lower()
    for item in lista:
        if limpo and " ".join(item[1].split()).lower() == limpo:
            return item
    for item in lista:
        if fabricante_do_provedor(item[2]) and not any(
                v in item[1].lower() for v in ("remote display", "virtual display", "basic")):
            return item
    return None


# ---------------------------------------------------------------------------
# AMD
# ---------------------------------------------------------------------------
_UMD_TEXTOS = ("VSyncControl", "TFQ", "Tessellation_OPTION", "Tessellation", "AnisoType", "AnisoDegree",
               "AntiAlias", "AntiAliasSamples", "TurboSync", "ShaderCache", "AntiStuttering")
_KMD_NUMEROS = ("KMD_DeLagEnabled", "KMD_USUEnable", "KMD_USUSharpeningDegree", "KMD_FRTEnabled",
                "KMD_MaxFrameRateRequested")


def ler_amd(indice):
    """Os valores brutos do driver AMD deste adaptador (ja decodificados para texto e numero)."""
    import winreg
    base = "%s\\%s" % (CLASSE_DE_VIDEO, indice)
    brutos = {}
    for nome, valor in _ler_valores(winreg.HKEY_LOCAL_MACHINE, base + "\\UMD", _UMD_TEXTOS).items():
        brutos[nome] = texto_utf16(valor)
    for nome, valor in _ler_valores(winreg.HKEY_LOCAL_MACHINE, base, _KMD_NUMEROS).items():
        try:
            brutos[nome] = int(valor)
        except (TypeError, ValueError):
            pass
    painel = _ler_valores(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AMD\CN", ("CNVersion", "DriverVersion"))
    # A versao que a pessoa ve ("26.5.2") esta na lista de programas instalados; a CNVersion e' o numero interno.
    brutos["painel_versao"] = versao_instalada("AMD Software") or str(painel.get("CNVersion", "") or "")
    gravacao = _ler_valores(winreg.HKEY_CURRENT_USER, r"Software\AMD\DVR", ("DvrEnabled",))
    if "DvrEnabled" in gravacao:
        try:
            brutos["DvrEnabled"] = int(gravacao["DvrEnabled"])
        except (TypeError, ValueError):
            pass
    return brutos


def _item(chave, nome, valor_lido, bruto, efeito, certo=True, mude=""):
    return {"chave": chave, "nome": nome, "valor": valor_lido, "bruto": "" if bruto is None else str(bruto),
            "efeito": efeito, "certo": bool(certo), "mude": mude}


def interpretar_amd(brutos, hz_da_tela=60):
    """Os valores brutos viram a lista da tela: o que cada opcao faz no ARENA e se vale mudar a mao.

    "certo" = esta como o ARENA precisa; "mude" = o que escolher no AMD Software (e por que). Regra do Rafael:
    nunca regresso de desempenho -- so entra como "mude" o que, mudado, nao pode piorar o jogo."""
    itens = []
    b = brutos or {}

    vs = b.get("VSyncControl", "")
    nomes_vs = {"0": "sempre desligado", "1": "desligado, salvo o que o jogo pedir",
                "2": "ligado, salvo o que o jogo pedir", "3": "sempre ligado"}
    itens.append(_item("vsync", "Aguardar a atualização vertical (VSync)", nomes_vs.get(vs, "não li"), vs,
                       "O ARENA já sincroniza cada quadro com a tela (vsync do RetroArch e dos emuladores). "
                       "Forçado no driver, nada muda no jogo; só o Mais quadros passa a seguir o driver.",
                       certo=True))

    tfq = b.get("TFQ", "")
    nomes_tfq = {"0": "alta", "1": "padrão", "2": "desempenho"}
    itens.append(_item("textura", "Qualidade da filtragem de textura", nomes_tfq.get(tfq, "não li"), tfq,
                       "Vale para todo jogo 3D (PS2, GameCube, Wii, PS1 desenhado grande): em \"desempenho\" o "
                       "driver simplifica as texturas e a imagem perde detalhe de perto.",
                       certo=tfq in ("", "0", "1"),
                       mude="" if tfq in ("", "0", "1") else
                       "Padrão (ou Alta). O custo na placa é pequeno e a textura do jogo volta inteira."))

    tess = b.get("Tessellation_OPTION", "")
    nomes_tess = {"0": "otimizado pela AMD", "1": "o que o jogo pedir", "2": "forçado em %sx" % b.get("Tessellation", "?")}
    itens.append(_item("tesselacao", "Tesselação", nomes_tess.get(tess, "não li"), tess,
                       "Os emuladores quase não usam; o \"otimizado pela AMD\" não atrapalha.", certo=tess != "2",
                       mude="" if tess != "2" else "Otimizado pela AMD: forçado só gasta placa à toa."))

    aniso, aa = b.get("AnisoType", ""), b.get("AntiAlias", "")
    forcados = (aniso == "1") or (aa == "3")
    itens.append(_item("filtros", "Filtragem anisotrópica e anti-serrilhado", "do jogo" if not forcados else "forçados pelo driver",
                       "%s / %s" % (aniso, aa),
                       "O ARENA escolhe os dois por console e pela nota da placa (graficos.json). Forçados no "
                       "driver, somam-se aos do ARENA e pesam duas vezes.", certo=not forcados,
                       mude="" if not forcados else "Usar as configurações do aplicativo, nos dois."))

    rsr = int(b.get("KMD_USUEnable", 0) or 0) == 1
    nitidez = float_de_dword(b.get("KMD_USUSharpeningDegree")) if "KMD_USUSharpeningDegree" in b else None
    itens.append(_item("rsr", "Radeon Super Resolution (RSR)",
                       ("ligado, nitidez %s" % nitidez) if rsr else "desligado", b.get("KMD_USUEnable"),
                       "Estica qualquer jogo em tela cheia desenhado menor que a tela. O ARENA já estica com o "
                       "filtro certo de cada console (pixel nítido, FSR, Catmull-Rom) e, ligado, o RSR estica por "
                       "cima: duas vezes o trabalho e a imagem mais borrada. Com o RSR ligado, o ARENA deixa o "
                       "FSR dele de lado e aplica só a nitidez.", certo=not rsr,
                       mude="" if not rsr else "Desligado: a escala do ARENA, por console, fica melhor e mais leve."))

    antilag = int(b.get("KMD_DeLagEnabled", 0) or 0) == 1
    itens.append(_item("antilag", "Radeon Anti-Lag", "ligado" if antilag else "desligado", b.get("KMD_DeLagEnabled"),
                       "Encurta a fila entre o processador e a placa: o controle responde um pouco antes. Ajuda "
                       "mais com o Mais quadros ligado (os quadros criados somam um pouco de atraso). Não medido "
                       "no ARENA.", certo=True))

    frt = int(b.get("KMD_FRTEnabled", 0) or 0) == 1
    limite = int(b.get("KMD_MaxFrameRateRequested", 0) or 0)
    hz = int(hz_da_tela or 60)
    itens.append(_item("limite", "Limite de quadros (Frame Rate Target Control)",
                       ("ligado, %d quadros por segundo" % limite) if frt else "desligado",
                       "%s / %s" % (b.get("KMD_FRTEnabled", ""), b.get("KMD_MaxFrameRateRequested", "")),
                       "O ARENA já segura cada emulador na velocidade do console. O limite do driver só pesa quando "
                       "é menor que a tela: aí o Mais quadros cria quadros que o driver descarta. O ARENA segue o "
                       "menor dos dois.", certo=(not frt) or limite >= hz,
                       mude="" if (not frt) or limite >= hz else
                       "Desligado, ou igual aos %d Hz da tela: hoje ele corta o Mais quadros em %d." % (hz, limite)))

    turbo = b.get("TurboSync", "")
    itens.append(_item("enhanced", "Enhanced Sync", "ligado" if turbo == "1" else "desligado", turbo,
                       "Troca o vsync por um quadro mais novo sem rasgar. Com o Mais quadros, quem sincroniza é o "
                       "programa de quadros; sem ele, o vsync do ARENA já faz o papel.", certo=True))

    cache = b.get("ShaderCache", "")
    itens.append(_item("cache", "Cache de shaders", "ligado" if cache in ("1", "2") else ("desligado" if cache == "0" else "não li"),
                       cache, "Guarda os shaders compilados: o PS2 e o Dolphin engasgam menos nas primeiras cenas.",
                       certo=cache != "0", mude="" if cache != "0" else "Otimizado pela AMD (ligado)."))

    if "DvrEnabled" in b:
        dvr = int(b.get("DvrEnabled", 0) or 0) == 1
        itens.append(_item("gravacao", "Gravação e replay do AMD Software", "ligada" if dvr else "desligada",
                           b.get("DvrEnabled"),
                           "Fica gravando a tela o tempo todo. No ARENA a gravação fica desligada de propósito "
                           "(dados dos alunos), e ela gasta placa durante o jogo.", certo=not dvr,
                           mude="" if not dvr else "Desligada."))
    return itens


# ---------------------------------------------------------------------------
# Intel (e NVIDIA): so o que da para conferir sem a maquina
# ---------------------------------------------------------------------------
def paineis_da_intel():
    """Os paineis da Intel instalados (pacotes da Loja, na lista do usuario): ["Intel Arc Control", ...]."""
    if os.name != "nt":
        return []
    import winreg
    achados = []
    for nome in _subchaves(winreg.HKEY_CURRENT_USER, PACOTES_APPX):
        for prefixo, titulo in PAINEIS_INTEL.items():
            if nome.startswith(prefixo + "_") and titulo not in achados:
                achados.append(titulo)
    return achados


# ---------------------------------------------------------------------------
# O que o ARENA usa
# ---------------------------------------------------------------------------
def situacao(nome_da_placa="", hz_da_tela=60):
    """Para a tela e para o alinhamento. Lido uma vez por abertura (cache): o registro nao muda sem reiniciar o
    painel, e a tela dos Ajustes pode pedir varias vezes."""
    chave = (nome_da_placa, int(hz_da_tela or 60))
    if chave in _CACHE:
        return _CACHE[chave]
    resultado = {"fabricante": "", "placa": nome_da_placa or "", "driver": "", "painel": "", "itens": [],
                 "le_as_opcoes": False, "hz_limite": None, "rsr": False, "antilag": False, "vsync_forcado": False}
    if os.name != "nt":
        _CACHE[chave] = resultado
        return resultado
    adaptador = adaptador_da_placa(nome_da_placa)
    if adaptador:
        indice, nome, provedor, versao = adaptador
        resultado.update({"fabricante": fabricante_do_provedor(provedor), "placa": nome, "driver": versao})
        if resultado["fabricante"] == "amd":
            brutos = ler_amd(indice)
            resultado["itens"] = interpretar_amd(brutos, hz_da_tela)
            resultado["le_as_opcoes"] = bool(brutos)
            resultado["painel"] = ("AMD Software: Adrenalin Edition " + brutos["painel_versao"]).strip() \
                if brutos.get("painel_versao") else ""
            resultado["rsr"] = int(brutos.get("KMD_USUEnable", 0) or 0) == 1
            resultado["antilag"] = int(brutos.get("KMD_DeLagEnabled", 0) or 0) == 1
            resultado["vsync_forcado"] = brutos.get("VSyncControl") == "3"
            if int(brutos.get("KMD_FRTEnabled", 0) or 0) == 1 and int(brutos.get("KMD_MaxFrameRateRequested", 0) or 0) > 0:
                resultado["hz_limite"] = int(brutos["KMD_MaxFrameRateRequested"])
        elif resultado["fabricante"] == "intel":
            paineis = paineis_da_intel()
            resultado["painel"] = " e ".join(paineis)
    _CACHE[chave] = resultado
    return resultado


def hz_efetivo(hz_da_tela, situacao_do_driver):
    """A frequencia que o Mais quadros deve seguir: a da tela, ou o limite do driver se for menor."""
    hz = int(hz_da_tela or 60)
    limite = (situacao_do_driver or {}).get("hz_limite")
    return min(hz, int(limite)) if limite else hz


def escala_com_o_driver(jeito, situacao_do_driver):
    """O filtro de escala do ARENA alinhado ao driver: com o RSR ligado, o driver ja estica (FSR dele) qualquer
    jogo desenhado menor que a tela -- o ARENA nao estica de novo com o FSR nem com o Catmull-Rom, so aplica a
    nitidez (rcas). O pixel nitido do 2D fica: o RSR nao sabe o que e' pixel de console."""
    if (situacao_do_driver or {}).get("rsr") and jeito in ("nitido", "catmull"):
        return "rcas"
    return jeito


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(situacao(sys.argv[1] if len(sys.argv) > 1 else ""), ensure_ascii=False, indent=1))
