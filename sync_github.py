#!/usr/bin/env python3
"""
Sincronizador automático do ARENA para GitHub.

Uso:
    python sync_github.py          # Sincronização completa
    python sync_github.py --status # Ver status
    python sync_github.py --help   # Mostrar ajuda

Requisitos:
    - Git instalado
    - gh CLI autenticado (gh auth login)
"""

import subprocess
import sys
from datetime import datetime

def executar(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
        return r.stdout, r.returncode
    except:
        return "", 1

def sincronizar():
    print("\n" + "="*50)
    print("SYNCRONIZADOR ARENA - GITHUB")
    print("="*50 + "\n")
    
    # Pull
    print("Baixando do GitHub...")
    out, rc = executar("git pull origin auditoria 2>&1")
    print("  Atualizado" if rc == 0 else f"  {out[:100]}")
    
    # Status
    out, _ = executar("git status --short")
    lines = [l for l in out.split("\n") if l.strip()]
    print(f"\nArquivos modificados: {len(lines)}")
    
    # Commit
    if lines:
        print("\nPreparando arquivos...")
        executar("git add -A")
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        out, rc = executar(f'git commit -m "Backup - {data}" 2>&1')
        if "nothing to commit" not in out:
            print("  Commit criado")
    
    # Push
    print("\nEnviando para o GitHub...")
    out, rc = executar("git push origin auditoria 2>&1")
    if rc == 0:
        print("  Enviado com sucesso!")
    elif "not authenticated" in out:
        print("  Execute: gh auth login")
    
    print("\n" + "="*50)
    print("SYNCRONIZADO")
    print("="*50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--status", "--help", "-h"]:
        print(__doc__)
    else:
        sincronizar()
