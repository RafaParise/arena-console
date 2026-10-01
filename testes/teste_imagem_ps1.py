# -*- coding: utf-8 -*-
r"""Qual opcao de imagem do SwanStation quebra o CTR (cores trocadas, texto
faltando, piscando)?

Achado com o Rafael (25/09/2026): com as opcoes que o ARENA monta para esta
maquina (nota alta), o CTR desenha blocos azul/rosa/amarelo; com o padrao
de fabrica, desenha certo. Aqui cada variante abre o jogo, o RetroArch tira
uma foto da tela no quadro N (--max-frames-ss, do --help dele) e fecha.
As fotos ficam na pasta indicada, para olhar.

Uso:
    servidor\python\python.exe testes\teste_imagem_ps1.py <partida.cfg da
        partida quebrada> <opcoes da partida quebrada> <jogo> <pasta saida> [quadro]
"""
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import protege_cfg  # noqa: E402

RAIZ = os.path.dirname(AQUI)
RETROARCH = os.path.join(RAIZ, "retroarch", "retroarch.exe")
NUCLEO = os.path.join(RAIZ, "retroarch", "cores", "swanstation_libretro.dll")

VARIANTES = {
    "0_quebrada": {},
    "1_msaa_1": {"swanstation_GPU_MSAA": "1"},
    "2_sem_pgxp_profundidade": {"swanstation_GPU_PGXPDepthBuffer": "false"},
    "3_sem_pgxp_cache_vertices": {"swanstation_GPU_PGXPVertexCache": "false"},
    "4_filtro_nearest": {"swanstation_GPU_TextureFilter": "Nearest"},
    "5_sem_cor_verdadeira": {"swanstation_GPU_TrueColor": "false"},
    "6_resolucao_1x": {"swanstation_GPU_ResolutionScale": "1"},
    "7_sem_pgxp": {"swanstation_GPU_PGXPEnable": "false",
                   "swanstation_GPU_PGXPDepthBuffer": "false",
                   "swanstation_GPU_PGXPVertexCache": "false"},
    "8_leitura_por_software": {"swanstation_GPU_UseSoftwareRendererForReadbacks": "true"},
    "9_resolucao_2x": {"swanstation_GPU_ResolutionScale": "2"},
    # O que o ARENA daria com a nota de placa CERTA desta maquina (3):
    # nota 3 = 4x, sem MSAA, sem xBR, sem PGXP de profundidade.
    "10_perfil_nota_3": {"swanstation_GPU_ResolutionScale": "4",
                         "swanstation_GPU_MSAA": "1",
                         "swanstation_GPU_TextureFilter": "Nearest",
                         "swanstation_GPU_PGXPDepthBuffer": "false"},
    "11_resolucao_3x": {"swanstation_GPU_ResolutionScale": "3"},
}


def ler_cfg(caminho):
    return dict(re.findall(r'^(\S+) = "(.*)"$', open(caminho, encoding="utf-8").read(), re.M))


def gravar_cfg(caminho, chaves):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join('%s = "%s"' % kv for kv in sorted(chaves.items())) + "\n")


def main():
    if len(sys.argv) < 5:
        print(__doc__)     # ferramenta de investigacao: sem os arquivos, so o uso
        return 2
    partida, opcoes, jogo, saida = sys.argv[1:5]
    jogo = os.path.abspath(jogo)   # o RetroArch roda dentro de retroarch\
    if not os.path.isfile(jogo):
        print("Jogo nao encontrado: %s" % jogo)
        return 1
    quadro = sys.argv[5] if len(sys.argv) > 5 else "1800"
    so = sys.argv[6].split(",") if len(sys.argv) > 6 else None
    base_partida, base_opcoes = ler_cfg(partida), ler_cfg(opcoes)
    os.makedirs(saida, exist_ok=True)
    for nome, trocas in VARIANTES.items():
        if so and nome not in so:
            continue
        pasta = os.path.join(saida, nome)
        os.makedirs(pasta, exist_ok=True)
        arquivo_opcoes = os.path.join(pasta, "opcoes.cfg")
        gravar_cfg(arquivo_opcoes, dict(base_opcoes, **trocas))
        extra = dict(base_partida)
        extra.update({
            "core_options_path": arquivo_opcoes, "config_save_on_exit": "false",
            "audio_enable": "false", "video_fullscreen": "false",
            "savefile_directory": pasta, "savestate_directory": pasta,
            "screenshot_directory": pasta, "network_cmd_enable": "false",
        })
        arquivo_extra = os.path.join(pasta, "partida.cfg")
        gravar_cfg(arquivo_extra, extra)
        foto = os.path.join(saida, nome + ".png")
        subprocess.run([RETROARCH, "-L", NUCLEO, "--appendconfig", arquivo_extra,
                        "--max-frames", quadro, "--max-frames-ss",
                        "--max-frames-ss-path", foto, jogo],
                       cwd=os.path.dirname(RETROARCH), timeout=300)
        print("%-28s foto: %s" % (nome, "sim (%d KB)" % (os.path.getsize(foto) // 1024)
                                   if os.path.exists(foto) else "NAO"))
    return 0


if __name__ == "__main__":
    sys.exit(protege_cfg.rodar(main))
