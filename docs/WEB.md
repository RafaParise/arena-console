# O ARENA na internet (versão web) — auditoria 4 (22/10/2026)

**Endereço:** https://rafaparise.github.io/arena-console/

O pedido do Rafael (22/10/2026): o APK não instalou no celular de um aluno
e, à noite, no Galaxy A12 dele (Android 12): "Como o app não é compatível com
seu smartphone, ele não foi instalado". A resposta foi preparar "um formato
que funcione para antigo e novo" — "pode preparar por favor, eu autorizo".

**Resposta curta:** é o mesmo ARENA do Chromebook (a mesma tela, o mesmo
RetroArch 1.22.2 compilado para o navegador), publicado no GitHub Pages.
Abre no Chrome de qualquer celular, tablet ou computador, sem instalar nada,
e "Adicionar à tela inicial" deixa como app, que abre sem internet depois.
Não depende do Android nem do processador: o celular de 32 bits (o mais
provável no A12) e o aparelho que não aceita APK de fora abrem igual.

## Para o aluno (no celular)

1. Abra o endereço no **Chrome** (ou no navegador do celular, atualizado).
2. Na primeira vez, use o Wi-Fi: a tela tem uns 3 MB, e cada console baixa o
   emulador dele (de 0,1 a 26 MB) na primeira vez que abre um jogo. Depois
   fica tudo guardado no aparelho.
3. Menu do Chrome (⋮) → **Adicionar à tela inicial** (ou **Instalar app**):
   aparece o ícone do ARENA, que abre em tela cheia, sem a barra do
   navegador, e funciona sem internet.
4. Os jogos livres que vêm com o ARENA já estão na lista.
5. Para um jogo seu: toque em **Guardar um jogo** (no aviso do alto ou na
   faixa dos consoles) e escolha o arquivo (o que você baixou fica na pasta
   Download). Ele fica guardado no aparelho, dentro do navegador.

## O controle na tela

Aparece sozinho em tela de toque e some quando um controle de verdade é
ligado (Bluetooth ou cabo) ou quando alguém usa o teclado.

| Na tela | O que faz | No Windows |
|---|---|---|
| Direcional, A, B, X, Y, L, R, START, SELECT | os botões do console | as teclas de jogo de sempre |
| MENU | abre o menu do RetroArch | Esc |
| SALVAR | salva o momento do jogo | F2 |
| CARREGAR | volta ao momento salvo | F4 |
| SAIR (toque duas vezes) | fecha o jogo e volta à lista | F10 |

De pé, SELECT e START ficam na altura do L e do R; deitado, embaixo, no meio.

## O que tem e o que não tem

É o modo do Chromebook: a lista do que tem e do que não tem está em
`docs\CHROMEBOOK.md`, seção "O que tem e o que não tem no Chromebook". Em
resumo: os consoles que o RetroArch do navegador roda (do Atari ao PS1, sem
N64, PSP nem os de fora: PS2, GameCube, PS3 e Xbox 360); sem Jogar Junto, sem
Biblioteca e sem Enviar recordes. Os recordes, os saves e o perfil ficam no
aparelho.

**No celular** (desde a auditoria 4): os consoles viram uma faixa que rola
para o lado no alto, a grade de jogos fica com a largura toda, o console sem
jogo sai da faixa e o aviso do alto oferece "Guardar um jogo" no lugar de
"Escolher a pasta do ARENA" (o Chrome do Android pode não escolher pasta;
onde escolhe, a opção continua em Ajustes → Máquina).

## Privacidade

Tudo fica no aparelho (o banco do navegador): jogos guardados, saves,
recordes, perfil. O ARENA não manda nada para lugar nenhum. O GitHub, como
qualquer site, recebe o endereço de internet de quem abre a página.

## Atualizar a versão web (professor)

O site é o ramo `gh-pages` do repositório, montado a partir do código:

```
git worktree add %LOCALAPPDATA%\ARENA-site gh-pages      (uma vez só)
servidor\python\python.exe ferramentas\montar_site.py %LOCALAPPDATA%\ARENA-site
```

Depois, na pasta `%LOCALAPPDATA%\ARENA-site`: `git add` dos arquivos, commit
e `git push` (sem `--force`). O GitHub publica sozinho em um ou dois
minutos. Na próxima vez que o aluno abrir, o celular percebe a tela nova (o
service worker leva a "impressão digital" do conteúdo) e a troca; os
núcleos só são baixados de novo se mudarem.

Antes de publicar: `servidor\python\python.exe testes\teste_versao_web.py`
(monta o site numa pasta temporária, imita o Chrome do Android e confere o
layout, o toque, o Guardar um jogo e o SAIR; 19 conferências).

## Limites do GitHub Pages

Arquivo de até 100 MB (o maior do ARENA tem 25,6 MB; o montador recusa
acima de 95 MB) e site de até 1 GB (o ARENA tem 92 MB). A banda tem um
limite "suave" de 100 GB por mês: dá para uns mil celulares baixarem tudo
pela primeira vez no mês. Fonte: docs.github.com, "GitHub Pages limits"
[Certo: conferido em 22/10/2026; o limite de 100 MB por arquivo é o do próprio GitHub].
