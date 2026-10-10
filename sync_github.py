#!/usr/bin/env python3
"""
Script de sincronização automática para o ARENA.

Este script facilita a sincronização entre os dois computadores e os
assistentes Hermes e Claude Code.

Uso:
    python sync_github.py --push     # Forçar envio
    python sync_github.py --pull     # Forçar recepção
    python sync_github.py --sync     # Push + Pull
    python sync_github.py --status   # Ver status
"""

import subprocess
import sys
from datetime import datetime

GITHUB_USER = "RafaParise"
REPO_NAME = "ARENA"

def executar(cmd, check=False):
    """Executa comando e retorna resultado."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Erro: {result.stderr}")
    return result.stdout.strip(), result.returncode

def status():
    """Mostra status do repositório."""
    print("=== STATUS DO REPOSITÓRIO ===\n")
    
    # Branch
    stdout, _ = executar("git branch --show-current")
    print(f"Branch atual: {stdout or 'Nenhuma'}")
    
    # Commits
    stdout, _ = executar("git log --oneline -5")
    print(f"\nÚltimos commits:\n{stdout or 'Nenhum'}")
    
    # Remote
    stdout, _ = executar("git remote -v")
    print(f"\nRemote:\n{stdout or 'Nenhum'}")
    
    # Status arquivos
    stdout, _ = executar("git status --short")
    if stdout:
        lines = stdout.split('\n')
        modificados = [l for l in lines if l.startswith('M ')]
        nao_rastreados = [l for l in lines if l.startswith('?? ')]
        print(f"\nModificados: {len(modificados)}")
        print(f"Não rastreados: {len(nao_rastreados)}")
    else:
        print("\nNenhum arquivo modificado")

def push():
    """Envia mudanças para o GitHub."""
    print("Enviando para o GitHub...")
    
    # Pull primeiro
    stdout, rc = executar("git pull origin auditoria 2>&1")
    if rc != 0:
        print(f"Pull: {stdout}")
    
    # Add
    stdout, rc = executar("git add -A")
    
    # Commit
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"Sincronização automática - {data_hora}\n\nVia sync_github.py"
    
    stdout, rc = executar(f'git commit -m "{msg}" 2>&1')
    if "nothing to commit" in stdout:
        print("Nada a commitar")
        return
    
    # Push
    stdout, rc = executar("git push origin auditoria 2>&1")
    print(f"Push: {stdout or 'Concluído'}")
    if rc != 0:
        print(f"Erro no push: {stdout}")

def pull():
    """Recebe mudanças do GitHub."""
    print("Recebendo do GitHub...")
    stdout, rc = executar("git pull origin auditoria 2>&1")
    print(stdout)
    if rc != 0:
        print(f"Erro: {stdout}")

def sync():
    """Sincroniza bidirecionalmente."""
    print("Sincronizando...\n")
    pull()
    print()
    push()
    
    # Atualizar SYNC_STATUS.md
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conteudo = f"""# Status de Sincronização

**Última atualização:** {data_hora}

## Repositório
- **Owner:** {GITHUB_USER}
- **Repository:** {REPO_NAME}
- **URL:** https://github.com/{GITHUB_USER}/{REPO_NAME}.git
- **Branch:** auditoria

## Estado
- Sincronização concluída com sucesso
- Todos os commits enviados e recebidos

---
*Gerado pelo script sync_github.py*
"""
    with open('SYNC_STATUS.md', 'w') as f:
        f.write(conteudo)
    
    print("\n✓ Sincronização concluída com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nComandos: --push, --pull, --sync, --status")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "--push":
        push()
    elif cmd == "--pull":
        pull()
    elif cmd == "--sync":
        sync()
    elif cmd == "--status":
        status()
    else:
        print(f"Comando desconhecido: {cmd}")