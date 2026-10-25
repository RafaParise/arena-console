# -*- coding: utf-8 -*-
r"""Auditoria do ARENA DENTRO do celular (adb, depuracao USB ligada), com os mesmos criterios da auditoria do PC.

So le e exercita o app; nada que apague dado de quem usa (nada de Monkey no aparelho do professor: ele toca em qualquer
botao, inclusive nos que mexem em configuracao). O que muda no aparelho e' desfeito no fim (a rotacao da tela).

Camada 1, com qualquer APK (o de producao tambem), so pelo adb:
  - o pacote: versao, SDK alvo, depuravel?, copia na nuvem (allowBackup), permissoes pedidas e concedidas;
  - os componentes EXPORTADOS do manifesto do APK (aapt2): outro app do aparelho pode abri-los;
  - os soquetes que o app escuta (so no 127.0.0.1? algum aberto para a rede?);
  - abrir a frio 5 vezes (tempo de abertura), a memoria (PSS) depois, a bateria e a temperatura antes e depois;
  - o ciclo de vida: tela inicial e volta, girar a tela e voltar, pouca memoria (trim), e o log de falhas (FATAL, ANR);
  - a pasta do ARENA no aparelho: espaco livre, banco de recordes puxado e conferido (PRAGMA integrity_check).

Camada 2, so com o APK de TESTE (montar_android.py --teste: o WebView aceita depuracao), pelo protocolo CDP:
  - a tela do ARENA NO tamanho real do celular: axe-core, contraste calculado, alvos de toque (as mesmas medidas do
    ferramentas\auditoria_front.py) em cada tela, gaveta e janela, e uma foto de cada uma;
  - todas as rotas GET do servidor, pelo proprio WebView (com o segredo): status e JSON valido.

Saida: docs\auditoria5\celular.json. Uso:
    servidor\python\python.exe ferramentas\auditoria_celular.py [--fotos PASTA] [--sem-ciclo]
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import adb_aparelho  # noqa: E402

PACOTE = "io.github.rafaparise.arena"
TELA_DO_ARENA = PACOTE + "/" + PACOTE + ".ArenaActivity"
LOOPBACK = ("0100007F", "00000000000000000000000001000000", "0000000000000000FFFF00000100007F")


def achar_adb():
    caminho, _origem = adb_aparelho.achar_adb()        # (caminho, de onde veio) ou (None, None)
    if not caminho:
        raise SystemExit("Nao achei o adb (ferramentas\\preparar_android.py instala o SDK).")
    return caminho


ADB = None
SERIE = None


def escolher_o_celular():
    """O numero de serie do celular (nunca o emulador): com os dois ligados, o adb recusa pedido sem '-s'."""
    saida = subprocess.run([ADB, "devices"], capture_output=True, timeout=30).stdout.decode("utf-8", "replace")
    fisicos = [linha.split()[0] for linha in saida.splitlines()[1:]
               if linha.strip().endswith("device") and not linha.startswith("emulator-")]
    if not fisicos:
        raise SystemExit("Nenhum celular com a depuracao USB ligada.")
    return os.environ.get("ANDROID_SERIAL") or fisicos[0]


def adb(*argumentos, segundos=120):
    return subprocess.run([ADB] + (["-s", SERIE] if SERIE else []) + list(argumentos), capture_output=True, timeout=segundos)


def texto(*argumentos, segundos=120):
    return adb(*argumentos, segundos=segundos).stdout.decode("utf-8", "replace")


def shell(comando, segundos=120):
    return texto("shell", comando, segundos=segundos)


# ---------------------------------------------------------------------------
# Camada 1
# ---------------------------------------------------------------------------

def dados_do_pacote():
    bruto = shell("dumpsys package " + PACOTE)

    def um(padrao):
        achado = re.search(padrao, bruto)
        return achado.group(1) if achado else None
    flags = (re.search(r"\n\s*flags=\[([^\]]*)\]", bruto) or [None, ""])[1].split()
    pedidas, concedidas = [], []
    pedindo = False
    for linha in bruto.splitlines():
        limpo = linha.strip()
        # "requested permissions:" lista uma permissao por linha, sem dois-pontos, ate a proxima secao
        if limpo == "requested permissions:":
            pedindo = True
            continue
        if pedindo:
            if re.fullmatch(r"[A-Za-z0-9_.]+", limpo):
                pedidas.append(limpo)
                continue
            pedindo = False
        # "permissao: granted=true, flags=[...]" (as de instalacao e as de execucao)
        achou = re.match(r"([A-Za-z0-9_.]+): granted=true", limpo)
        if achou:
            concedidas.append(achou.group(1))
    return {
        "versionName": um(r"versionName=(\S+)"), "versionCode": um(r"versionCode=(\d+)"),
        "targetSdk": um(r"targetSdk=(\d+)"), "minSdk": um(r"minSdk=(\d+)"),
        "depuravel": "DEBUGGABLE" in flags, "allowBackup": "ALLOW_BACKUP" in flags,
        "permissoes_pedidas": sorted(set(pedidas)), "permissoes_concedidas": sorted(set(concedidas)),
        "uid": um(r"userId=(\d+)"),
    }


def aapt2():
    achados = sorted(glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "ARENA-android", "sdk", "build-tools", "*", "aapt2.exe")))
    return achados[-1] if achados else None


def componentes_exportados(apk):
    """Os componentes do manifesto com android:exported verdadeiro (ou com filtro de intencao no SDK < 31)."""
    programa = aapt2()
    if not programa or not os.path.isfile(apk):
        return {"erro": "sem aapt2 ou sem o APK (%s)" % apk}
    arvore = subprocess.run([programa, "dump", "xmltree", "--file", "AndroidManifest.xml", apk],
                            capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    # O aapt2 imprime a arvore com recuo: "E: nome" abre um elemento e "A: atributo=valor" e' dele; um elemento
    # filho (intent-filter) fica mais fundo. Um componente acaba quando aparece outro elemento no mesmo recuo ou acima.
    saida, atual, recuo_do_atual = [], None, 0
    for linha in arvore.splitlines():
        recuo = len(linha) - len(linha.lstrip())
        corpo = linha.strip()
        if corpo.startswith("E: "):
            if atual is not None and recuo <= recuo_do_atual:
                atual = None
            nome_do_elemento = corpo[3:].split()[0]
            if nome_do_elemento in ("activity", "activity-alias", "service", "receiver", "provider"):
                atual = {"tipo": nome_do_elemento, "nome": "", "exportado": None, "filtro": False}
                recuo_do_atual = recuo
                saida.append(atual)
            elif nome_do_elemento == "intent-filter" and atual is not None:
                atual["filtro"] = True
        elif corpo.startswith("A: ") and atual is not None and recuo == recuo_do_atual + 2:
            # O aapt2 escreve o atributo com o endereco inteiro do espaco de nomes:
            #   A: http://schemas.android.com/apk/res/android:name(0x01010003)="io.github...ArenaActivity" (Raw: "...")
            if ":name(0x01010003)=" in corpo:
                achou = re.search(r'="([^"]+)"', corpo)
                atual["nome"] = achou.group(1) if achou else atual["nome"]
            elif ":exported(0x01010010)=" in corpo:
                # o aapt2 novo diz "=true"/"=false"; o antigo, "=(type 0x12)0xffffffff"
                atual["exportado"] = ("=true" in corpo) or bool(re.search(r"=\(type 0x12\)0x(?!0+$)[0-9a-f]+$", corpo))
            elif ":permission(0x01010006)=" in corpo:
                achou = re.search(r'="([^"]+)"', corpo)
                atual["permissao"] = achou.group(1) if achou else ""
    # Antes do Android 12 (SDK alvo < 31), um componente com filtro de intencao e sem "exported" vale como exportado.
    return [c for c in saida if c["exportado"] or (c["exportado"] is None and c["filtro"])]


def atributos_do_application(apk):
    """Os atributos de seguranca do <application> do manifesto: trafego em texto claro, copia na nuvem, depuravel..."""
    programa = aapt2()
    if not programa or not os.path.isfile(apk):
        return {"erro": "sem aapt2 ou sem o APK (%s)" % apk}
    arvore = subprocess.run([programa, "dump", "xmltree", "--file", "AndroidManifest.xml", apk],
                            capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    quero = {"usesCleartextTraffic", "allowBackup", "debuggable", "networkSecurityConfig", "requestLegacyExternalStorage",
             "testOnly", "extractNativeLibs", "largeHeap"}
    saida, dentro, recuo_do_app = {}, False, 0
    for linha in arvore.splitlines():
        recuo = len(linha) - len(linha.lstrip())
        corpo = linha.strip()
        if corpo.startswith("E: application"):
            dentro, recuo_do_app = True, recuo
        elif dentro and corpo.startswith("E: ") and recuo <= recuo_do_app:
            dentro = False
        elif dentro and corpo.startswith("A: ") and recuo == recuo_do_app + 2:
            achou = re.match(r"A: \S*:(\w+)\(0x[0-9a-f]+\)=(.*?)( \(Raw:.*)?$", corpo)
            if achou and achou.group(1) in quero:
                saida[achou.group(1)] = achou.group(2).strip('"')
    return saida


def soquetes_do_app(uid):
    """Os soquetes que o app escuta: {"tcp": [...], "udp": [...]}, cada um com endereco, porta e se e' so do aparelho."""
    resultado = {"tcp": [], "udp": []}
    for arquivo, chave in (("tcp", "tcp"), ("tcp6", "tcp"), ("udp", "udp"), ("udp6", "udp")):
        for linha in shell("cat /proc/net/%s" % arquivo).splitlines()[1:]:
            campos = linha.split()
            if len(campos) < 10 or campos[7] != str(uid):
                continue
            if chave == "tcp" and campos[3] != "0A":          # 0A = LISTEN
                continue
            endereco, porta = campos[1].split(":")
            resultado[chave].append({"porta": int(porta, 16), "so_do_aparelho": endereco in LOOPBACK, "endereco": endereco})
    return resultado


