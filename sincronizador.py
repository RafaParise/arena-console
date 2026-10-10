#!/usr/bin/env python3
"""
Sincronizador automático do ARENA para GitHub.
Backup completo e sincronização bidirecional.

Uso: python sincronizador.py [comando]

Comandos:
    run    - Executa sincronização completa (padrão)
    push   - Apenas enviar mudanças
    pull   - Apenas receber mudanças
    status - Verificar status
    help   - Mostrar ajuda
"""

import subprocess
import sys
import os
from datetime import datetime

def executar(comando):
    """Executa comando e retorna saída."""
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=120)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

def main():
    if len(sys.argv) < 2:
        cmd = "run"
    else:
        cmd = sys.argv[1].lower()
    
    if cmd == "help":
        print(__doc__)
        return
    
    # Garantir que estamos no diretório certo
    caminho_projeto = r"C:\Projetos\Criador De Apps Pedagogicos\ARENA\ARENA-unificado"
    
    if not os.path.exists(caminho_projeto):
        print(f"ERRO: Pasta não encontrada: {caminho_projeto}")
        input("Pressione Enter para continuar...")
        return
    
    os.chdir(caminho_projeto)
    
    print(f"\n{'='*50}")
    print("SYNCRONIZADOR ARENA")
    print(f"{'='*50}\n")
    
    if cmd in ["run", "pull"]:
        print("1. BAIXANDO do GitHub...")
        out, err, rc = executar("git pull origin auditoria 2>&1")
        print(out if out else "Nenhuma mudança para baixar")
        if rc != 0 and "nothing to pull" not in out.lower():
            print(f"Erro: {err}")
        print()
    
    if cmd in ["run", "push"]:
        if cmd == "push":
            print("PREPARANDO para envio...")
        else:
            print("3. ADICIONANDO arquivos...")
        out, err, rc = executar("git add -A")
        print("Arquivos preparados")
        print()
        
        print("4. CRIANDO commit...")
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"Backup automático - {data}\n\nSincronização via script automático"
        out, err, rc = executar(f'git commit -m "{msg}" 2>&1')
        
        if "nothing to commit" in out or "on branch" in out:
            print("Nenhum arquivo novo para commitar")
        else:
            print(f"Commit criado: {data}")
        print()
        
        print("5. ENVIANDO para o GitHub...")
        out, err, rc = executar("git push origin auditoria 2>&1")
        if rc == 0:
            print("✓ Enviado com sucesso!")
        else:
            if "not authenticated" in out.lower() or "401" in out:
                print("⚠️  AUTENTICAÇÃO NECESSÁRIA!")
                print("\nEXECUTE no terminal:")
                print("  gh auth login")
                print("\nDepois de autenticado, execute novamente.")
            elif "nothing to push" in out.lower():
                print("Nada para enviar (já sincronizado)")
            else:
                print(f"Resultado: {out}")
        print()
    
    if cmd in ["run", "status"]:
        print("6. STATUS ATUAL:")
        out, _, _ = executar("git log --oneline -3")
        print(f"Últimos commits:\n{out}")
        
        out, _, _ = executar("git status --short | find /c /v /n ''")
        lines = [l for l in out.split('\n') if l.strip()]
        print(f"\nArquivos modificados: {len(lines)}")
    
    print(f"\n{'='*50}")
    print("FINISH")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()