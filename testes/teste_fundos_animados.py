# -*- coding: utf-8 -*-
r"""Fundos da tela (ceu e campo): sempre aparecem; so se mexem quando devem.

Tarefa 8 do Rafael (01/10/2026), "os fundos animados nao funcionam mais".
Causa achada: com o Windows em "Ajustar para obter melhor desempenho"
(animacoes desligadas -- o caso do PC dele e do Celeron otimizado), o
navegador avisa "prefira menos movimento", e desde 23/09 o fundo, nesse
caso, nao desenhava NADA.

Confere, num navegador sem janela (testes\tela_sem_janela.py), com o
servidor de verdade:
  - nos dois temas, a cena cobre a tela inteira (160 x 90 pontos);
  - cada tema esconde o fundo do outro;
  - "automatico" + Windows pedindo menos movimento = cena PARADA (duas
    fotos iguais); sem o pedido = ANIMADA (duas fotos diferentes);
  - "sempre" anima mesmo com o pedido; "parado" nunca anima;
  - modo modesto + automatico = parada;
  - parada nao gasta processador; nenhum erro no console;
  - 02/10/2026 (Rafael): as visitas de jogos famosos (F-Zero, Kirby, Space
    Invaders e Arwing no ceu; Mario, Sonic, Duck Hunt e Kirby no campo)
    aparecem e VAO EMBORA sozinhas (a primeira versao do Kirby nunca ia), e o
    fundo animado, com visita na tela, gasta pouco processador.

Uso: servidor\python\python.exe testes\teste_fundos_animados.py
"""
import os
import subprocess
import sys
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tela_sem_janela import Navegador, achar_navegador  # noqa: E402

FOTO_DO_CANVAS = """(() => {
  const c = document.getElementById(document.body.dataset.tema === 'escuro' ? 'galaxyCanvas' : 'fieldCanvas');
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let opacos = 0, soma = 0;
  for (let i = 0; i < d.length; i += 4) { if (d[i + 3] > 0) opacos++; soma = (soma * 31 + d[i] + d[i + 1] * 7 + d[i + 2] * 13) >>> 0; }
  return JSON.stringify({opacos: opacos, soma: soma, display: getComputedStyle(c).display});
})()"""


# O servidor do teste abre numa porta so dele (ARENA_PORTA): assim o teste
# roda com o ARENA de verdade aberto na 8777 (20/10/2026: o papel de parede
# animado usa o ARENA aberto).
PORTA = 8792


