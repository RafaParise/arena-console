# Sincronização Cross-Assistente

## Objetivo
Permitir que você continue o trabalho tanto localmente quanto na nuvem (GitHub) com os assistentes Hermes e Claude Code sincronizados.

## Contas Configuradas
- **Hermes (este):** passospariserafael@gmail.com
- **Claude Code (1):** passospariserafael@gmail.com
- **Claude Code (2):** (conta institucional do professor)

## Repositório GitHub
- **Owner:** RafaParise
- **Repository:** ARENA
- **URL:** https://github.com/RafaParise/ARENA.git
- **Branch atual:** auditoria

## Instruções para o Outro Computador

### 1. Autenticar no GitHub
Execute no terminal:
\`\`\`bash
gh auth login
\`\`\`
Escolha:
- Account: Não tenho conta (Use GitHub CLI)
- Login method: Web browser
- Siga o link e autorize

### 2. Verificar repositório
\`\`\`bash
git remote -v
\`\`\`
Deve mostrar: https://github.com/RafaParise/ARENA.git

### 3. Baixar mudanças
\`\`\`bash
git pull origin auditoria
\`\`\`

### 4. Verificar status
\`\`\`bash
python sync_github.py --status
\`\`\`

## Instruções para Este Computador

### 1. Autenticar no GitHub (se não estiver autenticado)
\`\`\`bash
gh auth login
\`\`\`

### 2. Subir mudanças
\`\`\`bash
python sync_github.py --sync
\`\`\`
Ou manualmente:
\`\`\`bash
git add -A
git commit -m "Sincronização automática - data"
git push origin auditoria
\`\`\`

## Arquivos Criados para Sincronização

1. **sync_github.py** - Script de sincronização automática
2. **SYNC_STATUS.md** - Documentação automática de status
3. **GUIA_SYNC.md** - Guia rápido (em /scratch)
4. **SINCRONIZACAO_ASSISTENTES.md** - Documentação completa (em /scratch)

## Como os Assistentes Sincronizam

### Padrão de Trabalho
1. Ambos usam a mesma conta GitHub (RafaParise)
2. Ambos trabalham na branch `auditoria`
3. Commits menores são mais fáceis de resolver conflitos

### Regra de Ouro
**Sempre faça pull antes de push!**

## Contato
Email: passospariserafael@gmail.com

---
*Documento para sincronização entre computadores e assistentes*
