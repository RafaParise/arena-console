# -*- coding: utf-8 -*-
r"""O ARENA de verdade no Linux, num conteiner (item 13 do plano de 15/10/2026).

O que a bateria (testes\linux\bateria.sh) nao prova: que o RetroArch do Linux
abre, desenha o jogo e fecha, pelo mesmo caminho que o aluno usa. Aqui, num
Debian sem tela (o Xvfb faz a tela), numa copia do ARENA:

  A. o RetroArch sai do AppImage para o cache (o conteiner nao tem FUSE,
     como o Ubuntu 24.04), e cada jogo livre de testes\jogos_livres (e os
     programas que o teste dos consoles livres escreve na hora) abre no
     nucleo .so e mostra imagem de verdade: a foto do --max-frames-ss, a
     mesma conferencia de testes\teste_consoles_livres.py, com o Java ME
     no Java do Linux e o Apple II no nucleo do nightly;
  B. os mesmos jogos com a pasta num caminho com acento ("Pedagógicos"):
     direto, sem a ponte sem acento do Windows; so o Java ME vai pela ponte,
     como o ARENA faz no Linux (servidor\ponte_sem_acento.py);
  C. pelo servidor do ARENA, como a tela faz (POST /api/jogar): o jogo
     abre, a tela tem imagem (a foto do Xvfb, pelo xwd), e a sessao fica no
     banco quando o jogo fecha;
  D. o ARENA.sh abre o servidor e fecha com o Ctrl+C, inclusive quando o
     Python nao pode receber a permissao de executar (o pen drive FAT32:
     ele vai para ~/.cache/arena);
  E. o VERIFICAR.sh confere a copia;
  F. os emuladores de fora do Linux (PCSX2, RPCS3, Xenia) saem do AppImage
     e abrem;
  G. (so quando pedida) as medidas do item 15, as mesmas do Windows
     (testes\medidas_virtuais.py): quem a pede e' o testes\teste_sistemas_virtuais.py.

Os tempos ficam no resultado (o item 15 usa: quanto custa rodar num
sistema virtual).

No Windows, este mesmo arquivo monta a imagem do conteiner, se faltar
(testes\linux\Dockerfile, pelo WSLC, sem administrador), roda a si mesmo
dentro dele e guarda o resultado em docs\linux_bruto.json:
    servidor\python\python.exe testes\teste_linux.py [A,B,C,D,E,F,G] [pedaco do console]
"""
import json
import os
import shutil
import signal
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CONTAINER = r"C:\Program Files\WSL\container.exe"
IMAGEM = "arena-linux"
TELA = ":99"
COPIA = "/tmp/arena"
SAIDA = "/saida"
PORTA_C, PORTA_D = 8790, 8791
# Do ARENA de verdade, entram por atalho (os testes so leem); o que e' de
# quem usa (dados, jogos, BIOS, copias de seguranca) entra VAZIO: nada do
# Rafael nem dos alunos vai para o teste. O resto vira copia.
POR_ATALHO = {"emuladores", ".git"}
VAZIAS = {"dados", "jogos", "BIOS", "backup"}
FORA = {"ARENA-remake--master", "ARENA - Versão antiga para implementar", "Lossless Scaling", "perfil"}
# Do retroarch: o que o RetroArch e o ARENA gravam vira pasta vazia, de verdade.
RETROARCH_VAZIAS = {"system", "saves", "states", "screenshots", "cache", "remaps", "cheats", "controles",
                    "thumbnails", "playlists", "config"}


# ---------------------------------------------------------------------------
# No Windows: o conteiner
# ---------------------------------------------------------------------------

