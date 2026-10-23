# Relatório — Auditoria 4 do ARENA (22 e 23/10/2026)

> Quarta rodada, pedida pelo Rafael em 22/10/2026 (11h40, de fora de casa)
> e ampliada à noite. Os pedidos estão inteiros, sem resumir, no
> `docs\PLANO-AUDITORIA.md` (seção "Auditoria 4"). Começou pelo Android, como
> pedido, passou pela versão web, pela tela, pela escala da imagem e pelo
> pacote, e termina com as ações manuais e as opções para aparelho antigo,
> que o Rafael pediu para decidir no fim.

Ramo: `auditoria-4`, a partir do `main` `8cf3371` (a versão 2026.10.22).
Máquina das medições: Ryzen 5 5600G com a Vega integrada, tela 1440×900 —
**não é a máquina alvo** (Celeron N5100, `docs\MAQUINA-ALVO.md`). Android:
o emulador do AOSP (Android 15, 1080×2400). **Nada foi juntado ao `main` nem
publicado como versão nova**: isso espera o Rafael. A versão web foi
publicada no GitHub Pages, com a autorização dele ("pode preparar por favor,
eu autorizo").

## Resumo

| Pedido | O que mudou | Commit | Conferido |
|---|---|---|---|
| Sair do jogo no Android sem fechar o app | Botões MENU e SAIR no controle de toque; "Fechar" volta ao ARENA | `d05ff26` | No emulador: SAIR duas vezes volta à tela do ARENA |
| Sem jogos: passo a passo e achar as ROMs baixadas | "Procurar jogos baixados" (Download, WhatsApp, Telegram; pergunta antes de mover) | `07f0491` | No emulador: achou 2, levou 1 para a pasta certa |
| Segurança (Claude Security) | F3: outro app do celular por 127.x pulava o segredo; F4: capa por http | `c95688f`, `38306a7` | Testes novos; bateria |
| APK que não instala (A12, Android 12) | Versão web no GitHub Pages, com controle de toque e layout de celular | `333c0ca`, `665126a`, `f083ab3`, `4970dd3` | `teste_versao_web.py` 19/19; o endereço publicado num celular simulado |
| "A tela não estica até a borda" | Formato da imagem: Automático estica o 4:3 até a borda (até 16:9), Esticar, Do console | `477e05a` | Foto da tela: borda a borda em 1440×900 |
| Atualizar copiando o zip por cima, sem perder nada | A configuração do RetroArch e dos emuladores vai no pacote só como modelo | `cc7f714` | `teste_atualizar_por_cima.py` 5/5 (12.397 arquivos) |
| Android: botões na tela sim ou não; "PC" no celular | Botões na tela: Automático, Sempre, Nunca; "aparelho" no lugar de "computador" | `f148a9c` | `test_android` 44 OK; APK de teste no emulador |
| Perceber queda de desempenho e ajustar sozinho | Desempenho que aprende: o console no limite joga um degrau mais leve | `0808dd9` | Medição real de um processo ocupado |
| As funções do Lossless Scaling | Anime4K e Inteiro (as que faltavam); mapa Lossless → ARENA no guia 3 | `b2f8418` | Foto da tela: Anime4K compila e enche a tela; Inteiro com borda |
| Instalar no A12 pelo cabo | `ferramentas\instalar_no_celular.py` (32 bits → abre a versão web) | (este relatório) | Teste de unidade; no emulador |

Bateria do servidor ao fim: **651 testes, OK** no Windows e **651 OK no Linux** (o Debian 13 do
contêiner do WSL; um teste do Java ME era só do Windows e reprovava lá desde 18/10: corrigido).
Versão web: 19/19. Chromebook: 41/41. Atualizar por cima: 5/5. Android no emulador: inteiro;
estresse (Monkey de 3.000 toques, matar e voltar, girar, pouca memória, sem rede): 5/5.

---

## Android (Fases 1 e 4)

### Achados e o que foi feito

| # | Achado | Gravidade | Situação |
|---|---|---|---|
| A1/A2 | O Android pedia permissão sem explicar | média | Corrigido: janela "Antes de começar" (`d05ff26`) |
| A3/A5 | Consoles sem jogo e consoles que só rodam no computador enchendo a lista | baixa | No celular, o console sem jogo sai da faixa (`665126a`) |
| A4 | A pasta de jogos ficava privada sem a permissão | média | Explicado na janela de permissões e em Ajustes → Máquina |
| A6 | O teclado cobre a tela deitada ao digitar o apelido | baixa | Registrado (o Enter funciona) |
| A7 | A tela dizia "computador" no celular | baixa | Corrigido: "aparelho" (`f148a9c`) |
| A8 | O Voltar do aparelho não faz nada no jogo | média | Contornado: MENU e SAIR no controle de toque; o Voltar depende do RetroArch |
| A9/A10 | O menu do RetroArch (RGUI) é pequeno e erra o toque de pé | média | Contornado: o menu anda pelo direcional do controle de toque |
| A11 | A barra de navegação cobre os botões de baixo em alguns aparelhos | baixa | Registrado: conferir num aparelho de verdade |
| A12 | O controle de toque saía esticado de pé | média | Corrigido (`input_overlay_auto_rotate`) |
| A14 | A tela no celular de pé ficava apertada | alta | Corrigido: faixa de consoles e grade na largura toda (`665126a`) |

### Pedidos de 22/10 à noite

- **Botões na tela** (Ajustes → Simples, só no Android): Automático (some com
  um controle de verdade), Sempre, Nunca.
- **Até 8 jogadores e o Jogar Junto**: já seguiam as regras do Windows. Os
  jogadores de cada jogo vêm do `servidor\multitap.json`; o `--host` e o
  `--connect` chegam ao RetroArch do app pelo remendo `arena-args.patch`; o
  anúncio da partida chega pelo roteador do celular ou pelo mesmo Wi-Fi
  porque o serviço segura o "multicast" do Wi-Fi (`MulticastLock`). **Falta
  conferir com dois celulares de verdade** (roteiro no fim).
- **Pela internet, cada um em casa**: fica para depois, como o Rafael
  permitiu ("se for implementação grande deixa para depois"). Precisaria de
  um servidor de passagem (o do libretro ou um da escola) e de cuidado com
  alunos menores: a pesquisa dos apps lembrou que nenhum app de sala de aula
  deveria expor a partida numa lista pública.

### Teste no emulador

O APK de teste com as mudanças desta noite (`montar_android.py --abi x86_64
--teste`, 226 MB) passou inteiro no `testes\teste_android.py` (22/10, 23h20):
instala e ganha a permissão, acha a pasta do ARENA sozinho, a lista tem os
jogos, o jogo de CHIP-8 abre no RetroArch nativo e fecha com o F10 duas
vezes, a partida a dois chega ao RetroArch do Android (`--host --port
55435`), "Usar a pasta do app" reabre o servidor com o segredo novo, e o
mesmo pedido de fora da tela é recusado (403). O aviso de "app sem resposta"
que apareceu uma vez é do emulador lento (desenho por software, 2 núcleos):
o teste toca em "Esperar", como já fazia. Fotos em
`%TEMP%\teste_android_fotos`.

### Estresse (novo: `testes\teste_android_estresse.py`)

No mesmo emulador, em 23/10 (`docs\auditoria4\android_estresse_bruto.json`),
**5 de 5**:

| Passo | Resultado |
|---|---|
| Monkey: 3.000 toques, deslizes e teclas ao acaso dentro do app (a tela do ARENA e o RetroArch) | foi até o fim em 154 s, sem queda e sem travamento do ARENA |
| Matar e voltar (o Android fecha o app à força) | abre de novo |
| Girar a tela (deitado e de pé) | a tela do ARENA continua na frente |
| Pouca memória (o aviso de memória crítica do Android a cada processo do app) | continua vivo |
| Sem rede (Wi-Fi e dados desligados) | abre de novo, offline |

Achado no próprio teste: a primeira rodada parou em 93 toques porque o
Monkey desiste no primeiro "não responde" de qualquer app, e o do sistema
apareceu no emulador lento. Com o Monkey indo até o fim e anotando só as
quedas e os travamentos do ARENA, a rodada mede o que interessa. O teste
agora reprova se o Monkey não chegar a 90% dos toques.

---

## Versão web (o APK que não instala)

Pedido: "precisa ter ou um formato que funcione para antigo e novo". O
Galaxy A12 do Rafael (Android 12) disse: "Como o app não é compatível com
seu smartphone, ele não foi instalado". O mais provável **[Provável]** é o
Android de 32 bits: o APK do ARENA só tem as versões de 64 bits (arm64-v8a e
x86_64). A ferramenta `instalar_no_celular.py` confirma isso no aparelho
(`ro.product.cpu.abilist`).

**Publicada:** https://rafaparise.github.io/arena-console/ (ramo
`gh-pages`, `docs\WEB.md`). É o modo do Chromebook, com:

