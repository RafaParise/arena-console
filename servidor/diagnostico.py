# -*- coding: utf-8 -*-
"""
ARENA - Verificar e reparar
============================
Confere a instalacao inteira e conserta o que der para consertar sozinho.

Roda pelo VERIFICAR.bat, ou pelo terminal:
    python diagnostico.py            confere e conserta
    python diagnostico.py --so-ver   so confere, nao mexe em nada

Nunca apaga jogo, save nem save state. O que ele mexe: pastas que faltam,
arquivos temporarios esquecidos, configuracao ilegivel, catalogo corrompido
e banco de recordes danificado (restaurado da copia de seguranca).
"""

import json
import os
import shutil
import sqlite3
import sys

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA_SERVIDOR)

PASTAS = [
    "dados", "backup", "launcher", "servidor",
    "jogos", "jogos/livres", "jogos/turma", "jogos/pessoais",
    "retroarch", "retroarch/cores", "retroarch/system", "retroarch/saves",
    "retroarch/states", "retroarch/cheats", "retroarch/remaps",
    "retroarch/controles", "retroarch/screenshots",
]

PROGRAMA = [
    "ARENA.bat", "LEIA-ME.md",
    "launcher/index.html", "launcher/estilo.css", "launcher/app.js",
    "servidor/arena.py", "servidor/indexador.py", "servidor/hardware.py",
    "servidor/cheats.py", "servidor/graficos.py",
    "servidor/consoles.json", "servidor/graficos.json", "servidor/recursos.json",
]

JSONS = ["servidor/consoles.json", "servidor/graficos.json",
         "servidor/recursos.json"]

SO_VER = "--so-ver" in sys.argv

ok = []
consertado = []
atencao = []
grave = []


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def titulo(texto):
    print()
    print(texto)
    print("-" * len(texto))


# ---------------------------------------------------------------------------
titulo("1. Pastas")

faltando = [p for p in PASTAS if not os.path.isdir(caminho(*p.split("/")))]
if not faltando:
    ok.append("todas as %d pastas no lugar" % len(PASTAS))
    print("  todas as %d pastas no lugar" % len(PASTAS))
else:
    for p in faltando:
        if SO_VER:
            atencao.append("pasta faltando: %s" % p)
            print("  FALTA  %s" % p)
        else:
            os.makedirs(caminho(*p.split("/")), exist_ok=True)
            consertado.append("pasta recriada: %s" % p)
            print("  criei  %s" % p)


# ---------------------------------------------------------------------------
titulo("2. Arquivos do programa")

perdidos = [a for a in PROGRAMA if not os.path.isfile(caminho(*a.split("/")))]
if perdidos:
    for a in perdidos:
        grave.append("arquivo do programa faltando: %s" % a)
        print("  FALTA  %s" % a)
    print("  Sem esses arquivos o ARENA nao abre. Copie a pasta original de novo.")
else:
    print("  os %d arquivos do programa estao presentes" % len(PROGRAMA))
    ok.append("arquivos do programa presentes")

for arquivo in JSONS:
    alvo = caminho(*arquivo.split("/"))
    if not os.path.isfile(alvo):
        continue
    try:
        with open(alvo, encoding="utf-8") as f:
            json.load(f)
        print("  ok     %s" % arquivo)
    except (ValueError, OSError) as falha:
        grave.append("%s ilegivel: %s" % (arquivo, falha))
        print("  QUEBRADO  %s (%s)" % (arquivo, str(falha)[:44]))
        print("            Copie esse arquivo da pasta original.")


# ---------------------------------------------------------------------------
titulo("3. Arquivos temporarios esquecidos")

sobras = []
for pasta in ("dados", "retroarch", "servidor"):
    alvo = caminho(pasta)
    if not os.path.isdir(alvo):
        continue
    sobras += [os.path.join(pasta, n) for n in os.listdir(alvo)
               if n.endswith(".tmp")]

if not sobras:
    print("  nenhum")
    ok.append("sem temporarios esquecidos")
