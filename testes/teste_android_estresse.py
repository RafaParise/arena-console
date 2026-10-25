# -*- coding: utf-8 -*-
r"""Estresse do ARENA no Android, no emulador (auditoria 4, Fase 1).

O pedido do Rafael (22/10/2026): "testes de stress diversos e simule o uso de
todos os recursos no android". No aparelho virtual do teste_android.py, com
o APK de teste ja instalado (ou instalado aqui):
  1. o Monkey do Android: milhares de toques, deslizes e teclas ao acaso
     dentro do app (a tela do ARENA e o RetroArch), sem as teclas de sistema;
     reprova se o ARENA travar ("app nao responde") ou cair;
  2. matar e voltar: o Android fecha o app a forca (como faz com pouca
     memoria) e o aluno abre de novo;
  3. girar a tela: deitado e de pe, com a tela do ARENA aberta;
  4. pouca memoria: o Android pede ao app para soltar memoria (o aviso de
     memoria critica);
  5. sem rede: Wi-Fi e dados desligados, o app abre de novo (offline).
Em cada passo: os processos do app continuam vivos e o registro de quedas do
Android (logcat -b crash) nao ganhou nada do ARENA.
Uso: servidor\python\python.exe testes\teste_android_estresse.py [--toques=N] [--saida=arquivo.json]
     [--manter-ligado]
"""
import json
import os
import re
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import teste_android as base  # noqa: E402

PACOTE = base.PACOTE


def argumento(nome, padrao):
    for a in sys.argv[1:]:
        if a.startswith("--%s=" % nome):
            return a.split("=", 1)[1]
    return padrao


def processos_do_app():
    """Os processos do app vivos ({nome: pid})."""
    vivos = {}
    for linha in base.adb_texto("shell", "ps", "-A", "-o", "PID,NAME").splitlines():
        partes = linha.split()
        if len(partes) == 2 and partes[1].startswith(PACOTE):
            vivos[partes[1]] = partes[0]
    return vivos


def quedas_do_app():
    """As quedas do ARENA no registro de quedas do Android."""
    texto = base.adb_texto("logcat", "-b", "crash", "-d", segundos=60)
    return [linha for linha in texto.splitlines() if PACOTE in linha and ("FATAL" in linha or "Process:" in linha)]


def abrir_o_arena(segundos=20):
    base.adb("shell", "am", "start", "-n", base.TELA_DO_ARENA)
    fim = time.monotonic() + segundos
    while time.monotonic() < fim:
        if "ArenaActivity" in base.tela_de_cima() and len(processos_do_app()) >= 1:
            time.sleep(3)
            return True
        time.sleep(1)
    return False


def passo(resultado, nome, fazer):
    """Roda um passo e confere: o app vivo, a tela do ARENA na frente (ou
    voltando) e nenhuma queda nova."""
    antes = len(quedas_do_app())
    inicio = time.monotonic()
    detalhe = fazer() or {}
    base.sem_aviso_do_sistema()
    vivo = bool(processos_do_app()) or abrir_o_arena()
    quedas = quedas_do_app()[antes:]
    resultado[nome] = dict(detalhe, segundos=round(time.monotonic() - inicio, 1), app_vivo=vivo,
                           quedas_novas=quedas[:5], tela=base.tela_de_cima()[:160])
    passou = vivo and not quedas and not detalhe.get("travou")
    print("  [%s] %s" % ("OK" if passou else "FALHOU", nome))
    return passou


def monkey(toques):
    # Sem os "--ignore", o Monkey desiste no primeiro aviso de "nao responde"
    # de QUALQUER app: no emulador lento, o da interface do sistema parou a
    # primeira rodada em 93 toques (23/10/2026). Com eles, ele vai ate o fim
    # e continua escrevendo cada queda e cada travamento: o do ARENA reprova.
    saida = base.adb_texto("shell", "monkey", "-p", PACOTE, "--pct-syskeys", "0", "--pct-appswitch", "2",
                           "--ignore-timeouts", "--ignore-crashes", "--ignore-security-exceptions",
                           "--throttle", "120", "-s", "2026", "-v", str(toques), segundos=1800)
    travou = [linha.strip() for linha in saida.splitlines()
              if ("// CRASH" in linha or "// NOT RESPONDING" in linha) and PACOTE in linha]
    outros = [linha.strip() for linha in saida.splitlines()
              if ("// CRASH" in linha or "// NOT RESPONDING" in linha) and PACOTE not in linha]
    eventos = re.search(r"Events injected:\s*(\d+)", saida)
    feitos = int(eventos.group(1)) if eventos else 0
    terminou = "Monkey finished" in saida
    resultado = {"eventos": feitos, "travou": travou[:5], "avisos_de_outros_apps": outros[:5], "terminou": terminou}
    if not terminou or feitos < 0.9 * toques:
        resultado["travou"] = travou[:5] or ["o Monkey parou em %d de %d toques" % (feitos, toques)]
        resultado["fim_da_saida"] = saida.strip().splitlines()[-12:]
    return resultado