- controle de toque no jogo (direcional, A/B/X/Y, L/R, START/SELECT, MENU,
  SALVAR, CARREGAR e SAIR com dois toques);
- layout de celular (faixa de consoles, grade na largura toda);
- "Guardar um jogo" (o arquivo baixado fica no aparelho);
- service worker com a "impressão digital" do conteúdo (o celular pega a
  tela nova sozinho) e os núcleos em guarda própria;
- dois defeitos achados antes de publicar: o `.git` do ramo entrava na lista
  do celular e derrubaria a instalação offline (`f083ab3`); e o número da
  versão sozinho não fazia o celular buscar a tela nova.

---

## Imagem: "a tela não estica até a borda" e o Lossless Scaling

**A causa.** O RetroArch sempre usou a proporção do console: o 4:3 fica com
faixas pretas dos lados numa tela larga. O "como fazia antes" é o Lossless
Scaling do Rafael esticando até a borda; desde 16/10, o perfil "ARENA" que o
ARENA grava nele usava o modo "Aspect ratio".

**O que mudou:** o **Formato da imagem** (Ajustes → Simples). No Automático,
os consoles de TV e de computador (4:3) esticam até a borda da tela larga,
até 16:9 (no celular deitado, de 20:9, o 4:3 até a borda ficaria largo
demais). Portátil de tela quadrada, fliperama, WonderSwan e Vectrex (que
têm jogo em pé) ficam no formato deles. Vale no RetroArch (Windows, Linux,
Android e navegador), no PCSX2, no Dolphin, no RPCS3 e no Lossless.
Conferido com foto da tela: o MSX de borda a borda em 1440×900.