def porta_ocupada():
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", PORTA)) == 0
    finally:
        s.close()


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    if not achar_navegador():
        print("Sem Edge nem Chrome nesta maquina: nada a testar.")
        return 0
    if porta_ocupada():
        print("A porta %d (a do teste) esta ocupada: feche o que a usa e rode de novo." % PORTA)
        return 1
    servidor = subprocess.Popen([os.path.join(RAIZ, "servidor", "python", "python.exe"),
                                 os.path.join(RAIZ, "servidor", "arena.py")], cwd=RAIZ,
                                env=dict(os.environ, ARENA_SEM_JANELA="1", ARENA_PORTA=str(PORTA)),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/api/estado" % PORTA, timeout=1).read()
                break
            except OSError:
                time.sleep(0.2)
        with Navegador() as nav:
            nav.comando("Performance.enable")
            nav.abrir("http://127.0.0.1:%d" % PORTA, 1366, 768, 1)
            nav.avaliar("window.__erros = 0; const e0 = console.error; console.error = function () "
                        "{ window.__erros++; e0.apply(console, arguments); }; 1")

            def ajustar(tema, fundo, menos_movimento, modesto=False):
                nav.comando("Emulation.setEmulatedMedia", features=[
                    {"name": "prefers-reduced-motion", "value": "reduce" if menos_movimento else "no-preference"}])
                nav.avaliar("estado.config.tema = '%s'; estado.config.fundo_animado = '%s'; "
                            "estado.config.modo_modesto = %s; atualizarBotaoTema(); 1"
                            % (tema, fundo, "true" if modesto else "false"))
                time.sleep(3.5)      # o vigia do fundo olha a cada 3 s

            def anda():
                import json
                a = json.loads(nav.avaliar(FOTO_DO_CANVAS))
                time.sleep(1.5)
                b = json.loads(nav.avaliar(FOTO_DO_CANVAS))
                return a, b["soma"] != a["soma"]

            for tema in ("claro", "escuro"):
                ajustar(tema, "automatico", menos_movimento=False)
                foto, mexeu = anda()
                confere("%s: a cena cobre a tela inteira" % tema, foto["opacos"] == 160 * 90, str(foto))
                confere("%s: automatico sem pedido do Windows = animada" % tema, mexeu)
                outro = "galaxyCanvas" if tema == "claro" else "fieldCanvas"
                confere("%s: o fundo do outro tema fica escondido" % tema,
                        nav.avaliar("getComputedStyle(document.getElementById('%s')).display" % outro) == "none")

                # Visitas de jogos famosos: cada uma aparece e vai embora sozinha.
                gancho = "window.__fundoEscuro" if tema == "escuro" else "window.__fundoClaro"
                confere("%s: os sprites carregaram (pixel-sprites.js)" % tema,
                        nav.avaliar("!!(window.SpritesRetro && %s)" % gancho) is True)
                nomes = nav.avaliar("%s.visitas" % gancho) or []
                for nome in nomes:
                    nav.avaliar("%s.chamar('%s'); %s.velocidade(8); 1" % (gancho, nome, gancho))
                    foi_embora = False
                    for _ in range(60):
                        time.sleep(0.25)
                        if not nav.avaliar("%s.rodando()" % gancho):
                            foi_embora = True
                            break
                    nav.avaliar("%s.velocidade(1); 1" % gancho)
                    confere("%s: a visita '%s' aparece e vai embora sozinha" % (tema, nome), foi_embora)
                # Quanto o fundo gasta animando, com a visita mais cheia na tela.
                nav.avaliar("%s.chamar('%s'); 1" % (gancho, "fzero" if tema == "escuro" else "mario"))
                time.sleep(0.5)
                m0 = {x["name"]: x["value"] for x in nav.comando("Performance.getMetrics")["metrics"]}
                time.sleep(4)
                m1 = {x["name"]: x["value"] for x in nav.comando("Performance.getMetrics")["metrics"]}
                gasto = (m1.get("ScriptDuration", 0) - m0.get("ScriptDuration", 0)) * 1000
                confere("%s: animado, com visita na tela, gasta pouco (%.0f ms de script em 4 s = %.1f%% "
                        "de um nucleo)" % (tema, gasto, gasto / 40.0), gasto < 240)

                ajustar(tema, "automatico", menos_movimento=True)
                foto, mexeu = anda()
                confere("%s: Windows pedindo menos movimento = cena PARADA, mas inteira" % tema,
                        not mexeu and foto["opacos"] == 160 * 90, str(foto))

                ajustar(tema, "sempre", menos_movimento=True)
                _foto, mexeu = anda()
                confere("%s: 'sempre animado' anima mesmo com o pedido do Windows" % tema, mexeu)

                ajustar(tema, "parado", menos_movimento=False)
                foto, mexeu = anda()
                confere("%s: 'parado' nunca anima (e a cena continua inteira)" % tema,
                        not mexeu and foto["opacos"] == 160 * 90)
                m0 = {x["name"]: x["value"] for x in nav.comando("Performance.getMetrics")["metrics"]}
                time.sleep(4)
                m1 = {x["name"]: x["value"] for x in nav.comando("Performance.getMetrics")["metrics"]}
                gasto = (m1.get("ScriptDuration", 0) - m0.get("ScriptDuration", 0)) * 1000
                confere("%s: parado nao gasta processador (%.1f ms de script em 4 s)" % (tema, gasto), gasto < 20)

                ajustar(tema, "automatico", menos_movimento=False, modesto=True)
                _foto, mexeu = anda()
                confere("%s: modo modesto + automatico = parada" % tema, not mexeu)

            confere("nenhum erro no console", nav.avaliar("window.__erros") == 0,
                    str(nav.avaliar("window.__erros")))
    finally:
        servidor.kill()

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Fundos animados: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