def bateria():
    bruto = shell("dumpsys battery")
    nivel = re.search(r"level: (\d+)", bruto)
    temp = re.search(r"temperature: (\d+)", bruto)
    return {"nivel": int(nivel.group(1)) if nivel else None, "temperatura_c": int(temp.group(1)) / 10 if temp else None}


def abrir_a_frio(vezes=5):
    tempos = []
    for _ in range(vezes):
        shell("am force-stop " + PACOTE)
        time.sleep(2)
        saida = shell("am start -W -n " + TELA_DO_ARENA)
        total = re.search(r"TotalTime: (\d+)", saida)
        if total:
            tempos.append(int(total.group(1)))
        time.sleep(8)
    return {"tempos_ms": tempos, "mediana_ms": int(statistics.median(tempos)) if tempos else None}


def processos_do_app():
    """Os processos vivos do app: o da tela (PACOTE:tela, onde roda tambem o servidor) e, durante um jogo, o do RetroArch."""
    vivos = {}
    for nome in (PACOTE + ":tela", PACOTE):
        pid = shell("pidof " + nome).strip().split()
        if pid:
            vivos[nome] = pid[0]
    return vivos


def memoria():
    """O PSS (memoria que o app usa de verdade) de cada processo dele."""
    medidas = {}
    for nome in processos_do_app():
        bruto = shell("dumpsys meminfo " + nome)
        total = re.search(r"TOTAL PSS:\s+(\d+)", bruto) or re.search(r"\n\s*TOTAL\s+(\d+)", bruto)
        medidas[nome] = round(int(total.group(1)) / 1024, 1) if total else None
    return {"pss_mb": medidas}


