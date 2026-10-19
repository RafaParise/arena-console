# O papel de parede do ARENA

Documento de referência do papel de parede da area de trabalho, feito a
partir da cena do proprio ARENA (`launcher\galaxy-background.js`).

## O que e'

A cena de galaxia que ja roda no launcher (o canvas logico 160×90) virada
um papel de parede do Windows, ampliado **por bloco inteiro**, sem perder a
nitidez da pixel art.

```
servidor\python\python.exe ferramentas\papel_de_parede.py
```

Isso gera o PNG, confere a ampliacao e aplica no Windows. Para gerar
tambem o video animado:

```
servidor\python\python.exe ferramentas\papel_de_parede.py --animado
```

Outras opcoes: `--tamanhos 1440x900,1920x1080` (gera varios tamanhos),
`--aplicar` (so aplica, sem gerar de novo), `--sem-aplicar` (so gera).

## Por que nao ampliado do GIF

O `arena-escuro.gif` da raiz tem 960×480 (é 2:1: a cena 160×80 ampliada
6×) e o `arena-escuro-curto.gif` tem 1280×640 (também 2:1). Ampliar esses
arquivos cortaria a cena e esticaria o ceu.

O papel de parede é gerado da fonte de verdade: o proprio JavaScript do
launcher, renderizado sem janela e lido ponto a ponto.

## A matemática do redimensionamento

Duas regras, e a segunda é a que segura a qualidade:

1. **Escala inteira.** Cada ponto da cena vira um bloco de N×N pixels de
   uma cor só. N é sempre inteiro: 9 na tela de 1440×900, 12 na de
   1920×1080. Nada de reescalonamento suave, que inventaria cores que não
   existem (dois pontos vizinhos virariam uma cor intermediária).
2. **A cena não é esticada.** A escala é a mesma na horizontal e na
   vertical.

A segunda regra tem uma consequência prática. A cena nasce 160×90 (16:9) e
a tela deste computador é 1440×900 (16:10): esticar 90 linhas em 100 daria
9× de um lado e 10× do outro, e a cena deformaria.

A solução é calcular a **altura lógica** a partir da proporção da tela
(160 dividido pela proporção) e deixar o chão descer junto com o céu:

| Tela | Cena | Escala | O que acontece |
|---|---|---|---|
| 1440×900 | 160×100 | 9×9 | o céu ganha 10 linhas de estrelas; serra, pistas e planeta descem 10 |
| 1920×1080 | 160×90 | 12×12 | a cena original, sem mexer em nada |

O que está preso a um número fixo (`planeta.y`, `PISTA`, `PISTA_KART`) desce
pela mesma quantidade, então as distâncias entre as coisas continuam as
mesmas. O que é do céu (aurora, galáxia, estrelas) fica onde está. A serra
das montanhas já é relativa à altura, então desce sozinha.

A altura lógica fica entre 80 e 120, para o céu não ficar nem curto demais
nem alto demais.

## A conferência (a prova de que ficou perfeito)

A ferramenta **relê o PNG gravado** e compara cada linha com a linha da
origem repetida. Se um único pixel estiver fora do bloco, ela reprova e
não gera o arquivo final.

O teste `testes\teste_papel_de_parede.py` faz a mesma coisa e ainda
confere que a conferência **reprova** uma imagem estragada (senão ela não
serviria de prova de nada).

## O que acontece se o launcher mudar

A ferramenta troca a marca `const W = 160, H = 90;` no JavaScript e as
âncoras do chão. Se algum desses trechos mudar no launcher, a ferramenta
**recusa** (erro claro) em vez de gerar um papel de parede errado em
silêncio. O teste `test_cena_tem_a_marca_esperada` vigia isso.

## No Windows

A aplicação usa `SystemParametersInfoW` com `SPI_SETDESKWALLPAPER`, mais o
registro (`Wallpaper`, `WallpaperStyle=10`, `TileWallpaper=0`). Sem
administrador, sem instalar nada.

A imagem fica em `%LOCALAPPDATA%\ARENA\arena-papel-de-parede.png`.

**O Windows não anima vídeo como papel de parede.** O `.mp4` (ida e volta,
para fechar em loop sem o pulo do fim) é material complementar: para ele
ficar animado na tela é preciso um visualizador externo (Lively, Wallpaper
Engine). O PNG é o papel de parede que funciona sozinho.

## Arquivos

| Arquivo | O que é |
|---|---|
| `ferramentas\papel_de_parede.py` | a ferramenta (só biblioteca padrão) |
| `testes\teste_papel_de_parede.py` | os testes da matemática e do PNG |
| `docs\imagens\arena-papel-de-parede-1440x900.png` | o papel de parede desta tela |
| `docs\imagens\arena-papel-de-parede-1920x1080.png` | a variante 16:9 |
| `docs\imagens\arena-papel-de-parede-1440x900.mp4` | a versão animada (complementar) |
