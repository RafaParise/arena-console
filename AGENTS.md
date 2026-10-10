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
agentes trabalham no mesmo projeto, então:

1. **No começo:** `git pull` (puxar o que os outros enviaram).
2. **No fim:** atualizar a seção "Estado atual" do `CLAUDE.md`, fazer o
   commit e `git push` (enviar).
3. Se duas pessoas mexeram no mesmo arquivo, resolver o conflito com
   cuidado: nunca apagar o trabalho do outro para o seu passar.
