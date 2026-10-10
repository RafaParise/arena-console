# PASSO A PASSO - SINCRONIZAÇÃO COMPLETA

## ⚠️ IMPORTANTE - AUTENTICAÇÃO NO GITHUB

**Antes de qualquer coisa, você PRECISA autenticar no GitHub.**

### Passo 1: Autenticar no GitHub
Abra o terminal (CMD ou PowerShell) e execute:

```bash
gh auth login
```

**Siga exatamente este fluxo:**
1. Pressione Enter
2. Digite: `1` (Login with a web browser) → Enter
3. Abra o link no navegador que aparecer
4. Faça login com: **passospariserafael@gmail.com**
5. Clique em "Authorize hermes"
6. Volte ao terminal e pressione Enter

---

## Opção 1: Usar o Script Automático

### Para sincronizar tudo (recomendado):
```bash
cd C:\Projetos
python sincronizador.py run
```

### Ou usar o .bat:
```bash
cd C:\Projetos
SINCRONIZAR_ARENA.bat
```

---

## Opção 2: Comandos Manualmente (se preferir)

### 1. Entrar na pasta do projeto:
```bash
cd "C:\Projetos\Criador De Apps Pedagogicos\ARENA\ARENA-unificado"
```

### 2. Baixar mudanças:
```bash
git pull origin auditoria
```

### 3. Adicionar todos os arquivos:
```bash
git add -A
```

### 4. Criar commit:
```bash
git commit -m "Backup automático - $(date)"
```

### 5. Enviar para o GitHub:
```bash
git push origin auditoria
```

---

## ✅ DEPOIS DE SINCRONIZAR

1. Abra: https://github.com/RafaParise/ARENA
2. Clique em "auditoria" (branch)
3. Verifique se os arquivos estão lá:
   - sync_github.py
   - SYNC_STATUS.md
   - CLAUDE.md

---

## CONTAS SINCRONIZADAS
- passospariserafael@gmail.com
- (conta institucional do professor)

---

**📝 DICA:** O script `sincronizador.py` também verifica se você está autenticado e mostra instruções se precisar autenticar.