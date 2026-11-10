# -*- coding: utf-8 -*-
r"""O DreamPotato pelo ARENA de verdade (10/11/2026): o VMU do Dreamcast numa janela a parte, aberto JUNTO com o jogo e
fechado com ele (servidor\companheiros.py; acessorio "dc_encaixes_{n}", encaixe 1 = "DreamPotato").

Monta uma COPIA do ARENA (testes\copia_do_arena.py) com o Flycast, um jogo de Dreamcast do professor e o DreamPotato
(emuladores\DreamPotato, que o ARENA nao distribui: o zip dele traz a BIOS do VMU da Sega).

  1. Sem o encaixe ligado: o jogo abre e o DreamPotato NAO abre.
  2. Com o encaixe 1 do controle 1 em "DreamPotato": os dois abrem; a janela do DreamPotato mostra imagem; o registro do
     RetroArch mostra o Flycast falando com ele.
  3. Fechar o jogo pela janela (como o aluno) fecha o DreamPotato tambem.

Uso:
    servidor\python\python.exe testes\teste_dreampotato_pelo_arena.py [pasta do jogo de Dreamcast]
(sem jogo: o primeiro de jogos\pessoais\Dreamcast; precisa do DreamPotato em emuladores\DreamPotato)
"""
import glob
import os
import shutil
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
from teste_consoles_livres import imagem_de_verdade  # noqa: E402

RAIZ = c.RAIZ
NUCLEO = "flycast_libretro.dll"
ACESSORIO = "dc_encaixes_1"


def jogo_de_dreamcast():
    pasta = os.path.join(RAIZ, "jogos", "pessoais", "Dreamcast")
    if not os.path.isdir(pasta):
        return None
    itens = sorted(os.path.join(pasta, n) for n in os.listdir(pasta))
    # O Capcom vs. SNK 2 usa o VMU para salvar (o melhor jogo para ver a telinha); senao, o primeiro.
    return next((i for i in itens if "Capcom" in os.path.basename(i)), itens[0] if itens else None)


