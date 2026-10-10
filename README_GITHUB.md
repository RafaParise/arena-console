# ARENA - Console de Jogos Trintão Portátil

**Console/launcher de jogos retrô portátil e sem instalação**, baseado em RetroArch.

![Imagem do ARENA em execução](docs/arena-screenshot.png)

## 🚀 O Que é o ARENA?

O ARENA é um projeto educacional completo que permite:
- Executar cerca de 47 consoles emulados (de NES ao PS2)
- Trabalhar de qualquer computador
- Sincronizar automaticamente com GitHub
- Executar jogos de forma portátil (pen drive, disco externo)

## 📋 Características

- ✅ Portátil - Roda de uma pasta única
- ✅ Sem instalação - Não precisa de administrador
- ✅ Educacional - Focado em salas de aula
- ✅ Sincronizável - Trabalhe localmente ou na nuvem
- ✅ Multijogador - Até 5 jogadores simultâneos

## 🛠️ Como Usar

### 1. Clonar o projeto
```bash
git clone https://github.com/RafaParise/ARENA.git
```

### 2. Entrar na pasta
```bash
cd ARENA
git checkout auditoria
```

### 3. Executar
```bash
ARENA.bat
```

## 📦 Estrutura do Projeto

```
ARENA-unificado/
├── ARENA.bat           # Launcher principal
├── servidor/           # Servidor web local
├── jogos/              # Jogos dos consoles
├── BIOS/               # Arquivos de BIOS (não incluídos)
├── docs/               # Documentação
│   ├── PLANO-AUDITORIA.md
│   └── RELATORIO-QUALIDADE.md
├── testes/             # Testes automatizados
├── ferramentas/        # Ferramentas auxiliares
└── sincronizador.py    # Script de sincronização automática
```

## 🔄 Sincronização

O projeto sincroniza automaticamente com o GitHub:

```bash
python sync_github.py
# Ou
SINCRONIZAR_ARENA.bat
```

### Fluxo Diário

1. **No início:** `python sync_github.py` (pull)
2. **Durante:** Trabalhe normalmente
3. **No fim:** `python sync_github.py` (push)

## 🎮 Consoles Suportados

| Console | Emulador | Status |
|---------|----------|--------|
| Nintendo Entertainment System | FCEUX | ✅ Testado |
| Super Nintendo | Snes9x | ✅ Testado |
| PlayStation 1 | Swanstation | ✅ Testado |
| PlayStation 2 | PCSX2 | ✅ Testado |
| Game Boy | Gambatte | ✅ Testado |
| ... e 41 outros | | |

## 📚 Documentação

- [PLANO-AUDITORIA.md](docs/PLANO-AUDITORIA.md) - Plano de desenvolvimento
- [RELATORIO-QUALIDADE.md](docs/RELATORIO-QUALIDADE.md) - Relatório técnico
- [CLAUDE.md](CLAUDE.md) - Estado atual do projeto
- [SYNC_STATUS.md](SYNC_STATUS.md) - Status de sincronização

## 🤝 Contribuição

Este projeto é colaborativo. Para contribuir:

1. Clone o repositório
2. Entre na branch `auditoria`
3. Faça suas alterações
4. Sincronize automaticamente
5. Commit e push

## 📧 Contato

**Rafael Parise Passos**
Email: passospariserafael@gmail.com

---

**MIT License** - Ver [LICENSE](LICENSE) para detalhes.

**GitHub:** [https://github.com/RafaParise/ARENA](https://github.com/RafaParise/ARENA)
