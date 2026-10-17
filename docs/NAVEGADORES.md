# A tela do ARENA em qualquer navegador — item 11 (17/10/2026)

O pedido do Rafael (15/10/2026): o ARENA "deve ser possível rodar em
qualquer navegador padrão que o aluno tenha, e deve ser perfeitamente
funcional assim como é no Edge", com "testes para provar o desempenho em
outros navegadores", "compatível e otimizado com todos".

## O que mudou

- **A tela abre no navegador padrão do aluno** (`servidor\navegadores.py`,
  commit `7352fa8`). Antes, o ARENA procurava o Edge e o Chrome em caminhos
  fixos, nessa ordem, mesmo com outro navegador como padrão. Agora vale o
  escolhido em **Ajustes → Simples → Abrir a tela em**; sem escolha, o padrão
  do computador (o registro do Windows diz qual é, sem administrador); sem
  padrão conhecido, o primeiro que achar (o Edge primeiro).
- **Como abre:** Edge, Chrome, Brave, Vivaldi e Chromium como janela de
  aplicativo (sem abas nem barra de endereço); Firefox (e LibreWolf,
  Waterfox, Floorp) numa janela nova, porque o Firefox tirou o modo
  aplicativo em 2021; Opera numa janela nova.
- **O código da tela foi conferido:** nada exclusivo do Chromium. As barras
  de rolagem têm o jeito padrão (o Firefox lê) e o `-webkit-` (o Chromium e o
  Safari leem); `color-mix`, `:has()` e o corte de texto em duas linhas
  existem nos três motores atuais.

## Como foi testado

`testes\teste_navegadores.py` (commit `7a70549`): numa **cópia** do ARENA
com os 10 jogos livres, o mesmo roteiro em cada navegador, numa tela de
1366×768 como a do notebook da escola. O roteiro é um JavaScript só, igual
em todos: clica e escolhe pela própria página, como o aluno.

Os navegadores, sem instalar nada no Windows (`testes\navegadores_de_teste.py`):

| Navegador | De onde | Como o teste fala com ele |
|---|---|---|
| Microsoft Edge | o do Windows | protocolo de depuração do Chrome (CDP) |
| Chrome for Testing 155 | o .zip do Google para testes | CDP |
| Firefox 158 | o instalador oficial, conferido pela lista SHA-256 da Mozilla e pela assinatura digital, só extraído | WebDriver BiDi (o padrão do W3C) |

## Resultado: 30 de 30

As 10 conferências passaram nos três navegadores, sem janela e com janela:

1. a tela fica pronta e mostra os 10 jogos;
2. nenhum erro de JavaScript;
3. nada vaza para os lados;
4. Ajustes abre, e as 5 abas mostram o painel;
5. a Escala da tela tem as 5 escolhas, e trocar grava no servidor;
6. "Abrir a tela em" lista o padrão e os instalados;
7. a busca filtra a lista;
8. o jogo clicado mostra os detalhes;
9. o tema troca;
10. a Biblioteca abre.

As fotos da tela saem iguais nos três.

## O desempenho (com janela, como o aluno vê)

Medido com a janela de verdade, depois de 30 s parado (o perfil novo de
teste faz o navegador trabalhar no primeiro minuto) e por 10 s
(`docs\navegadores_com_janela_bruto.json`):

| Navegador | Tela pronta | Fundo animado | A página parada | O navegador inteiro |
|---|---|---|---|---|
| Edge | 0,57 s | 60 quadros/s | 0,9% de um núcleo, 178 MB | 289 MB em 8 processos |
| Chrome for Testing | 0,51 s | 60 quadros/s | 1,1% de um núcleo, 223 MB | 309 MB em 10 processos |
| Firefox | 0,89 s | 60 quadros/s | 1,2% de um núcleo, 425 MB* | 784 MB em 12 processos |

\* No Firefox, "a página" são todos os processos de conteúdo, inclusive os
que ele já deixa abertos de reserva: ele separa cada site em processos
próprios.

**O que isso quer dizer:** a tela do ARENA funciona igual e pesa o mesmo no
processador nos três (cerca de 1% de um núcleo parada). O Firefox abre um
pouco mais devagar e usa **2,5 vezes a memória** do Edge. No notebook da
escola (7,7 GB, com 3,8 GB livres para tudo), o Edge e o Chrome são a melhor
escolha; com o Firefox como padrão, o ARENA funciona, só gasta mais
memória. A explicação na tela (Ajustes → Simples) diz isso.

## Achados no caminho

- **O proxy Headroom (kit de IA do professor) escuta na porta 8787**, a
  mesma da cópia do ARENA dos testes. A conferência antiga perguntava ao
  servidor e via o "404" dele como porta livre: os testes que usam a cópia
  conversavam com o proxy. Consertado em `testes\copia_do_arena.py` (a porta
  é testada de verdade; se estiver ocupada, usa outra).
- **Sem janela, o processador não compara navegadores:** cada um desenha de
  um jeito. E o Edge com perfil novo gastou 20% de um núcleo no primeiro
  minuto (componentes e índices do perfil), não por causa do ARENA.
- No Windows, o Firefox abre por um processo lançador que inicia o
  navegador de verdade e sai (`testes\firefox_bidi.py`, `pids`).

## O que ficou de fora

- **Safari:** só existe no Mac e no iPhone, fora do ARENA (Windows). O motor
  dele, o WebKit, fica para o teste no Linux (item 13).
- O teste não roda os jogos (isso é dos testes do RetroArch): confere a tela.
