# Auditoria da tela e proposta de layout (10/11/2026)

Pedido do Rafael: auditar a tela e propor um layout novo (abas, distribuição), **o mesmo no computador, no celular e no
Chromebook**. A auditoria e os consertos de defeito já entraram (`78a469e`). O layout novo é escolha de gosto, então
fica como proposta: nada abaixo foi implementado.

## O que a auditoria achou e já foi consertado

Varredura automática em 6 larguras (360, 412, 768, 1024, 1280 e 1366 px) procurando página rolando de lado, botão fora
da tela e texto cortado, mais fotos de cada largura:

| Largura | Defeito | Conserto |
|---|---|---|
| 768 px (tablet de pé, Chromebook com a janela pela metade) | a página rolava de lado e o **Ajustes ficava fora da tela** | a fileira de botões quebra linha de verdade (`flex-shrink`) |
| 1366 px (notebook da escola) com apelido comprido | processador e memória no topo saíam como "Ryzen _" e "11,_" | aparecem inteiros ou somem, medido a cada mudança de tamanho |
| 768 a 1366 px | nomes da barra de consoles cortados ("Mega Drive, Master System e Ga...", "Todos os j...") | quebram em duas linhas; no celular as pílulas continuam numa linha |

Depois: 0 problemas nas 6 larguras, acessibilidade 10 de 10, navegadores 30 de 30.

## O que continua estranho (não é defeito, é desenho)

1. **Oito botões soltos no topo**, todos com o mesmo peso: o perfil (apelido), Amigos, Recordes, Conquistas,
   Biblioteca, Claro/Escuro, Enviar recordes e Ajustes. Três deles são do mesmo assunto (Recordes, Conquistas, Enviar
   recordes), e o tema claro/escuro ocupa um lugar de destaque que quase ninguém usa toda hora.
2. **No celular, o Ajustes fica escondido**: os oito botões viram uma faixa que rola para o lado e o último (Ajustes)
   começa fora da tela, sem dica de que há mais.
3. **Duas faixas que rolam de lado no celular** (botões e consoles), uma em cima da outra. Antes do primeiro jogo, o
   aluno já gastou um terço da tela.
4. **No computador, três colunas** (consoles, jogos e o painel do jogo escolhido): em 1366 px cabem só 3 cartões por
   linha.

## Proposta: as mesmas 5 abas em todo aparelho

```
Computador e Chromebook (abas no alto)          Celular (abas embaixo, ao alcance do polegar)
+---------------------------------------------+  +---------------------------+
| ARENA  [Jogos] [Amigos] [Placar]            |  | ARENA            (perfil) |
|        [Biblioteca] [Ajustes]      (perfil) |  | [Procurar jogo         ] |
+--------+-----------------------+------------+  | (Todos)(PS1)(SNES)(NES)> |
| Todos  | [Procurar jogo]       | painel do  |  | +--------+ +--------+    |
| PS1    | +----+ +----+ +----+  | jogo       |  | | jogo   | | jogo   |    |
| SNES   | |jogo| |jogo| |jogo|  | escolhido  |  | +--------+ +--------+    |
| ...    | +----+ +----+ +----+  |            |  |            ...            |
+--------+-----------------------+------------+  +---------------------------+
                                                  |Jogos|Amigos|Placar|Bib|Aj|
                                                  +---------------------------+
```

- **Jogos**: a lista de hoje (consoles, busca, Todos/Favoritos/Recentes, cartões).
- **Amigos**: igual a hoje (código de amigo, lista, conexões da rede). O Jogar Junto continua começando pelo cartão
  do jogo.
- **Placar**: Recordes, Conquistas e o "Enviar recordes", juntos numa aba só, com o número de pendentes na própria aba.
- **Biblioteca**: os jogos livres para baixar.
- **Ajustes**: igual a hoje.
- **O perfil** (apelido) vira um botão redondo no canto, e o **tema claro/escuro** vai para dentro dele (ou para
  Ajustes).

Ganhos: 5 abas em vez de 8 botões; no celular a barra de baixo é o padrão dos apps que o aluno já usa, nada fica
escondido e sobra uma faixa a menos no alto; a mesma palavra no mesmo lugar em todo aparelho, o que ajuda quem joga em
casa no celular e na escola no notebook.

Riscos: muda o lugar de tudo para quem já usa (os guias 1 a 6 e as fotos deles precisam acompanhar); os testes de tela
(`teste_acessibilidade_tela`, `teste_navegadores`, `teste_chromebook`) procuram os botões de hoje e terão de ser
ajustados; o guia 5 descreve o botão Amigos "do topo".

## O que o Rafael decide

1. **Topo de linha:** as 5 abas da proposta, ou manter os botões de hoje (os consertos de defeito já resolvem o que
   estava quebrado)?
2. **No celular:** abas embaixo (padrão do Android) ou em cima (igual ao computador)?
3. **Tema claro/escuro:** dentro do perfil, dentro de Ajustes, ou continua no topo?

Com as respostas, a mudança cabe numa sessão: tela, guias, testes de tela e fotos dos guias.
