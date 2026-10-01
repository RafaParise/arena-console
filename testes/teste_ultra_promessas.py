# -*- coding: utf-8 -*-
r"""O ultra desempenho faz o que promete? Conferido de FORA, pelo Windows.

Achado de 30/09/2026: o ultra prometia "emulador em prioridade alta e o
ARENA na mais baixa" e nenhuma das duas acontecia (duas prioridades juntas
viravam "acima do normal"; a chamada do ARENA ia com um identificador
cortado e falhava em silencio). E se o emulador nem abria, o vigia da rede
ficava suspenso ate reabrir o ARENA.

Monta um ARENA isolado (copia temporaria, RetroArch de mentira) e abre um
jogo pela rota real /api/jogar com o ultra ligado. O "emulador" e' um
processo que so espera alguns segundos. Durante o jogo, confere:
  1. emulador "acima do normal" (o Windows confirma);
  2. emulador fora da economia de energia (o Windows confirma);
  3. o ARENA "abaixo do normal" e com memoria de prioridade baixa;
  4. vigia da rede suspenso;
  5. opcoes de ultra no arquivo que o RetroArch le.
Depois do jogo, tudo de volta ao normal. E de novo com um emulador que NAO
abre: tudo tem que voltar ao normal tambem.

Uso: servidor\python\python.exe testes\teste_ultra_promessas.py
"""
import os
import shutil
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teste_partida_aparece as base  # noqa: E402

PORTA = 8794


def main():
    falhas = []

    def confere(nome, ok, detalhe=""):
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe))
        if not ok:
            falhas.append(nome)

    pasta, A = base.montar_copia("U", PORTA)
    import processos   # o da copia (mesmo codigo)
    servidor = None
    popen_original = subprocess.Popen
    abertos = []
    modo = {"falhar": False}

    def popen_falso(comando, *args, **kwargs):
        # So o "emulador" e' trocado; qualquer outro programa segue normal.
        if comando and str(comando[0]).lower().endswith("retroarch.exe"):
            if modo["falhar"]:
                raise OSError("emulador de mentira que nao abre")
            filho = popen_original([sys.executable, "-c", "import time; time.sleep(4)"],
                                   creationflags=kwargs.get("creationflags", 0))
            abertos.append((filho, kwargs))
            return filho
        return popen_original(comando, *args, **kwargs)

    try:
        cfg = A.carregar_config()
        cfg.update(apelido="Teste", ultra_desempenho=True, modo_desempenho=True)
        A.salvar_config(cfg)
        servidor = A.Servidor(("127.0.0.1", PORTA), A.Manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        jogo = base.achar_jogo_no_catalogo(base.pedir(PORTA, "/api/catalogo"), "Jogo de Teste")
        subprocess.Popen = popen_falso

        print("\n1. Jogo aberto com o ultra ligado")
        base.pedir(PORTA, "/api/jogar", {"jogo_id": jogo["id"]})
        limite = time.monotonic() + 15
        while not abertos and time.monotonic() < limite:
            time.sleep(0.1)
        confere("o ARENA abriu o emulador", bool(abertos))
        filho, kwargs = abertos[0]
        time.sleep(0.8)   # tempo de o ARENA aplicar os ajustes
        confere("pediu so 'acima do normal' (nao duas prioridades juntas)",
                kwargs.get("creationflags") == processos.ACIMA_DO_NORMAL,
                hex(kwargs.get("creationflags", 0)))
        confere("Windows: emulador acima do normal",
                processos.prioridade_de(filho.pid) == processos.ACIMA_DO_NORMAL,
                str(processos.NOMES_PRIORIDADE.get(processos.prioridade_de(filho.pid))))
        energia = processos.economia_de_energia_de(filho.pid) or {}
        confere("Windows: emulador fora da economia de energia",
                energia.get("controle") == 5 and energia.get("ligado") == 0, str(energia))
        confere("Windows: ARENA abaixo do normal durante o jogo",
                processos.prioridade_de() == processos.ABAIXO_DO_NORMAL,
                str(processos.NOMES_PRIORIDADE.get(processos.prioridade_de())))
        confere("Windows: memoria do ARENA com prioridade baixa",
                processos.memoria_de() == processos.MEMORIA_BAIXA, str(processos.memoria_de()))
        confere("vigia da rede suspenso", A.VIGIA["suspenso"] is True)
        override = open(A.ARQUIVO_OVERRIDE, encoding="utf-8").read()
        confere("opcoes de ultra no arquivo do RetroArch",
                'audio_driver = "wasapi"' in override and 'video_fullscreen = "true"' in override)

        filho.wait()
        limite = time.monotonic() + 10
        while A.JOGO_EM_ANDAMENTO["ativo"] and time.monotonic() < limite:
            time.sleep(0.1)
        print("\n2. Jogo fechado")
        confere("ARENA de volta ao normal", processos.prioridade_de() == processos.NORMAL,
                str(processos.NOMES_PRIORIDADE.get(processos.prioridade_de())))
        confere("memoria do ARENA de volta ao normal",
                processos.memoria_de() == processos.MEMORIA_NORMAL)
        confere("vigia da rede de volta", A.VIGIA["suspenso"] is False)

        print("\n3. Emulador que NAO abre")
        modo["falhar"] = True
        base.pedir(PORTA, "/api/jogar", {"jogo_id": jogo["id"]})
        limite = time.monotonic() + 10
        time.sleep(0.5)
        while A.JOGO_EM_ANDAMENTO["ativo"] and time.monotonic() < limite:
            time.sleep(0.1)
        confere("vigia da rede volta mesmo sem o jogo abrir (antes ficava parado)",
                A.VIGIA["suspenso"] is False)
        confere("ARENA volta ao normal mesmo sem o jogo abrir",
                processos.prioridade_de() == processos.NORMAL)
    except Exception as falha:
        import traceback
        traceback.print_exc()
        falhas.append("excecao: %s" % falha)
    finally:
        subprocess.Popen = popen_original
        processos.prioridade_do_arena(processos.NORMAL)
        processos.memoria_do_arena(processos.MEMORIA_NORMAL)
        if servidor:
            servidor.shutdown()
            servidor.server_close()
        A.VIGIA["encerrar"].set()
        try:
            A.fechar_banco()
        except Exception:
            pass
        time.sleep(1.0)
        shutil.rmtree(pasta, ignore_errors=True)

    print("\nRESULTADO:", "PASSOU" if not falhas else "FALHOU (%s)" % ", ".join(falhas))
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
