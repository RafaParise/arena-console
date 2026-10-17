# -*- coding: utf-8 -*-
r"""Prepara os nucleos do RetroArch para navegador (a versao do Chromebook).

Por que existe (17/10/2026, item 12 do plano de 15/10): no Chromebook da
escola o Linux vem desligado pelo administrador, entao o ARENA roda dentro do
proprio Chrome (ARENA-CHROMEBOOK.html), com a mesma tela. Os jogos rodam no
mesmo RetroArch do Windows (1.22.2), na versao que o libretro compila para
WebAssembly. O que esta ferramenta faz, passo a passo:

  1. baixa o RetroArch 1.22.2 para navegador do endereco oficial (o
     buildbot do libretro) e confere a marca SHA-256 gravada aqui. O
     buildbot nao publica a marca: esta e' a do arquivo baixado em
     17/10/2026, e um arquivo diferente (trocado ou corrompido) e' recusado;
  2. tira do .7z so os nucleos que o ARENA usa no navegador (a chave
     "core_navegador" de servidor\consoles.json), com o 7-Zip;
  3. converte cada nucleo para abrir direto do pen drive (file://), onde o
     Chrome nao deixa ler arquivo com fetch nem abrir modulo JavaScript:
       - o .js vira script comum: o import.meta.url vira o endereco do
         proprio script e o "export default" vira um registro em
         window.ARENA_NUCLEOS;
       - o .wasm vai compactado (gzip, um terco do tamanho) e escrito em
         base64 num .js (window.ARENA_WASM_GZ). O navegador descompacta
         (DecompressionStream) e entrega ao nucleo pronto (wasmBinary);
  4. grava launcher\navegador\nucleos\lista.js, com o tamanho e a marca de
     cada nucleo (a tela mostra so os consoles que tem nucleo ali).

Nao precisa de administrador nem de internet depois do download. O 7-Zip
precisa estar no computador de quem monta o pacote (7-zip.org, livre).

Uso:
    servidor\python\python.exe ferramentas\preparar_nucleos_navegador.py [--7z RetroArch.7z]

--7z   usa um RetroArch.7z ja baixado (a marca e' conferida do mesmo jeito)
"""
import base64
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
import limpeza  # noqa: E402

DESTINO = os.path.join(RAIZ, "launcher", "navegador", "nucleos")
CONSOLES = os.path.join(RAIZ, "servidor", "consoles.json")

VERSAO = "1.22.2"
ENDERECO = "https://buildbot.libretro.com/stable/1.22.2/emscripten/RetroArch.7z"
SHA256 = "00e17fda8792ee15a9d9ea4fc769e9f937e525c722ae10dabba2c993941f55f4"
TAMANHO = 749072539
CACHE = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "ARENA-montagem")
LUGARES_DO_7ZIP = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"]


def marca(caminho):
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def baixar(destino):
    print("Baixando o RetroArch %s para navegador (715 MB, uma vez so)..." % VERSAO, flush=True)
    parcial = destino + ".baixando"
    with urllib.request.urlopen(ENDERECO, timeout=60) as resposta, open(parcial, "wb") as arquivo:
        shutil.copyfileobj(resposta, arquivo, 1 << 20)
    os.replace(parcial, destino)


def achar_7zip():
    for lugar in [shutil.which("7z"), shutil.which("7za")] + LUGARES_DO_7ZIP:
        if lugar and os.path.isfile(lugar):
            return lugar
    return None


def nucleos_do_catalogo():
    """{"fceumm": ["nes"], "genesis_plus_gx": ["megadrive", "segacd"], ...}"""
    with open(CONSOLES, encoding="utf-8") as arquivo:
        plataformas = json.load(arquivo)["plataformas"]
    nucleos = {}
    for p in plataformas:
        if p.get("core_navegador"):
            nucleos.setdefault(p["core_navegador"], []).append(p["id"])
    return nucleos


def script_comum(texto, nucleo):
    """O nucleo vem como modulo ES (import/export): o Chrome nao abre modulo
    de file://. Vira script comum, que registra a fabrica do nucleo em
    window.ARENA_NUCLEOS. Confere cada troca: se o libretro mudar o jeito de
    gerar o arquivo, a ferramenta para em vez de gravar um nucleo quebrado."""
    antes = "var _scriptDir = import.meta.url;"
    if texto.count(antes) != 1:
        raise ValueError("%s: o comeco do nucleo mudou (sem o _scriptDir)" % nucleo)
    texto = texto.replace(antes, "var _scriptDir = (document.currentScript && document.currentScript.src) || '';")
    texto = texto.replace("import.meta.url", "(_scriptDir || location.href)")
    saidas = re.findall(r"^export default (\w+);\s*$", texto, flags=re.M)
    if len(saidas) != 1:
        raise ValueError("%s: o fim do nucleo mudou (sem o export default)" % nucleo)
    texto = re.sub(r"^export default (\w+);\s*$",
                   lambda m: "(window.ARENA_NUCLEOS = window.ARENA_NUCLEOS || {})[%s] = %s;\n"
                   % (json.dumps(nucleo), m.group(1)), texto, flags=re.M)
    if "import.meta" in texto or re.search(r"^\s*(import|export)\s", texto, flags=re.M):
        raise ValueError("%s: sobrou import/export no nucleo" % nucleo)
    return texto