**O Lossless Scaling.** É pago e fechado: abrir o código dele para copiar
algoritmo fere a licença, e o repositório é público. As funções dele entram
por técnicas abertas:

| No Lossless (3.2.2) | No ARENA |
|---|---|
| LS1 (fechado) | o FSR da AMD faz o mesmo papel |
| FSR, SharpBilinear, Nearest | Nítido (FSR), Pixel nítido, Original |
| Anime4K, Integer | **novos**: Anime4K e Inteiro (`b2f8418`) |
| xBR | o Suave (ScaleFX): pesa menos (+5,7 contra +8,8 pontos de placa) |
| NIS, SGSR | não vêm no RetroArch 1.22; o FSR cobre |
| Fullscreen / Aspect ratio | o Formato da imagem |
| LSFG (geração de quadros) | só no Lossless de quem comprou (o ARENA continua usando o programa de verdade); em Python puro não cabe, e em emulador ajuda pouco: o jogo lento continua lento |

**Desempenho que aprende** ("deve saber identificar queda de desempenho"):
durante o jogo, a thread mais ocupada do emulador e a placa de vídeo. Ficou
no limite? O console joga um degrau mais leve na próxima vez, só no
Automático; três partidas folgadas devolvem o degrau (Ajustes → Máquina). Por
que não o FPS: o RetroArch 1.22 só põe o FPS no título da janela com o
contador desenhado em cima do jogo, e o registro dele não guarda a média
(conferido nesta rodada).

