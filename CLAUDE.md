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
- **O repositório é só esta pasta.** Nunca `git init` na pasta dos alunos
  (`..\ARENA`) nem em pasta com jogos, BIOS ou dados.
- Sincronizar só com o `SINCRONIZAR.bat` (ou `git pull --ff-only` /
  `git push`). Ele confere o que vai junto antes de enviar
  (`ferramentas\conferir_antes_de_publicar.py`) e recusa BIOS, jogo, banco,
  save, e-mail institucional, senha e token. Nunca `git push --force` (o
  GitHub recusa).
- **O repositório é público** (`https://github.com/RafaParise/arena-console`):
  nada de e-mail, senha ou token em arquivo.

## Estado atual (resumo; o detalhe está em docs\RELATORIO-QUALIDADE.md)

Auditoria 3, ramo `auditoria` (no GitHub desde 11/10/2026). O `main` do
GitHub tem a versão aprovada (2026.10.03.2); a auditoria entra nele na
Fase 8. Fases 0 a 4 em commit. A Fase 5 (matriz de jogos) entrou no commit
`b2fdf44` junto com textos da Fase 7 (a mensagem dele fala de
sincronização, mas o conteúdo é esse); a acessibilidade da tela (Fase 7) no
`b2e45f8`. Faltam: fechar a Fase 5 (revisão independente), Fase 6
(portabilidade: rodada 14 de 14), o resto da Fase 7, a Fase 8 (relatório
final, rodada completa, juntar ao `main`, atualizar a versão dos alunos) e a
publicação completa (README, imagem, Release com o pacote sem BIOS).

Em 10 e 11/10/2026 outro assistente (Hermes) trocou o `.gitignore`, publicou
no GitHub um "ARENA" de exemplo e tentou enviar a pasta dos alunos (com BIOS
e o banco dos recordes) por envio forçado. Nada disso foi publicado; os
arquivos que ele apagou foram devolvidos (detalhe no `..\CLAUDE.md`).
