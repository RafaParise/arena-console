# -*- coding: utf-8 -*-
r"""O KOF 2002 convertido abre no FBNeo, com o nome certo na lista.

Achado de 02/10/2026 (Rafael: "o ARENA nao reconhece o motivo do kof2002 nao
rodar"): o kof2002.zip dele era o conjunto DECRIPTADO de emulador antigo
(kof2k2_*.rom). Nem o MAME nem o FBNeo abriam. Virou o conjunto "Fully
Decrypted" do FBNeo (kof2k2fd), com o programa de som como correcao em
retroarch\system\fbneo\patched (ferramentas\converter_fliperama_decriptado.py).

Confere com o jogo e o FBNeo DE VERDADE:
  1. a lista: o jogo aparece no Neo Geo como "The King of Fighters 2002",
     sem aviso nenhum (o banco do RetroArch nao tem o kof2k2fd: o nome vem
     de nomes_arcade.NOMES_FORA_DO_BANCO);
  2. o FBNeo acha a correcao, nao pede parte nenhuma e mostra o jogo (foto
     da demonstracao e da tela de titulo);
  3. o ARENA nao acharia motivo de "nao abriu" no registro.
Pastas de save, estado e foto vao para o temporario; o retroarch.cfg volta
como estava (protege_cfg).

Uso: servidor\python\python.exe testes\teste_kof2002_convertido.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import jogos_de_teste  # noqa: E402
import limpeza  # noqa: E402
import motivo_do_erro  # noqa: E402
import protege_cfg  # noqa: E402

RA = os.path.join(RAIZ, "retroarch")
CORRECAO = os.path.join(RA, "system", "fbneo", "patched", "kof2k2fd.zip")


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, "" if ok else detalhe), flush=True)
        if not ok:
            falhas.append(nome)

    jogo = jogos_de_teste.achar("Neo Geo", "kof2k2fd.zip")
    if not jogo or not os.path.isfile(CORRECAO):
        print("Sem o KOF 2002 convertido nesta pasta (jogos\\pessoais\\Neo Geo\\kof2k2fd.zip e a correcao "
              "em retroarch\\system\\fbneo\\patched). Rode ferramentas\\converter_fliperama_decriptado.py.")
        return 1

    print("1. A lista de jogos")
    import indexador
    cartao = next((j for j in indexador.indexar(forcar=True)["jogos"]
                   if os.path.basename(j["arquivo"]).lower() == "kof2k2fd.zip"), None)
    confere("o jogo esta na lista, no Neo Geo", bool(cartao) and cartao["plataforma"] == "neogeo",
            cartao and cartao["plataforma"])
    if cartao:
        confere("com o nome certo", cartao["titulo"] == "The King of Fighters 2002", cartao["titulo"])
        confere("sem aviso nenhum", not cartao.get("avisos"), cartao.get("avisos"))

    print("2. O FBNeo de verdade")
    pasta = tempfile.mkdtemp(prefix="arena_kof_convertido_")
    try:
        extra = os.path.join(pasta, "extra.cfg")
        with open(extra, "w", encoding="utf-8") as f:
            f.write('config_save_on_exit = "false"\naudio_enable = "false"\nvideo_fullscreen = "false"\n'
                    'savefile_directory = "%s"\nsavestate_directory = "%s"\nscreenshot_directory = "%s"\n'
                    % (pasta, pasta, pasta))
        fotos = {}
        texto = ""
        for quadros in (1800, 3000):        # 30 s: demonstracao; 50 s: tela de titulo
            registro, foto = os.path.join(pasta, "ra_%d.log" % quadros), os.path.join(pasta, "foto_%d.png" % quadros)
            subprocess.run([os.path.join(RA, "retroarch.exe"), "-L", os.path.join(RA, "cores", "fbneo_libretro.dll"),
                            "--appendconfig", extra, "--verbose", "--log-file", registro,
                            "--max-frames=%d" % quadros, "--max-frames-ss", "--max-frames-ss-path=" + foto, jogo],
                           cwd=RA, timeout=240, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            texto = open(registro, encoding="utf-8", errors="replace").read() if os.path.isfile(registro) else ""
            fotos[quadros] = os.path.getsize(foto) if os.path.isfile(foto) else 0
        confere("o FBNeo achou a correcao do som", "Patched romset found" in texto and "kof2k2fd" in texto)
        confere("e nao pediu parte nenhuma", "is required" not in texto,
                [l for l in texto.splitlines() if "is required" in l][:3])
        confere("mostrou o jogo (fotos de %d e %d KB)" % (fotos[1800] // 1024, fotos[3000] // 1024),
                fotos[1800] > 50000 and fotos[3000] > 50000, fotos)
        print("3. O motivo de 'nao abriu'")
        confere("o ARENA nao acha motivo nenhum no registro",
                motivo_do_erro.analisar(texto, jogo, "fbneo_libretro.dll") is None)
    finally:
        limpeza.apagar_pasta(pasta)

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("KOF 2002 convertido: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
