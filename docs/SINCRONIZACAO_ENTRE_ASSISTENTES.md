# Sincronização entre Assistentes - Guia Completo

## Contas Sincronizadas
- **Hermes:** passospariserafael@gmail.com
- **Claude Code (1):** passospariserafael@gmail.com
- **Claude Code (2):** [e-mail removido]

## Repositório GitHub
- **Owner:** RafaParise
- **Repository:** ARENA
- **URL:** https://github.com/RafaParise/ARENA.git
- **Branch:** auditoria

## Estados Atuais por Commit

### Commit 3086334 - Fase 0
Linha de base, inventário e rodada de referência

### Commit a0f464c - Fase 1
Varredura e limpeza do código (C1-C7, R1-R5)

### Commit b0f55bd - Fase 2
Leveza e desempenho

### Commit dc143ca - Fase 3
Servidor e API (offline e online)

### Commit 80ef090 - Fase 4
Rede Publica, FAT32

### Commit e752b0b - Sync
Arquivos de sincronização criados

### Commit 69cc361 - CLAUDE.md
Atualização do estado atual

## Pendências de Sincronização

### CRÍTICO: Autenticação GitHub
O outro computador e este computador precisam autenticar no GitHub.

**Comando:**
```bash
gh auth login
```

Escolher:
1. Account: "Skip, already authenticated" ou autenticar
2. Login method: Web browser
3. Siga o link e autorize

### Depois da autenticação:
```bash
git push origin auditoria
```

## Fluxo Diário Recomendado

### Início do Dia:
```bash
git pull origin auditoria
# Verificar se há conflitos
# Se houver: resolver manualmente
git status
```

### Durante o Trabalho:
```bash
git add -A
git commit -m "Descrição curta do que foi feito"
# Repetir conforme necessário
```

### Fim do Dia:
```bash
git push origin auditoria
```

## Arquivos Importantes

### Documentação
- `docs/PLANO-AUDITORIA.md` - Plano detalhado das 8 fases
- `docs/RELATORIO-QUALIDADE.md` - Relatório da auditoria
- `CLAUDE.md` - Estado atualizado
- `ESTADO_ATUAL.md` - Estado resumido

### Código
- `servidor/arena.py` - Código principal
- `testes/` - Testes automatizados
- `ferramentas/` - Ferramentas de apoio

## Como os Assistentes Se Comunicam

### Via GitHub
1. Ambos fazem pull no início
2. Ambos fazem push no fim
3. Cada commit tem mensagem descritiva

### Via Arquivos
- `CLAUDE.md` é atualizado após cada sessão
- `ESTADO_ATUAL.md` mostra resumo rápido
- `RESUMO_SYNC.md` mostra pendências de sync

## Próximos Passos

### Fase 5 - Matriz de Jogos (INICIAR)
Para cada console:
- [ ] Verificar se jogo abre
- [ ] Verificar se controle funciona
- [ ] Verificar salvar/carregar
- [ ] Verificar cheats
- [ ] Medir FPS

### Fase 6 - Portabilidade
Testar em diferentes cenários

### Fase 7 - Clareza
Revisar textos da interface

### Fase 8 - Relatório Final
Preparar para merge com main

## Comando de Sincronização Rápida

```bash
# Sincronizar tudo de uma vez
python sync_github.py --sync

# Ou manualmente
git add -A
git commit -m "Sincronização automática"
git push origin auditoria
```

## Contato
Email: passospariserafael@gmail.com

---
*Documento criado para sincronização entre assistentes Hermes e Claude Code*