---

## O pacote: atualizar por cima sem perder nada

O pacote completo levava a configuração de verdade do RetroArch e dos
emuladores: copiado por cima, trocava a de quem usa. Agora ela vai como
modelo (`.padrao`), e o ARENA só usa o modelo na primeira vez
(`cc7f714`). O teste monta o pacote de verdade, "instala", "usa" (perfil,
recordes, jogos, BIOS, saves, estados, cartões de memória e configuração
mudada) e copia o pacote inteiro por cima: nada de quem usa mudou. O guia 6
diz agora que o completo também serve para atualizar. **Os pacotes
completos até a 2026.10.22 ainda levam a configuração de verdade**: para
eles, o pacote de atualização.

---

## Segurança (Fase 3)

- **F3** (Claude Security): no Android, outro app do mesmo celular entrava no
  servidor do ARENA por 127.0.0.2 sem o segredo. Corrigido (`c95688f`).
- **F4**: a capa do Xbox 360 vinha por http; os downloads agora são só por
  HTTPS (`38306a7`).
- As duas varreduras grandes pararam no limite da sessão (5 de 44 e 6 de 20
  leitores): o que voltou está corrigido acima. A revisão das mudanças desta
  noite (o diff de `333c0ca` até `b2f8418`, 35 arquivos) foi feita duas
  vezes: por um modelo gratuito de auditoria do kit do Rafael (Nemotron 3
  Ultra, pelo OmniRoute) e aqui, arquivo por arquivo. Nenhum achado real: a
  rota nova (`/api/desempenho/zerar`) é só deste computador e não mexe em
  caminho; os valores que vão para a configuração dos emuladores saem de
  listas fechadas; o modelo `.padrao` nunca grava por cima do que existe; o
  service worker só guarda o que o próprio site serve. Um reforço pequeno: o
  nome do APK baixado do GitHub pela ferramenta do celular vira só nome de
  arquivo, nunca uma pasta. **Recomendado na próxima sessão:** a varredura
  do Claude Security das mudanças do ramo (a de "scan changes"), mais barata
  que a do repositório inteiro.

---

## Ideias dos apps de sucesso (Fase 2)

A engenharia reversa do **Lemuroid** (código e APK 1.17.0, GPL-3.0: só as
ideias, nenhum código copiado) e a pesquisa sobre RetroArch, ES-DE, Dolphin
e PPSSPP (feita pelos modelos gratuitos do kit, conferida aqui) deram estas
ideias para as próximas rodadas, da mais útil para a sala:

| Ideia | De onde | Esforço |
|---|---|---|
| Salvar sozinho quando o app vai para o fundo (uma ligação no meio do jogo) | Lemuroid | M |
| Slots de save com a foto do momento e a data | Lemuroid | M |
| MENU do toque abrindo só se segurar meio segundo (sem abrir sem querer) | Lemuroid | P |
| Início com "Continuar jogando" e "Favoritos" em fileiras | Lemuroid | M |
| Segurar o cartão do jogo abre as opções (continuar, recomeçar, favoritar) | Lemuroid | M |
| A transparência do controle de toque ajustável | Lemuroid, RetroArch | P |
| Reconhecer o jogo pelo cabeçalho e pelo CRC do zip, sem descompactar | Lemuroid | G |
| Ajuste por jogo (não só por console) | Dolphin, PPSSPP | M |

---

## O que não deu e por quê

- **Geração de quadros (LSFG)**: proprietária; em Python puro, sem instalar
  nada, não cabe. O ARENA usa o Lossless de verdade quando ele existe.
