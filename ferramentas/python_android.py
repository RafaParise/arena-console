# -*- coding: utf-8 -*-
r"""O Python do ARENA no Android (item 14): o mesmo Python 3.13.16 do Linux
(servidor\python-linux), na versao para Android, e o lancador do ARENA.

O servidor do ARENA e' o mesmo programa no Windows, no Linux e no Android: no
APK ele roda com o CPython 3.13.16 compilado para Android pelo Chaquopy
(chaquo.com, licenca MIT), sem mudanca no Python. O Chaquopy publica no Maven
Central o "target" de cada processador (libpython3.13.so, o OpenSSL, o SQLite
e os modulos nativos) e a biblioteca padrao ja compilada (stdlib-pyc).
Cada pacote confere pela marca SHA-256 (em 18/10/2026 a SHA-1 que o Maven
Central publica tambem bateu).

O Python do Android vem so como biblioteca, sem o programa "python": o
lancador do ARENA (android\python\lancador.c, um main de uma linha que chama
o Py_BytesMain, o mesmo do python.exe) e' esse programa, compilado com o NDK
(ferramentas\preparar_android.py).

No APK (por_no_apk):
  lib\<abi>\libarenapython.so      o lancador (o Android so roda programa da
                                   pasta de bibliotecas do app, e so copia
                                   para la os arquivos lib*.so)
  lib\<abi>\libpython3.13.so, libssl_python.so, libcrypto_python.so,
            libsqlite3_python.so   o Python e o que ele pede
  assets\arena-python\lib\python313.zip       a biblioteca padrao (.pyc),
                                              onde o Python a procura sozinho
  assets\arena-python\lib\python3.13\lib-dynload\*.so
                                   os modulos nativos (sem os de teste)
O ArenaServico.java copia a pasta arena-python para a pasta do app (na
primeira vez e quando o APK muda) e roda o servidor com o lancador, com
PYTHONHOME apontando para ela.

Uso (so para conferir; quem chama e' o ferramentas\montar_android.py):
    servidor\python\python.exe ferramentas\python_android.py [--abi x86_64]
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
import limpeza  # noqa: E402
import preparar_android as sdk  # noqa: E402  (o NDK, em %LOCALAPPDATA%\ARENA-android)
import preparar_linux  # noqa: E402  (o cache e o download com a marca)

VERSAO = "3.13.16"
MAVEN = "https://repo.maven.apache.org/maven2/com/chaquo/python/target/3.13.16-0/"
PACOTES = {
    "arm64-v8a": {"sha256": "fae8cfd4d3910b6f978b22279fe820c0c6ba49d0ea20f7b106aa6130f1c8f355",
                  "tamanho": 7309656},
    "x86_64": {"sha256": "77a6a3325aff0a171c36c11c8c3b2204a53783a3d42c29cff10a5ddecee5bfb6",
               "tamanho": 7541472},
    "stdlib-pyc": {"sha256": "170942687a810350589202a65b4ee3b4b4c6344c5ddd750cdef35ab6cb727066",
                   "tamanho": 4334436},
}
for _nome, _item in PACOTES.items():
    _item["endereco"] = MAVEN + "target-3.13.16-0-%s.zip" % _nome
    _item["arquivo"] = os.path.join("android", "python-3.13.16", "target-3.13.16-0-%s.zip" % _nome)
# O que o Python pede ao Android alem dele mesmo (llvm-readelf -d): o OpenSSL
# (o _ssl e o _hashlib) e o SQLite (o _sqlite3). Os *_chaquopy.so e o
# libpython3.so sao so apelidos para pacotes de fora, que o ARENA nao usa.
BIBLIOTECAS = ["libpython3.13.so", "libssl_python.so", "libcrypto_python.so", "libsqlite3_python.so"]
# Os modulos nativos so de teste do proprio Python: ficam de fora.
MODULOS_DE_TESTE = ("_xxtestfuzz", "xxsubtype", "xxlimited", "xxlimited_35", "_testcapi", "_testinternalcapi",
                    "_testbuffer", "_testimportmultiple", "_testmultiphase", "_testsinglephase", "_ctypes_test",
                    "_testclinic", "_testexternalinspection")
LANCADOR = os.path.join(RAIZ, "android", "python", "lancador.c")
PRONTOS = os.path.join(sdk.BASE, "python-lancador")
TRIPLA = {"arm64-v8a": "aarch64-linux-android", "x86_64": "x86_64-linux-android"}
API_MINIMA = 24     # a mesma do APK (Android 7) e a menor do Python do Chaquopy


def pacote(nome):
    return preparar_linux.baixado(PACOTES[nome])


def ferramenta_do_ndk(nome):
    ndk = os.path.join(sdk.SDK, *sdk.NDK.split(";"))
    return os.path.join(ndk, "toolchains", "llvm", "prebuilt", "windows-x86_64", "bin", nome)


def lancador(abi):
    """O libarenapython.so desta ABI, compilado so quando o lancador.c, o
    NDK ou o Python mudam."""
    if not os.path.isfile(ferramenta_do_ndk("clang.exe")):
        raise SystemExit("Falta o NDK do Android: rode antes o ferramentas\\preparar_android.py.")
    pasta = os.path.join(PRONTOS, abi)
    pronto = os.path.join(pasta, "libarenapython.so")
    marca = {"lancador": preparar_linux.marca(LANCADOR), "ndk": sdk.NDK, "python": PACOTES[abi]["sha256"]}
    arquivo_da_marca = pronto + ".arena.json"
    try:
        with open(arquivo_da_marca, encoding="utf-8") as entrada:
            if os.path.isfile(pronto) and json.load(entrada) == marca:
                return pronto
    except (OSError, ValueError):
        pass
    # O libpython3.13.so so para ligar (o -lpython3.13): o do proprio pacote.
    ligar = os.path.join(pasta, "ligar")
    os.makedirs(ligar, exist_ok=True)
    with zipfile.ZipFile(pacote(abi)) as zip_python:
        with open(os.path.join(ligar, "libpython3.13.so"), "wb") as saida:
            saida.write(zip_python.read("jniLibs/%s/libpython3.13.so" % abi))
    feito = subprocess.run([ferramenta_do_ndk("clang.exe"), "--target=%s%d" % (TRIPLA[abi], API_MINIMA),
                            "-O2", "-fPIE", "-pie", "-Wall", "-Werror", "-o", pronto + ".parcial", LANCADOR,
                            "-L", ligar, "-lpython3.13", "-Wl,-rpath,$ORIGIN"], capture_output=True, text=True)
    if feito.returncode != 0:
        raise SystemExit("O NDK nao compilou o lancador do Python (%s):\n%s" % (abi, feito.stdout + feito.stderr))
    subprocess.run([ferramenta_do_ndk("llvm-strip.exe"), pronto + ".parcial"], check=True)
    os.replace(pronto + ".parcial", pronto)
    limpeza.apagar_pasta(ligar)
    with open(arquivo_da_marca, "w", encoding="utf-8") as saida:
        json.dump(marca, saida, indent=1)
    return pronto


def por_no_apk(pasta_apk, abi):
    """Poe o Python e o lancador no APK desmontado (ver o topo). Devolve o
    numero de modulos nativos."""
    destino_lib = os.path.join(pasta_apk, "lib", abi)
    os.makedirs(destino_lib, exist_ok=True)
    shutil.copyfile(lancador(abi), os.path.join(destino_lib, "libarenapython.so"))
    casa = os.path.join(pasta_apk, "assets", "arena-python", "lib")
    dinamicos = os.path.join(casa, "python3.13", "lib-dynload")
    os.makedirs(dinamicos, exist_ok=True)
    shutil.copyfile(pacote("stdlib-pyc"), os.path.join(casa, "python313.zip"))
    modulos = 0
    with zipfile.ZipFile(pacote(abi)) as zip_python:
        for nome in BIBLIOTECAS:
            with open(os.path.join(destino_lib, nome), "wb") as saida:
                saida.write(zip_python.read("jniLibs/%s/%s" % (abi, nome)))
        prefixo = "lib-dynload/%s/" % abi
        for item in zip_python.namelist():
            arquivo = item[len(prefixo):]
            if not item.startswith(prefixo) or not arquivo.endswith(".so") or "/" in arquivo:
                continue
            if arquivo.split(".", 1)[0] in MODULOS_DE_TESTE:
                continue
            with open(os.path.join(dinamicos, arquivo), "wb") as saida:
                saida.write(zip_python.read(item))
            modulos += 1
    return modulos


def principal():
    abis = [sys.argv[sys.argv.index("--abi") + 1]] if "--abi" in sys.argv else list(TRIPLA)
    for abi in abis:
        print("%s: %s" % (abi, lancador(abi)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
