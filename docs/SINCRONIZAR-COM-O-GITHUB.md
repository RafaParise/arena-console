# Trabalhar no ARENA em vários lugares (GitHub)

O GitHub guarda a **cópia central** do ARENA:
<https://github.com/RafaParise/ARENA>. Cada computador, e cada assistente
(Claude Code no computador ou na nuvem, Hermes), trabalha numa cópia própria
e conversa com a central: **no começo, puxa; no fim, envia.**

É como um caderno que fica na sala dos professores: cada um tira uma cópia,
trabalha nela e, no fim do dia, devolve as páginas novas para o caderno. Quem
chega depois copia o caderno já com as páginas de todo mundo.

---

## Uma vez em cada computador

1. **Git para Windows** instalado ([git-scm.com](https://git-scm.com)). Ele traz
   junto o login do GitHub (o Gerenciador de Credenciais do Git).
2. **Baixar o código:**

   ```
   git clone https://github.com/RafaParise/ARENA.git
   ```

   Numa pasta do ARENA que já existe e ainda não conhece o GitHub:

   ```
   git remote add origin https://github.com/RafaParise/ARENA.git
   ```

3. **O que é pesado não vem pelo git:** o Python embutido
   (`servidor\python`), o RetroArch, os emuladores, os jogos e as BIOS. Para
   ter um ARENA que abre, copie essas pastas de um ARENA que já funciona (pen
   drive) ou do pacote completo da página **Releases** do GitHub.
4. **O primeiro envio pede login:** o Windows abre a página do GitHub, você
   entra com a conta do ARENA e pronto. O login fica guardado no Windows
   (Gerenciador de Credenciais), **nunca** dentro da pasta. Ninguém precisa
   digitar senha num arquivo, nem criar token.

---

## Todo dia

| Quando | O que fazer |
|---|---|
| **Começo** | Dois cliques no `SINCRONIZAR.bat` (ou peça ao assistente: "puxe do GitHub") |
| **Fim** | O assistente faz o commit do que ele fez, com uma mensagem que diga o que mudou, e envia (ou dois cliques no `SINCRONIZAR.bat`) |

O `SINCRONIZAR.bat` também aceita: `estado` (só mostra), `puxar`, `enviar`.

### O que o SINCRONIZAR.bat faz

- **Puxa** o que os outros enviaram. Se os dois lados mudaram arquivos
  diferentes, junta. Se os dois mudaram o **mesmo trecho** do mesmo arquivo,
  desiste sem mexer em nada e avisa: aí um assistente junta com cuidado.
- **Envia** os commits feitos aqui.

### O que ele NÃO faz (de propósito)

- **Não faz commit sozinho** do que ainda não tem commit: só mostra a lista.
  Commit é de quem fez o trabalho, com uma mensagem que diga o que mudou.
- Para mandar tudo mesmo assim, o professor pede, com a mensagem:

  ```
  SINCRONIZAR.bat enviar --tudo "o que mudou"
  ```

**Por que assim:** em 10/10/2026, um script de sincronização juntava tudo o
que estava na pasta num commit "Backup automático". Um assistente estava no
meio de um trabalho (a Fase 5 da auditoria), e esse trabalho foi parar num
commit chamado "Documentação completa para sincronização", sem dizer o que
mudou. Nada se perdeu, mas ficou impossível saber, pelo histórico, o que era
o quê.

---

## Regras para os assistentes (Claude Code, Hermes e outros)

Estão também no `AGENTS.md`, na raiz:

1. **No começo, puxar** (`git pull --ff-only`, ou o `SINCRONIZAR.bat puxar`).
2. **Nunca `git add -A` nem `git add .`**: adicione só os arquivos que você
   mudou (`git add caminho\do\arquivo`). Outro assistente pode estar no meio
   de um trabalho na mesma pasta.
3. **Antes do commit**, `git status` e `git diff --staged`: arquivo que você
   não mexeu não é seu.
4. **Mensagem de commit que diga o que mudou e por quê**, em português.
5. **No fim, enviar** (`git push`), depois de atualizar a seção "Estado
   atual" do `CLAUDE.md`.
6. **Conflito:** juntar com cuidado. Nunca apagar o trabalho do outro para o
   seu passar.
7. **Nunca** forçar a entrada de dado do aluno, jogo, BIOS ou save
   (`git add -f`), nem gravar senha, token ou e-mail num arquivo do
   repositório: **o repositório é público.**

---

## O que nunca vai para o GitHub

O `.gitignore` já barra: `dados\` (recordes, perfis, configuração de quem
usa), `BIOS\`, os jogos, os saves e estados, os emuladores e o RetroArch
inteiro, as coletas de máquina (`perfil\`), as cópias de segurança
(`backup\`) e todo `.zip`.
