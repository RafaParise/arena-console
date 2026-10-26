# -*- coding: utf-8 -*-
r"""
ARENA - o painel "Este celular" do ARENA do Android (Ajustes -> Maquina).

Pedido do Rafael (25/10/2026): "a parte que mostra o hardware no android tem informacoes redundantes, como
processador duas vezes [...] unifique todas as informacoes em menos campos, mas agora completos e revisados, para
poder usar o arena para ver sempre a saude da bateria, miliamperes, quanto de energia esta gastando no momento,
temperatura, memoria RAM em tempo real".

O app (android\src\...\ArenaServico.java, aparelho()) le o que o Android entrega e o servidor chama esta funcao para
montar os GRUPOS de linhas que a tela desenha (launcher\app.js, mostrarAparelho): [{titulo, linhas}], cada linha
[rotulo, valor] ou [rotulo, valor, {"pct": 0 a 100, "nivel": "ok" | "atencao" | "ruim"}] (a barrinha). A conta fica
aqui, e nao na tela, para ter teste (servidor\tests\test_painel_do_aparelho.py): so formata o que veio e nunca
inventa o que nao veio (leitura que o aparelho nao da simplesmente nao aparece).

E' a mesma ideia do painel do celular ligado no cabo, lido pelo computador (adb_aparelho.py): os mesmos grupos e os
mesmos nomes, para o aluno achar tudo no mesmo lugar nos dois.
"""
from adb_aparelho import SAUDE_DA_BATERIA, br, data_br, duracao, tamanho

# BatteryManager.EXTRA_STATUS
CARREGANDO, DESCARREGANDO, SEM_CARREGAR, CHEIA = 2, 3, 4, 5
# BatteryManager.EXTRA_PLUGGED (soma de bits): (bit, "carregando ___", "ligado ___")
TOMADAS = ((1, "pela tomada", "na tomada"), (2, "pelo cabo USB", "no cabo USB"),
           (4, "pelo carregador sem fio", "no carregador sem fio"))
# PowerManager.THERMAL_STATUS_*: o que o proprio Android diz do calor
CALOR = {0: ("normal", "ok"),
         1: ("um pouco quente", "atencao"),
         2: ("quente: o Android pode começar a segurar o processador", "atencao"),
         3: ("muito quente: o Android está segurando o processador", "ruim"),
         4: ("crítico", "ruim"), 5: ("emergência", "ruim"), 6: ("desligando", "ruim")}
MOTORES_DE_VIDEO = {"gl": "OpenGL ES", "vulkan": "Vulkan", "glcore": "OpenGL", "d3d11": "Direct3D 11"}


def _numero(dados, chave):
    valor = dados.get(chave)
    return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else None


def milis(bruto):
    """A corrente do Android em mA. O Android diz microampere, mas alguns aparelhos dizem miliampere direto (o Galaxy A12
    do Rafael diz -166 enquanto carrega: so pode ser mA). Um celular carregando ou gastando, com a tela acesa, nunca
    passa de 10 A (10 000 mA) nem fica abaixo de 10 mA (10 000 uA): abaixo de 10 000 e' mA, de 10 000 para cima e' uA."""
    if bruto is None:
        return None
    valor = abs(bruto)
    return float(valor) if 0 < valor < 10000 else valor / 1000.0


def como_esta_a_bateria(d):
    """(texto do estado, carregando?) pelo ESTADO que o Android da, nunca pelo sinal da corrente: cada fabricante poe o
    sinal de um jeito."""
    estado, tomada = d.get("bateria_estado"), d.get("tomada") or 0
    fonte = next(((por, em) for bit, por, em in TOMADAS if tomada & bit), None)
    if estado == CHEIA:
        return "cheia" + (", ligada %s" % fonte[1] if fonte else ""), False
    if estado == CARREGANDO:
        return "carregando" + (" %s" % fonte[0] if fonte else ""), True
    if estado == SEM_CARREGAR and fonte:
        return "ligado %s, sem carregar" % fonte[1], False
    if d.get("na_tomada") and fonte:
        return "ligado %s" % fonte[1], False
    return "usando a bateria", False


def qualidade_do_wifi(dbm):
    return ("excelente" if dbm >= -55 else "bom" if dbm >= -67 else "razoável" if dbm >= -75 else "fraco")