def wasm_em_script(dados, nucleo):
    compactado = gzip.compress(dados, 9, mtime=0)
    texto = "(window.ARENA_WASM_GZ = window.ARENA_WASM_GZ || {})[%s] = \"%s\";\n" % (
        json.dumps(nucleo), base64.b64encode(compactado).decode("ascii"))
    return texto, len(compactado)


def gravar(caminho, texto):
    temporario = caminho + ".gravando"
    with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
    os.replace(temporario, caminho)


def principal():
    nucleos = nucleos_do_catalogo()
    if not nucleos:
        print("Nenhum console tem \"core_navegador\" no servidor\\consoles.json.")
        return 1
    sete = achar_7zip()
    if not sete:
        print("Falta o 7-Zip neste computador (7-zip.org, livre). Instale e rode de novo.")
        return 1
    if "--7z" in sys.argv:
        arquivo_7z = os.path.abspath(sys.argv[sys.argv.index("--7z") + 1])
    else:
        os.makedirs(CACHE, exist_ok=True)
        arquivo_7z = os.path.join(CACHE, "RetroArch-%s-emscripten.7z" % VERSAO)
        if not (os.path.isfile(arquivo_7z) and os.path.getsize(arquivo_7z) == TAMANHO):
            baixar(arquivo_7z)
    print("Conferindo a marca do arquivo...", flush=True)
    if os.path.getsize(arquivo_7z) != TAMANHO or marca(arquivo_7z) != SHA256:
        print("A marca do RetroArch.7z nao confere: o arquivo veio diferente do baixado em "
              "17/10/2026. Nada foi mudado.")
        return 1
    trabalho = tempfile.mkdtemp(prefix="arena_nucleos_navegador_")
    try:
        nomes = []
        for nucleo in sorted(nucleos):
            nomes += ["retroarch/%s_libretro.js" % nucleo, "retroarch/%s_libretro.wasm" % nucleo]
        print("Tirando %d nucleos do .7z (uns 2 minutos)..." % len(nucleos), flush=True)
        r = subprocess.run([sete, "e", arquivo_7z, "-o" + trabalho, "-y"] + nomes,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("O 7-Zip nao conseguiu tirar os nucleos:\n" + (r.stdout + r.stderr)[-1500:])
            return 1
        os.makedirs(DESTINO, exist_ok=True)
        lista = {}
        for nucleo in sorted(nucleos):
            js = os.path.join(trabalho, nucleo + "_libretro.js")
            wasm = os.path.join(trabalho, nucleo + "_libretro.wasm")
            if not (os.path.isfile(js) and os.path.isfile(wasm)):
                print("O nucleo %s nao veio no RetroArch %s para navegador." % (nucleo, VERSAO))
                return 1
            with open(js, encoding="utf-8") as arquivo:
                gravar(os.path.join(DESTINO, nucleo + ".js"), script_comum(arquivo.read(), nucleo))
            with open(wasm, "rb") as arquivo:
                dados = arquivo.read()
            texto, compactado = wasm_em_script(dados, nucleo)
            gravar(os.path.join(DESTINO, nucleo + ".wasm.js"), texto)
            lista[nucleo] = {"consoles": nucleos[nucleo], "wasm_bytes": len(dados), "gzip_bytes": compactado,
                             "sha256": hashlib.sha256(dados).hexdigest()}
            print("  %-16s %5.1f MB -> %4.1f MB (%s)" % (nucleo, len(dados) / 1048576, compactado / 1048576,
                                                        ", ".join(nucleos[nucleo])), flush=True)
        gravar(os.path.join(DESTINO, "lista.js"),
               "// Gerado por ferramentas\\preparar_nucleos_navegador.py: nao edite a mao.\n"
               "window.ARENA_NUCLEOS_LISTA = %s;\n"
               % json.dumps({"retroarch": VERSAO, "origem": ENDERECO, "nucleos": lista},
                            ensure_ascii=False, indent=1))
        # Nucleo que saiu do catalogo nao fica para tras ocupando o pen drive.
        for nome in os.listdir(DESTINO):
            base = nome.split(".")[0]
            if nome.endswith((".js", ".gravando")) and nome != "lista.js" and base not in lista:
                os.remove(os.path.join(DESTINO, nome))
        total = sum(os.path.getsize(os.path.join(DESTINO, n)) for n in os.listdir(DESTINO))
        print("Pronto: %d nucleos em %s (%.0f MB no total)." % (len(lista), DESTINO, total / 1048576))
        return 0
    finally:
        limpeza.apagar_pasta(trabalho)


if __name__ == "__main__":
    sys.exit(principal())
