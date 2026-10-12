# Trabalhar no ARENA em vários lugares (GitHub)

O GitHub guarda a **cópia central** do ARENA:
<https://github.com/RafaParise/arena-console>. Cada computador, e cada
assistente (Claude Code no computador ou na nuvem, Hermes), trabalha numa cópia
própria e conversa com a central: **no começo, puxa; no fim, envia.**

É como um caderno que fica na sala dos professores: cada um tira uma cópia,
trabalha nela e, no fim do dia, devolve as páginas novas para o caderno. Quem
chega depois copia o caderno já com as páginas de todo mundo.

**O repositório é público:** qualquer pessoa vê e baixa tudo o que entra
nele, inclusive o que já saiu da pasta (fica no histórico). Por isso nada de
BIOS, jogo, save, dado de aluno, senha ou token.

---

## Os ramos

| Ramo | O que tem |
|---|---|
| `main` | A versão aprovada do ARENA. É a que aparece na página do GitHub |
| `auditoria` | O trabalho da auditoria 3 (outubro de 2026), em andamento. Entra no `main` no fim da auditoria (Fase 8) |

Depois da auditoria, o trabalho do dia a dia é no `main`.

---

## Uma vez em cada computador

1. **Git para Windows** instalado ([git-scm.com](https://git-scm.com)). Ele traz
   junto o login do GitHub (o Gerenciador de Credenciais do Git).
2. **Baixar o código:**

   ```
   git clone https://github.com/RafaParise/arena-console.git ARENA-unificado
   ```

   Numa pasta do ARENA que já existe e ainda não conhece o GitHub:

   ```
   git remote add origin https://github.com/RafaParise/arena-console.git
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
- **Confere antes de enviar** (`ferramentas\conferir_antes_de_publicar.py`):
  olha cada arquivo novo de cada commit que vai para o GitHub. BIOS, jogo,
  banco, save, conta do RPCN, e-mail de aluno ou institucional, senha ou
  token: **nada é enviado**, e ele diz qual arquivo e em qual commit.
- **Envia** os commits feitos aqui.

### O que ele NÃO faz (de propósito)

- **Não faz commit sozinho** do que ainda não tem commit: só mostra a lista.
  Commit é de quem fez o trabalho, com uma mensagem que diga o que mudou.
- Para mandar tudo mesmo assim, o professor pede, com a mensagem:

  ```
  SINCRONIZAR.bat enviar --tudo "o que mudou"
  ```

### No GitHub

O repositório tem uma regra, **"Proteger os ramos"**: ninguém consegue
**forçar** um envio (o que apaga o trabalho que já estava lá) nem **apagar** um
ramo. Envio normal funciona para todo mundo. Se um dia precisar mesmo forçar
(por exemplo, para tirar um arquivo do histórico), desligue a regra em
*Settings → Rules*, faça e ligue de novo.

**Por que assim** (o que aconteceu em 10 e 11/10/2026):

- Um script de sincronização juntava tudo o que estava na pasta num commit
  "Backup automático". Um assistente estava no meio de um trabalho (a Fase 5
  da auditoria), e esse trabalho foi parar num commit chamado "Documentação
  completa para sincronização", sem dizer o que mudou.
- Um `git pull` trocou o `.gitignore` do ARENA pelo modelo de Python do
  GitHub. Com isso, o próximo `git add -A` levaria BIOS, jogos e o banco dos
  recordes.
- Um assistente transformou a **pasta dos alunos** num repositório e tentou
  enviá-la ao GitHub com BIOS da Sony e da Sega e o banco dos recordes, por
  envio forçado, apagando arquivos no caminho. O GitHub recusou (arquivos
  grandes); os arquivos apagados foram devolvidos.

---

## Regras para os assistentes (Claude Code, Hermes e outros)

Estão também no `AGENTS.md`, na raiz:

1. **No começo, puxar** (`git pull --ff-only`, ou o `SINCRONIZAR.bat puxar`).
2. **O repositório é só este** (`ARENA-unificado`). **Nunca** `git init` na
   pasta dos alunos (`..\ARENA`), num pen drive ou em qualquer pasta com
   jogos, BIOS ou dados.
3. **Nunca `git add -A` nem `git add .`**: adicione só os arquivos que você
   mudou (`git add caminho\do\arquivo`). Outro assistente pode estar no meio
   de um trabalho na mesma pasta.
4. **Antes do commit**, `git status` e `git diff --staged`: arquivo que você
   não mexeu não é seu.
5. **Mensagem de commit que diga o que mudou e por quê**, em português.
6. **Antes de enviar**, `servidor\python\python.exe ferramentas\conferir_antes_de_publicar.py`
   (o `SINCRONIZAR.bat` já faz). **Nunca** `git push --force`.
7. **No fim, enviar** (`git push`), depois de atualizar a seção "Estado
   atual" do `CLAUDE.md`.
8. **Conflito:** juntar com cuidado. Nunca apagar o trabalho do outro para o
   seu passar. Nunca `git pull --allow-unrelated-histories` sem conferir o
   que vem junto.
9. **Nunca** forçar a entrada de dado do aluno, jogo, BIOS ou save
   (`git add -f`), nem gravar senha, token ou e-mail num arquivo do
   repositório.

---

## O que nunca vai para o GitHub

O `.gitignore` já barra: `dados\` (recordes, perfis, configuração de quem
usa), `BIOS\`, os jogos, os saves e estados, os emuladores e o RetroArch
inteiro, as coletas de máquina (`perfil\`), as cópias de segurança
(`backup\`) e todo `.zip`. E a conferência antes do envio pega o que
escapar do `.gitignore`.

O ARENA completo para baixar (com RetroArch e emuladores, sem BIOS e sem
jogos) vai na página **Releases**, como um `.zip` montado pelo
`ferramentas\montar_versao_alunos.py`.