def ciclo_de_vida():
    """Tela inicial e volta, girar e voltar, pouca memoria: o app segue vivo e sem falha."""
    vivo = lambda: bool(processos_do_app())   # noqa: E731
    passos = {}
    original = (shell("settings get system accelerometer_rotation").strip(), shell("settings get system user_rotation").strip())
    try:
        shell("input keyevent KEYCODE_HOME")
        time.sleep(3)
        shell("am start -n " + TELA_DO_ARENA)
        time.sleep(4)
        passos["home_e_volta"] = vivo()
        shell("settings put system accelerometer_rotation 0")
        for rotacao in (1, 0, 3, 0):
            shell("settings put system user_rotation %d" % rotacao)
            time.sleep(2.5)
        passos["girar_e_voltar"] = vivo()
        shell("am send-trim-memory %s RUNNING_CRITICAL" % PACOTE)
        time.sleep(3)
        passos["pouca_memoria"] = vivo()
    finally:
        shell("settings put system user_rotation %s" % (original[1] if original[1].isdigit() else "0"))
        shell("settings put system accelerometer_rotation %s" % (original[0] if original[0].isdigit() else "1"))
    return passos


def falhas_no_log(desde_marca):
    """As quedas e os 'app nao responde' DO ARENA no registro do Android, e (a parte) os de outros apps do aparelho.
    No A12 do professor, o app da Samsung com.dti.samsung cai a cada poucos segundos: nao e' do ARENA."""
    bruto = texto("logcat", "-d", "-v", "time", "-b", "main,crash,system", "*:E", segundos=60)
    do_arena, de_outros = [], {}
    linhas = bruto.splitlines()
    for numero, linha in enumerate(linhas):
        if "FATAL EXCEPTION" in linha:
            # a linha seguinte diz o processo: "Process: com.dti.samsung, PID: 29548"
            achou = re.search(r"Process: ([\w.:]+)", " ".join(linhas[numero + 1:numero + 3]))
            processo = achou.group(1) if achou else "?"
            if processo.startswith(PACOTE):
                do_arena.append(linha[:200])
            else:
                de_outros[processo] = de_outros.get(processo, 0) + 1
        elif re.search(r"ANR in %s|Traceback \(most recent" % re.escape(PACOTE), linha):
            do_arena.append(linha[:200])
    return {"do_arena": do_arena[:20], "de_outros_apps": de_outros}