- **FPS medido por dentro**: o RetroArch 1.22 não dá sem desenhar na tela
  (ver acima); o desempenho que aprende mede a carga.
- **Jogar Junto pela internet**: para depois (grande, e pede cuidado com
  menores).
- **APK de 32 bits**: o Rafael pediu para decidir a ordem no fim (abaixo).

---

## Opções para aparelho antigo (para o Rafael decidir a ordem)

O pedido: "a ideia é do ARENA ser também a salvação de versões de Android
mais antigas [...] que qualquer computador mesmo desatualizado possa usar o
ARENA [...] só no final junto com as etapas manuais vem essa opção para eu
verificar a melhor ordem de implementação".

| # | Opção | Para quem | Esforço | Recomendo |
|---|---|---|---|---|
| 1 | **Versão web** (pronta e publicada) | Qualquer celular, tablet ou computador com Chrome, Edge ou Firefox atualizado (no Android, do 8 em diante **[Provável]**) | feito | Já |
| 2 | **APK leve de 32 bits**: o RetroArch de 32 bits (armeabi-v7a) com a tela do ARENA no modo "servidor dentro da página" (o mesmo do Chromebook, que o app já tem de reserva), **sem o Python** — que é o que falta em 32 bits | O A12 e os celulares baratos de 32 bits, com o RetroArch nativo (mais rápido que o navegador) | M | 2º |
| 3 | **Computador antigo pelo navegador**: abrir o `ARENA-CHROMEBOOK.html` no Firefox ESR ou no Chrome que a máquina ainda tiver (Windows 7, por exemplo) | PC com Windows 7 ou 8 | P (testar) | 3º |
| 4 | **ARENA "legado" para Windows antigo/32 bits**: Python antigo (3.8, o último para Windows 7) e RetroArch de 32 bits | PC que não roda o ARENA de hoje nem um navegador novo | G | Só se a 3 não servir |
| 5 | **APK com a conta de desenvolvedor do Google** (gratuita, até 20 aparelhos; ou a paga, US$ 25) | Instalar o APK nos celulares dos alunos depois da verificação de desenvolvedor do Android **[Provável: no Brasil desde 30/09/2026]** | P (manual) | Quando for distribuir APK |

---

## Ações manuais (ficam com o Rafael)

1. **Testar a versão web no A12**: abrir https://rafaparise.github.io/arena-console/
   no Chrome, Wi-Fi ligado; menu → "Adicionar à tela inicial".
2. **Instalar no A12 pelo cabo** (se for de 64 bits; se for de 32, a
   ferramenta abre a versão web e explica): ligar a Depuração USB (Configurações
   → Sobre o telefone → Informações do software → 7 toques em "Número de
   compilação" → Opções do desenvolvedor → Depuração USB), ligar o cabo,
   aceitar "Permitir depuração USB" e rodar
   `servidor\python\python.exe ferramentas\instalar_no_celular.py` (ou pedir
   ao Claude). Ela mostra o que vai copiar (BIOS, saves e os jogos que o
   celular roda) e pergunta antes.
3. **No seu computador**: Ajustes → Simples → **Formato da imagem** (o
   Automático já estica até a borda) e Ajustes → Máquina → **Desempenho que
   aprende**. Se quiser o jogo esticado também no Lossless, deixe ele fechado
   ao abrir o jogo (o ARENA ajusta o perfil "ARENA").
4. **Jogar Junto com dois celulares**: um liga o roteador do celular, o
   outro entra nele; os dois abrem o ARENA → Amigos → Jogar junto. Contar se
   a partida aparece e abre nos dois.
5. **Aprovar**: juntar o ramo `auditoria-4` ao `main` e publicar a versão
   nova (o pacote completo passa a poder ser copiado por cima sem perder
   nada).
6. **Escolher a ordem das opções para aparelho antigo** (tabela acima).
7. Se for distribuir APK aos alunos: a conta de desenvolvedor do Google
   (gratuita até 20 aparelhos).