else:
    for s in sobras:
        if SO_VER:
            atencao.append("temporario esquecido: %s" % s)
            print("  sobrou %s" % s)
        else:
            try:
                os.remove(caminho(*s.split(os.sep)))
                consertado.append("temporario apagado: %s" % s)
                print("  apaguei %s" % s)
            except OSError:
                atencao.append("nao consegui apagar %s" % s)


# ---------------------------------------------------------------------------
titulo("4. Suas configuracoes")

config = caminho("dados", "config.json")
if not os.path.isfile(config):
    print("  ainda nao existe. O ARENA cria na primeira abertura.")
else:
    try:
        with open(config, encoding="utf-8") as f:
            dados = json.load(f)
        apelido = dados.get("apelido") or "(sem apelido)"
        amigos = len(dados.get("servidores") or [])
        print("  ok     apelido: %s | amigos cadastrados: %d" % (apelido, amigos))
        ok.append("configuracao valida")
    except (ValueError, OSError):
        if SO_VER:
            grave.append("config.json ilegivel")
            print("  QUEBRADO  config.json")
        else:
            shutil.move(config, config + ".quebrado")
            consertado.append("config.json quebrado foi posto de lado")
            print("  QUEBRADO  guardei como config.json.quebrado")
            print("            O ARENA cria um novo na proxima abertura.")
            print("            Voce vai precisar reescrever seu apelido.")


# ---------------------------------------------------------------------------
titulo("5. Catalogo de jogos")

manifesto = caminho("dados", "manifesto.json")
if not os.path.isfile(manifesto):
    print("  ainda nao existe. O ARENA monta na abertura.")
else:
    try:
        with open(manifesto, encoding="utf-8") as f:
            dados = json.load(f)
        print("  ok     %d jogo(s) no catalogo" % dados.get("total", 0))
        ok.append("catalogo valido")
    except (ValueError, OSError):
        if SO_VER:
            atencao.append("manifesto.json ilegivel")
            print("  QUEBRADO  manifesto.json")
        else:
            os.remove(manifesto)
            consertado.append("catalogo apagado para ser remontado")
            print("  QUEBRADO  apaguei. O ARENA remonta sozinho, sem perder nada.")


# ---------------------------------------------------------------------------
titulo("6. Banco de recordes")

banco = caminho("dados", "arena.db")
if not os.path.isfile(banco):
    print("  ainda nao existe. O ARENA cria na primeira abertura.")
else:
    saudavel = False
    try:
        conexao = sqlite3.connect(banco)
        resultado = conexao.execute("PRAGMA integrity_check").fetchone()[0]
        quantos = conexao.execute("SELECT COUNT(*) FROM placar").fetchone()[0]
        sessoes = conexao.execute("SELECT COUNT(*) FROM sessao").fetchone()[0]
        pendentes = conexao.execute(
            "SELECT COUNT(*) FROM placar WHERE enviado = 0").fetchone()[0]
        conexao.close()
        saudavel = (resultado == "ok")
        print("  integridade: %s" % resultado)
        print("  %d pontuacao(oes), %d partida(s), %d aguardando envio"
              % (quantos, sessoes, pendentes))
        if saudavel:
            ok.append("banco de recordes integro")
    except sqlite3.DatabaseError as falha:
        print("  QUEBRADO  %s" % str(falha)[:52])

    if not saudavel:
        copias = []
        pasta_backup = caminho("backup")
        if os.path.isdir(pasta_backup):
            copias = sorted(
                d for d in os.listdir(pasta_backup)
                if os.path.isfile(os.path.join(pasta_backup, d, "arena.db")))
        if not copias:
            grave.append("banco danificado e sem copia de seguranca")
            print("  Nao ha copia de seguranca em backup/.")
        elif SO_VER:
            atencao.append("banco danificado, ha copia de %s" % copias[-1])
            print("  Ha copia de seguranca de %s." % copias[-1])
        else:
            origem = os.path.join(pasta_backup, copias[-1], "arena.db")
            shutil.move(banco, banco + ".quebrado")
            shutil.copy2(origem, banco)
            consertado.append("banco restaurado da copia de %s" % copias[-1])
            print("  restaurei a copia de %s" % copias[-1])
            print("  o banco danificado ficou como arena.db.quebrado")