def pasta_do_arena():
    """O espaco livre e a pasta ARENA do cartao/armazenamento (se o professor usa uma). O banco de recordes mora na
    pasta interna do app (/data/user/0/<pacote>/files/arena/dados), que o adb nao alcanca sem root; quem o abre e' o
    servidor, e a camada da tela confere o estado dele pela rota /api/estado."""
    resultado = {"livre_mb": None}
    df = shell("df -k /sdcard | tail -1").split()
    if len(df) >= 4 and df[3].isdigit():
        resultado["livre_mb"] = int(df[3]) // 1024
    achado = next((c for c in ("/sdcard/ARENA", "/storage/emulated/0/ARENA") if shell("ls %s 2>/dev/null" % c).strip()), None)
    resultado["pasta_no_armazenamento"] = achado
    if achado:
        resultado["itens"] = shell("ls %s" % achado).split()[:20]
        if "arena.db" in shell("ls %s/dados 2>/dev/null" % achado):
            destino = os.path.join(tempfile.mkdtemp(prefix="arena_cel_"), "arena.db")
            adb("pull", achado + "/dados/arena.db", destino)
            for sufixo in ("-wal", "-shm"):
                adb("pull", achado + "/dados/arena.db" + sufixo, destino + sufixo)
            if os.path.isfile(destino):
                try:
                    conexao = sqlite3.connect(destino)
                    resultado["integrity_check"] = conexao.execute("PRAGMA integrity_check").fetchone()[0]
                    resultado["placar"] = conexao.execute("SELECT COUNT(*) FROM placar").fetchone()[0]
                    resultado["sessao"] = conexao.execute("SELECT COUNT(*) FROM sessao").fetchone()[0]
                    conexao.close()
                except sqlite3.Error as falha:
                    resultado["integrity_check"] = "erro: %s" % falha
    return resultado


def tela_depuravel():
    """O WebView do app aceita depuracao (o APK de montar_android.py --teste)? Ha o soquete webview_devtools_remote_<pid>."""
    pid = shell("pidof %s:tela" % PACOTE).strip().split()
    return bool(pid) and ("webview_devtools_remote_%s" % pid[0]) in shell("cat /proc/net/unix")


