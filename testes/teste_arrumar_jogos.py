# -*- coding: utf-8 -*-
r"""O botao "Arrumar" de ponta a ponta, com o Killer Instinct de verdade.

Pedido do Rafael (03/10/2026): "O ARENA deve saber como cada jogo deve ser
posicionado, por exemplo o Killer Instinct que deve ter uma pasta com o
mesmo nome da rom com o arquivo .chd". Em 02/10 o kinst.zip dele estava
DENTRO da pasta kinst, junto do disco -- e assim o MAME nao abre ("unknown
option: kinst").

Num ARENA isolado (copia no temporario, com copias do kinst.zip e do
kinst.chd da pasta de desenvolvimento):

  1. o jogo posto do jeito errado (Arcade\kinst\kinst.zip + kinst.chd): o
     cartao tem o aviso e, na tela, o botao "Arrumar: tirar o kinst.zip da
     pasta kinst"; o clique arruma (Arcade\kinst.zip + Arcade\kinst\kinst.chd);
  2. o MAME de verdade abre o jogo arrumado (foto da tela, sem "NOT FOUND");
  3. o disco solto ao lado do zip (Arcade\kinst.chd): o cartao do disco some,
     o do zip avisa, e o Arrumar devolve o disco para Arcade\kinst;
  4. jogo de CD dentro de .zip (PS1): o cartao avisa, o Jogar recusa com a
     explicacao, o Arrumar descompacta em segundo plano (andamento pela
     rota) e o jogo passa a ser o da pasta.

Uso: servidor\python\python.exe testes\teste_arrumar_jogos.py [--sem-retroarch]
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import jogos_de_teste  # noqa: E402
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402


def pedir_com_erro(porta, caminho, corpo):
    """POST que devolve tambem o corpo da resposta de erro (a explicacao)."""
    import json
    import urllib.error
    import urllib.request
    pedido = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, caminho), data=json.dumps(corpo).encode(),
                                    method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return resposta.status, json.loads(resposta.read() or b"{}")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read() or b"{}")
        except ValueError:
            return erro.code, {}


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    zip_real = jogos_de_teste.achar("Arcade", "kinst.zip")
    chd_real = jogos_de_teste.achar("Arcade", "kinst.chd")
    confere("o Killer Instinct (kinst.zip e kinst.chd) está na pasta Arcade", bool(zip_real and chd_real),
            (zip_real, chd_real))
    if not (zip_real and chd_real):
        return 1

    pasta = tempfile.mkdtemp(prefix="arena_arrumar_ponta_")
    try:
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        arcade = os.path.join(copia, "jogos", "pessoais", "Arcade")
        errado = os.path.join(arcade, "kinst")
        os.makedirs(errado)
        shutil.copy2(zip_real, os.path.join(errado, "kinst.zip"))       # do jeito errado
        shutil.copy2(chd_real, os.path.join(errado, "kinst.chd"))
        ps1 = os.path.join(copia, "jogos", "pessoais", "PS1")
        os.makedirs(ps1, exist_ok=True)
        with zipfile.ZipFile(os.path.join(ps1, "Jogo de CD (USA).zip"), "w") as z:
            z.writestr("Jogo de CD (USA).cue", 'FILE "Jogo de CD (USA).bin" BINARY\n  TRACK 01 MODE2/2352\n'
                                                '    INDEX 01 00:00:00\n')
            z.writestr("Jogo de CD (USA).bin", b"\0" * (3 * 1024 * 1024))

        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            confere("o servidor abre", servidor_de_teste.esperar_servidor(porta))

            def jogo(final):
                _s, resposta = servidor_de_teste.pedir(porta, "GET", "/api/catalogo", espera=30)
                return next((j for j in resposta.get("jogos", [])
                             if j["arquivo"].replace("\\", "/").endswith(final)), None)

            def reindexar():
                servidor_de_teste.pedir(porta, "POST", "/api/indexar", {}, espera=60)

            print("1. O kinst.zip dentro da pasta do disco")
            cartao = jogo("Arcade/kinst/kinst.zip")
            acoes = [a.get("arrumar", {}).get("acao") for a in (cartao or {}).get("avisos", [])]
            confere("o cartão avisa e oferece o Arrumar", "zip_na_pasta_do_disco" in acoes, acoes)
            with tela_sem_janela.Navegador() as nav:
                nav.comando("Runtime.enable")
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                nav.avaliar("(() => { const c = document.querySelector('[data-jogo=\"%s\"]'); "
                            "if (c) c.click(); return !!c; })()" % cartao["id"])
                time.sleep(0.8)
                botoes = nav.avaliar("[...document.querySelectorAll('#detalhesArrumar button')]"
                                     ".map((b) => b.textContent)") or []
                confere("a tela mostra o botão com o que ele faz",
                        "Arrumar: tirar o kinst.zip da pasta kinst" in botoes, botoes)
                nav.foto(os.path.join(pasta, "arrumar.png"))
                # --foto=<arquivo>: guarda a foto do cartao com o botao, para ver depois.
                destino_foto = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--foto=")), "")
                if destino_foto:
                    shutil.copy2(os.path.join(pasta, "arrumar.png"), destino_foto)
                nav.avaliar("document.querySelector('#detalhesArrumar button').click(); 1")
                time.sleep(2.5)
                recado = nav.avaliar("(document.querySelector('#recado') || {}).innerText || ''") or ""
                erros = [e["params"].get("exceptionDetails", {}).get("text") for e in nav.eventos
                         if e.get("method") == "Runtime.exceptionThrown"]
                confere("sem erro de JavaScript", not erros, erros)
            confere("o clique arrumou: Arcade\\kinst.zip e Arcade\\kinst\\kinst.chd",
                    os.path.isfile(os.path.join(arcade, "kinst.zip"))
                    and os.path.isfile(os.path.join(arcade, "kinst", "kinst.chd"))
                    and not os.path.exists(os.path.join(arcade, "kinst", "kinst.zip")), (recado, os.listdir(arcade)))
            cartao = jogo("Arcade/kinst.zip")
            confere("o cartão novo não pede mais nada",
                    cartao is not None and not any(a.get("arrumar") for a in cartao.get("avisos", [])),
                    (cartao or {}).get("avisos"))

            print("2. O MAME abre o jogo arrumado")
            if "--sem-retroarch" in sys.argv:
                print("  (pulado: --sem-retroarch)")
            else:
                import teste_matriz_multitap as base
                sub = os.path.join(pasta, "ra")
                os.makedirs(sub)
                cfg = base.config_base(sub, {"audio_enable": "false"})
                foto, registro = os.path.join(sub, "foto.png"), os.path.join(sub, "ra.log")
                try:
                    subprocess.run([base.RETROARCH, "-L", os.path.join(RAIZ, "retroarch", "cores", "mame_libretro.dll"),
                                    "--appendconfig", cfg, "--verbose", "--log-file", registro, "--max-frames=900",
                                    "--max-frames-ss", "--max-frames-ss-path=" + foto,
                                    os.path.join(arcade, "kinst.zip")],
                                   cwd=os.path.dirname(base.RETROARCH), timeout=240,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.TimeoutExpired:
                    pass
                log = open(registro, encoding="utf-8", errors="ignore").read() if os.path.isfile(registro) else ""
                ruins = [l.strip()[:120] for l in log.splitlines()
                         if re.search(r"NOT FOUND|unknown option|Required files are missing|Falha ao carregar", l)]
                tamanho = os.path.getsize(foto) if os.path.isfile(foto) else 0
                confere("o MAME abre e desenha, sem reclamar do disco", tamanho > 6000 and not ruins,
                        {"foto": tamanho, "registro": ruins[:3]})

            print("3. O disco solto ao lado do zip")
            shutil.move(os.path.join(arcade, "kinst", "kinst.chd"), os.path.join(arcade, "kinst.chd"))
            os.rmdir(os.path.join(arcade, "kinst"))
            reindexar()
            confere("o disco solto não vira um jogo", jogo("Arcade/kinst.chd") is None)
            cartao = jogo("Arcade/kinst.zip")
            acoes = [a.get("arrumar", {}).get("acao") for a in (cartao or {}).get("avisos", [])]
            confere("o zip avisa e oferece o Arrumar", "disco_solto" in acoes, acoes)
            status, resposta = servidor_de_teste.pedir(porta, "POST", "/api/jogo/arrumar",
                                                       {"jogo_id": cartao["id"], "acao": "disco_solto"})
            confere("o Arrumar devolve o disco para Arcade\\kinst",
                    status == 200 and os.path.isfile(os.path.join(arcade, "kinst", "kinst.chd")), (status, resposta))
            status, _r = servidor_de_teste.pedir(porta, "POST", "/api/jogo/arrumar",
                                                 {"jogo_id": cartao["id"], "acao": "disco_solto"})
            confere("de novo: recusa (já está arrumado)", status == 400, status)

            print("4. Jogo de CD dentro de .zip")
            cartao = jogo("PS1/Jogo de CD (USA).zip")
            avisos = (cartao or {}).get("avisos", [])
            confere("o cartão avisa que precisa descompactar",
                    any(a.get("descompactar") for a in avisos), avisos)
            status, resposta = pedir_com_erro(porta, "/api/jogar", {"jogo_id": cartao["id"]})
            confere("o Jogar recusa com a explicação", status == 400 and "Arrumar" in (resposta.get("erro") or ""),
                    (status, resposta))
            status, resposta = servidor_de_teste.pedir(porta, "POST", "/api/jogo/arrumar",
                                                       {"jogo_id": cartao["id"], "acao": "descompactar"})
            confere("o Arrumar começa a descompactar", status == 200 and resposta.get("tarefa"), (status, resposta))
            situacao = {}
            fim = time.monotonic() + 60
            while time.monotonic() < fim:
                _s, situacao = servidor_de_teste.pedir(porta, "GET", "/api/arrumar/progresso?tarefa=%s"
                                                       % resposta.get("tarefa", ""))
                if situacao.get("estado") != "rodando":
                    break
                time.sleep(0.3)
            confere("termina, e diz onde ficou", situacao.get("estado") == "pronto", situacao)
            confere("o jogo agora é o da pasta (o .cue), e o zip saiu da lista",
                    jogo("PS1/Jogo de CD (USA)/Jogo de CD (USA).cue") is not None
                    and jogo("PS1/Jogo de CD (USA).zip") is None)
            confere("o .zip continua lá", os.path.isfile(os.path.join(ps1, "Jogo de CD (USA).zip")))
        finally:
            servidor_de_teste.derrubar(processo)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Arrumar de ponta a ponta: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
