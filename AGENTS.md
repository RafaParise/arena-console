# Instruções para agentes

Este arquivo existe para os agentes de programação que procuram `AGENTS.md`
(Codex, Hermes e outros). **As instruções do projeto ficam no
[`CLAUDE.md`](CLAUDE.md)**, na mesma pasta: leia o arquivo inteiro antes de
mudar qualquer coisa. Ele vale para qualquer agente, não só para o Claude.

O essencial, que nunca muda:

- Tudo em português do Brasil: respostas, código comentado, textos da tela,
  guias e mensagens de commit.
- Python puro (só a biblioteca padrão), sem `pip install`, sem senha de
  administrador, caminhos relativos (o ARENA roda de pen drive) e tudo
  funcionando sem internet.
- A régua de desempenho é o notebook mais fraco da escola (Celeron N5100,
  `docs/MAQUINA-ALVO.md`), não o computador de quem programa.
- Nunca apagar jogos, saves, BIOS, núcleos, memory cards nem a pasta `dados\`.
- Gravação de vídeo e transmissão ao vivo ficam desligadas de propósito
  (alunos menores de idade): não reativar.
- Antes de cada commit: `servidor\python\python.exe servidor\tests\run.py`
  (a bateria). Mudou a área de um teste de `testes\`? Rode o dele também.

## Trabalhar em mais de um lugar

O repositório do GitHub é a cópia central. Vários computadores, contas e
agentes trabalham no mesmo projeto, às vezes **na mesma pasta ao mesmo
tempo**. Então (detalhes em `docs/SINCRONIZAR-COM-O-GITHUB.md`):

1. **No começo:** `git pull --ff-only` (ou `SINCRONIZAR.bat puxar`).
2. **Nunca `git add -A` nem `git add .`**: adicione só os arquivos que você
   mudou. Outro agente pode estar no meio de um trabalho; em 10/10/2026 um
   script de sincronização juntou o trabalho pela metade de outro agente num
   commit com mensagem que não dizia o que era.
3. **Antes do commit:** `git status` e `git diff --staged`. Arquivo que você
   não mexeu não é seu.
4. **Mensagem de commit** em português, dizendo o que mudou e por quê.
5. **No fim:** atualizar a seção "Estado atual" do `CLAUDE.md` (acrescentar,
   não apagar o que outro escreveu), fazer o commit e `git push`.
6. **Conflito:** juntar com cuidado. Nunca apagar o trabalho do outro para o
   seu passar.
7. **O repositório é público:** nada de senha, token ou e-mail em arquivo, e
   nunca `git add -f` em dado do aluno, jogo, BIOS ou save.