# Para a janela/gaveta 'id' (aberta): quais irmaos dela no <body> continuam visiveis ao leitor de tela
# (sem inert nem aria-hidden), e se ela se declara modal.
ISOLAMENTO = r"""
(() => {
  const id = %s;
  const el = document.getElementById(id);
  if (!el) return JSON.stringify({id, erro: 'sem elemento'});
  // As janelas (.modal) levam o papel na caixa de dentro (.modal-caixa); as gavetas, no proprio <aside>.
  const caixa = el.matches('[role=dialog]') ? el : (el.querySelector('[role=dialog]') || el);
  const fundo = [...document.body.children].filter(c => c !== el && !c.contains(el) && !el.contains(c)
    && !['SCRIPT', 'STYLE', 'CANVAS', 'LINK', 'TEMPLATE'].includes(c.tagName) && getComputedStyle(c).display !== 'none');
  const escondido = c => c.inert || c.getAttribute('aria-hidden') === 'true' || c.hidden;
  const larg = el.getBoundingClientRect().width;
  return JSON.stringify({id, papel: caixa.getAttribute('role'), aria_modal: caixa.getAttribute('aria-modal'),
    cobre_a_tela: larg >= innerWidth - 2,
    fundo_exposto: fundo.filter(c => !escondido(c)).map(c => c.tagName.toLowerCase() + (c.id ? '#' + c.id : '')).slice(0, 8)});
})()
"""

# Rotas GET que o teste deixa de fora: procuram no armazenamento inteiro, medem disco, vao a internet ou abrem
# programas/pastas no aparelho. Todas as outras so leem.
ROTAS_FORA_DA_VARREDURA = re.compile(r"procurar|medir|armazenamento/|baixar|buscar|reparar|biblioteca-|pasta/abrir|bios/abrir|celular/")


# ---------------------------------------------------------------------------
# Camada 2 (APK de teste)
# ---------------------------------------------------------------------------

def camada_da_tela(fotos):
    import auditoria_front as f
    import teste_android as t
    t.ADB = ADB
    pagina = t.Pagina()
    resultado = {"telas": [], "rotas": []}
    try:
        info = json.loads(pagina.avaliar("JSON.stringify({w: innerWidth, h: innerHeight, dpr: devicePixelRatio, tema: document.body.dataset.tema})"))
        resultado["viewport"] = info
        pagina.avaliar(f.baixar_o_axe() + "; true")
        for nome, ligar, desligar in f.estados(pagina):
            try:
                pagina.avaliar(ligar)
                time.sleep(0.6)
                medidas = json.loads(pagina.avaliar(f.CHECAGENS))
                medidas["axe"] = json.loads(pagina.avaliar(f.AXE_EXEC))
                medidas["tela"] = nome
                resultado["telas"].append(medidas)
                imagem = adb("exec-out", "screencap", "-p").stdout
                with open(os.path.join(fotos, "celular_%s.png" % nome.replace(":", "_")), "wb") as arquivo:
                    arquivo.write(imagem)
            except (OSError, RuntimeError, ValueError) as falha:
                resultado["telas"].append({"tela": nome, "erro": str(falha)[:200]})
            finally:
                try:
                    pagina.avaliar(desligar)
                except (OSError, RuntimeError):
                    pass
        fonte = open(os.path.join(RAIZ, "servidor", "arena.py"), encoding="utf-8", errors="replace").read()
        miolo = fonte[fonte.index("    def api_get("):fonte.index("    def api_post(")]
        rotas = sorted(set(re.findall(r'caminho == "(/api/[a-z0-9_\-/]+)"', miolo)))
        resultado["rotas_fora_da_varredura"] = [r for r in rotas if ROTAS_FORA_DA_VARREDURA.search(r)]
        for rota in [r for r in rotas if not ROTAS_FORA_DA_VARREDURA.search(r)]:
            resposta = pagina.avaliar("fetch(%s).then(async r => ({status: r.status, json: await r.text().then(t => { try { JSON.parse(t); return true } catch (e) { return false } })})).catch(e => ({status: 0, erro: String(e)}))" % json.dumps(rota))
            resultado["rotas"].append({"rota": rota, "status": resposta.get("status"), "json_valido": resposta.get("json"),
                                       "erro": resposta.get("erro")})
        estado = pagina.pedir("/api/estado") or {}
        resultado["estado_android"] = estado.get("android")
        resultado["plataforma"] = estado.get("plataforma")
        # Janela e gaveta abertas: o resto da tela fica escondido do leitor de tela (TalkBack)? Sem isso, quem usa o
        # leitor ouve os botoes de tras da janela (o WCAG 2.4.3 e o aria-modal).
        resultado["janelas_isolam_o_fundo"] = []
        for nome, ligar, desligar in f.estados(pagina):
            if ":" in nome or nome in ("inicio", "detalhes_do_jogo"):
                continue
            try:
                pagina.avaliar(ligar)
                time.sleep(0.4)
                achado = json.loads(pagina.avaliar(ISOLAMENTO % json.dumps(nome)))
                resultado["janelas_isolam_o_fundo"].append(achado)
            except (OSError, RuntimeError, ValueError):
                pass
            finally:
                try:
                    pagina.avaliar(desligar)
                except (OSError, RuntimeError):
                    pass
    finally:
        pagina.fechar()
    return resultado