def pelo_conteiner(argumentos, copiar_para=None):
    imagens = subprocess.run([CONTAINER, "image", "list"], capture_output=True, text=True, errors="replace").stdout
    if IMAGEM not in imagens:
        print("Montando a imagem %s (uma vez so)..." % IMAGEM, flush=True)
        subprocess.run([CONTAINER, "build", "-t", IMAGEM, os.path.join(AQUI, "linux")], check=True)
    saida = tempfile.mkdtemp(prefix="arena_teste_linux_")
    comando = [CONTAINER, "run", "--rm", "-e", "PYTHONDONTWRITEBYTECODE=1",
               "-v", RAIZ + ":/arena:ro", "-v", saida + ":" + SAIDA, IMAGEM,
               "/arena/servidor/python-linux/bin/python3.13", "-X", "utf8", "/arena/testes/teste_linux.py"]
    inicio = time.monotonic()
    codigo = subprocess.run(comando + argumentos).returncode
    resultado = os.path.join(saida, "resultado.json")
    if os.path.isfile(resultado):
        with open(resultado, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        dados["segundos_com_o_conteiner"] = round(time.monotonic() - inicio, 1)
        if copiar_para:                 # o teste do item 15 le o resultado daqui
            with open(copiar_para, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=1)
        if not argumentos:              # so a rodada inteira vai para o docs
            with open(os.path.join(RAIZ, "docs", "linux_bruto.json"), "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=1)
            print("Resultado: docs\\linux_bruto.json")
        for pasta, rotulo in (("fotos", "Fotos"), ("registros", "Registros das falhas")):
            if os.path.isdir(os.path.join(saida, pasta)):
                print("%s: %s" % (rotulo, os.path.join(saida, pasta)))
    return codigo


# ---------------------------------------------------------------------------
# No Linux: a copia gravavel
# ---------------------------------------------------------------------------

def para_a_copia(argumentos):
    """Copia o ARENA (montado so de leitura em /arena) para /tmp/arena e
    roda este teste de la: o ARENA grava nos dados, no retroarch.cfg..."""
    origem = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(COPIA):
        shutil.rmtree(COPIA)
    os.makedirs(COPIA)
    for nome in os.listdir(origem):
        caminho = os.path.join(origem, nome)
        if nome in FORA:
            continue
        if nome in VAZIAS:
            os.makedirs(os.path.join(COPIA, nome))
        elif nome in POR_ATALHO:
            os.symlink(caminho, os.path.join(COPIA, nome))
        elif nome == "retroarch":
            os.makedirs(os.path.join(COPIA, nome))
            for parte in os.listdir(caminho):
                alvo = os.path.join(COPIA, nome, parte)
                if parte in RETROARCH_VAZIAS:
                    os.makedirs(alvo)
                elif parte.endswith((".cfg", ".opt")):
                    shutil.copy2(os.path.join(caminho, parte), alvo)
                else:
                    os.symlink(os.path.join(caminho, parte), alvo)
        elif os.path.isdir(caminho):
            shutil.copytree(caminho, os.path.join(COPIA, nome), symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(caminho, os.path.join(COPIA, nome))
    python = os.path.join(COPIA, "servidor", "python-linux", "bin", "python3.13")
    os.execv(python, [python, "-X", "utf8", os.path.join(COPIA, "testes", "teste_linux.py"), "--na-copia"]
             + argumentos)


# ---------------------------------------------------------------------------
# Ajudantes
# ---------------------------------------------------------------------------

def ligar_a_tela():
    """O Xvfb: a tela virtual (1280x720, 24 bits) onde o RetroArch desenha."""
    tela = subprocess.Popen(["Xvfb", TELA, "-screen", "0", "1280x720x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    soquete = "/tmp/.X11-unix/X" + TELA.lstrip(":")
    for _ in range(100):
        if os.path.exists(soquete):
            break
        time.sleep(0.1)
    os.environ["DISPLAY"] = TELA
    return tela


def cores_da_imagem(pontos):
    """(quantas cores, fracao da mais comum) de uma lista de (r, g, b)."""
    contagem = {}
    for ponto in pontos:
        contagem[ponto] = contagem.get(ponto, 0) + 1
    maior = max(contagem.values()) if contagem else 0
    return len(contagem), (maior / float(len(pontos)) if pontos else 1.0)


def foto_da_tela():
    """A tela inteira do Xvfb pelo xwd (o formato XWD, lido aqui): os pontos
    (r, g, b), um de cada 4 nas duas direcoes."""
    bruto = subprocess.run(["xwd", "-root", "-silent", "-display", TELA], capture_output=True, timeout=30).stdout
    campos = struct.unpack(">25I", bruto[:100])
    tamanho_cabecalho, largura, altura = campos[0], campos[4], campos[5]
    bits, por_linha, cores_do_mapa = campos[11], campos[12], campos[19]
    inicio = tamanho_cabecalho + cores_do_mapa * 12
    ordem = "<" if campos[7] == 0 else ">"      # byte_order: 0 = LSBFirst
    pontos = []
    if bits == 32:
        for y in range(0, altura, 4):
            linha = bruto[inicio + y * por_linha: inicio + (y + 1) * por_linha]
            for x in range(0, largura, 4):
                valor, = struct.unpack(ordem + "I", linha[x * 4: x * 4 + 4])
                pontos.append(((valor >> 16) & 255, (valor >> 8) & 255, valor & 255))
    return largura, altura, pontos


def pedir(porta, rota, corpo=None, segundos=15):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, rota), data=dados,
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=segundos) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def esperar_porta(porta, segundos):
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def processos_com(nome):
    """Os numeros (PID) dos processos deste usuario com 'nome' no comando."""
    achados = []
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open("/proc/%s/cmdline" % pid, "rb") as arquivo:
                    comando = arquivo.read().replace(b"\0", b" ").decode("utf-8", "replace")
            except OSError:
                continue
            if nome in comando and "teste_linux.py" not in comando:
                achados.append(int(pid))
    return achados


def memoria_mb(pid):
    try:
        with open("/proc/%d/status" % pid, encoding="utf-8") as arquivo:
            for linha in arquivo:
                if linha.startswith("VmRSS:"):
                    return round(int(linha.split()[1]) / 1024.0, 1)
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# As partes
# ---------------------------------------------------------------------------

def parte_a_b(resultado, falhas, filtro, partes):
    """A e B: cada jogo livre no RetroArch do Linux, numa pasta comum e numa
    com acento. A conferencia da foto e os jogos sao os do teste dos
    consoles livres do Windows (testes\\teste_consoles_livres.py)."""
    import bios
    import java_do_arena
    import plataforma
    import ponte_sem_acento
    import teste_consoles_livres as livres
    import limpeza
    graficos = livres.base.graficos
    graficos.corrigir_caminhos_retroarch_cfg()          # o cfg do Windows vira o do Linux
    cfg_principal = os.path.join(graficos.PASTA_RETROARCH, "retroarch.cfg")
    appimage = plataforma.executavel_do_retroarch(graficos.PASTA_RETROARCH)
    inicio = time.monotonic()
    programa = plataforma.retroarch_que_roda(appimage)
    resultado["retroarch_tirar_do_appimage_s"] = round(time.monotonic() - inicio, 2)
    inicio = time.monotonic()
    plataforma.retroarch_que_roda(appimage)
    resultado["retroarch_ja_pronto_s"] = round(time.monotonic() - inicio, 3)
    resultado["retroarch"] = programa
    if not programa.endswith("AppRun"):
        falhas.append("o RetroArch nao saiu do AppImage (%s)" % programa)
        return
    with open(os.path.join(livres.PASTA_JOGOS, "lista.json"), encoding="utf-8") as arquivo:
        jogos = json.load(arquivo)["arquivos"]
    todas = livres.plataformas()
    fotos = os.path.join(SAIDA, "fotos")
    os.makedirs(fotos, exist_ok=True)
    rodadas = []
    for item in jogos + livres.GERADOS:
        if filtro and filtro not in item["console"] and filtro not in item["jogo"].lower():
            continue
        p = todas.get(item["console"])
        if not p:
            continue
        nucleo = plataforma.arquivo_do_nucleo(p["core"])
        caminho_nucleo = os.path.join(graficos.PASTA_RETROARCH, "cores", nucleo)
        if not os.path.isfile(caminho_nucleo):
            falhas.append("%s: falta o nucleo %s" % (p["nome"], nucleo))
            continue
        regras = livres.POR_CONSOLE.get(item["console"], {})
        quadros = regras.get("quadros", 600)
        lugares = [r for r in (("A", "pasta comum", "arena_linux_"), ("B", "pasta com acento", "arena_linux_Pedagógicos_"))
                   if r[0] in partes]
        for parte, rotulo, prefixo in lugares:
            trabalho = tempfile.mkdtemp(prefix=prefixo)
            try:
                sistema = os.path.join(trabalho, "system")
                os.makedirs(sistema)
                bios.instalar_livres(sistema)
                if item.get("gerar"):
                    jogo = os.path.join(trabalho, item["arquivo"])
                    with open(jogo, "wb") as arquivo:
                        arquivo.write(item["gerar"]())
                else:
                    origem = os.path.join(livres.PASTA_JOGOS, *item["origem"].split("/"))
                    if regras.get("montar"):
                        extensao, montar = regras["montar"]
                        jogo = os.path.join(trabalho, os.path.splitext(os.path.basename(origem))[0].lower() + extensao)
                        montar(jogo, origem)
                    else:
                        jogo = os.path.join(trabalho, os.path.basename(origem))
                        shutil.copyfile(origem, jogo)
                pasta = os.path.join(trabalho, "rodada")
                os.makedirs(pasta)
                cfg = livres.base.config_base(pasta, p.get("opcoes_retroarch", {}))
                # O jogo e a BIOS pela ponte sem acento, quando o ARENA
                # tambem os mandaria por ela (arena.py, antes de abrir o jogo).
                devolver = None
                if ponte_sem_acento.precisa(caminho_nucleo, sistema, jogo):
                    jogo, opcoes_ponte, devolver = ponte_sem_acento.preparar(caminho_nucleo, sistema, jogo)
                    sistema = opcoes_ponte.get("system_directory", sistema)
                extra = os.path.join(pasta, "system.cfg")
                with open(extra, "w", encoding="utf-8") as arquivo:
                    arquivo.write('system_directory = "%s"\n' % sistema)
                foto = os.path.join(pasta, "foto.png")
                registro = os.path.join(pasta, "ra.log")
                ambiente = java_do_arena.ambiente() if p.get("usa_java") else None
                comando = plataforma.comando_do_retroarch(appimage, cfg_principal) + [
                    "-L", caminho_nucleo, "--appendconfig", cfg + "|" + extra, "--verbose", "--log-file", registro,
                    "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo]
                antes = time.monotonic()
                try:
                    subprocess.run(comando, cwd=graficos.PASTA_RETROARCH, timeout=240, env=ambiente,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    travou = False
                except subprocess.TimeoutExpired:
                    travou = True
                finally:
                    if devolver:
                        devolver()
                segundos = time.monotonic() - antes
                ok, detalhe = livres.imagem_de_verdade(foto, item.get("cor"))
                texto = open(registro, encoding="utf-8", errors="ignore").read() if os.path.exists(registro) else ""
                if regras.get("registro") and ok:
                    import re
                    ok = bool(re.search(regras["registro"], texto))
                    detalhe += "" if ok else ", o registro nao diz %r" % regras["registro"]
                if (not ok or travou) and texto:    # o registro diz por que falhou
                    registros = os.path.join(SAIDA, "registros")
                    os.makedirs(registros, exist_ok=True)
                    with open(os.path.join(registros, "%s - %s.log" % (item["console"], rotulo)), "w",
                              encoding="utf-8") as arquivo:
                        arquivo.write(texto)
                if os.path.isfile(foto):
                    shutil.copyfile(foto, os.path.join(fotos, "%s - %s.png" % (item["console"], rotulo)))
                rodadas.append({"parte": parte, "console": item["console"], "jogo": item["jogo"], "nucleo": nucleo,
                                "imagem": ok, "detalhe": detalhe, "travou": travou, "segundos": round(segundos, 1),
                                "pela_ponte": bool(devolver),
                                "quadros": quadros, "quadros_por_segundo": round(quadros / segundos, 1) if segundos else 0})
                print("   %s %-12s %-17s imagem: %-3s (%s)%s" % (parte, item["console"], rotulo, "sim" if ok else "NAO",
                                                              detalhe, " TRAVOU" if travou else ""), flush=True)
                if not ok or travou:
                    falhas.append("%s, %s: sem imagem (%s)%s" % (p["nome"], rotulo, detalhe,
                                                                 " (travou)" if travou else ""))
                if p.get("usa_java"):
                    time.sleep(1)
                    sobras = processos_com("freej2me-lr.jar")
                    for pid in sobras:
                        os.kill(pid, signal.SIGKILL)
                    if sobras:
                        falhas.append("%s, %s: o Java ficou aberto depois do jogo" % (p["nome"], rotulo))
            finally:
                limpeza.apagar_pasta(trabalho)
    resultado["jogos"] = rodadas


def parte_c(resultado, falhas):
    """C: pelo servidor do ARENA, como a tela faz."""
    import plataforma
    with open(os.path.join(COPIA, "servidor", "consoles.json"), encoding="utf-8") as arquivo:
        consoles = {p["id"]: p for p in json.load(arquivo)["plataformas"]}
    with open(os.path.join(COPIA, "testes", "jogos_livres", "lista.json"), encoding="utf-8") as arquivo:
        jogo = next(j for j in json.load(arquivo)["arquivos"] if j["console"] == "chip8")
    # O jogo na pasta do console, numa pasta "jogos" so desta copia.
    jogos = os.path.join(COPIA, "jogos")
    if os.path.islink(jogos):
        os.remove(jogos)
    pasta = os.path.join(jogos, "pessoais", consoles["chip8"]["pasta"])
    os.makedirs(pasta, exist_ok=True)
    shutil.copyfile(os.path.join(COPIA, "testes", "jogos_livres", *jogo["origem"].split("/")),
                    os.path.join(pasta, os.path.basename(jogo["origem"])))
    ambiente = dict(os.environ, ARENA_SEM_JANELA="1", ARENA_PORTA=str(PORTA_C))
    python = plataforma.python_que_veio_junto(os.path.join(COPIA, "servidor"))
    inicio = time.monotonic()
    servidor = subprocess.Popen([python, os.path.join(COPIA, "servidor", "arena.py")], cwd=COPIA, env=ambiente,
                                stdout=open(os.path.join(SAIDA, "servidor_c.txt"), "w"), stderr=subprocess.STDOUT)
    try:
        if not esperar_porta(PORTA_C, 60):
            falhas.append("C: o servidor nao abriu a porta %d" % PORTA_C)
            return
        resultado["servidor_abriu_s"] = round(time.monotonic() - inicio, 2)
        estado = pedir(PORTA_C, "/api/estado")
        resultado["sistema_do_computador"] = estado.get("sistema_do_computador")
        resultado["maquina"] = {chave: estado.get("maquina", {}).get(chave) for chave in ("sistema", "processador",
                                                                                     "driver_video")}
        catalogo = pedir(PORTA_C, "/api/catalogo", segundos=60)
        lista = catalogo.get("jogos", catalogo) if isinstance(catalogo, dict) else catalogo
        do_chip8 = [j for j in lista if j.get("plataforma") == "chip8"]
        if not do_chip8:
            falhas.append("C: o jogo de CHIP-8 nao entrou no catalogo")
            return
        time.sleep(1)
        resultado["servidor_memoria_mb"] = memoria_mb(servidor.pid)
        antes = time.monotonic()
        resposta = pedir(PORTA_C, "/api/jogar", {"jogo_id": do_chip8[0]["id"]}, segundos=120)
        if not resposta.get("ok", True) or resposta.get("erro"):
            falhas.append("C: /api/jogar respondeu %s" % resposta)
            return
        retroarch = []
        for _ in range(60):
            retroarch = processos_com("AppRun") or processos_com("/usr/bin/retroarch")
            if retroarch:
                break
            time.sleep(0.5)
        if not retroarch:
            falhas.append("C: o RetroArch nao abriu pelo servidor")
            return
        time.sleep(8)
        resultado["jogo_abriu_s"] = round(time.monotonic() - antes, 1)
        largura, altura, pontos = foto_da_tela()
        cores, maior = cores_da_imagem(pontos)
        resultado["tela_do_jogo"] = {"largura": largura, "altura": altura, "cores": cores,
                                     "a_mais_comum": round(maior, 3)}
        resultado["retroarch_memoria_mb"] = max((memoria_mb(pid) or 0) for pid in retroarch)
        if cores < 2 or maior > 0.999:
            falhas.append("C: a tela do jogo aberto pelo servidor nao tem imagem (%d cores)" % cores)
        for pid in retroarch:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        fechou = False
        for _ in range(40):
            if not pedir(PORTA_C, "/api/estado").get("jogo_em_andamento", {}).get("ativo"):
                fechou = True
                break
            time.sleep(0.5)
        if not fechou:
            falhas.append("C: o servidor nao viu o jogo fechar")
        with sqlite3.connect(os.path.join(COPIA, "dados", "arena.db")) as banco:
            sessoes = banco.execute("SELECT COUNT(*) FROM sessao WHERE encerrada = 1").fetchone()[0]
        resultado["sessoes_encerradas"] = sessoes
        if not sessoes:
            falhas.append("C: a sessao do jogo nao ficou no banco")
    finally:
        servidor.terminate()
        try:
            servidor.wait(15)
        except subprocess.TimeoutExpired:
            servidor.kill()


def parte_d(resultado, falhas):
    """D: o ARENA.sh, com o Python que nao pode ganhar a permissao de
    executar (um chmod que recusa, como o do pen drive FAT32)."""
    casa = tempfile.mkdtemp(prefix="arena_casa_")
    falso = os.path.join(casa, "bin")
    os.makedirs(falso)
    with open(os.path.join(falso, "chmod"), "w", encoding="utf-8") as arquivo:
        arquivo.write('#!/bin/sh\ncase "$*" in *"/.cache/"*) exec /bin/chmod "$@" ;; *) exit 1 ;; esac\n')
    os.chmod(os.path.join(falso, "chmod"), 0o755)
    python = os.path.join(COPIA, "servidor", "python-linux", "bin", "python3.13")
    os.chmod(python, 0o644)              # como veio do zip, sem a permissao
    ambiente = dict(os.environ, HOME=casa, PATH=falso + os.pathsep + os.environ.get("PATH", ""),
                    ARENA_SEM_JANELA="1", ARENA_PORTA=str(PORTA_D))
    ambiente.pop("XDG_CACHE_HOME", None)
    inicio = time.monotonic()
    arena_sh = subprocess.Popen(["sh", os.path.join(COPIA, "ARENA.sh")], cwd=COPIA, env=ambiente,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                start_new_session=True)
    try:
        abriu = esperar_porta(PORTA_D, 120)
        resultado["arena_sh_abriu_s"] = round(time.monotonic() - inicio, 2)
        if not abriu:
            falhas.append("D: o ARENA.sh nao abriu o servidor")
        copias = [n for n in os.listdir(os.path.join(casa, ".cache", "arena"))] if os.path.isdir(
            os.path.join(casa, ".cache", "arena")) else []
        resultado["arena_sh_cache"] = copias
        if not any(n.startswith("python-3.13-") for n in copias):
            falhas.append("D: o Python nao foi para ~/.cache/arena (%s)" % copias)
        os.killpg(arena_sh.pid, signal.SIGINT)          # o Ctrl+C na janela do terminal
        texto = arena_sh.communicate(timeout=30)[0].decode("utf-8", "replace")
        resultado["arena_sh_saida"] = texto[-600:]
        if "ARENA encerrado" not in texto:
            falhas.append("D: o ARENA.sh nao fechou do jeito normal com o Ctrl+C")
    finally:
        if arena_sh.poll() is None:
            os.killpg(arena_sh.pid, signal.SIGKILL)
        os.chmod(python, 0o755)


def parte_e(resultado, falhas):
    """E: o VERIFICAR.sh na copia."""
    feito = subprocess.run(["sh", os.path.join(COPIA, "VERIFICAR.sh")], cwd=COPIA, capture_output=True,
                           stdin=subprocess.DEVNULL, timeout=300)
    texto = feito.stdout.decode("utf-8", "replace")
    resultado["verificar_sh"] = texto[texto.find("RESUMO"):][:1500] if "RESUMO" in texto else texto[-1500:]
    if feito.returncode != 0 or "RESUMO" not in texto:
        falhas.append("E: o VERIFICAR.sh nao terminou (codigo %d)" % feito.returncode)
    if "RetroArch-Linux-x86_64.AppImage encontrado" not in texto:
        falhas.append("E: o VERIFICAR.sh nao achou o RetroArch do Linux")


def abre_sem_jogo(comando, sinal, segundos=60, aberto_depois=3):
    """Abre o Xenia sem jogo (a pasta de trabalho dele, --storage_root, e' um
    temporario) e espera a frase 'sinal' na saida (a prova de que a tela
    abriu); vale so se ele continua aberto 'aberto_depois' segundos depois
    dela (o que cai logo apos criar a tela nao conta). Depois fecha o grupo
    inteiro. Devolve (abriu, amostra da saida, codigo de saida ou None se
    ficou aberto)."""
    import limpeza
    pasta = tempfile.mkdtemp(prefix="arena_externo_")
    saida = os.path.join(pasta, "saida.txt")

    def ler():
        with open(saida, encoding="utf-8", errors="replace") as arquivo:
            return arquivo.read()
    try:
        with open(saida, "wb") as arquivo:
            processo = subprocess.Popen(comando + ["--storage_root=" + pasta], cwd=pasta, stdin=subprocess.DEVNULL,
                                        stdout=arquivo, stderr=subprocess.STDOUT, start_new_session=True)
        fim = time.monotonic() + segundos
        texto = ""
        while time.monotonic() < fim and processo.poll() is None and sinal not in texto:
            time.sleep(0.5)
            texto = ler()
        if sinal in texto and processo.poll() is None:
            time.sleep(aberto_depois)
        codigo = processo.poll()
        if codigo is None:
            os.killpg(processo.pid, signal.SIGKILL)
            processo.wait()
        texto = ler()
        linha = next((l for l in texto.splitlines() if sinal in l), texto[-200:])
        return sinal in texto and codigo is None, linha.strip()[:200], codigo
    finally:
        limpeza.apagar_pasta(pasta)


def parte_f(resultado, falhas):
    """F: os emuladores de fora do Linux saem do AppImage e abrem. O PCSX2 e
    o RPCS3 respondem a ajuda (ou a versao); o Xenia nao escreve nada na
    ajuda (sai com 0 e calado, achado de 21/10/2026): ele abre sem jogo e
    vale quando cria a tela (o Vulkan, aqui o llvmpipe do Mesa)."""
    import plataforma
    externos = {}
    for nome, pasta, argumento in (("PCSX2", os.path.join("PCSX2", "PCSX2"), "-help"),
                                   ("RPCS3", os.path.join("RPCS3", "RPCS3"), "--version"),
                                   ("Xenia", os.path.join("Xenia", "Xenia"), None)):
        onde = os.path.join(COPIA, "emuladores", pasta)
        appimage = next((os.path.join(onde, n) for n in sorted(os.listdir(onde)) if n.lower().endswith(".appimage")),
                        None) if os.path.isdir(onde) else None
        if not appimage:
            falhas.append("F: falta o %s do Linux" % nome)
            continue
        inicio = time.monotonic()
        programa = plataforma.programa_que_roda(appimage, nome)
        tirar = round(time.monotonic() - inicio, 1)
        codigo = None
        try:
            if argumento:
                feito = subprocess.run([programa, argumento], capture_output=True, timeout=60,
                                       stdin=subprocess.DEVNULL)
                codigo = feito.returncode
                abriu = codigo in (0, 1) and bool(feito.stdout or feito.stderr)
                amostra = (feito.stdout or feito.stderr).decode("utf-8", "replace")[:200]
            else:
                abriu, amostra, codigo = abre_sem_jogo([programa], "VulkanPresenter: Created")
        except (OSError, subprocess.TimeoutExpired) as falha:
            abriu, amostra = False, str(falha)
        externos[nome] = {"tirar_do_appimage_s": tirar, "abriu": abriu, "codigo": codigo, "saida": amostra,
                          "programa": programa}
        if not programa.endswith("AppRun") or not abriu:
            falhas.append("F: o %s do Linux nao abriu (codigo %s: %s)" % (nome, codigo, amostra[:120]))
    resultado["externos"] = externos


def parte_g(resultado, falhas):
    """As medidas do item 15 (testes/medidas_virtuais.py), as mesmas do
    Windows: o processador, o RetroArch do Linux sem freio em quatro nucleos
    e a gravacao em disco, aqui dentro do conteiner."""
    import medidas_virtuais
    import plataforma
    pasta = os.path.join(COPIA, "retroarch")
    programa = plataforma.retroarch_que_roda(os.path.join(pasta, plataforma.APPIMAGE_RETROARCH))
    medidas = medidas_virtuais.medir_aqui(programa, os.path.join(pasta, "cores"), ".so",
                                          antes_do_comando=["--config", os.path.join(pasta, "retroarch.cfg")])
    resultado["medidas"] = medidas
    for console, medida in medidas["nucleos"].items():
        print("  %-6s %s" % (console, medida.get("fps") or medida), flush=True)
    if not any(m.get("fps") for m in medidas["nucleos"].values()):
        falhas.append("G: nenhum nucleo deu a medida (%s)" % medidas["nucleos"])


def dentro_do_linux(argumentos):
    sys.path.insert(0, os.path.join(COPIA, "servidor"))
    sys.path.insert(0, os.path.join(COPIA, "testes"))
    # As partes vem em maiusculas ("A,F"); o filtro, em minusculas ("gba" nao e' G, B e A).
    escolha = next((a for a in argumentos if a and a == a.upper() and set(a) <= set("ABCDEFG,")), "A,B,C,D,E,F")
    partes = set(escolha.upper().replace(",", ""))
    filtro = " ".join(a for a in argumentos if a != escolha and not a.startswith("--")).lower()
    os.makedirs(SAIDA, exist_ok=True)
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "partes": sorted(partes)}
    falhas = []
    import plataforma
    resultado["sistema"] = plataforma.descricao()
    tela = ligar_a_tela()
    inicio = time.monotonic()
    try:
        if partes & {"A", "B"}:
            print("== A e B: os jogos livres no RetroArch do Linux", flush=True)
            parte_a_b(resultado, falhas, filtro, partes)
        if "C" in partes:
            print("== C: pelo servidor do ARENA", flush=True)
            parte_c(resultado, falhas)
        if "D" in partes:
            print("== D: o ARENA.sh", flush=True)
            parte_d(resultado, falhas)
        if "E" in partes:
            print("== E: o VERIFICAR.sh", flush=True)
            parte_e(resultado, falhas)
        if "F" in partes:
            print("== F: os emuladores de fora do Linux", flush=True)
            parte_f(resultado, falhas)
        if "G" in partes:
            print("== G: as medidas do item 15", flush=True)
            parte_g(resultado, falhas)
    except Exception as erro:           # o erro vai para o resultado, nao so para a tela
        import traceback
        falhas.append("erro no teste: %s" % "".join(traceback.format_exception_only(type(erro), erro)).strip())
        traceback.print_exc()
    finally:
        tela.terminate()
        resultado["segundos"] = round(time.monotonic() - inicio, 1)
        resultado["falhas"] = falhas
        with open(os.path.join(SAIDA, "resultado.json"), "w", encoding="utf-8") as arquivo:
            json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    if falhas:
        print("\nFALHAS:\n  " + "\n  ".join(falhas))
        return 1
    print("\nTudo certo (%.0f s)." % resultado["segundos"])
    return 0


def principal():
    argumentos = [a for a in sys.argv[1:] if a != "--na-copia"]
    if sys.platform.startswith("win"):
        return pelo_conteiner(argumentos)
    if "--na-copia" not in sys.argv:
        para_a_copia(argumentos)            # nao volta: roda de novo da copia
    return dentro_do_linux(argumentos)


if __name__ == "__main__":
    sys.exit(principal())
