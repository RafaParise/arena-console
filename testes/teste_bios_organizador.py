# -*- coding: utf-8 -*-
r"""A pasta BIOS do ARENA funciona de ponta a ponta, com o servidor de verdade?

Pedido do Rafael (03/10/2026): "faca o ARENA criar pastas de todas as BIOS
necessarias para ler e organizar (...) A parte de emuladores do ARENA deve
conversar com essas pastas e subpastas onde as bios vao residir, e quando
posicionada corretamente deve constar ativa assim como e' feito nos
emuladores como pcsx2".

Num ARENA isolado (copia no temporario), com os PACOTES DE VERDADE que o
Rafael baixou (segamegacdbios.zip, segasaturnbios.zip, dc_boot.zip) largados
em retroarch\system, como ele fez:

  1. o servidor abre e, sozinho, cria BIOS\<console>\<regiao> com os LEIA e
     instala as BIOS dos pacotes com o nome certo (bios_CD_E.bin...);
  2. /api/bios diz "ativa" para elas e "falta" para o resto;
  3. uma BIOS posta na prateleira (com outro nome) fica ativa no Conferir,
     sem fechar o ARENA;
  4. "Abrir a pasta" recusa BIOS e console inventados (nada abre);
  5. a tela (Edge sem janela): Ajustes -> Emuladores mostra a lista, o
     resumo e os botoes, sem erro de JavaScript (foto em 1366x768).

Uso: servidor\python\python.exe testes\teste_bios_organizador.py
"""
import os
import shutil
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import limpeza  # noqa: E402
import protege_cfg  # noqa: E402
import tela_sem_janela  # noqa: E402
import teste_servidor_que_cai as servidor_de_teste  # noqa: E402

PACOTES = ("segamegacdbios.zip", "segasaturnbios.zip", "dc_boot.zip")


