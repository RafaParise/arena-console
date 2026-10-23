# -*- coding: utf-8 -*-
r"""Atualizar copiando o pacote COMPLETO por cima, sem perder nada (22/10/2026).

O pedido do Rafael: "o arena deve ser sempre baixar e jogar, e a atualizacao
deve ser abrir a pasta compactada copiar tudo e arrastar para o arena e
atualiza sem perder nada de progresso, perfil, saves e nem bios importantes
ou suas configuracoes, tudo integro".

O teste, numa pasta temporaria (nada do ARENA de verdade e' tocado):
  1. monta o pacote de verdade (ferramentas\montar_versao_alunos.py, sem BIOS,
     o mesmo do Release);
  2. "instala": copia o pacote e faz a primeira abertura (os modelos .padrao
     viram a configuracao: graficos.instalar_configuracoes_que_faltam);
  3. "usa": cria perfil, recordes, controles, jogos, BIOS, saves, estados,
     cartoes de memoria (PS2, GameCube, Dreamcast), e muda a configuracao do
     RetroArch e dos emuladores;
  4. copia o pacote inteiro por cima, SUBSTITUINDO tudo (o "Substituir os
     arquivos no destino" do Windows ao descompactar o zip);
  5. confere: cada arquivo de quem usa igualzinho (sha256), a configuracao
     mudada continua a de quem usa, e a abertura seguinte nao troca nada.
Uso: servidor\python\python.exe testes\teste_atualizar_por_cima.py [--saida=arquivo.json]
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path[0:0] = [AQUI, os.path.join(RAIZ, "ferramentas"), os.path.join(RAIZ, "servidor")]
import graficos  # noqa: E402
import limpeza  # noqa: E402
import montar_versao_alunos as montador  # noqa: E402

# O que uma turma deixa numa versao em uso (caminho -> conteudo).
DE_QUEM_USA = {
    os.path.join("dados", "config.json"): '{"apelido": "Turma 2C", "formato_da_imagem": "esticar"}',
    os.path.join("dados", "arena.db"): b"SQLite format 3\x00" + bytes(range(256)) * 8,
    os.path.join("dados", "controles.json"): '{"jogador1": {"a": "x"}}',
    os.path.join("dados", "perfil", "foto.png"): b"\x89PNG\r\n\x1a\n" + b"\x00" * 64,
    os.path.join("jogos", "pessoais", "NES", "Meu Jogo.nes"): b"NES\x1a" + b"\x01" * 512,
    os.path.join("BIOS", "PS1", "scph1001.bin"): b"\x13" * 1024,
    os.path.join("retroarch", "saves", "Meu Jogo.srm"): b"\x42" * 8192,
    os.path.join("retroarch", "states", "Meu Jogo.state1"): b"\x24" * 4096,
    os.path.join("retroarch", "remaps", "FCEUmm", "Meu Jogo.rmp"): 'input_player1_btn_a = "8"\n',
    os.path.join("retroarch", "system", "dc", "vmu_save_A1.bin"): b"\x55" * 2048,
    os.path.join("emuladores", "PCSX2", "PCSX2", "memcards", "Mcd001.ps2"): b"\x77" * 4096,
    os.path.join("emuladores", "Dolphin", "Dolphin-x64", "User", "GC", "USA", "Card A", "jogo.gci"):
        b"\x66" * 2048,
    os.path.join("emuladores", "Dolphin", "Dolphin-x64", "User", "Config", "Dolphin.ini"):
        "[Interface]\nConfirmStop = False\n",
    os.path.join("backup", "copia.zip"): b"PK\x05\x06" + b"\x00" * 18,
}
MARCA = "configuracao de quem usa (teste_atualizar_por_cima)"


def resumo(caminho):
    with open(caminho, "rb") as arquivo:
        return hashlib.sha256(arquivo.read()).hexdigest()


def escrever(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as arquivo:
        arquivo.write(conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8"))


def copiar_por_cima(pacote, destino):
    """O 'copiar tudo e arrastar' do pedido: cada arquivo do pacote vai para
    o mesmo lugar no destino, substituindo o que tiver o mesmo nome."""
    copiados = 0
    for atual, _pastas, nomes in os.walk(pacote):
        for nome in nomes:
            origem = os.path.join(atual, nome)
            alvo = os.path.join(destino, os.path.relpath(origem, pacote))
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            shutil.copy2(origem, alvo)
            copiados += 1
    return copiados


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def main():
    saida = argumento("saida", os.path.join(tempfile.gettempdir(), "teste_atualizar_por_cima.json"))
    trabalho = tempfile.mkdtemp(prefix="arena_por_cima_")
    r = {"conferencias": []}
    try:
        pacote = os.path.join(trabalho, "pacote", montador.NOME_DESTINO)
        inicio = time.time()
        montador.montar(pacote)
        r["segundos_montando"] = round(time.time() - inicio)
        r["modelos_no_pacote"] = sorted(rel for rel in graficos.CONFIGURACOES_COM_MODELO
                                        if os.path.isfile(os.path.join(pacote, rel + graficos.SUFIXO_DO_MODELO)))
        r["configuracao_de_verdade_no_pacote"] = sorted(
            rel for rel in graficos.CONFIGURACOES_COM_MODELO if os.path.exists(os.path.join(pacote, rel)))

        # 2. Instala e abre pela primeira vez.
        em_uso = os.path.join(trabalho, "em_uso", "ARENA")
        shutil.copytree(pacote, em_uso)
        r["primeira_abertura"] = graficos.instalar_configuracoes_que_faltam(em_uso)

        # 3. Usa.
        for rel, conteudo in DE_QUEM_USA.items():
            escrever(os.path.join(em_uso, rel), conteudo)
        mudadas = []
        for rel in r["primeira_abertura"]:
            with open(os.path.join(em_uso, rel), "a", encoding="utf-8") as arquivo:
                arquivo.write("\n# %s\n" % MARCA)
            mudadas.append(rel)
        antes = {rel: resumo(os.path.join(em_uso, rel)) for rel in list(DE_QUEM_USA) + mudadas}

        # 4. Copia o pacote inteiro por cima, substituindo.
        r["arquivos_copiados_por_cima"] = copiar_por_cima(pacote, em_uso)

        # 5. Confere.
        depois = {rel: (resumo(os.path.join(em_uso, rel)) if os.path.isfile(os.path.join(em_uso, rel)) else None)
                  for rel in antes}
        r["mudaram"] = sorted(rel for rel in antes if depois[rel] != antes[rel])
        r["segunda_abertura"] = graficos.instalar_configuracoes_que_faltam(em_uso)
        r["conferencias"] = [
            ("o pacote leva a configuracao do RetroArch e dos emuladores so como modelo (.padrao)",
             not r["configuracao_de_verdade_no_pacote"] and os.path.join("retroarch", "retroarch.cfg")
             in r["modelos_no_pacote"]),
            ("a primeira abertura poe a configuracao no lugar",
             os.path.join("retroarch", "retroarch.cfg") in r["primeira_abertura"]),
            ("perfil, recordes, controles, jogos, BIOS, saves, estados e cartoes ficam iguais",
             not [rel for rel in DE_QUEM_USA if rel in r["mudaram"]]),
            ("a configuracao mudada por quem usa continua a de quem usa",
             bool(mudadas) and not [rel for rel in mudadas if rel in r["mudaram"]]),
            ("a abertura depois da atualizacao nao troca nenhuma configuracao", r["segunda_abertura"] == []),
        ]
    except (OSError, SystemExit, ValueError) as falha:
        r["falha"] = str(falha)
    finally:
        limpeza.apagar_pasta(trabalho)
    for item, passou in r["conferencias"]:
        print("  [%s] %s" % ("OK" if passou else "FALHOU", item))
    if r.get("mudaram"):
        print("  mudaram:", r["mudaram"][:10])
    if r.get("falha"):
        print("  falha:", r["falha"])
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(dict(r, data=time.strftime("%Y-%m-%d %H:%M")), arquivo, ensure_ascii=False, indent=1)
    falhas = sum(1 for _item, passou in r["conferencias"] if not passou)
    total = len(r["conferencias"])
    print("\nAtualizar por cima: %d de %d certos. Resultado: %s" % (total - falhas, total, saida))
    return 1 if falhas or not total else 0


if __name__ == "__main__":
    sys.exit(main())