def main():
    global ADB, SERIE
    for saida in (sys.stdout, sys.stderr):      # os nomes das telas tem simbolos que o cano do Windows nao aceita
        try:
            saida.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    analise = argparse.ArgumentParser()
    analise.add_argument("--fotos", default=os.path.join(os.environ.get("TEMP", "."), "arena_fotos_celular"))
    analise.add_argument("--apk", default=os.path.join(os.environ.get("LOCALAPPDATA", ""), "ARENA-android", "apk", "ARENA-2026.10.22-arm64-v8a-teste.apk"))
    analise.add_argument("--sem-ciclo", action="store_true")
    analise.add_argument("--saida", default=os.path.join(RAIZ, "docs", "auditoria5", "celular.json"))
    argumentos = analise.parse_args()
    ADB = achar_adb()
    SERIE = escolher_o_celular()
    os.environ["ANDROID_SERIAL"] = SERIE          # o teste_android.Pagina chama o adb sem '-s'
    os.makedirs(argumentos.fotos, exist_ok=True)
    resultado = {"feito_em": time.strftime("%Y-%m-%d %H:%M"),
                 "aparelho": {"modelo": shell("getprop ro.product.model").strip(), "android": shell("getprop ro.build.version.release").strip(),
                              "abis": shell("getprop ro.product.cpu.abilist").strip()}}
    adb("logcat", "-c")
    resultado["pacote"] = dados_do_pacote()
    resultado["exportados_no_manifesto"] = componentes_exportados(argumentos.apk)
    resultado["manifesto_application"] = atributos_do_application(argumentos.apk)
    resultado["bateria_antes"] = bateria()
    resultado["abertura_a_frio"] = abrir_a_frio()
    resultado["soquetes"] = soquetes_do_app(resultado["pacote"]["uid"])
    resultado["memoria"] = memoria()
    if not argumentos.sem_ciclo:
        resultado["ciclo_de_vida"] = ciclo_de_vida()
    resultado["bateria_depois"] = bateria()
    resultado["pasta_do_arena"] = pasta_do_arena()
    resultado["falhas_no_log"] = falhas_no_log(None)
    if tela_depuravel():
        resultado["camada_da_tela"] = camada_da_tela(argumentos.fotos)
    else:
        resultado["camada_da_tela"] = "pulada: o APK instalado nao e' o de teste (montar_android.py --teste); o WebView nao aceita depuracao"
    shell("am force-stop " + PACOTE)
    os.makedirs(os.path.dirname(argumentos.saida), exist_ok=True)
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    p = resultado["pacote"]
    print("Aparelho: %(modelo)s, Android %(android)s (%(abis)s)" % resultado["aparelho"])
    print("Pacote %s (%s), SDK alvo %s, depuravel=%s, copia na nuvem=%s" % (p["versionName"], p["versionCode"], p["targetSdk"], p["depuravel"], p["allowBackup"]))
    print("Componentes exportados: %s" % (json.dumps(resultado["exportados_no_manifesto"], ensure_ascii=False)[:300]))
    print("Soquetes do app: %s" % json.dumps(resultado["soquetes"]))
    print("Abertura a frio: mediana %s ms; memoria %s MB; bateria %s -> %s; falhas no log: %d" % (
        resultado["abertura_a_frio"]["mediana_ms"], json.dumps(resultado["memoria"]["pss_mb"]), resultado["bateria_antes"],
        resultado["bateria_depois"], len(resultado["falhas_no_log"]["do_arena"])))
    if resultado["falhas_no_log"]["de_outros_apps"]:
        print("Quedas de OUTROS apps (nao do ARENA): %s" % json.dumps(resultado["falhas_no_log"]["de_outros_apps"]))
    print("Ciclo de vida: %s" % resultado.get("ciclo_de_vida"))
    print("Pasta do ARENA: %s" % resultado["pasta_do_arena"])
    print("-> %s" % argumentos.saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
