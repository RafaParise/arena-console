r"""Protege os arquivos DE VERDADE enquanto um teste abre um emulador.

Achado real (revisao pos-auditoria): o RetroArch grava a configuracao ao
fechar (config_save_on_exit), e leva junto os valores que o teste mandou
por --appendconfig -- pastas temporarias que depois sao apagadas. O
retroarch.cfg de verdade ficou com saves e historico apontando para o Temp.

Achado da Fase 8 da auditoria 3 (12/10/2026): ligar um jogo tambem grava em
dado de quem joga, e a rodada nao via. Na rodada de 11/10 o
teste_pcsx2_inicia mudou os cartoes de memoria do PS2 do professor (a BIOS
do PS2 atualiza o historico no cartao do slot 1: 5 paginas de 16.384 no
Mcd001.ps2, 8 de 131.072 no cartao de 64 MB); o teste_emuladores_de_fora, os
dados do sistema do Wii (Dolphin) e o perfil do Xbox 360 (Xenia); o
teste_qual_opcao_de_nucleo_vale, o historico do RetroArch (dados\builtin); o
teste_rpcs3_controles, a configuracao do RPCS3. Nenhum save de jogo foi
sobrescrito, mas era dado de quem joga mudando a cada rodada.

Uso, no fim de todo script que abre o RetroArch:
    if __name__ == "__main__":
        sys.exit(protege_cfg.rodar(main))
e no que abre um emulador de fora (PCSX2, Dolphin, RPCS3, Xenia):
        sys.exit(protege_cfg.rodar(main, emuladores=True))

Guarda uma copia antes e devolve igualzinho no fim -- passou, falhou ou deu
erro no meio: o arquivo que mudou ou sumiu volta (com a data de antes); o que
o teste criou dentro de uma pasta protegida sai. A copia fica numa pasta
"protege_arena_*" do Temp, e nao "arena_*" (a rodada apaga as "arena_*"
esquecidas): se o teste for morto no meio, ela continua la para devolver.
"""
import os
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(RAIZ, "retroarch", "retroarch.cfg")
_EMU = os.path.join(RAIZ, "emuladores")
# O que o RetroArch grava ao abrir um jogo: a configuracao (ao fechar) e o
# historico e os favoritos (dados\builtin).
DO_RETROARCH = [CFG, os.path.join(RAIZ, "dados", "builtin")]
# O que os emuladores de fora gravam ao ligar um jogo: cartoes de memoria,
# saves, perfil, tempo de jogo, historico e a configuracao que o ARENA
# completa a cada jogo.
DOS_EMULADORES = [
    os.path.join(_EMU, "PCSX2", "PCSX2", "memcards"),
    os.path.join(_EMU, "PCSX2", "PCSX2", "inis", "PCSX2.ini"),
    os.path.join(_EMU, "Dolphin", "Dolphin-x64", "User", "Wii"),
    os.path.join(_EMU, "Dolphin", "Dolphin-x64", "User", "GC"),
    os.path.join(_EMU, "Dolphin", "Dolphin-x64", "User", "Config"),
    os.path.join(_EMU, "Xenia", "Xenia", "content"),
    os.path.join(_EMU, "Xenia", "Xenia", "recent.toml"),
    os.path.join(_EMU, "Xenia", "Xenia", "xenia-canary.config.toml"),
    os.path.join(_EMU, "RPCS3", "RPCS3", "dev_hdd0", "home"),
    os.path.join(_EMU, "RPCS3", "RPCS3", "config"),
    os.path.join(_EMU, "RPCS3", "RPCS3", "GuiConfigs"),
]


def arquivos(caminho):
    """Cada arquivo de 'caminho' (ele mesmo, se for um arquivo)."""
    if os.path.isfile(caminho):
        return [caminho]
    achados = []
    for atual, _pastas, nomes in os.walk(caminho):
        achados += [os.path.join(atual, nome) for nome in nomes]
    return achados


def guardar(caminhos):
    """Copia cada arquivo (com a data) para uma pasta protege_arena_* do Temp."""
    guarda = {"pasta": tempfile.mkdtemp(prefix="protege_arena_"), "arquivos": {},
              "caminhos": [c for c in caminhos if os.path.exists(c)]}
    for caminho in guarda["caminhos"]:
        for arquivo in arquivos(caminho):
            copia = os.path.join(guarda["pasta"], str(len(guarda["arquivos"])))
            shutil.copy2(arquivo, copia)
            guarda["arquivos"][arquivo] = copia
    return guarda


def devolver(guarda):
    """Devolve o que mudou ou sumiu; tira o que nasceu numa pasta protegida.
    Devolve (devolvidos, tirados, problemas)."""
    devolvidos, tirados, problemas = [], [], []
    for arquivo, copia in guarda["arquivos"].items():
        try:
            agora, antes = os.stat(arquivo), os.stat(copia)
            if (agora.st_size, agora.st_mtime_ns) == (antes.st_size, antes.st_mtime_ns):
                continue
        except FileNotFoundError:
            pass
        try:
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            provisorio = arquivo + ".protege.tmp"
            shutil.copy2(copia, provisorio)
            os.replace(provisorio, arquivo)
            devolvidos.append(arquivo)
        except OSError as erro:
            problemas.append("%s: %s" % (arquivo, erro))
    for caminho in guarda["caminhos"]:
        if os.path.isdir(caminho):
            for arquivo in arquivos(caminho):
                if arquivo not in guarda["arquivos"]:
                    try:
                        os.remove(arquivo)
                        tirados.append(arquivo)
                    except OSError as erro:
                        problemas.append("%s: %s" % (arquivo, erro))
    return devolvidos, tirados, problemas


def rodar(funcao, emuladores=False):
    guarda = guardar(DO_RETROARCH + (DOS_EMULADORES if emuladores else []))
    try:
        return funcao()
    finally:
        devolvidos, tirados, problemas = devolver(guarda)
        if problemas:
            print("[protege_cfg] NAO deu para devolver tudo (a copia ficou em %s):" % guarda["pasta"])
            for problema in problemas:
                print("   ", problema)
        else:
            shutil.rmtree(guarda["pasta"], ignore_errors=True)
        nomes = [os.path.relpath(a, RAIZ) for a in devolvidos]
        print("[protege_cfg] arquivos de verdade devolvidos como estavam antes do teste: %s%s" % (
            ", ".join(nomes) if nomes else "nenhum mudou",
            "; tirados (o teste criou): %s" % ", ".join(os.path.relpath(a, RAIZ) for a in tirados)
            if tirados else ""))
