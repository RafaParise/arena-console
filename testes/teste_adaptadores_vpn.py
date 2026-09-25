# -*- coding: utf-8 -*-
r"""Revisao pos-auditoria: classificacao de endereco pelo NOME do adaptador.

1. Casos fixos (nomes reais do Windows): VPN, Hyper-V, Wi-Fi virtual,
   ponto de acesso do Windows, Wi-Fi de verdade, cabo direto.
2. Nesta maquina, de verdade: espera o ARENA descobrir os nomes em segundo
   plano e confere que nenhum adaptador com nome de virtual/VPN aparece como
   "Rede local" ou "Cabo direto".
"""
import importlib.util
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CASOS = [
    ("10.8.0.6", "ethernet 3 tap-windows adapter v9", "vpn"),
    ("10.5.0.2", "nordlynx nordlynx tunnel", "vpn"),
    ("100.101.102.103", "tailscale tailscale tunnel", "vpn"),
    ("192.168.96.1", "vethernet (default switch) hyper-v virtual ethernet adapter", "virtual"),
    ("169.254.186.45", "conexão local* 10 ", "virtual"),
    ("169.254.9.9", "local area connection* 2 microsoft wi-fi direct virtual adapter", "virtual"),
    ("192.168.137.1", "conexão local* 2 microsoft wi-fi direct virtual adapter #2", "ponto_acesso"),
    ("192.168.18.17", "wi-fi intel(r) wi-fi 6e ax210 160mhz", "rede_local"),
    ("169.254.20.5", "ethernet realtek pcie gbe family controller", "cabo_direto"),
    ("10.0.0.5", "", "rede_local"),  # sem nome ainda: continua pela faixa
]


def main():
    sys.path.insert(0, os.path.join(RAIZ, "servidor"))
    spec = importlib.util.spec_from_file_location("arena_vpn", os.path.join(RAIZ, "servidor", "arena.py"))
    arena = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arena)

    ok = True
    for ip, nome, esperado in CASOS:
        tipo, rotulo = arena.classificar_endereco(ip, nome)
        certo = tipo == esperado
        ok = ok and certo
        print("  %-16s %-12s %s" % (ip, tipo, "OK" if certo else "ERRADO (esperado %s)" % esperado))

    print("\nNesta maquina (nomes descobertos em segundo plano):")
    arena.enderecos_locais(forcar=True)
    for _ in range(40):
        if arena._adaptadores["quando"]:
            break
        time.sleep(0.5)
    for e in arena.enderecos_locais(forcar=True):
        nome = arena._adaptadores["mapa"].get(e["ip"], "")
        suspeito = any(p in nome for p in arena.PALAVRAS_VIRTUAL + arena.PALAVRAS_VPN) or "local*" in nome
        errado = suspeito and e["tipo"] in ("rede_local", "cabo_direto")
        ok = ok and not errado
        print("  %-16s %-12s %-45s %s" % (e["ip"], e["tipo"], nome[:45], "ERRADO" if errado else "ok"))
    print("\nRESULTADO:", "PASSOU" if ok else "FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
