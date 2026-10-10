# CLAUDE.md (dentro do repositório)

**Não substitua este arquivo inteiro.** Ele é lido por todo assistente que
abre o ARENA (Claude Code no computador ou na nuvem, Hermes e outros):
acrescente na seção certa e mantenha o que os outros escreveram.

## Onde estão as instruções do projeto

A memória completa do ARENA (o que é, para quem, as restrições que não se
negociam, as decisões e o porquê de cada uma, o histórico de defeitos e o
"Estado atual") ainda está no `CLAUDE.md` da pasta de cima (`..\CLAUDE.md`),
fora do git. Ela vem para cá, inteira, quando o ARENA for publicado no
GitHub, no fim da auditoria 3.

Até lá, valem as regras do `AGENTS.md` (nesta pasta) e do
`docs\SINCRONIZAR-COM-O-GITHUB.md`. As que mais importam agora:

- **Nunca `git add -A` nem `git add .`**: só os arquivos que você mudou.
  Mais de um assistente trabalha nesta pasta, às vezes ao mesmo tempo.
- Sincronizar só com o `SINCRONIZAR.bat` (ou `git pull --ff-only` /
  `git push`). Os scripts antigos (`sync_github.py`, `sincronizador.py`,
  `SINCRONIZAR_ARENA.bat`) foram trocados por ele em 10/10/2026: juntavam
  tudo num commit "Backup automático" e procuravam a pasta sem o acento.
- O repositório vai ser público: nada de e-mail, senha ou token em arquivo.

## Estado atual (resumo; o detalhe está em docs\RELATORIO-QUALIDADE.md)

Auditoria 3, ramo `auditoria`. Fases 0 a 4 em commit. A Fase 5 (matriz de
jogos) entrou no commit `b2fdf44` junto com textos da Fase 7 (a mensagem
dele fala de sincronização, mas o conteúdo é esse); a acessibilidade da tela
(Fase 7) no `b2e45f8`. Faltam: fechar a Fase 5 (revisão independente),
Fase 6 (portabilidade), o resto da Fase 7, a Fase 8 (relatório final, rodada
completa, juntar ao `main`, atualizar a versão dos alunos) e a publicação no
GitHub.
