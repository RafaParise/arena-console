# -*- coding: utf-8 -*-
r"""Continuar de onde parou pelo ARENA de verdade (10/11/2026), com o RetroArch e um jogo livre de MSX.

1. Liga a chave em Ajustes, abre o jogo e fecha pela janela: o RetroArch tem de gravar o ponto automatico
   (states\<Nucleo>\<jogo>.state.auto).
2. Abre de novo: o ARENA manda voltar ao ponto (savestate_auto_load = "true" no arena_override.cfg).
3. Poe um save do jogo MAIS NOVO que o ponto (como se o app tivesse sido fechado a forca depois de salvar no jogo) e
   abre de novo: o ARENA NAO volta ao ponto, e o ponto velho e' trocado na saida.
4. Desliga a chave: as duas opcoes voltam a "false".
Tudo numa COPIA do ARENA (testes\copia_do_arena.py); nada da pasta do Rafael muda.

Uso:
    servidor\python\python.exe testes\teste_continuar_pelo_arena.py
"""
import os
import shutil
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import copia_do_arena as c  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402

RAIZ = c.RAIZ
NUCLEO = "bluemsx_libretro.dll"
JOGO = os.path.join(AQUI, "jogos_livres", "MSX", "noborunoca.rom")
MAQUINAS = os.path.join(RAIZ, "retroarch", "system", "Machines")


def main():
    if not os.path.isfile(JOGO) or not os.path.isdir(MAQUINAS):
        print("Faltam o jogo livre do MSX (testes\\jogos_livres\\MSX) ou retroarch\\system\\Machines.")
        return 1
    if c.porta_ocupada():
        print("Ja ha um servidor na porta da copia (%d), de um teste anterior: feche-o antes." % c.PORTA)
        return 1
    trabalho, copia = c.nova_pasta()
    retroarch = os.path.join(copia, "retroarch")
    override = os.path.join(copia, "dados", "arena_override.cfg")
    registro = os.path.join(trabalho, "servidor.log")
    falhas = []
    servidor = None

    def confere(nome, ok, detalhe=None):
        print("  %-6s %s%s" % ("ok" if ok else "FALHOU", nome, (" (%s)" % (detalhe,)) if detalhe else ""), flush=True)
        if not ok:
            falhas.append(nome)

    def retroarchs():
        return c.processos("retroarch", retroarch)

    def opcao(chave):
        try:
            with open(override, encoding="utf-8", errors="replace") as arquivo:
                for linha in arquivo:
                    if linha.split("=")[0].strip() == chave:
                        return linha.split("=", 1)[1].strip().strip('"')
        except OSError:
            return None
        return None

    def ponto():
        pasta = os.path.join(retroarch, "states")
        for atual, _, arquivos in os.walk(pasta):
            for nome in arquivos:
                if nome == "noborunoca.state.auto":
                    return os.path.join(atual, nome)
        return None

    def jogar_e_fechar(jogo_id, segundos=12):
        resposta = c.pedir("/api/jogar", {"jogo_id": jogo_id}, espera=30)
        aberto = c.esperar(retroarchs, 30)
        time.sleep(segundos)
        c.fechar_pela_janela(retroarch, 30)
        fechou = c.esperar(lambda: not retroarchs(), 30)
        return bool(resposta.get("ok")) and bool(aberto) and bool(fechou), resposta

    try:
        print("Copiando o ARENA (com o MSX) para %s ..." % copia, flush=True)
        c.montar(copia, [NUCLEO], {"MSX": [JOGO]})
        shutil.copytree(MAQUINAS, os.path.join(retroarch, "system", "Machines"))
        servidor = c.subir_servidor(copia, registro)
        c.pedir("/api/indexar", {}, espera=90)
        achados = c.esperar(lambda: c.jogos_do_console(c.pedir("/api/catalogo", espera=30), "msx"), 60)
        confere("o jogo aparece no MSX", bool(achados))
        if not achados:
            return 1
        jogo_id = achados[0]["id"]
        c.pedir("/api/config", {"continuar_de_onde_parou": True}, espera=15)

        print("1. Primeira vez: grava o ponto ao fechar.", flush=True)
        ok, resposta = jogar_e_fechar(jogo_id)
        confere("abriu e fechou", ok, None if ok else resposta)
        confere("so grava, nao carrega", opcao("savestate_auto_save") == "true" and opcao("savestate_auto_load") == "false",
                (opcao("savestate_auto_save"), opcao("savestate_auto_load")))
        arquivo_do_ponto = c.esperar(ponto, 15)
        confere("o RetroArch gravou o ponto automatico", bool(arquivo_do_ponto), arquivo_do_ponto)
        if not arquivo_do_ponto:
            return 1

        print("2. Segunda vez: volta ao ponto.", flush=True)
        ok, resposta = jogar_e_fechar(jogo_id)
        confere("abriu e fechou", ok, None if ok else resposta)
        confere("manda voltar ao ponto", opcao("savestate_auto_load") == "true", opcao("savestate_auto_load"))

        print("3. Save do jogo mais novo que o ponto: comeca pelo save.", flush=True)
        save = os.path.join(retroarch, "saves", "blueMSX", "noborunoca.srm")
        os.makedirs(os.path.dirname(save), exist_ok=True)
        with open(save, "wb") as arquivo:
            arquivo.write(b"\0" * 64)
        futuro = time.time() + 600
        os.utime(save, (futuro, futuro))
        hora_antes = os.path.getmtime(arquivo_do_ponto)
        ok, resposta = jogar_e_fechar(jogo_id, segundos=6)
        confere("abriu e fechou", ok, None if ok else resposta)
        confere("NAO volta ao ponto", opcao("savestate_auto_load") == "false", opcao("savestate_auto_load"))
        confere("o ponto velho foi trocado na saida", os.path.getmtime(arquivo_do_ponto) > hora_antes)
        with open(registro, encoding="utf-8", errors="replace") as arquivo:
            texto = arquivo.read()
        confere("o registro explica a escolha", "mais novo que o ponto automatico" in texto)

        print("4. Chave desligada: nada de ponto.", flush=True)
        c.pedir("/api/config", {"continuar_de_onde_parou": False}, espera=15)
        ok, resposta = jogar_e_fechar(jogo_id, segundos=6)
        confere("abriu e fechou", ok, None if ok else resposta)
        confere("as duas opcoes desligadas",
                opcao("savestate_auto_save") == "false" and opcao("savestate_auto_load") == "false",
                (opcao("savestate_auto_save"), opcao("savestate_auto_load")))
    finally:
        for pid in retroarchs():
            c.subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        if servidor is not None:
            c.derrubar(copia)
        limpeza.apagar_pasta(trabalho)
    print()
    if falhas:
        print("FALHOU: %d de %s" % (len(falhas), ", ".join(falhas)))
        return 1
    print("Continuar de onde parou pelo ARENA: tudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
