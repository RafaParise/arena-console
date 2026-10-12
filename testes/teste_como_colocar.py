# -*- coding: utf-8 -*-
r"""Como colocar jogos: o guia de cada console diz a verdade?

Pedido do Rafael (02/10/2026): instrucoes claras de como adicionar os jogos,
quais arquivos, se vai em pasta ou .zip -- "de uma forma extremamente
simples de entender". O guia (servidor\como_colocar.py, botao "Como colocar
jogos") promete coisas; aqui elas sao conferidas:

  1. todo console do consoles.json tem guia: pasta, formatos, regra de .zip
     (CD: nao; fliperama: tem que ser; emulador de fora: nao) e exemplo;
  2. BIOS: "ja esta" so quando o arquivo esta mesmo em retroarch\system
     (uma das da lista para o PS1; TODAS para o Intellivision);
  3. a promessa do .zip de cartucho, de verdade: um jogo de SNES zipado, na
     pasta do SNES, e' reconhecido como SNES pelo indexador e ABRE no
     RetroArch (foto da tela);
  4. a tela (Edge sem janela, ARENA isolado): o botao abre a gaveta, cada
     console mostra o que deve, e "Abrir a pasta" recusa console inventado.

Uso: servidor\python\python.exe testes\teste_como_colocar.py [--sem-retroarch]
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import como_colocar  # noqa: E402
import jogos_de_teste  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402

DISCO = {"ps1", "segacd", "saturn", "dreamcast", "pcfx", "threedo", "cdi", "psp"}
FLIPERAMA = {"arcade", "neogeo"}
DE_FORA = {"ps2", "gamecube", "wii", "ps3", "xbox360"}


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_como_colocar_")
    try:
        plataformas = json.load(open(os.path.join(RAIZ, "servidor", "consoles.json"),
                                     encoding="utf-8"))["plataformas"]
        sistema = os.path.join(pasta, "system")
        os.makedirs(sistema)

        print("1. Todo console tem guia")
        guia = {c["id"]: c for c in como_colocar.guia(plataformas, sistema, os.path.join(pasta, "jogos"))}
        incompletos = [i for i, c in guia.items()
                       if not (c["pasta"].startswith("jogos\\pessoais\\") and c["formatos"] and c["como"]
                               and c["zip_texto"] and c["exemplo"].startswith(c["pasta"]))]
        confere("os %d consoles tem pasta, formatos, como guardar, regra de zip e exemplo" % len(guia),
                len(guia) == len(plataformas) and not incompletos, incompletos)
        errados = sorted([i for i in DISCO if guia[i]["zip"] != "nao"]
                         + [i for i in FLIPERAMA if guia[i]["zip"] != "obrigatorio"]
                         + [i for i in DE_FORA if guia[i]["zip"] != "nao"])
        confere("CD e emulador de fora: zip nao; fliperama: zip obrigatorio", not errados, errados)
        confere("o exemplo usa um formato que o console aceita",
                all(os.path.splitext(c["exemplo"])[1].lower() in [f.lower() for f in c["formatos"]]
                    for i, c in guia.items() if i not in ("scummvm", "dos")),
                [(i, c["exemplo"]) for i, c in guia.items()
                 if i not in ("scummvm", "dos")
                 and os.path.splitext(c["exemplo"])[1].lower() not in [f.lower() for f in c["formatos"]]])

        documento = open(os.path.join(RAIZ, "2-JOGOS.md"), encoding="utf-8").read()
        trecho = documento[documento.find("### Colocar um jogo seu"):documento.find("### Como o ARENA reconhece")]
        faltando = [c["nome"] for c in guia.values() if "| %s | `%s` |" % (c["nome"], c["pasta"].split("\\")[-1])
                    not in trecho]
        confere("o 2-JOGOS.md tem a linha de cada console (gerada dos mesmos dados)", not faltando, faltando)

        print("2. BIOS: 'ja esta' so quando esta")
        confere("PS1 sem BIOS na pasta: falta", guia["ps1"]["bios"]["tem"] is False)
        open(os.path.join(sistema, "SCPH5501.BIN"), "wb").close()      # maiuscula: o Windows nao liga
        open(os.path.join(sistema, "exec.bin"), "wb").close()
        guia = {c["id"]: c for c in como_colocar.guia(plataformas, sistema, os.path.join(pasta, "jogos"))}
        confere("PS1 com UMA das BIOS (em maiusculas): pronta", guia["ps1"]["bios"]["tem"] is True)
        confere("Intellivision com so uma das duas: ainda falta", guia["intellivision"]["bios"]["tem"] is False)
        confere("console sem BIOS: o guia diz que nao precisa", guia["megadrive"]["bios"] is None)
        # 03/10/2026: o SNES ganhou a BIOS do Satellaview, so para os jogos "BS".
        confere("SNES: BIOS so para alguns jogos (Satellaview)",
                (guia["snes"]["bios"] or {}).get("so_para_alguns") is True, guia["snes"]["bios"])

        print("3. O zip de cartucho, de verdade")
        if "--sem-retroarch" in sys.argv:
            print("  (pulado: --sem-retroarch)")
        else:
            # Um jogo de SNES da pasta (a pasta do console e' "Super Nintendo"),
            # menos os "BS ..." de Satellaview: esses nao abrem sem a BIOS BS-X,
            # zipados ou nao -- a primeira versao deste teste pegava um deles.
            original = next((os.path.join(raiz, nome) for raiz, _p, nomes in sorted(os.walk(
                os.path.join(RAIZ, "jogos", "pessoais", "Super Nintendo")))
                for nome in sorted(nomes)
                if nome.lower().endswith((".sfc", ".smc")) and not nome.upper().startswith("BS ")), None)
            if not original:
                confere("um jogo de SNES na pasta para zipar", False)
            else:
                pasta_snes = os.path.join(pasta, "jogos", "pessoais", "Super Nintendo")
                os.makedirs(pasta_snes)
                zipado = os.path.join(pasta_snes, "Jogo Zipado.zip")
                with zipfile.ZipFile(zipado, "w", zipfile.ZIP_DEFLATED) as arquivo_zip:
                    arquivo_zip.write(original, os.path.basename(original))
                import indexador
                guardado = (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                            indexador.ARQUIVO_MANUAIS, indexador.arquivo_de_jogadores)
                dados = os.path.join(pasta, "dados")
                os.makedirs(dados)
                try:
                    indexador.PASTA_JOGOS = os.path.join(pasta, "jogos")
                    indexador.PASTA_DADOS = dados
                    indexador.ARQUIVO_MANIFESTO = os.path.join(dados, "manifesto.json")
                    indexador.ARQUIVO_MANUAIS = os.path.join(dados, "consoles_manuais.json")
                    indexador.arquivo_de_jogadores = lambda: os.path.join(dados, "jogadores.txt")
                    jogos = indexador.indexar(forcar=True).get("jogos", [])
                finally:
                    (indexador.PASTA_JOGOS, indexador.PASTA_DADOS, indexador.ARQUIVO_MANIFESTO,
                     indexador.ARQUIVO_MANUAIS, indexador.arquivo_de_jogadores) = guardado
                console = next((j.get("plataforma") for j in jogos if j["arquivo"].endswith("Jogo Zipado.zip")), None)
                confere("o .zip na pasta do SNES aparece como SNES", console == "snes", console)
                import teste_matriz_multitap as base
                sub = os.path.join(pasta, "ra")
                cfg = base.config_base(sub, {"audio_enable": "false"})
                foto, registro = os.path.join(sub, "foto.png"), os.path.join(sub, "ra.log")
                try:
                    subprocess.run([base.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", "snes9x_libretro.dll"),
                                    "--appendconfig", cfg, "--verbose", "--log-file", registro, "--max-frames=600",
                                    "--max-frames-ss", "--max-frames-ss-path=" + foto, zipado],
                                   cwd=os.path.dirname(base.RETROARCH), timeout=120,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.TimeoutExpired:
                    pass
                tamanho = os.path.getsize(foto) if os.path.isfile(foto) else 0
                log = open(registro, encoding="utf-8", errors="ignore").read() if os.path.isfile(registro) else ""
                confere("o RetroArch abre o jogo de dentro do .zip e mostra imagem",
                        tamanho > 2000, {"foto": tamanho, "erros": base.erros_importantes(log)[:2]})

        print("4. A tela (Edge sem janela)")
        import teste_servidor_que_cai as servidor_de_teste
        import tela_sem_janela
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            servidor_de_teste.esperar_servidor(porta)
            status, resposta = servidor_de_teste.pedir(porta, "GET", "/api/como-colocar")
            confere("a rota devolve o guia dos %d consoles" % len(plataformas),
                    status == 200 and len(resposta.get("consoles", [])) == len(plataformas), status)
            # FAT32 (auditoria 3, Fase 6): a rota diz o formato do disco, e os
            # consoles de jogo maior que 4 GB vem marcados.
            formato = (resposta.get("formato_do_disco") or "").upper()
            grandes = {c["id"] for c in resposta.get("consoles", []) if c.get("jogo_grande")}
            confere("a rota diz o formato do disco (%s) e marca PS2, PS3, Wii e Xbox 360 como jogo grande"
                    % (formato or "?"), bool(formato) and {"ps2", "ps3", "wii", "xbox360"} <= grandes
                    and "snes" not in grandes, sorted(grandes))
            status, resposta = servidor_de_teste.pedir(porta, "POST", "/api/pasta/abrir", {"plataforma": "../../x"})
            confere("'Abrir a pasta' recusa console inventado (nada abre)", status == 400, status)
            with tela_sem_janela.Navegador() as nav:
                nav.comando("Runtime.enable")
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                nav.avaliar("document.querySelector('#btnComoColocar').click(); 1")
                time.sleep(1.5)
                aberta = nav.avaliar("!document.querySelector('#gavetaComoColocar').hidden")
                confere("o botao 'Como colocar jogos' abre a gaveta", aberta is True)
                textos = {}
                for console in ("ps1", "arcade", "snes", "ps2"):
                    nav.avaliar("(() => { const l = document.querySelector('#listaComoColocar'); l.value = '%s';"
                                " l.dispatchEvent(new Event('change')); return 1; })()" % console)
                    time.sleep(0.4)
                    textos[console] = nav.avaliar("document.querySelector('#cartaoComoColocar').innerText") or ""
                confere("PS1: zip nao, BIOS do PS1, pasta jogos\\pessoais\\PS1",
                        "Não pode ser .zip" in textos["ps1"] and "scph5501.bin" in textos["ps1"]
                        and "jogos\\pessoais\\PS1" in textos["ps1"], textos["ps1"][:300])
                confere("Arcade: tem que ser .zip, com o nome curto", "Tem que ser .zip" in textos["arcade"]
                        and "nome curto" in textos["arcade"], textos["arcade"][:300])
                confere("SNES: pode ser .zip, BIOS so para os jogos de Satellaview", "Pode ser .zip" in textos["snes"]
                        and "Satellaview" in textos["snes"] and "BS-X.bin" in textos["snes"], textos["snes"][:300])
                confere("PS2: diz o emulador e a BIOS de 4 MB", "PCSX2" in textos["ps2"] and "4 MB" in textos["ps2"],
                        textos["ps2"][:300])
                if formato != "FAT32":
                    confere("PS2 num disco %s: sem o aviso do FAT32" % formato, "FAT32" not in textos["ps2"],
                            textos["ps2"][:300])
                # O disco daqui nao e' FAT32: a tela finge que e', e o aviso tem que
                # aparecer ANTES de copiar -- no PS2 (DVD), nao no SNES (cartucho).
                avisos = {}
                for console in ("ps2", "snes"):
                    nav.avaliar("(() => { estado.formatoDoDisco = 'FAT32';"
                                " const l = document.querySelector('#listaComoColocar'); l.value = '%s';"
                                " l.dispatchEvent(new Event('change')); return 1; })()" % console)
                    time.sleep(0.4)
                    avisos[console] = nav.avaliar("document.querySelector('#cartaoComoColocar').innerText") or ""
                confere("pen drive em FAT32: o PS2 avisa do limite de 4 GB e diz o exFAT",
                        "FAT32" in avisos["ps2"] and "exFAT" in avisos["ps2"], avisos["ps2"][:400])
                confere("pen drive em FAT32: o SNES (jogo pequeno) nao avisa", "FAT32" not in avisos["snes"],
                        avisos["snes"][:300])
                nav.foto(os.path.join(pasta, "como_colocar_jogos.png"))
                nav.esperar(0.3)
                erros = [e["params"].get("exceptionDetails", {}).get("text") for e in nav.eventos
                         if e.get("method") == "Runtime.exceptionThrown"]
                confere("sem erro de JavaScript", not erros, erros)
        finally:
            servidor_de_teste.derrubar(processo)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Como colocar jogos: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