def painel(d, extras=None):
    """Os grupos do painel: [{"titulo", "linhas": [[rotulo, valor] ou [rotulo, valor, {pct, nivel}]]}]."""
    extras = extras or {}
    grupos = []

    def grupo(titulo, linhas):
        linhas = [linha for linha in linhas if linha and linha[1] not in (None, "")]
        if linhas:
            grupos.append({"titulo": titulo, "linhas": linhas})

    def linha(rotulo, valor, pct=None, nivel="ok"):
        if valor in (None, ""):
            return None
        if pct is None:
            return [rotulo, valor]
        return [rotulo, valor, {"pct": max(0, min(100, round(pct))), "nivel": nivel}]

    # ------------------------------------------------------------------ o aparelho
    marca = " ".join(p for p in (d.get("fabricante"), d.get("modelo")) if p)
    nome = d.get("nome")
    sdk = d.get("android_sdk")
    seguranca = data_br(d.get("seguranca"))
    android = None
    if d.get("android"):
        android = "%s (API %s)" % (d["android"], sdk) if sdk else str(d["android"])
        if seguranca:
            android += " · atualização de segurança de %s" % seguranca
    tela = d.get("tela")
    linha_da_tela = None
    if isinstance(tela, str) and "x" in tela:
        largura, _, altura = tela.partition("x")
        modos = [m for m in d.get("tela_modos_hz") or [] if isinstance(m, (int, float))]
        linha_da_tela = linha("Tela", "%s × %s pontos" % (largura, altura)
                              + (" · %s polegadas" % br(d["tela_polegadas"], 1) if _numero(d, "tela_polegadas") else "")
                              + (" · %d dpi" % d["tela_dpi"] if _numero(d, "tela_dpi") else "")
                              + (" · %d Hz" % d["tela_hz"] if _numero(d, "tela_hz") else "")
                              + (" (a tela aceita %s Hz)" % ", ".join(str(int(m)) for m in modos) if len(modos) > 1 else ""))
    grupo("O aparelho", [
        linha("Modelo", marca + (" (“%s”)" % nome if nome and marca else nome or "")),
        linha("Android", android),
        linha("Versão do sistema", d.get("versao_do_sistema")),
        linha("Kernel (Linux)", d.get("kernel")),
        linha_da_tela,
        linha("Ligado há", duracao(d["ligado_ha_s"]) if _numero(d, "ligado_ha_s") is not None else None),
    ])

    # ------------------------------------------------------------------ processador e video
    maximas = [m for m in d.get("nucleos_mhz") or [] if isinstance(m, (int, float)) and m > 0]
    agora = [a for a in d.get("nucleos_agora_mhz") or [] if isinstance(a, (int, float)) and a > 0]
    grupos_de_nucleos = {}
    for m in maximas:
        grupos_de_nucleos[m] = grupos_de_nucleos.get(m, 0) + 1
    nucleos = " + ".join("%d × até %s GHz" % (quantos, br(m / 1000.0, 1))
                         for m, quantos in sorted(grupos_de_nucleos.items(), reverse=True))
    if nucleos and d.get("nucleos"):
        nucleos = "%d núcleos: %s" % (d["nucleos"], nucleos)
    elif d.get("nucleos"):
        nucleos = "%d núcleos" % d["nucleos"]
    velocidade = None
    if agora and maximas:
        # So conta os nucleos ligados agora (o Android desliga os que nao precisa); o 100% e' cada um no maximo dele.
        pct_nucleos = 100.0 * sum(agora) / sum(sorted(maximas, reverse=True)[:len(agora)])
        velocidade = ("%s GHz no mais rápido · núcleos ligados a %d%% do máximo" % (br(max(agora) / 1000.0, 1), round(pct_nucleos)),
                      min(100.0, pct_nucleos))
    arquiteturas = d.get("arquiteturas") or []
    de_64 = any(a in ("arm64-v8a", "x86_64") for a in arquiteturas)
    processador = d.get("processador") or ""
    if d.get("hardware") and d["hardware"].lower() not in processador.lower():
        processador = "%s (%s)" % (processador, d["hardware"]) if processador else d["hardware"]
    vulkan = d.get("vulkan_versao") or ("sim" if d.get("vulkan") else None)
    grupo("Processador e vídeo", [
        linha("Processador (SoC)", processador),
        linha("Núcleos", nucleos),
        linha("Velocidade agora", velocidade[0], velocidade[1], "ok") if velocidade else None,
        linha("Arquitetura", (", ".join(arquiteturas) + (" · 64 bits" if de_64 else " · só 32 bits")) if arquiteturas else None),
        linha("Placa de vídeo", d.get("placa_de_video")),
        linha("OpenGL ES", d.get("opengl_es")),
        linha("Vulkan", vulkan if vulkan else ("este celular não tem" if d.get("vulkan") is False else None)),
    ])

    # ------------------------------------------------------------------ memoria e armazenamento
    total, livre = _numero(d, "memoria_total_mb"), _numero(d, "memoria_livre_mb")
    memoria = None
    if total and livre is not None:
        usada = max(0, total - livre)
        pct = 100.0 * usada / total
        sufoco = bool(d.get("memoria_baixa")) or livre < 300
        nivel = "ruim" if sufoco else ("atencao" if livre < 700 or pct >= 85 else "ok")
        memoria = linha("Memória RAM", "%s: %s em uso · %s livres" % (tamanho(total), tamanho(usada), tamanho(livre))
                        + (" · o Android está com pouca memória" if sufoco else ""), pct, nivel)
    troca_total, troca_livre = _numero(d, "troca_total_mb"), _numero(d, "troca_livre_mb")
    troca = None
    if troca_total and troca_livre is not None:
        usada = max(0, troca_total - troca_livre)
        troca = linha("Memória virtual (zRAM)", "%s: %s em uso" % (tamanho(troca_total), tamanho(usada)),
                      100.0 * usada / troca_total, "ok")
    disco_total, disco_livre = _numero(d, "armazenamento_total_mb"), _numero(d, "armazenamento_livre_mb")
    disco = None
    if disco_total and disco_livre is not None:
        pct = 100.0 * (disco_total - disco_livre) / disco_total
        nivel = "ruim" if disco_livre < 1024 or pct >= 95 else ("atencao" if pct >= 90 else "ok")
        disco = linha("Armazenamento", "%s: %s livres (%d%% usado)" % (tamanho(disco_total), tamanho(disco_livre), round(pct)),
                      pct, nivel)
    grupo("Memória e armazenamento", [memoria, troca, disco])

    # ------------------------------------------------------------------ bateria e energia
    if d.get("tem_bateria") is False:
        grupo("Bateria e energia", [linha("Bateria", "este aparelho não tem bateria")])
    elif d.get("tem_bateria"):
        linhas = []
        pct = _numero(d, "bateria_pct")
        estado, carregando = como_esta_a_bateria(d)
        if pct is not None:
            fraca = pct < 15 and not d.get("na_tomada")
            linhas.append(linha("Nível", "%d%% · %s" % (pct, estado), pct, "ruim" if fraca else ("atencao" if pct < 30 and not d.get("na_tomada") else "ok")))
        ma = milis(_numero(d, "corrente_ua"))
        volts = (_numero(d, "bateria_voltagem_mv") or 0) / 1000.0
        if d.get("bateria_estado") in (CHEIA, SEM_CARREGAR):
            # Na tomada sem carregar, o aparelho vive da energia da tomada: a corrente da bateria e' perto de zero, e
            # o numero (de uns poucos uA ou mA) nao se deixa ler com certeza.
            linhas.append(linha("Corrente na bateria", "quase nenhuma: a energia vem da tomada, não da bateria"))
        elif ma is not None:
            watts = ma * volts / 1000.0
            linhas.append(linha("Entrando na bateria agora" if carregando else "Gastando agora",
                                "%s mA" % br(ma, 0) + (" (≈ %s W)" % br(watts, 1) if volts else "")))
        media = milis(_numero(d, "corrente_media_ua"))
        if media is not None and ma is not None and abs(media - ma) >= 20:
            linhas.append(linha("Média recente", "%s mA" % br(media, 0)))
        linhas.append(linha("Voltagem", "%s V" % br(volts, 2) if volts else None))
        temperatura = _numero(d, "bateria_temperatura_c")
        if temperatura is not None:
            linhas.append(linha("Temperatura da bateria", "%s °C" % br(temperatura, 1)
                                + (" · quente: tire a capa e dê um tempo" if temperatura >= 42 else "")))
        status = d.get("termico")
        if status in CALOR:
            texto = CALOR[status][0]
            margem = _numero(d, "margem_termica")
            linhas.append(linha("Calor do aparelho", texto + (" · a %d%% do limite em que ele começa a se defender" % round(100 * margem)
                                                              if margem is not None and margem >= 0 else "")))
        saude = SAUDE_DA_BATERIA.get(d.get("bateria_saude"))
        if saude and d.get("bateria_saude") != 1:
            linhas.append(linha("Saúde, pelo Android", saude + (" · %d%%" % d["bateria_saude_pct"] if _numero(d, "bateria_saude_pct") else "")))
        elif _numero(d, "bateria_saude_pct"):
            linhas.append(linha("Saúde, pelo Android", "%d%%" % d["bateria_saude_pct"]))
        fabrica, carga = _numero(d, "bateria_capacidade_mah"), _numero(d, "bateria_carga_mah")
        if fabrica:
            linhas.append(linha("Capacidade de fábrica", "%s mAh (o que o perfil de energia do próprio Android declara)" % br(fabrica)))
        if carga:
            linhas.append(linha("Carga guardada agora", "%s mAh" % br(carga)))
        if fabrica and carga and pct is not None and pct >= 15:
            conta = round(carga / (pct / 100.0))
            linhas.append(linha("Conta: carga ÷ nível",
                                "uns %s mAh, ou %d%% da de fábrica. É só uma pista, não uma medida: o nível é um número inteiro, e "
                                "alguns aparelhos usam a capacidade de fábrica como base do contador e não mostram o desgaste. "
                                "Com a bateria mais cheia, a conta fica mais justa." % (br(conta), round(100.0 * conta / fabrica))))
        if _numero(d, "bateria_ciclos") is not None:
            linhas.append(linha("Ciclos de carga", str(int(d["bateria_ciclos"]))))
        faltam = _numero(d, "falta_para_encher_s")
        if faltam and carregando:
            linhas.append(linha("Falta para encher", "uns %s" % duracao(faltam)))
        linhas.append(linha("Economia de bateria", "ligada: o Android corta o desempenho de propósito" if d.get("economia") else "desligada",
                            None))
        linhas.append(linha("Tipo da bateria", d.get("bateria_tecnologia")))
        grupo("Bateria e energia", linhas)

    # ------------------------------------------------------------------ para jogar com controle
    controles = [c for c in d.get("controles") or [] if isinstance(c, dict) and c.get("nome")]
    jogadores = ["%s (jogador %d)" % (c["nome"], c["jogador"]) for c in controles if c.get("jogador")]
    teclados = [c["nome"] for c in controles if c.get("teclado")]
    ligados = None
    if "controles" in d:
        ligados = ("%d: %s" % (len(jogadores), ", ".join(jogadores)) if jogadores
                   else "nenhum: o controle de toque aparece na tela do jogo")
        if teclados:
            ligados += " · teclado: %s" % ", ".join(teclados)
    recursos = d.get("recursos") or {}

    def tem(chave, sim="tem", nao="não tem"):
        return None if chave not in recursos else (sim if recursos[chave] else nao)

    grupo("Para jogar com controle", [
        linha("Controles ligados agora", ligados),
        linha("Controle por cabo (USB-C ou OTG)", tem("usb_host")),
        linha("Controle por Bluetooth", None if "bluetooth" not in recursos
              else ("tem" + (" (e Bluetooth LE)" if recursos.get("bluetooth_le") else "") if recursos["bluetooth"] else "não tem")),
        linha("Giroscópio", tem("giroscopio")),
        linha("Acelerômetro (inclinar o celular)", tem("acelerometro")),
        linha("Toque com vários dedos", tem("multitoque")),
        linha("Vibração", tem("vibracao")),
    ])

    # ------------------------------------------------------------------ rede
    wifi = d.get("wifi")
    if isinstance(wifi, dict) and _numero(wifi, "sinal_dbm") is not None:
        faixa = wifi.get("frequencia_mhz")
        texto_wifi = "sinal %s (%d dBm)" % (qualidade_do_wifi(wifi["sinal_dbm"]), wifi["sinal_dbm"])
        if _numero(wifi, "velocidade_mbps"):
            texto_wifi += " · %d Mb/s" % wifi["velocidade_mbps"]
        if isinstance(faixa, (int, float)) and faixa > 0:
            texto_wifi += " · %s GHz" % ("5" if faixa >= 4900 else "2,4")
    elif d.get("wifi_ligado") is True:
        texto_wifi = "ligado, mas sem rede conectada"
    elif d.get("wifi_ligado") is False:
        texto_wifi = "desligado"
    else:
        texto_wifi = None
    internet = extras.get("internet")
    grupo("Rede", [
        linha("Wi-Fi", texto_wifi),
        linha("Internet", None if internet is None else
              ("conectado — a cópia de segurança acontece sozinha" if internet
               else "sem internet — tudo continua funcionando e sobe depois")),
    ])

    # ------------------------------------------------------------------ o que o ARENA mediu e decidiu aqui
    economico = extras.get("economico")
    grupo("O ARENA neste aparelho", [
        linha("Modo do ARENA", None if economico is None else
              ("Econômico — rede e cópias de segurança mais espaçadas, para poupar a máquina" if economico
               else "Normal — todos os consoles na lista, com o selo de cada um")),
        linha("Motor de vídeo", MOTORES_DE_VIDEO.get(extras.get("motor"), extras.get("motor"))),
        linha("Velocidade medida", ("%s× o notebook mais fraco da escola, por núcleo" % br(extras["velocidade_relativa"], 2))
              if _numero(extras, "velocidade_relativa") is not None else None),
        linha("Gravação medida", ("%s MB por segundo" % br(extras["gravacao_mbs"], 0)) if _numero(extras, "gravacao_mbs") else None),
    ])
    return grupos
