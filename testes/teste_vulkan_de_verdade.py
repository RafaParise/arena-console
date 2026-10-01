# -*- coding: utf-8 -*-
r"""Motor automatico: Vulkan so quando o Vulkan enxerga uma placa de verdade.

Achado de 01/10/2026: o automatico escolhia Vulkan so porque o
vulkan-1.dll carrega -- e esse arquivo pode ter sobrado de outra placa (o
PC do Rafael ainda tem no registro uma GeForce 210 que ja saiu). Vulkan
sem placa = jogo que abre e fecha sem explicar. Agora o ARENA pergunta ao
Vulkan, num processo separado e em segundo plano (driver velho pode
derrubar quem pergunta), e troca para d3d11 se nao houver placa.

Confere:
  - neste PC a pergunta funciona e responde rapido;
  - "0 placas" = nao serve; ajudante que cai = nao serve; ajudante que
    demora demais = nao sabe (None), e o ARENA nao muda nada;
  - conferir_vulkan troca o motor so quando a resposta e' "nao serve".

Uso: servidor\python\python.exe testes\teste_vulkan_de_verdade.py
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "servidor"))
import hardware  # noqa: E402


def main():
    falhas, total = [], [0]

    def confere(nome, ok, detalhe=""):
        total[0] += 1
        print("  [%s] %s %s" % ("OK" if ok else "FALHOU", nome, detalhe if not ok else ""))
        if not ok:
            falhas.append(nome)

    inicio = time.perf_counter()
    resposta = hardware.vulkan_tem_placa()
    gasto = time.perf_counter() - inicio
    confere("neste PC a pergunta responde (True, False ou None) em menos de 5 s",
            resposta in (True, False, None) and gasto < 5, "%r em %.2f s" % (resposta, gasto))

    original = hardware._PERGUNTA_VULKAN
    try:
        hardware._PERGUNTA_VULKAN = 'print("placas=0")'
        confere("Vulkan sem placa = nao serve", hardware.vulkan_tem_placa() is False)
        hardware._PERGUNTA_VULKAN = "import os; os._exit(3221225477)"   # queda dentro do driver
        confere("ajudante que cai (driver quebrado) = nao serve", hardware.vulkan_tem_placa() is False)
        hardware._PERGUNTA_VULKAN = "import time; time.sleep(30)"
        inicio = time.perf_counter()
        confere("ajudante que demora demais = nao sabe (None), sem esperar para sempre",
                hardware.vulkan_tem_placa(limite=1) is None and time.perf_counter() - inicio < 5)
        hardware._PERGUNTA_VULKAN = 'print("placas=2")'
        confere("duas placas = serve", hardware.vulkan_tem_placa() is True)
    finally:
        hardware._PERGUNTA_VULKAN = original

    import arena  # noqa: E402
    guardado = (dict(arena.MAQUINA), hardware.vulkan_tem_placa)
    try:
        for resposta, motor_antes, esperado in ((False, "vulkan", "d3d11"), (True, "vulkan", "vulkan"),
                                                (None, "vulkan", "vulkan"), (False, "d3d11", "d3d11")):
            arena.MAQUINA["driver_video"] = motor_antes
            hardware.vulkan_tem_placa = lambda limite=10, r=resposta: r
            arena.conferir_vulkan()
            confere("motor %s + resposta %r -> %s" % (motor_antes, resposta, esperado),
                    arena.MAQUINA["driver_video"] == esperado, arena.MAQUINA["driver_video"])
    finally:
        arena.MAQUINA.clear()
        arena.MAQUINA.update(guardado[0])
        hardware.vulkan_tem_placa = guardado[1]

    print()
    if falhas:
        print("FALHOU: %d de %d" % (len(falhas), total[0]))
        return 1
    print("Vulkan de verdade: %d de %d certos." % (total[0], total[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