# ---------------------------------------------------------------------------
titulo("7. RetroArch e emuladores")

exe = caminho("retroarch", "retroarch.exe")
if os.path.isfile(exe):
    print("  ok     retroarch.exe encontrado")
    ok.append("retroarch presente")
else:
    atencao.append("retroarch.exe nao encontrado")
    print("  FALTA  retroarch.exe em retroarch\\")
    print("         Sem ele o ARENA abre mas nenhum jogo inicia.")

pasta_cores = caminho("retroarch", "cores")
cores = []
if os.path.isdir(pasta_cores):
    cores = [n for n in os.listdir(pasta_cores) if n.lower().endswith(".dll")]
print("  %d emulador(es) instalado(s)" % len(cores))
if not cores:
    atencao.append("nenhum emulador instalado")
    print("         Baixe pelo RetroArch: Carregar Nucleo, Baixar um Nucleo.")

sistema = caminho("retroarch", "system")
quantos_sistema = 0
if os.path.isdir(sistema):
    quantos_sistema = sum(
        1 for n in os.listdir(sistema)
        if os.path.isfile(os.path.join(sistema, n)) and not n.lower().endswith(".txt"))
print("  %d arquivo(s) de sistema na pasta system" % quantos_sistema)


# ---------------------------------------------------------------------------
titulo("8. Espaco em disco")

try:
    uso = shutil.disk_usage(RAIZ)
    livre_gb = uso.free / (1024 ** 3)
    print("  %.1f GB livres de %.1f GB" % (livre_gb, uso.total / (1024 ** 3)))
    if livre_gb < 0.5:
        grave.append("menos de 0,5 GB livres")
        print("  POUCO ESPACO. O ARENA pode falhar ao gravar.")
    elif livre_gb < 2:
        atencao.append("menos de 2 GB livres")
        print("  Espaco apertado. Apague save states que nao usa.")
    else:
        ok.append("espaco em disco suficiente")
except OSError:
    pass


# ---------------------------------------------------------------------------
titulo("9. Copias de seguranca")

pasta_backup = caminho("backup")
copias = []
pacotes = []
if os.path.isdir(pasta_backup):
    copias = [d for d in os.listdir(pasta_backup)
              if os.path.isdir(os.path.join(pasta_backup, d))]
    pacotes = [d for d in os.listdir(pasta_backup) if d.endswith(".zip")]
print("  %d copia(s) automatica(s), %d pacote(s) de progresso"
      % (len(copias), len(pacotes)))
if not copias:
    print("  Ainda nao ha copia. A primeira sai quando voce fechar um jogo.")


# ---------------------------------------------------------------------------
titulo("10. Servidor local")

import socket
porta = 8777
livre = True
try:
    with socket.create_connection(("127.0.0.1", porta), timeout=1.0):
        livre = False
except OSError:
    pass

if livre:
    print("  a porta %d esta livre. O ARENA vai conseguir abrir." % porta)
    ok.append("porta livre")
else:
    print("  ja tem alguma coisa escutando na porta %d." % porta)
    print("  Se o ARENA ja estiver aberto, tudo bem. Se nao, feche o outro")
    print("  programa que esta usando essa porta.")
    atencao.append("porta %d ocupada" % porta)


# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("RESUMO")
print("=" * 60)
print("  Tudo certo:   %d" % len(ok))
print("  Consertado:   %d" % len(consertado))
print("  Atencao:      %d" % len(atencao))
print("  Grave:        %d" % len(grave))

for item in consertado:
    print("   [consertei] %s" % item)
for item in atencao:
    print("   [atencao]   %s" % item)
for item in grave:
    print("   [grave]     %s" % item)

print()
if grave:
    print("  Tem coisa que eu nao consigo consertar sozinho. Veja acima.")
elif consertado:
    print("  Consertei o que estava errado. Pode abrir o ARENA.")
else:
    print("  Nada a consertar. O ARENA esta saudavel.")

if SO_VER:
    print()
    print("  (modo so conferir: nada foi alterado)")