def main():
    caminhos = [a for a in sys.argv[1:] if not a.startswith("--")]
    jogo = os.path.abspath(caminhos[0]) if caminhos else jogo_de_dreamcast()
    original = os.path.join(RAIZ, "emuladores", "DreamPotato")
    if not jogo or not os.path.exists(jogo) or not os.path.isfile(os.path.join(original, "DreamPotato.exe")):
        print("Faltam: um jogo em jogos\\pessoais\\Dreamcast e o DreamPotato em emuladores\\DreamPotato.")
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    pasta_do_potato = os.path.join(copia, "emuladores", "DreamPotato")
    registro = os.path.join(trabalho, "servidor.log")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    def potatos():
        return c.processos("DreamPotato", pasta_do_potato)

    def retroarchs():
        return c.processos("retroarch", retroarch)

    def arquivos_do_potato():
        achados = []
        for raiz, _pastas, nomes in os.walk(pasta_do_potato):
            achados += [os.path.relpath(os.path.join(raiz, n), pasta_do_potato) for n in nomes]
        return achados

    def registro_do_retroarch():
        achados = sorted(glob.glob(os.path.join(copia, "dados", "retroarch__*.log")), key=os.path.getmtime)
        if not achados:
            return ""
        with open(achados[-1], encoding="utf-8", errors="replace") as arquivo:
            return arquivo.read()

    def fechar_o_jogo():
        c.fechar_pela_janela(retroarch, 30)
        return c.esperar(lambda: not retroarchs(), 20)

    try:
        print("Copiando o ARENA (com %s) para %s ..." % (os.path.basename(jogo), copia), flush=True)
        c.montar(copia, [NUCLEO], {"Dreamcast": [jogo]})
        shutil.copytree(original, pasta_do_potato, ignore=shutil.ignore_patterns("imgui.ini", "*.log"))
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=90)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "dreamcast"), 60)
        confere("o jogo aparece no Dreamcast", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]

        print("1. Sem o encaixe: so o jogo", flush=True)
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id, "jeito": "livre"}, espera=30)
        confere("o jogo abriu", bool(resposta.get("ok")), resposta)
        confere("o RetroArch abriu", bool(c.esperar(retroarchs, 30)))
        time.sleep(8)
        confere("o DreamPotato NAO abriu", not potatos())
        confere("o jogo fechou pela janela", fechar_o_jogo())

        print("2. Com o encaixe 1 em DreamPotato", flush=True)
        c.pedir("/api/config", {"acessorios": {ACESSORIO: {"encaixe1": "DreamPotato"}}})
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id, "jeito": "livre"}, espera=30)
        confere("o jogo abriu", bool(resposta.get("ok")), resposta)
        confere("o RetroArch abriu", bool(c.esperar(retroarchs, 30)))
        programa = c.esperar(potatos, 30)
        confere("o DreamPotato abriu junto", bool(programa))
        antes_dos_arquivos = set(arquivos_do_potato())
        time.sleep(12)
        if programa and "--encaixar" in sys.argv:
            # Como a pessoa faz na primeira vez: Insert na janela do DreamPotato encaixa o VMU no controle (o README
            # dele; desencaixado, ele dorme e a ligacao com o Flycast cai: "DreamPotato[0] receive failed").
            c.subprocess.run(["powershell", "-NoProfile", "-Command",
                              "$w = New-Object -ComObject WScript.Shell; [void]$w.AppActivate(%d); Start-Sleep -Milliseconds 600; "
                              "$w.SendKeys('{INSERT}')" % programa[0]], capture_output=True)
            print("  (Insert apertado na janela do DreamPotato)", flush=True)
        time.sleep(18)
        foto = os.path.join(trabalho, "foto_dreampotato.png")
        ok, detalhe = False, "o DreamPotato nao abriu"
        for _ in range(3 if programa else 0):
            c.foto_da_janela(programa[0], foto)
            ok, detalhe = imagem_de_verdade(foto)
            if ok:
                break
            time.sleep(5)
        confere("a janela do DreamPotato mostra imagem", ok, detalhe)
        if os.path.isfile(foto):
            shutil.copyfile(foto, os.path.join(c.tempfile.gettempdir(), "arena_dreampotato.png"))
        texto = registro_do_retroarch()
        with open(os.path.join(c.tempfile.gettempdir(), "arena_dreampotato_retroarch.log"), "w", encoding="utf-8") as copia_do_registro:
            copia_do_registro.write(texto)
        linhas = [l.strip() for l in texto.splitlines() if "dreampotato" in l.lower() or "dreamlink" in l.lower()]
        confere("o Flycast procurou o DreamPotato (o encaixe 1 chegou a ele)", bool(linhas), linhas[:4])
        confere("o Flycast ficou ligado ao DreamPotato", any("Connected to DreamPotato" in l for l in linhas)
                and "receive failed" not in (linhas[-1] if linhas else ""), linhas[-3:])

        print("3. Fechar o jogo fecha os dois", flush=True)
        confere("o jogo fechou pela janela", fechar_o_jogo())
        confere("o DreamPotato fechou junto", bool(c.esperar(lambda: not potatos(), 20)), potatos())
        novos = sorted(set(arquivos_do_potato()) - antes_dos_arquivos)
        print("  arquivos que o DreamPotato criou: %s" % (novos or "nenhum"), flush=True)
        for novo in novos:
            if novo.lower().endswith((".json", ".ini", ".txt", ".cfg")):
                with open(os.path.join(pasta_do_potato, novo), encoding="utf-8", errors="replace") as arquivo:
                    print("  --- %s ---\n%s" % (novo, arquivo.read()[:1500]), flush=True)
    finally:
        for pid in potatos() + retroarchs():
            c.subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        if servidor is not None:
            c.derrubar(copia)
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        print("FALHOU: %d de %s" % (len(falhas), ", ".join(falhas)))
        return 1
    print("DreamPotato pelo ARENA: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