def achar_pacote(nome):
    """O pacote do Rafael: em retroarch\\system ou ja na prateleira da pasta BIOS."""
    for atual, _subpastas, arquivos in os.walk(os.path.join(RAIZ, "retroarch", "system")):
        if nome in arquivos:
            return os.path.join(atual, nome)
        break
    for atual, _subpastas, arquivos in os.walk(os.path.join(RAIZ, "BIOS")):
        if nome in arquivos:
            return os.path.join(atual, nome)
    return None


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    pasta = tempfile.mkdtemp(prefix="arena_bios_ponta_")
    try:
        copia = os.path.join(pasta, "isolado", "ARENA")
        os.makedirs(copia)
        servidor_de_teste.preparar_copia(copia)
        # As marcas (MD5) das BIOS vem dos .info do RetroArch.
        shutil.copytree(os.path.join(RAIZ, "retroarch", "info"), os.path.join(copia, "retroarch", "info"))
        sistema = os.path.join(copia, "retroarch", "system")
        os.makedirs(sistema)
        achados = {nome: achar_pacote(nome) for nome in PACOTES}
        confere("os 3 pacotes de BIOS do Rafael estão na pasta", all(achados.values()), achados)
        for nome, caminho in achados.items():
            if caminho:
                shutil.copy2(caminho, os.path.join(sistema, nome))

        print("1. O servidor abre e arruma sozinho")
        porta = tela_sem_janela.porta_livre()
        processo = servidor_de_teste.subir(copia, porta, True, os.path.join(pasta, "sem-trava"))
        try:
            confere("o servidor abre", servidor_de_teste.esperar_servidor(porta))
            esperados = ("bios_CD_U.bin", "bios_CD_E.bin", "bios_CD_J.bin", "mpr-17933.bin", "sega_101.bin",
                         os.path.join("dc", "dc_boot.bin"))
            # Instalar vem antes de escrever os LEIA: espera o resumo (o ultimo).
            resumo_raiz = os.path.join(copia, "BIOS", "LEIA - O QUE FALTA.txt")
            fim = time.monotonic() + 30
            while time.monotonic() < fim and not (os.path.isfile(resumo_raiz) and all(
                    os.path.isfile(os.path.join(sistema, n)) for n in esperados)):
                time.sleep(0.5)
            faltam = [n for n in esperados if not os.path.isfile(os.path.join(sistema, n))]
            confere("as 6 BIOS dos pacotes foram para retroarch\\system com o nome certo", not faltam, faltam)
            prateleiras = [os.path.join("Sega CD", "Europa"), os.path.join("Sega Saturn", "Japão"), "Dreamcast",
                           "PS1", os.path.join("PS2", "EUA"), "PC-FX"]
            sem_leia = [p for p in prateleiras if not os.path.isfile(os.path.join(copia, "BIOS", p, "LEIA.txt"))]
            confere("as prateleiras foram criadas, cada uma com o LEIA", not sem_leia, sem_leia)
            confere("o resumo da raiz existe",
                    os.path.isfile(os.path.join(copia, "BIOS", "LEIA - O QUE FALTA.txt")))
            confere("a cópia da BIOS foi para a prateleira dela",
                    os.path.isfile(os.path.join(copia, "BIOS", "Sega CD", "Europa", "bios_CD_E.bin")))

            print("2. /api/bios")
            status, resposta = servidor_de_teste.pedir(porta, "GET", "/api/bios")
            itens = {i["id"]: i for i in resposta.get("itens", [])}
            confere("a rota responde com a lista inteira", status == 200 and len(itens) >= 40, status)
            certas = [i for i in ("segacd-eua", "segacd-europa", "segacd-japao", "saturn-eua-europa", "saturn-japao",
                                  "dreamcast-boot") if itens.get(i, {}).get("estado") != "certa"]
            confere("Sega CD (3), Saturn (2) e Dreamcast: ativas, versão conferida", not certas,
                    {i: itens.get(i, {}).get("estado") for i in certas})
            confere("PC-FX: falta", itens.get("pcfx", {}).get("ativa") is False)
            resumo = resposta.get("resumo", {})
            confere("o resumo conta as que os jogos precisam", resumo.get("precisa", [0, 0])[1] >= 15, resumo)

            print("3. BIOS posta na prateleira fica ativa no Conferir")
            coleco = os.path.join(copia, "BIOS", "ColecoVision", "BIOS do Coleco (1982).rom")
            with open(coleco, "wb") as arquivo:
                arquivo.write(b"\x31" * 8192)          # tamanho certo, marca desconhecida
            status, resposta = servidor_de_teste.pedir(porta, "POST", "/api/bios/conferir", {}, espera=60)
            instaladas = [i["id"] for i in resposta.get("instaladas", [])]
            confere("o Conferir instala a do ColecoVision", status == 200 and "colecovision" in instaladas,
                    (status, instaladas))
            confere("ela vai com o nome certo", os.path.isfile(os.path.join(sistema, "colecovision.rom")))
            item = next((i for i in resposta.get("itens", []) if i["id"] == "colecovision"), {})
            confere("e fica 'ativa, de outra versão' (a marca não é a recomendada)",
                    item.get("ativa") is True and item.get("estado") == "outra", item.get("estado"))
            status, resposta = servidor_de_teste.pedir(porta, "POST", "/api/bios/conferir", {}, espera=60)
            confere("Conferir de novo: nada novo", status == 200 and not resposta.get("instaladas"),
                    resposta.get("instaladas"))

            print("4. Abrir a pasta: só pasta de verdade")
            status, _r = servidor_de_teste.pedir(porta, "POST", "/api/bios/pasta", {"id": "../../windows"})
            confere("BIOS inventada: recusa", status == 400, status)
            status, _r = servidor_de_teste.pedir(porta, "POST", "/api/bios/pasta", {"console": "megadrive"})
            confere("console sem BIOS: recusa", status == 400, status)

            print("5. A tela")
            with tela_sem_janela.Navegador() as nav:
                nav.comando("Runtime.enable")
                nav.abrir("http://127.0.0.1:%d/" % porta, espera=4)
                nav.avaliar("document.querySelector('#btnAjustes').click(); 1")
                time.sleep(0.8)
                nav.avaliar("document.querySelector('.aba[data-aba=\"emuladores\"]').click(); 1")
                time.sleep(2.0)
                lista = nav.avaliar("document.querySelector('#listaBiosConsoles').innerText") or ""
                resumo_tela = nav.avaliar("document.querySelector('#biosResumo').innerText") or ""
                confere("a lista mostra o Sega CD ativo e o PC-FX faltando",
                        "Sega CD" in lista and "Ativa" in lista and "PC-FX" in lista and "Falta" in lista,
                        lista[:400])
                confere("a lista do PS2 diz que basta uma região", "PS2" in lista, lista[:200])
                confere("o resumo diz quantas estão ativas", "as que os jogos precisam" in resumo_tela, resumo_tela)
                botoes = nav.avaliar("[...document.querySelectorAll('#listaBiosConsoles button')].length")
                confere("cada console tem o botão de abrir a pasta", (botoes or 0) >= 20, botoes)
                nav.avaliar("document.querySelector('#listaBiosConsoles').scrollIntoView(); 1")
                nav.foto(os.path.join(pasta, "bios_dos_consoles.png"))
                # O "Como colocar jogos" do Sega CD aponta a prateleira.
                nav.avaliar("document.querySelector('[data-fechar=\"gavetaAjustes\"]').click(); 1")
                nav.avaliar("document.querySelector('#btnComoColocar').click(); 1")
                time.sleep(1.5)
                nav.avaliar("(() => { const l = document.querySelector('#listaComoColocar'); l.value = 'segacd';"
                            " l.dispatchEvent(new Event('change')); return 1; })()")
                time.sleep(0.5)
                cartao = nav.avaliar("document.querySelector('#cartaoComoColocar').innerText") or ""
                confere("Como colocar jogos (Sega CD): a pasta BIOS\\Sega CD e os botões",
                        "BIOS\\Sega CD" in cartao and "Abrir a pasta da BIOS" in cartao and "Ativa" in cartao,
                        cartao[:400])
                nav.esperar(0.3)
                erros = [e["params"].get("exceptionDetails", {}).get("text") for e in nav.eventos
                         if e.get("method") == "Runtime.exceptionThrown"]
                confere("sem erro de JavaScript", not erros, erros)
                # --foto=<arquivo>: guarda a foto da lista para ver depois.
                destino = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--foto=")), "")
                if destino:
                    shutil.copy2(os.path.join(pasta, "bios_dos_consoles.png"), destino)
        finally:
            servidor_de_teste.derrubar(processo)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Pasta BIOS de ponta a ponta: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
