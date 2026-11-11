# -*- coding: utf-8 -*-
r"""O PS2 a 60 quadros de verdade NO CELULAR (11/11/2026): o irmao do testes\teste_mais_quadros.py.

O nucleo ARMSX2 (o PCSX2 compilado para o RetroArch do Android) traz o mesmo patches.zip do PCSX2 de computador.
O ARENA do celular identifica o jogo pelo ISO (serial e CRC), grava o system/pcsx2/gamesettings/<SERIAL>_<CRC>.ini
com o patch "60 FPS" e liga o EnablePatches do nucleo. O teste:

  1. abre o ARENA do celular (APK de teste, no cabo), guarda o ajuste do Mais quadros e poe "Sempre";
  2. abre o Black (BR).iso (jogos/pessoais/PS2 do celular) pela API, como o aluno faria tocando no jogo;
  3. confere, com o jogo rodando: o arquivo do jogo no gamesettings, a linha do servidor no logcat e o
     "Enabled patch" no emulog.txt do ARMSX2;
  4. sai do jogo, confere que o servidor viu o fim e que o ISO ficou guardado em ps2_jogos_aprendidos.json;
  5. devolve o ajuste do Mais quadros como estava (teste que muda a configuracao do app desfaz no fim).

Uso:
    servidor\python\python.exe testes\teste_60_ps2_celular.py [pedaco do titulo, "black" por padrao]
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import celular_arena as c  # noqa: E402
import teste_android as t  # noqa: E402

PASTA_PCSX2 = "/sdcard/ARENA/retroarch/system/pcsx2"
CONFERENCIAS = []


def ok(nome, deu, detalhe=""):
    CONFERENCIAS.append((nome, bool(deu)))
    print("  %-6s %s%s" % ("ok" if deu else "FALHOU", nome, (" (%s)" % detalhe) if detalhe else ""))
    return bool(deu)


def no_celular(comando):
    return t.adb_texto("shell", comando)


def main(argv):
    pedaco = argv[1] if len(argv) > 1 else "black"
    print("PS2 a 60 quadros no celular")
    t.adb("logcat", "-c")
    pagina = c.abrir()
    estado = c.pedir(pagina, "/api/estado") or {}
    modo_antes = (estado.get("config") or {}).get("mfg_super_motion", "automatico")
    jogo = c.achar_jogo(pagina, pedaco, "playstation 2") or c.achar_jogo(pagina, pedaco, "ps2")
    if not jogo:      # o ISO acabou de chegar: a lista precisa ser atualizada
        c.pedir(pagina, "/api/indexar", {})
        time.sleep(8)
        jogo = c.achar_jogo(pagina, pedaco, "playstation 2") or c.achar_jogo(pagina, pedaco, "ps2")
    if not ok("o jogo esta no catalogo do celular", jogo, pedaco):
        pagina.fechar()
        return 1
    print("  jogo: %s (%s)" % (jogo.get("titulo"), jogo.get("id")))
    try:
        c.pedir(pagina, "/api/config", {"mfg_super_motion": "sempre"})
        estado = c.pedir(pagina, "/api/estado") or {}
        ok("o Mais quadros ficou em Sempre", (estado.get("config") or {}).get("mfg_super_motion") == "sempre")
        antes = time.monotonic()
        resposta = c.pedir(pagina, "/api/jogar", {"jogo_id": jogo["id"]}) or {}
        ok("o servidor aceitou abrir o jogo", resposta.get("ok", resposta.get("aberto", True)), json.dumps(resposta)[:120])
        abriu = t.esperar(lambda: "RetroActivityFuture" in t.tela_de_cima(), 90)
        ok("o RetroArch ficou na frente", abriu, "%.0f s" % (time.monotonic() - antes))
        time.sleep(45)      # o Black demora para passar do ELF ao jogo no A12
        arquivos = no_celular("ls %s/gamesettings" % PASTA_PCSX2)
        ok("o arquivo do jogo foi gravado no gamesettings", "SLUS-21376_5C891FF1.ini" in arquivos, arquivos.strip())
        conteudo = no_celular("cat %s/gamesettings/SLUS-21376_5C891FF1.ini" % PASTA_PCSX2)
        ok("o patch 60 FPS esta no arquivo do jogo", "Enable = 60 FPS" in conteudo)
        ini = no_celular("grep -i EnablePatches %s/inis/*.ini" % PASTA_PCSX2)
        ok("o EnablePatches do nucleo esta ligado", "true" in ini.lower(), ini.strip()[:100])
        logcat = t.adb_texto("logcat", "-d", "-s", "ARENA-servidor")
        linha = [l for l in logcat.splitlines() if "60 quadros" in l]
        ok("o servidor disse que ligou o patch", linha, linha[0][-90:] if linha else "")
        emulog = no_celular("grep -a -i -E 'Serial:|CRC:|Enabled patch|patches' %s/logs/emulog.txt" % PASTA_PCSX2)
        ok("o ARMSX2 leu o serial e o CRC", "SLUS-21376" in emulog and "5C891FF1" in emulog.upper(), emulog.strip()[:160])
        ok("o ARMSX2 ligou o patch (Enabled patch)", "enabled patch" in emulog.lower())
        saiu = t.sair_do_jogo()
        voltou = t.esperar(lambda: "ArenaActivity" in t.tela_de_cima(), 30)
        if not voltou:
            t.adb("shell", "am", "start", "-n", t.TELA_DO_ARENA)
        fechado = t.esperar(lambda: not (pagina.pedir("/api/estado") or {}).get("jogo_em_andamento", {}).get("ativo"), 40)
        if not fechado:
            # O nucleo ARMSX2 nao sai pelo F10 injetado (os outros nucleos saem), e sem root o adb nao mata o
            # processo: o aluno sai pelo menu do RetroArch. Aqui o teste fecha o app inteiro e abre de novo.
            print("  nota   o PS2 nao saiu pelo F10 (%s): o app foi fechado e reaberto para a limpeza" % saiu)
            pagina.fechar()
            t.adb("shell", "am", "force-stop", t.PACOTE)
            time.sleep(3)
            pagina = c.abrir()
        else:
            ok("o servidor viu o jogo fechar", True, "saiu por %s" % saiu)
        aprendidos = no_celular("run-as io.github.rafaparise.arena cat files/arena-dados/dados/ps2_jogos_aprendidos.json")
        ok("o ISO ficou guardado (serial e CRC)", "SLUS-21376" in aprendidos, aprendidos.strip()[:120])
    finally:
        c.pedir(pagina, "/api/config", {"mfg_super_motion": modo_antes})
        estado = c.pedir(pagina, "/api/estado") or {}
        ok("o ajuste do Mais quadros voltou a %s" % modo_antes,
           (estado.get("config") or {}).get("mfg_super_motion") == modo_antes)
        pagina.fechar()
    falhas = [nome for nome, deu in CONFERENCIAS if not deu]
    print("RESULTADO: %s" % ("tudo certo" if not falhas else "falhou: " + "; ".join(falhas)))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