def matar_e_voltar():
    base.adb("shell", "am", "force-stop", PACOTE)
    time.sleep(2)
    return {"voltou": abrir_o_arena(40)}


def girar():
    base.adb("shell", "settings", "put", "system", "accelerometer_rotation", "0")
    fotos = []
    for rotacao in ("1", "0"):            # deitado e de pe
        base.adb("shell", "settings", "put", "system", "user_rotation", rotacao)
        time.sleep(5)
        fotos.append(os.path.basename(base.foto("estresse-girar-%s" % rotacao)[0]))
    return {"fotos": fotos, "na_frente": "ArenaActivity" in base.tela_de_cima()}


def pouca_memoria():
    enviados = []
    for nome in processos_do_app():
        base.adb("shell", "am", "send-trim-memory", nome, "RUNNING_CRITICAL")
        enviados.append(nome)
    time.sleep(5)
    return {"processos": enviados}


def sem_rede():
    for comando in (("svc", "wifi", "disable"), ("svc", "data", "disable")):
        base.adb("shell", *comando)
    try:
        base.adb("shell", "am", "force-stop", PACOTE)
        time.sleep(2)
        voltou = abrir_o_arena(40)
        time.sleep(8)
        return {"abriu_sem_rede": voltou}
    finally:
        for comando in (("svc", "wifi", "enable"), ("svc", "data", "enable")):
            base.adb("shell", *comando)


def principal():
    toques = int(argumento("toques", "3000"))
    saida = argumento("saida", os.path.join(os.environ.get("TEMP", "."), "teste_android_estresse.json"))
    resultado = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "toques": toques}
    base.so_o_emulador()      # o Monkey, a rotacao e o "sem rede" nunca vao para o celular do professor (25/10/2026)
    processo, ligou = base.ligar_emulador()
    base.conferir_que_e_emulador()
    resultado["emulador_ligou_s"] = round(ligou, 1)
    base.adb("root", segundos=60)
    time.sleep(3)
    base.adb("wait-for-device", segundos=120)
    if ligou:
        time.sleep(30)
    certos = []
    try:
        if not base.adb_texto("shell", "pm", "path", PACOTE).strip():
            raise SystemExit("O ARENA nao esta instalado no emulador: rode antes o testes\\teste_android.py.")
        for permissao in ("READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"):
            base.adb("shell", "pm", "grant", PACOTE, "android.permission." + permissao)
        base.adb("shell", "settings", "put", "secure", "immersive_mode_confirmations", "confirmed")
        base.adb("logcat", "-b", "crash", "-c")
        resultado["abriu"] = abrir_o_arena(60)
        print("== Estresse do ARENA no Android (%s, %d toques)" % (
            base.adb_texto("shell", "getprop", "ro.build.version.release").strip(), toques))
        certos.append(passo(resultado, "Monkey: toques ao acaso", lambda: monkey(toques)))
        certos.append(passo(resultado, "matar e voltar", matar_e_voltar))
        certos.append(passo(resultado, "girar a tela", girar))
        certos.append(passo(resultado, "pouca memoria", pouca_memoria))
        certos.append(passo(resultado, "sem rede", sem_rede))
    finally:
        resultado["avisos_do_sistema_fechados"] = list(base.AVISOS_DO_SISTEMA)
        if "--manter-ligado" not in sys.argv:
            base.desligar_emulador(processo)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=1)
    print("\nEstresse no Android: %d de %d certos. Resultado: %s" % (sum(certos), len(certos), saida))
    return 0 if certos and all(certos) else 1


if __name__ == "__main__":
    sys.exit(principal())
